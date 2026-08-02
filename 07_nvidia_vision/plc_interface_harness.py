from dataclasses import dataclass
import sys
from pathlib import Path

EDGE_SERVICE_DIR = Path(__file__).resolve().parent / "edge_service"
if str(EDGE_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(EDGE_SERVICE_DIR))
from protocol import HEARTBEAT_TIMEOUT_MS


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
    fault: bool = False


class VisionContract:
    """Protocol oracle for interface tests; it is not PLC execution or DeepStream runtime."""

    def __init__(self, timeout_ms: int = 1000, heartbeat_timeout_ms: int = HEARTBEAT_TIMEOUT_MS):
        self.timeout_ms = timeout_ms
        self.heartbeat_timeout_ms = heartbeat_timeout_ms
        self.pending_id = None
        self.trigger_ms = 0
        self.last_heartbeat = None
        self.last_heartbeat_change_ms = 0

    def trigger(self, inspection_id: int, now_ms: int, ready: bool, busy: bool) -> str:
        if self.pending_id is not None or not ready or busy:
            return "HOLD_NOT_READY"
        self.pending_id = inspection_id
        self.trigger_ms = now_ms
        return "TRIGGERED"

    def evaluate(self, now_ms: int, ready: bool, heartbeat: int, result: VisionResult | None) -> str:
        if heartbeat != self.last_heartbeat:
            self.last_heartbeat = heartbeat
            self.last_heartbeat_change_ms = now_ms
        if not ready or now_ms - self.last_heartbeat_change_ms > self.heartbeat_timeout_ms:
            self.pending_id = None
            return "HOLD_HEALTH"
        if self.pending_id is None:
            return "IDLE"
        if now_ms - self.trigger_ms > self.timeout_ms:
            self.pending_id = None
            return "HOLD_TIMEOUT"
        if result is None or not result.valid:
            return "WAIT"
        if result.result_id != self.pending_id:
            self.pending_id = None
            return "HOLD_STALE_ID"
        self.pending_id = None
        accepted = (result.bottle_1_pass and result.bottle_2_pass and
                    result.fill_1_status == 2 and result.fill_2_status == 2 and
                    not result.leak_or_spill and not result.low_confidence and not result.fault)
        return "PASS" if accepted else "HOLD_QUALITY"
