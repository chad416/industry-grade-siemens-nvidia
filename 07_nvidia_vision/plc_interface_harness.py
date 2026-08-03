from dataclasses import dataclass
import sys
from pathlib import Path

EDGE_SERVICE_DIR = Path(__file__).resolve().parent / "edge_service"
if str(EDGE_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(EDGE_SERVICE_DIR))
from protocol import HEARTBEAT_TIMEOUT_MS, heartbeat_advance


@dataclass(frozen=True)
class VisionResult:
    valid: bool
    result_id: int
    bottle_1_pass: bool
    bottle_2_pass: bool
    fill_1_status: int = 2
    fill_2_status: int = 2
    leak_or_spill: bool = False
    low_confidence: bool = False
    warning: bool = False
    fault: bool = False
    session_epoch: int = 1
    model_id: str = "TEST-BACKEND-NOT-A-MODEL"
    model_hash: str = "a" * 64


class VisionContract:
    """Protocol oracle for interface tests; it is not PLC execution or DeepStream runtime."""

    def __init__(self, timeout_ms: int = 1000, heartbeat_timeout_ms: int = HEARTBEAT_TIMEOUT_MS):
        self.timeout_ms = timeout_ms
        self.heartbeat_timeout_ms = heartbeat_timeout_ms
        self.pending_id = None
        self.trigger_ms = 0
        self.last_heartbeat = None
        self.last_heartbeat_change_ms = 0
        self.last_issued_id = 0
        self.session_epoch = 1
        self.hold_latched = False
        self.result_must_clear = False
        self.result_ack_id = 0
        self.expected_model = ("TEST-BACKEND-NOT-A-MODEL", "a" * 64)

    def trigger(self, inspection_id: int, now_ms: int, ready: bool, busy: bool, session_epoch: int = 1) -> str:
        if session_epoch != self.session_epoch:
            if not heartbeat_advance(self.session_epoch, session_epoch):
                self.hold_latched = True
                return "HOLD_SESSION"
            self.session_epoch = session_epoch
            self.pending_id = None
            self.last_issued_id = 0
            self.hold_latched = False
            self.result_must_clear = False
            self.result_ack_id = 0
            self.last_heartbeat = None
            self.last_heartbeat_change_ms = 0
        if inspection_id == 0 or inspection_id <= self.last_issued_id:
            self.hold_latched = True
            return "HOLD_NONMONOTONIC_ID"
        if self.pending_id is not None or self.result_must_clear or not ready or busy or self.hold_latched:
            return "HOLD_NOT_READY"
        self.pending_id = inspection_id
        self.last_issued_id = inspection_id
        self.trigger_ms = now_ms
        return "TRIGGERED"

    def evaluate(self, now_ms: int, ready: bool, heartbeat: int, result: VisionResult | None) -> str:
        if self.last_heartbeat is None:
            self.last_heartbeat = heartbeat
            self.last_heartbeat_change_ms = now_ms
        elif heartbeat_advance(self.last_heartbeat, heartbeat):
            self.last_heartbeat = heartbeat
            self.last_heartbeat_change_ms = now_ms
        elif heartbeat != self.last_heartbeat:
            self.pending_id = None
            self.hold_latched = True
            return "HOLD_HEALTH"
        if not ready or now_ms - self.last_heartbeat_change_ms >= self.heartbeat_timeout_ms:
            self.pending_id = None
            return "HOLD_HEALTH"
        if self.pending_id is None:
            if result is not None and result.valid:
                if self.result_must_clear and result.result_id == self.result_ack_id:
                    return "WAIT_RESULT_CLEAR"
                self.result_ack_id = result.result_id
                self.result_must_clear = True
                self.hold_latched = True
                return "HOLD_UNSOLICITED_RESULT"
            return "IDLE"
        elapsed = now_ms - self.trigger_ms
        if elapsed > self.timeout_ms or (elapsed == self.timeout_ms and (result is None or not result.valid)):
            self.pending_id = None
            self.hold_latched = True
            self.result_must_clear = True
            return "HOLD_TIMEOUT"
        if result is None or not result.valid:
            return "WAIT"
        # Transport acknowledgement is independent of product acceptance.  Every
        # complete publication is acknowledged so a rejected/stale payload clears.
        self.result_ack_id = result.result_id
        self.result_must_clear = True
        if result.result_id != self.pending_id:
            self.pending_id = None
            self.hold_latched = True
            return "HOLD_STALE_ID"
        if result.session_epoch != self.session_epoch:
            self.pending_id = None
            self.hold_latched = True
            return "HOLD_SESSION"
        self.pending_id = None
        accepted = (result.bottle_1_pass and result.bottle_2_pass and
                    result.fill_1_status == 2 and result.fill_2_status == 2 and
                    not result.leak_or_spill and not result.low_confidence and not result.warning and not result.fault and
                    (result.model_id, result.model_hash.lower()) == (self.expected_model[0], self.expected_model[1].lower()))
        return "PASS" if accepted else "HOLD_QUALITY"

    def acknowledgement(self) -> int:
        return self.result_ack_id

    def observe_publication_clear(self, result_valid: bool) -> str:
        if self.result_must_clear and not result_valid:
            self.result_must_clear = False
            return "CLEARED"
        return "WAIT_RESULT_CLEAR" if self.result_must_clear else "IDLE"

    def reset(self, *, ready: bool, busy: bool, result_valid: bool, trigger_edge: bool = False) -> str:
        if ready and not busy and not result_valid and not trigger_edge and self.pending_id is None:
            self.hold_latched = False
            self.result_must_clear = False
            return "RESET"
        return "RESET_BLOCKED"
