"""Deterministic independent oracles for Revision-D interface contracts.

These models exercise specified state transitions; they are not a Siemens SCL
compiler, PLCSIM evidence, or proof of scan-identical PLC execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


UINT32_MAX = 0xFFFFFFFF


class VisionDiag(IntEnum):
    OK = 0
    READY_TIMEOUT = 1
    RESULT_TIMEOUT = 2
    RESULT_ID_MISMATCH = 3
    QUALITY_BLOCK = 4
    HEARTBEAT_LOSS = 5
    INTERFACE_CONTRADICTION = 6
    RESULT_STUCK_VALID = 7
    NON_MONOTONIC_REQUEST = 8
    SESSION_MISMATCH = 9


@dataclass
class VisionInterfaceModel:
    timeout_ms: int = 100
    heartbeat_timeout_ms: int = 100
    pending: bool = False
    triggered: bool = False
    fault: bool = False
    hold: bool = False
    quality_pass: bool = False
    accepted: bool = False
    trigger: bool = False
    publication_ack: bool = False
    result_must_clear: bool = False
    result_stuck_high: bool = False
    diag: VisionDiag = VisionDiag.OK
    last_issued_id: int = 0
    issued_once: bool = False
    latched_id: int = 0
    latched_session_epoch: int = 0
    current_session_epoch: int = 0
    phase_elapsed_ms: int = 0
    clear_elapsed_ms: int = 0
    heartbeat_elapsed_ms: int = 0
    last_heartbeat: int | None = None
    heartbeat_healthy: bool = True

    def scan(
        self,
        *,
        enable: bool = True,
        trigger_edge: bool = False,
        inspection_id: int = 0,
        session_epoch: int = 1,
        ready: bool = True,
        busy: bool = False,
        result_valid: bool = False,
        result_id: int = 0,
        result_session_epoch: int = 1,
        result_quality_pass: bool = True,
        result_warning: bool = False,
        heartbeat: int = 1,
        reset_edge: bool = False,
        dt_ms: int = 10,
    ) -> None:
        self.trigger = False
        self.accepted = False
        self.publication_ack = result_valid
        publication_was_awaiting_clear = self.result_must_clear
        if result_valid:
            self.result_must_clear = True

        if session_epoch != self.current_session_epoch:
            if self.pending or result_valid:
                self.fault = True
                self.hold = True
                self.pending = False
                self.triggered = False
                self.diag = VisionDiag.SESSION_MISMATCH
            else:
                self.current_session_epoch = session_epoch
                self.issued_once = False
                self.last_issued_id = 0
                self.result_must_clear = False

        if not enable:
            self.last_heartbeat = heartbeat
            self.heartbeat_elapsed_ms = 0
            self.heartbeat_healthy = True
        elif self.last_heartbeat is None:
            self.last_heartbeat = heartbeat
            self.heartbeat_elapsed_ms = 0
        elif heartbeat == self.last_heartbeat:
            self.heartbeat_elapsed_ms += dt_ms
        elif heartbeat < self.last_heartbeat and not (self.last_heartbeat > UINT32_MAX - 255 and heartbeat < 256):
            self.heartbeat_healthy = False
        else:
            self.last_heartbeat = heartbeat
            self.heartbeat_elapsed_ms = 0
            self.heartbeat_healthy = True
        if enable and self.heartbeat_elapsed_ms >= self.heartbeat_timeout_ms:
            self.heartbeat_healthy = False

        if self.result_must_clear:
            if result_valid:
                self.clear_elapsed_ms += dt_ms
            else:
                self.result_must_clear = False
                self.clear_elapsed_ms = 0

        if enable and result_valid and not self.pending and not publication_was_awaiting_clear:
            self.result_stuck_high = True
            self.fault = True
            self.hold = True
            if self.diag == VisionDiag.OK:
                self.diag = VisionDiag.RESULT_STUCK_VALID

        contradiction = (busy and not ready) or (busy and result_valid)
        if enable and contradiction and not self.fault:
            self.fault = True
            self.hold = True
            self.pending = False
            self.triggered = False
            self.diag = VisionDiag.INTERFACE_CONTRADICTION

        if trigger_edge and enable and not result_valid and not self.pending and not self.fault and not self.hold and not self.result_must_clear:
            monotonic = 0 < inspection_id <= UINT32_MAX and (
                not self.issued_once or (self.last_issued_id < UINT32_MAX and inspection_id > self.last_issued_id)
            )
            if not 0 < session_epoch <= UINT32_MAX:
                self.fault = True
                self.hold = True
                self.diag = VisionDiag.SESSION_MISMATCH
            elif not monotonic:
                self.fault = True
                self.hold = True
                self.diag = VisionDiag.NON_MONOTONIC_REQUEST
            else:
                self.pending = True
                self.triggered = False
                self.latched_id = inspection_id
                self.latched_session_epoch = session_epoch
                self.last_issued_id = inspection_id
                self.issued_once = True
                self.quality_pass = False
                self.phase_elapsed_ms = 0

        if self.pending and not self.triggered:
            if ready and not busy and not self.fault:
                self.trigger = True
                self.triggered = True
                self.phase_elapsed_ms = 0
            else:
                self.phase_elapsed_ms += dt_ms

        # A result sampled on the deadline scan wins over the timeout. This is
        # the declared discrete-scan boundary convention for the oracle/SCL.
        if self.pending and self.triggered and result_valid and not self.fault:
            self.result_must_clear = True
            self.clear_elapsed_ms = 0
            if result_session_epoch != self.latched_session_epoch:
                self.fault = True
                self.hold = True
                self.pending = False
                self.triggered = False
                self.diag = VisionDiag.SESSION_MISMATCH
            elif result_id != self.latched_id:
                self.fault = True
                self.hold = True
                self.pending = False
                self.triggered = False
                self.diag = VisionDiag.RESULT_ID_MISMATCH
            else:
                self.accepted = True
                self.quality_pass = result_quality_pass and not result_warning
                self.hold = not self.quality_pass
                self.pending = False
                self.triggered = False
                self.diag = VisionDiag.OK if self.quality_pass else VisionDiag.QUALITY_BLOCK
        elif self.pending and self.triggered:
            self.phase_elapsed_ms += dt_ms

        if not self.fault:
            if self.pending and not self.triggered and self.phase_elapsed_ms >= self.timeout_ms:
                self.fault = True
                self.hold = True
                self.pending = False
                self.diag = VisionDiag.READY_TIMEOUT
            elif self.pending and self.triggered and self.phase_elapsed_ms >= self.timeout_ms:
                self.fault = True
                self.hold = True
                self.pending = False
                self.triggered = False
                self.result_must_clear = True
                self.diag = VisionDiag.RESULT_TIMEOUT
            elif not self.heartbeat_healthy:
                self.fault = True
                self.hold = True
                self.pending = False
                self.triggered = False
                self.diag = VisionDiag.HEARTBEAT_LOSS
            elif self.result_must_clear and self.clear_elapsed_ms >= self.timeout_ms:
                self.result_stuck_high = True
                self.fault = True
                self.hold = True
                if self.diag == VisionDiag.OK:
                    self.diag = VisionDiag.RESULT_STUCK_VALID

        if not enable and self.pending:
            self.fault = True
            self.hold = True
            self.pending = False
            self.triggered = False
            if self.diag == VisionDiag.OK:
                self.diag = VisionDiag.INTERFACE_CONTRADICTION
        if self.fault:
            self.trigger = False
            self.triggered = False

        if reset_edge and not self.pending and not busy and not result_valid and not trigger_edge and ((enable and ready and self.heartbeat_healthy) or not enable):
            self.fault = False
            self.hold = False
            self.quality_pass = False
            self.result_must_clear = False
            self.result_stuck_high = False
            self.diag = VisionDiag.OK


@dataclass
class QualityArbitrationModel:
    state: str = "AUTOMATIC"
    release_permissive: bool = True
    alarm_active: bool = False

    def apply_vision(self, *, accepted: bool, quality_pass: bool, vision_fault: bool, hold_required: bool) -> None:
        blocking_fault = vision_fault
        self.alarm_active = vision_fault or hold_required
        self.release_permissive = not (blocking_fault or hold_required)
        if blocking_fault:
            self.state = "FAULTED"
        elif accepted and not quality_pass:
            self.state = "HOLDING"


@dataclass
class FillCompletionModel:
    active: bool = True
    closing: bool = False
    fault: bool = False

    def deadline_scan(self, *, target_reached: bool, timeout_elapsed: bool) -> None:
        # Mirrors the declared SCL ordering: reaching target on the same
        # discrete scan suppresses the fill timer before timeout evaluation.
        if target_reached:
            self.active = False
            self.closing = True
        elif timeout_elapsed:
            self.fault = True
            self.active = False
            self.closing = True


class FillDiag(IntEnum):
    OK = 0
    ANALOG_BROKEN_WIRE = 2
    NO_FLOW = 3
    PULSE_ANALOG_DISAGREE = 4
    UNDERFILL = 6
    OVERFILL = 7
    VALVE_OPEN_MISMATCH = 8
    VALVE_CLOSE_MISMATCH = 9
    CONTINUED_FLOW = 10
    PULSE_MISSING = 12
    ANALOG_NO_FLOW = 13
    PULSE_COUNTER_DISCONTINUITY = 14


@dataclass
class FillChannelDiagnosticModel:
    no_flow_min_l_min: float = 0.2
    plausibility_pct: float = 25.0
    timeout_s: float = 1.0
    window_count: int = 0
    condition_elapsed_s: float = 0.0
    condition: FillDiag = FillDiag.OK
    fault: bool = False
    diag: FillDiag = FillDiag.OK
    valve_open_cmd: bool = True
    pump_request: bool = True
    rollover_observed: bool = False
    counter_discontinuity: bool = False

    def _trip(self, diag: FillDiag) -> None:
        if not self.fault:
            self.fault = True
            self.diag = diag
        self.valve_open_cmd = False
        self.pump_request = False

    def observe_window(self, *, pulse_flow: float, analog_flow: float, dt_s: float, analog_fault: bool = False, pulse_fault: bool = False) -> None:
        if analog_fault:
            self._trip(FillDiag.ANALOG_BROKEN_WIRE)
            return
        if pulse_fault or self.counter_discontinuity:
            self._trip(FillDiag.PULSE_COUNTER_DISCONTINUITY)
            return
        self.window_count += 1
        if self.window_count == 1:
            self.condition = FillDiag.OK
            self.condition_elapsed_s = 0.0
            return
        pulse_present = pulse_flow >= self.no_flow_min_l_min
        analog_present = analog_flow >= self.no_flow_min_l_min
        if not pulse_present and not analog_present:
            new_condition = FillDiag.NO_FLOW
        elif not pulse_present and analog_present:
            new_condition = FillDiag.PULSE_MISSING
        elif pulse_present and not analog_present:
            new_condition = FillDiag.ANALOG_NO_FLOW
        elif abs(pulse_flow - analog_flow) * 100.0 > self.plausibility_pct * max(analog_flow, 0.1):
            new_condition = FillDiag.PULSE_ANALOG_DISAGREE
        else:
            new_condition = FillDiag.OK
        if new_condition == self.condition:
            self.condition_elapsed_s += dt_s
        else:
            self.condition = new_condition
            self.condition_elapsed_s = dt_s if new_condition != FillDiag.OK else 0.0
        if new_condition != FillDiag.OK and self.condition_elapsed_s >= self.timeout_s:
            self._trip(new_condition)

    def counter_delta(self, previous: int, current: int) -> int:
        if current >= previous:
            return current - previous
        if previous > UINT32_MAX - 255 and current < 256:
            self.rollover_observed = True
            return UINT32_MAX - previous + current + 1
        self.counter_discontinuity = True
        self._trip(FillDiag.PULSE_COUNTER_DISCONTINUITY)
        return 0

    def close_diagnostics(self, *, valve_closed: bool, flow_present: bool, elapsed_s: float) -> None:
        if not valve_closed and elapsed_s >= self.timeout_s:
            self._trip(FillDiag.VALVE_CLOSE_MISMATCH)
        elif flow_present and elapsed_s >= self.timeout_s:
            self._trip(FillDiag.CONTINUED_FLOW)

    def complete(self, delivered_ml: float, target_ml: float, under_tol_ml: float, over_tol_ml: float) -> None:
        if delivered_ml < target_ml - under_tol_ml:
            self._trip(FillDiag.UNDERFILL)
        elif delivered_ml > target_ml + over_tol_ml:
            self._trip(FillDiag.OVERFILL)
