"""Deterministic Revision-F PLC/vision behavioral fault-injection model.

This model consumes structured injected PLC/edge observations. Scenario-file
expected fields are acceptance criteria and are not copied into the result.
It is independent Python design evidence, not Siemens PLCSIM, target NVIDIA
execution, hardware-in-the-loop testing, FAT, SAT or commissioning.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCENARIO_FILE = ROOT / "vision_fault_scenarios.json"


@dataclass(frozen=True)
class VisionScenario:
    scenario: str
    stimulus: str
    injection: dict[str, object]
    expected_state: str
    diagnostic: str
    result_class: str
    identity_policy: str
    recovery: str


@dataclass(frozen=True)
class VisionInputs:
    """Injected PLC/edge observations consumed by the acceptance model."""

    result_class: str = "PASS"
    result_present: bool = True
    identity_status: str = "EXACT"
    heartbeat_ok: bool = True
    camera_ok: bool = True
    model_loaded: bool = True
    confidence_ok: bool = True
    payload_valid: bool = True
    publication_order_valid: bool = True
    opcua_connected: bool = True
    reconnect_event: bool = False
    reconnect_coherent: bool = True
    edge_restarted: bool = False
    recipe_unchanged: bool = True
    clock_stable: bool = True
    audit_storage_ok: bool = True
    configuration_valid: bool = True
    model_hash_valid: bool = True
    latency_ok: bool = True
    queue_within_limit: bool = True
    bypass_requested: bool = False
    deadline_expired: bool = False
    recovery_completed: bool = False
    contradictory: bool = False

    @classmethod
    def from_injection(cls, values: dict[str, object]) -> "VisionInputs":
        unknown = sorted(set(values) - set(cls.__dataclass_fields__))
        if unknown:
            raise ValueError(f"unknown injected input(s): {unknown}")
        return cls(**values)


@dataclass(frozen=True)
class VisionSilResult:
    scenario: str
    final_state: str
    diagnostic: str
    result_class: str
    session_epoch: int
    inspection_id: int
    product_released: bool
    pump_cmd: bool
    valve_1_cmd: bool
    valve_2_cmd: bool
    automatic_restart: bool
    identity_accepted: bool
    explicit_recovery: str
    evidence_class: str = "BEHAVIORAL_FAULT_INJECTION_MODEL"

    def as_row(self) -> dict[str, object]:
        return asdict(self)


def evaluate_inputs(inputs: VisionInputs) -> tuple[str, str, str, bool, str]:
    """Evaluate observable inputs using deterministic first-out precedence."""

    exact = inputs.identity_status == "EXACT"
    if inputs.identity_status == "SESSION_CHANGED":
        return "STOPPED", "PLC_SESSION_CHANGED", "INVALID", False, "DISABLED_SYNC_EXPLICIT_START"
    if inputs.recovery_completed:
        return "STOPPED", "RECOVERY_COMPLETE", "INVALID", exact, "EXPLICIT_NEW_START"
    if not inputs.configuration_valid:
        return "FAULTED", "CONFIG_INVALID", "INVALID", exact, "RESTORE_APPROVED_CONFIG_RESTART"
    if not inputs.model_hash_valid:
        return "FAULTED", "MODEL_HASH_MISMATCH", "INVALID", exact, "ROLLBACK_APPROVED_MODEL_RESET"
    if not inputs.audit_storage_ok:
        return "FAULTED", "AUDIT_STORAGE_FAILURE", "INVALID", exact, "RESTORE_STORAGE_RESET"
    if not inputs.heartbeat_ok:
        return "FAULTED", "EDGE_HEARTBEAT_LOSS", "INVALID", exact, "RESTORE_HEARTBEAT_RESET_NEW_REQUEST"
    if not inputs.camera_ok:
        return "FAULTED", "CAMERA_DISCONNECTED", "INVALID", exact, "RESTORE_CAMERA_RECALIBRATE_RESET"
    if not inputs.model_loaded:
        return "FAULTED", "MODEL_UNAVAILABLE", "INVALID", exact, "LOAD_APPROVED_MODEL_RESET"
    if not inputs.opcua_connected:
        return "FAULTED", "OPCUA_DISCONNECTED", "INVALID", exact, "RECONNECT_RECONCILE_RESET"
    if inputs.reconnect_event and not inputs.reconnect_coherent:
        return "HOLDING", "RECONNECT_RECONCILIATION", "INVALID", exact, "DISABLED_SYNC_NEW_REQUEST"
    if inputs.edge_restarted:
        return "HOLDING", "EDGE_RESTART", "INVALID", exact, "RESTORE_OR_INVALIDATE_PUBLICATION_RESET"
    if not inputs.recipe_unchanged:
        return "HOLDING", "RECIPE_CHANGED", "INVALID", exact, "ABORT_CLEAR_NEW_REQUEST"
    if not inputs.clock_stable:
        return "HOLDING", "CLOCK_DISCONTINUITY", "INVALID", exact, "RESTORE_TIME_SYNC_RESET_NEW_REQUEST"
    if not inputs.queue_within_limit:
        return "FAULTED", "QUEUE_SATURATION", "INVALID", exact, "DRAIN_OR_RESTART_RESET"
    if inputs.bypass_requested:
        return "HOLDING", "BYPASS_REQUESTED", "INVALID", exact, "AUTHORIZED_DISPOSITION_ONLY"
    if inputs.deadline_expired:
        if inputs.result_present:
            return "HOLDING", "LATE_RESULT", "INVALID", False, "ACK_CLEAR_RESET_NEW_REQUEST"
        return "HOLDING", "RESULT_TIMEOUT", "INVALID", exact, "CLEAR_CAUSE_RESET_NEW_REQUEST"
    if inputs.identity_status == "STALE":
        return "HOLDING", "STALE_RESULT_ID", "INVALID", False, "ACK_CLEAR_RESET_NEW_REQUEST"
    if inputs.identity_status == "DUPLICATE":
        return "HOLDING", "DUPLICATE_RESULT", "INVALID", False, "ACK_CLEAR_RESET_NEW_REQUEST"
    if inputs.identity_status == "FUTURE":
        return "FAULTED", "FUTURE_RESULT_ID", "INVALID", False, "CLEAR_EDGE_STATE_RESET_NEW_SESSION"
    if not inputs.publication_order_valid:
        return "FAULTED", "PUBLICATION_ORDER_FAULT", "INVALID", exact, "CORRECT_EDGE_FAULT_RESET_NEW_REQUEST"
    if not inputs.payload_valid:
        return "FAULTED", "MALFORMED_RESULT", "INVALID", exact, "CORRECT_EDGE_FAULT_RESET_NEW_REQUEST"
    if inputs.contradictory:
        return "FAULTED", "RESULT_CONTRADICTION", "INVALID", exact, "CORRECT_EDGE_FAULT_RESET_NEW_REQUEST"
    if not inputs.latency_ok:
        return "HOLDING", "LATENCY_EXCEEDED", "INVALID", exact, "INVESTIGATE_PERFORMANCE_RESET_NEW_REQUEST"
    if not inputs.confidence_ok:
        return "HOLDING", "LOW_CONFIDENCE", "INVALID", exact, "OPERATOR_DISPOSITION"
    if inputs.result_class == "FAIL":
        return "HOLDING", "QUALITY_FAIL", "FAIL", exact, "OPERATOR_DISPOSITION"
    if inputs.result_class == "HOLD":
        return "HOLDING", "QUALITY_HOLD", "HOLD", exact, "OPERATOR_DISPOSITION"
    if inputs.result_class == "PASS" and inputs.result_present and exact:
        return "READY", "NONE", "PASS", True, "NONE"
    return "FAULTED", "MALFORMED_RESULT", "INVALID", exact, "CORRECT_EDGE_FAULT_RESET_NEW_REQUEST"


def load_scenarios() -> list[VisionScenario]:
    rows = json.loads(SCENARIO_FILE.read_text(encoding="utf-8"))
    return [VisionScenario(**row) for row in rows]


class VisionReadinessSil:
    """Behavioral fault-injection model for release and recovery invariants."""

    def __init__(self, session_epoch: int = 100, inspection_id: int = 42) -> None:
        if session_epoch <= 0 or inspection_id <= 0:
            raise ValueError("session epoch and inspection ID must be nonzero")
        self.session_epoch = session_epoch
        self.inspection_id = inspection_id

    def run(self, scenario: VisionScenario) -> VisionSilResult:
        inputs = VisionInputs.from_injection(scenario.injection)
        final_state, diagnostic, result_class, identity_accepted, recovery = evaluate_inputs(inputs)
        release = result_class == "PASS" and final_state == "READY" and identity_accepted
        result = VisionSilResult(
            scenario=scenario.scenario,
            final_state=final_state,
            diagnostic=diagnostic,
            result_class=result_class,
            session_epoch=self.session_epoch,
            inspection_id=self.inspection_id,
            product_released=release,
            pump_cmd=False,
            valve_1_cmd=False,
            valve_2_cmd=False,
            automatic_restart=False,
            identity_accepted=identity_accepted,
            explicit_recovery=recovery,
        )
        expected = (
            scenario.expected_state,
            scenario.diagnostic,
            scenario.result_class,
            scenario.identity_policy == "EXACT",
            scenario.recovery,
        )
        actual = (final_state, diagnostic, result_class, identity_accepted, recovery)
        if actual != expected:
            raise AssertionError(f"scenario acceptance criteria disagree with injected behavior: {scenario.scenario}")
        self._assert_invariants(result)
        return result

    @staticmethod
    def _assert_invariants(result: VisionSilResult) -> None:
        if result.product_released and result.result_class != "PASS":
            raise AssertionError("non-PASS result released product")
        if result.product_released and not result.identity_accepted:
            raise AssertionError("uncorrelated result released product")
        if any((result.pump_cmd, result.valve_1_cmd, result.valve_2_cmd)):
            raise AssertionError("inspection outcome energized a process output")
        if result.automatic_restart:
            raise AssertionError("inspection recovery caused automatic restart")
        if not result.product_released and result.explicit_recovery == "NONE":
            raise AssertionError("blocked product lacks a recovery/disposition path")


def run_all() -> list[VisionSilResult]:
    engine = VisionReadinessSil()
    return [engine.run(scenario) for scenario in load_scenarios()]
