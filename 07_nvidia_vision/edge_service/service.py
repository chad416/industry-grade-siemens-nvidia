"""Fail-closed edge-service core.

An OPC UA adapter and a real inference backend are deliberately not claimed.  Until a
signed model bundle is loaded, ``ready`` remains false and no inspection is accepted.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Protocol

from protocol import (
    InspectionRequest,
    InspectionResult,
    HEARTBEAT_TIMEOUT_MS,
    ProtocolError,
    validate_model_identity,
    validate_request,
    validate_result,
    heartbeat_advance,
    UINT32_MAX,
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
    published_result_id: int = 0
    diagnostic_code: str = "NO_CONTROLLED_MODEL"
    session_epoch: int = 0
    last_acknowledged_result_id: int = 0
    session_synchronized: bool = False


class VisionService:
    def __init__(self, backend: Backend | None = None, heartbeat_timeout_ms: int = HEARTBEAT_TIMEOUT_MS, inference_timeout_ms: int = 1000, clock_ms=None) -> None:
        self.backend = backend
        self.heartbeat_timeout_ms = heartbeat_timeout_ms
        self.inference_timeout_ms = inference_timeout_ms
        self.clock_ms = clock_ms or (lambda: time.monotonic_ns() // 1_000_000)
        self.state = ServiceState()
        self.events: list[dict] = []
        self.session_identity: tuple[str, str] | None = None
        self._validated_identity: tuple[str, str] | None = None
        self._refresh_backend_readiness()

    def _refresh_backend_readiness(self) -> None:
        try:
            identity = self.backend.controlled_identity if self.backend is not None else None
            self._validated_identity = validate_model_identity(identity)
            self.state.ready = self.state.session_synchronized
        except Exception:
            self._validated_identity = None
            self.state.ready = False
            self.state.warning = "NO CONTROLLED MODEL LOADED"
            self.state.diagnostic_code = "NO_CONTROLLED_MODEL"
            return
        if self.state.ready:
            self.state.warning = ""
            self.state.fault = ""
            self.state.diagnostic_code = "OK"
        else:
            self.state.warning = "AWAITING DISABLED SESSION SYNCHRONIZATION"
            self.state.diagnostic_code = "SESSION_SYNC_REQUIRED"

    def begin_session(self, session_epoch: int) -> None:
        if type(session_epoch) is not int or not 1 <= session_epoch <= UINT32_MAX:
            self._fault("SESSION_INVALID", "session epoch is outside nonzero UDINT bounds")
            raise ProtocolError(self.state.fault)
        if not self.state.session_synchronized:
            raise ProtocolError("disabled session synchronization is required before READY")
        if self.state.session_epoch == session_epoch:
            return
        self._fault("SESSION_SYNC_REQUIRED", "session change requires disabled synchronization")
        raise ProtocolError(self.state.fault)

    def reset(
        self,
        *,
        disabled: bool,
        session_epoch: int | None = None,
        observed_inspection_id: int = 0,
        observed_ack_id: int = 0,
        observed_plc_heartbeat: int = 0,
    ) -> None:
        if not disabled or self.state.busy:
            raise ProtocolError("service reset requires VISION_ENABLE low and no inference in progress")
        for name, value in (
            ("inspection identifier", observed_inspection_id),
            ("acknowledgement", observed_ack_id),
            ("PLC heartbeat", observed_plc_heartbeat),
        ):
            if type(value) is not int or not 0 <= value <= UINT32_MAX:
                raise ProtocolError(f"observed {name} is outside PLC UDINT bounds")
        if observed_ack_id > observed_inspection_id:
            raise ProtocolError("observed acknowledgement cannot exceed the PLC inspection identifier")
        if session_epoch is None:
            session_epoch = self.state.session_epoch
        if type(session_epoch) is not int or not 1 <= session_epoch <= UINT32_MAX:
            raise ProtocolError("disabled reset requires a nonzero PLC session epoch")
        if self.state.session_epoch and session_epoch != self.state.session_epoch and not heartbeat_advance(self.state.session_epoch, session_epoch):
            raise ProtocolError("session epoch did not advance")
        self.state.session_epoch = session_epoch
        self.state.session_synchronized = True
        self.state.result_valid = False
        self.state.published_result_id = 0
        # The PLC-owned counters are the restart baseline.  A cold edge process may
        # never reopen ID 1 in an unchanged session or accept an old heartbeat.
        self.state.last_inspection_id = observed_inspection_id
        self.state.last_acknowledged_result_id = observed_ack_id
        self.state.last_accepted_plc_heartbeat = observed_plc_heartbeat
        self.state.last_plc_heartbeat = observed_plc_heartbeat
        self.state.heartbeat_last_change_ms = None
        self.state.fault = ""
        self._refresh_backend_readiness()
        if self.state.ready:
            self.session_identity = self._validated_identity
        self.events.append({"event":"service_rearmed","session_epoch":self.state.session_epoch,"inspection_id":self.state.last_inspection_id,"acknowledgement_id":self.state.last_acknowledged_result_id,"plc_heartbeat":self.state.last_plc_heartbeat})

    def _fault(self, code: str, message: str, *, invalidate_publication: bool = True, inspection_id: int | None = None, plc_heartbeat: int | None = None) -> None:
        self.state.ready = False
        self.state.fault = message
        self.state.diagnostic_code = code
        if invalidate_publication:
            self.state.result_valid = False
            self.state.published_result_id = 0
        self.events.append({"event":"fault","code":code,"message":message,"session_epoch":self.state.session_epoch,"inspection_id":self.state.last_inspection_id if inspection_id is None else inspection_id,"plc_heartbeat":self.state.last_plc_heartbeat if plc_heartbeat is None else plc_heartbeat})

    def tick(self, plc_heartbeat: int, now_ms: int, session_epoch: int = 1) -> None:
        if type(plc_heartbeat) is not int or not 0 <= plc_heartbeat <= UINT32_MAX or type(now_ms) is not int or now_ms < 0:
            self._fault("PLC_HEARTBEAT_RANGE", "PLC heartbeat is outside UDINT bounds", plc_heartbeat=plc_heartbeat)
            return
        self.state.vision_heartbeat = (self.state.vision_heartbeat + 1) & UINT32_MAX
        if not self.state.session_synchronized:
            return
        self.begin_session(session_epoch)
        if self.state.heartbeat_last_change_ms is None:
            self.state.last_plc_heartbeat = plc_heartbeat
            self.state.heartbeat_last_change_ms = now_ms
        elif heartbeat_advance(self.state.last_plc_heartbeat, plc_heartbeat):
            self.state.last_plc_heartbeat = plc_heartbeat
            self.state.heartbeat_last_change_ms = now_ms
        elif plc_heartbeat != self.state.last_plc_heartbeat:
            self._fault("PLC_HEARTBEAT_REGRESSION", "PLC heartbeat regressed", plc_heartbeat=plc_heartbeat)
        elif now_ms - self.state.heartbeat_last_change_ms >= self.heartbeat_timeout_ms:
            self._fault("PLC_HEARTBEAT_TIMEOUT", "PLC heartbeat timeout", plc_heartbeat=plc_heartbeat)

    def acknowledge_result(self, result_id: int) -> None:
        if type(result_id) is not int or not 0 <= result_id <= UINT32_MAX:
            self._fault("RESULT_ACK_RANGE", "result acknowledgement is outside PLC UDINT bounds",
                        invalidate_publication=False)
            raise ProtocolError(self.state.fault)
        if self.state.result_valid and result_id == self.state.last_acknowledged_result_id and result_id != self.state.published_result_id:
            self.events.append({"event":"prior_result_acknowledgement_poll_ignored","session_epoch":self.state.session_epoch,"inspection_id":result_id,"plc_heartbeat":self.state.last_plc_heartbeat})
            return
        if not self.state.result_valid and result_id == self.state.last_acknowledged_result_id and result_id != 0:
            self.events.append({"event":"result_acknowledgement_poll_ignored","session_epoch":self.state.session_epoch,"inspection_id":result_id,"plc_heartbeat":self.state.last_plc_heartbeat})
            return
        if not self.state.result_valid or result_id != self.state.published_result_id:
            self._fault("RESULT_ACK_MISMATCH", "result acknowledgement does not match publication", inspection_id=result_id)
            raise ProtocolError(self.state.fault)
        self.state.result_valid = False
        self.state.published_result_id = 0
        self.state.last_acknowledged_result_id = result_id
        self.events.append({"event":"result_acknowledged","session_epoch":self.state.session_epoch,"inspection_id":result_id,"plc_heartbeat":self.state.last_plc_heartbeat})

    def inspect(self, request: InspectionRequest) -> InspectionResult:
        if not self.state.session_synchronized:
            raise ProtocolError("service is not ready: disabled session synchronization required")
        self.begin_session(request.session_epoch)
        if self.state.result_valid:
            self._fault("RESULT_UNACKNOWLEDGED", "previous result remains unacknowledged", invalidate_publication=False, inspection_id=request.inspection_id, plc_heartbeat=request.plc_heartbeat)
            raise ProtocolError(self.state.fault)
        if not self.state.ready or self.backend is None:
            raise ProtocolError("service is not ready: controlled model unavailable")
        try:
            expected_identity = validate_model_identity(self.backend.controlled_identity)
            if self.session_identity is None or (expected_identity[0], expected_identity[1].lower()) != (self.session_identity[0], self.session_identity[1].lower()):
                raise ProtocolError("controlled model identity changed after session synchronization")
        except Exception as exc:
            self._fault("MODEL_IDENTITY_INVALID", str(exc), inspection_id=request.inspection_id, plc_heartbeat=request.plc_heartbeat)
            raise ProtocolError(str(exc)) from exc
        if self.state.heartbeat_last_change_ms is not None and request.plc_heartbeat != self.state.last_plc_heartbeat:
            self._fault("REQUEST_HEARTBEAT_OLD", "request PLC heartbeat is older than the observed counter", inspection_id=request.inspection_id, plc_heartbeat=request.plc_heartbeat)
            raise ProtocolError(self.state.fault)
        try:
            validate_request(request, self.state.last_inspection_id, self.state.last_accepted_plc_heartbeat)
        except ProtocolError as exc:
            self._fault("REQUEST_INVALID", str(exc), inspection_id=request.inspection_id, plc_heartbeat=request.plc_heartbeat)
            raise
        self.state.busy = True
        start_ms = self.clock_ms()
        try:
            result = self.backend.infer(request)
            elapsed_ms = self.clock_ms() - start_ms
            if elapsed_ms >= self.inference_timeout_ms:
                raise ProtocolError("inference deadline exceeded; delayed result discarded")
            validate_result(request, result, expected_identity)
            self.state.last_inspection_id = request.inspection_id
            self.state.last_accepted_plc_heartbeat = request.plc_heartbeat
            self.state.result_valid = True
            self.state.published_result_id = result.result_id
            self.events.append({"event":"result_published","session_epoch":request.session_epoch,"inspection_id":result.result_id,"plc_heartbeat":request.plc_heartbeat,"duration_ms":elapsed_ms,"model_id":result.model_id,"model_hash":result.model_hash})
            return result
        except Exception as exc:
            self._fault("INSPECTION_FAILED", str(exc), inspection_id=request.inspection_id, plc_heartbeat=request.plc_heartbeat)
            raise
        finally:
            self.state.busy = False
