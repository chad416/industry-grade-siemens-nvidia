"""Fail-closed edge-service core.

An OPC UA adapter and a real inference backend are deliberately not claimed.  Until a
signed model bundle is loaded, ``ready`` remains false and no inspection is accepted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from protocol import (
    InspectionRequest,
    InspectionResult,
    HEARTBEAT_TIMEOUT_MS,
    ProtocolError,
    validate_model_identity,
    validate_request,
    validate_result,
)

class Backend(Protocol):
    @property
    def controlled_identity(self) -> tuple[str, str] | None: ...
    def infer(self, request: InspectionRequest) -> InspectionResult: ...


@dataclass
class ServiceState:
    ready: bool = False
    busy: bool = False
    result_valid: bool = False
    last_inspection_id: int = 0
    last_plc_heartbeat: int = 0
    last_accepted_plc_heartbeat: int = 0
    vision_heartbeat: int = 0
    warning: str = "NO CONTROLLED MODEL LOADED"
    fault: str = ""
    heartbeat_last_change_ms: int | None = None


class VisionService:
    def __init__(self, backend: Backend | None = None, heartbeat_timeout_ms: int = HEARTBEAT_TIMEOUT_MS) -> None:
        self.backend = backend
        self.heartbeat_timeout_ms = heartbeat_timeout_ms
        self.state = ServiceState()
        identity = backend.controlled_identity if backend is not None else None
        try:
            validate_model_identity(identity)
            self.state.ready = True
        except ProtocolError:
            self.state.ready = False
        if self.state.ready:
            self.state.warning = ""

    def tick(self, plc_heartbeat: int, now_ms: int) -> None:
        self.state.vision_heartbeat += 1
        if plc_heartbeat > self.state.last_plc_heartbeat:
            self.state.last_plc_heartbeat = plc_heartbeat
            self.state.heartbeat_last_change_ms = now_ms
        elif self.state.heartbeat_last_change_ms is None:
            self.state.heartbeat_last_change_ms = now_ms
        elif now_ms - self.state.heartbeat_last_change_ms >= self.heartbeat_timeout_ms:
            self.state.ready = False
            self.state.fault = "PLC heartbeat timeout"

    def inspect(self, request: InspectionRequest) -> InspectionResult:
        self.state.result_valid = False
        if not self.state.ready or self.backend is None:
            raise ProtocolError("service is not ready: controlled model unavailable")
        expected_identity = validate_model_identity(self.backend.controlled_identity)
        if request.plc_heartbeat < self.state.last_plc_heartbeat:
            self.state.fault = "request PLC heartbeat is older than the observed counter"
            self.state.ready = False
            raise ProtocolError(self.state.fault)
        try:
            validate_request(request, self.state.last_inspection_id, self.state.last_accepted_plc_heartbeat)
        except ProtocolError as exc:
            self.state.fault = str(exc)
            self.state.ready = False
            raise
        self.state.busy = True
        try:
            result = self.backend.infer(request)
            validate_result(request, result, expected_identity)
            self.state.last_inspection_id = request.inspection_id
            self.state.last_accepted_plc_heartbeat = request.plc_heartbeat
            self.state.result_valid = True
            return result
        except Exception as exc:
            self.state.fault = str(exc)
            self.state.ready = False
            raise
        finally:
            self.state.busy = False
