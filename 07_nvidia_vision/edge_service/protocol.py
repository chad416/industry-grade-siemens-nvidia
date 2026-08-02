"""PLC/vision contract validation independent of any model or OPC UA library."""
from __future__ import annotations

from dataclasses import dataclass
import math
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
    session_epoch: int = 1


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
    session_epoch: int = 1


MIN_TARGET_FILL_LEVEL = 0.1
MAX_TARGET_FILL_LEVEL = 1.0
HEARTBEAT_TIMEOUT_MS = 1000
MODEL_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
UINT16_MAX = 0xFFFF
UINT32_MAX = 0xFFFFFFFF


def validate_model_identity(identity: tuple[str, str] | None) -> tuple[str, str]:
    if (type(identity) is not tuple or len(identity) != 2
            or type(identity[0]) is not str or not 1 <= len(identity[0]) <= 32
            or type(identity[1]) is not str or MODEL_HASH_RE.fullmatch(identity[1]) is None):
        raise ProtocolError("controlled model identity/hash is absent or malformed")
    return identity


def validate_request_fields(expected_bottles: int, target_fill_level: float) -> None:
    if type(expected_bottles) is not int or expected_bottles != 2:
        raise ProtocolError("production contract requires exactly two bottles")
    if type(target_fill_level) not in {int, float} or not math.isfinite(target_fill_level) or not MIN_TARGET_FILL_LEVEL <= target_fill_level <= MAX_TARGET_FILL_LEVEL:
        raise ProtocolError("target fill level is outside controlled bounds")


def validate_request(request: InspectionRequest, previous_id: int, previous_heartbeat: int) -> None:
    if type(request.inspection_id) is not int or not 1 <= request.inspection_id <= UINT32_MAX:
        raise ProtocolError("inspection ID is outside nonzero PLC UDINT bounds")
    if request.inspection_id <= previous_id:
        raise ProtocolError("inspection ID is not strictly monotonic")
    if type(request.recipe_id) is not int or not 0 <= request.recipe_id <= UINT16_MAX:
        raise ProtocolError("recipe ID is outside PLC UINT bounds")
    if type(request.session_epoch) is not int or not 1 <= request.session_epoch <= UINT32_MAX:
        raise ProtocolError("session epoch is outside nonzero PLC UDINT bounds")
    if type(request.plc_heartbeat) is not int or not 0 <= request.plc_heartbeat <= UINT32_MAX:
        raise ProtocolError("PLC heartbeat is outside UDINT bounds")
    if previous_id != 0 and not heartbeat_advance(previous_heartbeat, request.plc_heartbeat):
        raise ProtocolError("PLC heartbeat is stale")
    validate_request_fields(request.expected_bottles, request.target_fill_level)


def validate_result(
    request: InspectionRequest,
    result: InspectionResult,
    expected_identity: tuple[str, str],
) -> None:
    if result.result_id != request.inspection_id:
        raise ProtocolError("result ID does not match pending inspection")
    if result.session_epoch != request.session_epoch:
        raise ProtocolError("result session epoch does not match pending inspection")
    if type(result.result_id) is not int or not 1 <= result.result_id <= UINT32_MAX:
        raise ProtocolError("result ID is outside nonzero PLC UDINT bounds")
    if type(result.session_epoch) is not int or not 1 <= result.session_epoch <= UINT32_MAX:
        raise ProtocolError("result session epoch is outside nonzero PLC UDINT bounds")
    if any(type(flag) is not bool for flag in (result.bottle_1_pass, result.bottle_2_pass, result.leak_or_spill, result.low_confidence, result.vision_warning, result.vision_fault)):
        raise ProtocolError("result quality flags are not PLC BOOL values")
    if type(result.fill_1_status) is not int or type(result.fill_2_status) is not int or result.fill_1_status not in {0, 1, 2, 3} or result.fill_2_status not in {0, 1, 2, 3}:
        raise ProtocolError("fill status is outside the controlled enumeration")
    if type(result.inference_time_ms) is not int or not 0 <= result.inference_time_ms <= UINT32_MAX:
        raise ProtocolError("inference time is outside UDINT bounds")
    if result.bottle_1_pass and result.fill_1_status != 2:
        raise ProtocolError("bottle 1 pass claim contradicts fill status")
    if result.bottle_2_pass and result.fill_2_status != 2:
        raise ProtocolError("bottle 2 pass claim contradicts fill status")
    pass_claim = result.bottle_1_pass and result.bottle_2_pass
    if pass_claim and (result.leak_or_spill or result.low_confidence or result.vision_warning or result.vision_fault):
        raise ProtocolError("pass claim contradicts a blocking quality condition")
    validate_model_identity((result.model_id, result.model_hash))
    if (result.model_id, result.model_hash.lower()) != (expected_identity[0], expected_identity[1].lower()):
        raise ProtocolError("result model identity does not match the controlled backend")


def quality_pass(result: InspectionResult) -> bool:
    return (result.bottle_1_pass and result.bottle_2_pass and
            result.fill_1_status == 2 and result.fill_2_status == 2 and
            not result.leak_or_spill and not result.low_confidence and not result.vision_warning and not result.vision_fault)


def heartbeat_advance(previous: int, current: int) -> bool:
    """RFC-1982-style 32-bit serial advance; wrap is valid, regression is not."""
    delta = (current - previous) & 0xFFFFFFFF
    return 0 < delta <= 0x7FFFFFFF
