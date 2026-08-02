"""PLC/vision contract validation independent of any model or OPC UA library."""
from __future__ import annotations

from dataclasses import dataclass
import re


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class InspectionRequest:
    inspection_id: int
    recipe_id: int
    expected_bottles: int
    target_fill_level: float
    plc_heartbeat: int


@dataclass(frozen=True)
class InspectionResult:
    result_id: int
    bottle_1_pass: bool
    bottle_2_pass: bool
    fill_1_status: int
    fill_2_status: int
    leak_or_spill: bool
    low_confidence: bool
    vision_warning: bool
    vision_fault: bool
    inference_time_ms: int
    model_id: str
    model_hash: str


MIN_TARGET_FILL_LEVEL = 0.1
MAX_TARGET_FILL_LEVEL = 1.0
HEARTBEAT_TIMEOUT_MS = 1000
MODEL_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def validate_model_identity(identity: tuple[str, str] | None) -> tuple[str, str]:
    if identity is None or not identity[0] or MODEL_HASH_RE.fullmatch(identity[1]) is None:
        raise ProtocolError("controlled model identity/hash is absent or malformed")
    return identity


def validate_request_fields(expected_bottles: int, target_fill_level: float) -> None:
    if expected_bottles != 2:
        raise ProtocolError("production contract requires exactly two bottles")
    if not MIN_TARGET_FILL_LEVEL <= target_fill_level <= MAX_TARGET_FILL_LEVEL:
        raise ProtocolError("target fill level is outside controlled bounds")


def validate_request(request: InspectionRequest, previous_id: int, previous_heartbeat: int) -> None:
    if request.inspection_id <= previous_id:
        raise ProtocolError("inspection ID is not strictly monotonic")
    if request.plc_heartbeat <= previous_heartbeat:
        raise ProtocolError("PLC heartbeat is stale")
    validate_request_fields(request.expected_bottles, request.target_fill_level)


def validate_result(
    request: InspectionRequest,
    result: InspectionResult,
    expected_identity: tuple[str, str],
) -> None:
    if result.result_id != request.inspection_id:
        raise ProtocolError("result ID does not match pending inspection")
    if result.fill_1_status not in {0, 1, 2, 3} or result.fill_2_status not in {0, 1, 2, 3}:
        raise ProtocolError("fill status is outside the controlled enumeration")
    if result.inference_time_ms < 0:
        raise ProtocolError("negative inference time")
    pass_claim = result.bottle_1_pass and result.bottle_2_pass
    if pass_claim and (result.fill_1_status != 2 or result.fill_2_status != 2):
        raise ProtocolError("pass claim contradicts fill status")
    if pass_claim and (result.leak_or_spill or result.low_confidence or result.vision_fault):
        raise ProtocolError("pass claim contradicts a blocking quality condition")
    validate_model_identity((result.model_id, result.model_hash))
    if (result.model_id, result.model_hash.lower()) != (expected_identity[0], expected_identity[1].lower()):
        raise ProtocolError("result model identity does not match the controlled backend")


def quality_pass(result: InspectionResult) -> bool:
    return (result.bottle_1_pass and result.bottle_2_pass and
            result.fill_1_status == 2 and result.fill_2_status == 2 and
            not result.leak_or_spill and not result.low_confidence and not result.vision_fault)
