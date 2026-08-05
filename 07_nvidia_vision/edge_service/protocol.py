"""PLC/vision contract validation independent of any model or OPC UA library."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag
import math
import re


class ProtocolError(ValueError):
    pass


class ProcessingState(IntEnum):
    NOT_READY = 0
    READY = 1
    CAPTURE_ACKNOWLEDGED = 2
    PROCESSING = 3
    RESULT_COMPLETE = 4
    FAULT = 5


class ResultDisposition(IntEnum):
    NONE = 0
    PASS = 1
    HOLD = 2
    FAIL = 3
    FAULT = 4


class ReasonBits(IntFlag):
    NONE = 0
    BOTTLE_MISSING = 1 << 0
    BOTTLE_MISALIGNED = 1 << 1
    UNDERFILL = 1 << 2
    OVERFILL = 1 << 3
    SEVERE_FOAM = 1 << 4
    SPILL_OR_LEAK = 1 << 5
    LOW_CONFIDENCE = 1 << 6
    CAMERA_UNHEALTHY = 1 << 7
    MODEL_UNAVAILABLE = 1 << 8
    TIMEOUT_OR_LATE = 1 << 9
    MALFORMED_OR_CONTRADICTORY = 1 << 10
    IDENTITY_MISMATCH = 1 << 11
    TRANSACTION_MISMATCH = 1 << 12
    COMMUNICATIONS_OR_HEARTBEAT = 1 << 13
    QUEUE_SATURATED = 1 << 14
    RECIPE_CHANGED = 1 << 15


@dataclass(frozen=True)
class InspectionRequest:
    inspection_id: int
    recipe_id: int
    expected_bottles: int
    target_fill_level: float
    plc_heartbeat: int
    session_epoch: int = 1
    maintenance_mode: bool = False
    expected_dataset_id: str = ""
    expected_calibration_id: str = ""


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
    capture_ack_id: int = 0
    processing_state: int = int(ProcessingState.RESULT_COMPLETE)
    disposition: int = int(ResultDisposition.NONE)
    reason_bits: int = 0
    confidence: float = 0.0
    dataset_id: str = ""
    calibration_id: str = ""
    capture_timestamp_utc_ms: int = 0
    inference_timestamp_utc_ms: int = 0
    publication_timestamp_utc_ms: int = 0
    processing_time_ms: int = 0
    service_healthy: bool = True
    camera_healthy: bool = False
    model_loaded: bool = False
    maintenance_active: bool = False
    diagnostic_code: int = 0
    queue_depth: int = 0


MIN_TARGET_FILL_LEVEL = 0.1
MAX_TARGET_FILL_LEVEL = 1.0
HEARTBEAT_TIMEOUT_MS = 1000
MODEL_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
CONTROLLED_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
UINT16_MAX = 0xFFFF
UINT32_MAX = 0xFFFFFFFF
UINT64_MAX = 0xFFFFFFFFFFFFFFFF
KNOWN_REASON_MASK = sum(int(reason) for reason in ReasonBits)


def validate_model_identity(identity: tuple[str, str] | None) -> tuple[str, str]:
    if (type(identity) is not tuple or len(identity) != 2
            or type(identity[0]) is not str or MODEL_ID_RE.fullmatch(identity[0]) is None
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
    if type(request.maintenance_mode) is not bool:
        raise ProtocolError("maintenance mode is not a PLC BOOL value")
    for name, value in (("dataset", request.expected_dataset_id),
                        ("calibration", request.expected_calibration_id)):
        if type(value) is not str or (value and CONTROLLED_ID_RE.fullmatch(value) is None):
            raise ProtocolError(f"expected {name} identity is malformed")
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
    if type(result.capture_ack_id) is not int or not 0 <= result.capture_ack_id <= UINT32_MAX:
        raise ProtocolError("capture acknowledgement is outside UDINT bounds")
    if result.capture_ack_id != request.inspection_id:
        raise ProtocolError("terminal result requires exact capture acknowledgement")
    if type(result.processing_state) is not int or result.processing_state not in set(ProcessingState):
        raise ProtocolError("processing state is outside the controlled enumeration")
    if type(result.disposition) is not int or result.disposition not in set(ResultDisposition):
        raise ProtocolError("result disposition is outside the controlled enumeration")
    if type(result.reason_bits) is not int or not 0 <= result.reason_bits <= UINT32_MAX:
        raise ProtocolError("reason mask is outside DWORD bounds")
    if result.reason_bits & ~KNOWN_REASON_MASK:
        raise ProtocolError("reason mask contains undefined bits")
    if type(result.confidence) not in {int, float} or not math.isfinite(result.confidence) or not 0.0 <= result.confidence <= 1.0:
        raise ProtocolError("confidence is outside the normalized range")
    for name, value in (("dataset", result.dataset_id), ("calibration", result.calibration_id)):
        if type(value) is not str or (value and CONTROLLED_ID_RE.fullmatch(value) is None):
            raise ProtocolError(f"result {name} identity is malformed")
    for name, value in (
        ("capture timestamp", result.capture_timestamp_utc_ms),
        ("inference timestamp", result.inference_timestamp_utc_ms),
        ("publication timestamp", result.publication_timestamp_utc_ms),
    ):
        if type(value) is not int or not 1 <= value <= UINT64_MAX:
            raise ProtocolError(f"{name} is outside the controlled range")
    if not (result.capture_timestamp_utc_ms <= result.inference_timestamp_utc_ms
            <= result.publication_timestamp_utc_ms):
        raise ProtocolError("result timestamps are not monotonically ordered")
    if type(result.processing_time_ms) is not int or not 0 <= result.processing_time_ms <= UINT32_MAX:
        raise ProtocolError("processing time is outside UDINT bounds")
    if result.processing_time_ms != result.inference_time_ms:
        raise ProtocolError("processing time does not match the controlled inference duration")
    if any(type(flag) is not bool for flag in (
        result.service_healthy, result.camera_healthy, result.model_loaded,
        result.maintenance_active,
    )):
        raise ProtocolError("result health flags are not PLC BOOL values")
    if type(result.diagnostic_code) is not int or not 0 <= result.diagnostic_code <= UINT32_MAX:
        raise ProtocolError("diagnostic code is outside UDINT bounds")
    if type(result.queue_depth) is not int or not 0 <= result.queue_depth <= UINT16_MAX:
        raise ProtocolError("queue depth is outside UINT bounds")
    if result.processing_state != ProcessingState.RESULT_COMPLETE:
        raise ProtocolError("terminal result requires complete processing state")
    if result.disposition == ResultDisposition.NONE:
        raise ProtocolError("terminal result requires an explicit disposition")
    if (not result.service_healthy or not result.camera_healthy or not result.model_loaded
            or result.maintenance_active):
        raise ProtocolError("terminal result contradicts service, camera, model or maintenance health")
    if result.disposition != ResultDisposition.PASS and result.reason_bits == 0:
        raise ProtocolError("non-PASS terminal result requires a controlled reason bit")
    if request.expected_dataset_id and result.dataset_id != request.expected_dataset_id:
        raise ProtocolError("result dataset identity does not match the PLC expectation")
    if request.expected_calibration_id and result.calibration_id != request.expected_calibration_id:
        raise ProtocolError("result calibration identity does not match the PLC expectation")
    if result.bottle_1_pass and result.fill_1_status != 2:
        raise ProtocolError("bottle 1 pass claim contradicts fill status")
    if result.bottle_2_pass and result.fill_2_status != 2:
        raise ProtocolError("bottle 2 pass claim contradicts fill status")
    pass_claim = result.bottle_1_pass and result.bottle_2_pass
    if pass_claim and (result.leak_or_spill or result.low_confidence or result.vision_warning or result.vision_fault):
        raise ProtocolError("pass claim contradicts a blocking quality condition")
    if result.disposition == ResultDisposition.PASS and (
            not pass_claim or result.reason_bits != 0 or not result.service_healthy
            or not result.camera_healthy or not result.model_loaded):
        raise ProtocolError("PASS disposition contradicts quality, reason or health fields")
    if result.disposition == ResultDisposition.FAULT and not result.vision_fault:
        raise ProtocolError("FAULT disposition requires the fault quality flag")
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
