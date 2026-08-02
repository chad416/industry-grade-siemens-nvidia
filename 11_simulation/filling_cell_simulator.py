"""Deterministic filling-cell plant, controller, vision, and capper simulation.

This model is independent verification support.  It is deliberately not represented as
Siemens PLC execution, a TIA compile, PLCSIM evidence, or a validated physics model.
The controller model consumes only simulated field/interface signals; hidden plant truth
is used by the simulated vision device, not by the controller.
"""

from __future__ import annotations

import math
import sys
from dataclasses import asdict, dataclass, field
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Iterable

EDGE_SERVICE_DIR = Path(__file__).resolve().parents[1] / "07_nvidia_vision" / "edge_service"
if str(EDGE_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(EDGE_SERVICE_DIR))
from protocol import HEARTBEAT_TIMEOUT_MS, ProtocolError, validate_request_fields


class MachineState(StrEnum):
    UNINITIALIZED = "UNINITIALIZED"
    STOPPED = "STOPPED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    INDEXING = "INDEXING"
    GATE_CLOSING = "GATE_CLOSING"
    CLAMPING = "CLAMPING"
    ZEROING = "ZEROING"
    FILLING = "FILLING"
    DRIP_SETTLE = "DRIP_SETTLE"
    VISION_REQUEST = "VISION_REQUEST"
    VISION_WAIT = "VISION_WAIT"
    TRANSFER = "TRANSFER"
    CAPPER_WAIT_BUSY = "CAPPER_WAIT_BUSY"
    CAPPER_WAIT_COMPLETE = "CAPPER_WAIT_COMPLETE"
    HOLDING = "HOLDING"
    CONTROLLED_STOPPING = "CONTROLLED_STOPPING"
    FAULTED = "FAULTED"


class FillStatus(IntEnum):
    UNKNOWN = 0
    UNDER = 1
    IN_RANGE = 2
    OVER = 3


@dataclass(frozen=True)
class SimulationConfig:
    dt_ms: int = 20
    max_time_ms: int = 15_000
    target_pulses: tuple[int, int] = (500, 500)
    target_volume_ml: float = 500.0
    pulses_per_ml: float = 1.0
    flow_rates_ml_s: tuple[float, float] = (260.0, 220.0)
    bottle_index_rate_s: float = 0.85
    gate_travel_ms: int = 280
    clamp_travel_ms: int = 260
    valve_travel_ms: int = 120
    pump_ramp_ms: int = 180
    position_timeout_ms: int = 3_000
    gate_timeout_ms: int = 900
    clamp_timeout_ms: int = 900
    fill_timeout_ms: int = 5_000
    no_flow_timeout_ms: int = 500
    flow_compare_delay_ms: int = 500
    valve_mismatch_ms: int = 160
    drip_settle_ms: int = 400
    vision_ready_timeout_ms: int = 1_000
    vision_result_timeout_ms: int = 1_000
    heartbeat_period_ms: int = 500
    heartbeat_stale_ms: int = HEARTBEAT_TIMEOUT_MS
    transfer_timeout_ms: int = 2_000
    capper_ready_timeout_ms: int = 1_000
    capper_busy_timeout_ms: int = 1_000
    capper_complete_timeout_ms: int = 2_000

    def __post_init__(self) -> None:
        if self.dt_ms <= 0:
            raise ValueError("dt_ms must be positive")
        if self.max_time_ms < 1_000:
            raise ValueError("max_time_ms is too short for a meaningful run")
        if any(target <= 0 for target in self.target_pulses):
            raise ValueError("target pulses must be positive")


@dataclass
class Commands:
    conveyor: bool = False
    gate_close: bool = False
    clamp: bool = False
    pump: bool = False
    valve_1: bool = False
    valve_2: bool = False
    reset_flow_totals: bool = False
    vision_enable: bool = True
    inspection_trigger: bool = False
    inspection_id: int = 0
    capper_request: bool = False
    transfer_mode: bool = False


@dataclass(frozen=True)
class OperatorEdges:
    reset: bool = False
    start: bool = False
    auto_mode: bool = True
    manual_pump: bool = False
    manual_valve_1: bool = False
    manual_valve_2: bool = False


@dataclass(frozen=True)
class VisionRequest:
    inspection_id: int
    recipe_id: int = 1
    expected_bottles: int = 2
    target_fill_level: float = 1.0


@dataclass(frozen=True)
class VisionResultPayload:
    result_id: int
    bottle_1_pass: bool
    bottle_2_pass: bool
    fill_1_status: FillStatus
    fill_2_status: FillStatus
    leak_or_spill_detected: bool = False
    low_confidence: bool = False
    vision_warning: bool = False
    vision_fault: bool = False
    inference_time_ms: int = 0


@dataclass(frozen=True)
class VisionDecision:
    protocol_valid: bool
    quality_pass: bool
    reason: str


def evaluate_vision_contract(
    request: VisionRequest,
    payload: VisionResultPayload | None,
    *,
    result_valid: bool,
    ready: bool,
    busy: bool,
    heartbeat_fresh: bool,
) -> VisionDecision:
    """Validate protocol semantics before a quality decision can grant transfer."""

    if not heartbeat_fresh:
        return VisionDecision(False, False, "VISION_HEARTBEAT_STALE")
    if not ready:
        return VisionDecision(False, False, "VISION_NOT_READY")
    if busy and result_valid:
        return VisionDecision(False, False, "VISION_BUSY_VALID_CONTRADICTION")
    if not result_valid or payload is None:
        return VisionDecision(False, False, "VISION_RESULT_NOT_VALID")
    if payload.vision_fault:
        return VisionDecision(False, False, "VISION_REPORTED_FAULT")
    if payload.result_id != request.inspection_id:
        return VisionDecision(False, False, "VISION_STALE_ID")
    valid_statuses = {FillStatus.UNDER, FillStatus.IN_RANGE, FillStatus.OVER}
    if payload.fill_1_status not in valid_statuses or payload.fill_2_status not in valid_statuses:
        return VisionDecision(False, False, "VISION_UNKNOWN_FILL_STATUS")
    if payload.bottle_1_pass and payload.fill_1_status is not FillStatus.IN_RANGE:
        return VisionDecision(False, False, "VISION_CHANNEL_1_SEMANTIC_CONTRADICTION")
    if payload.bottle_2_pass and payload.fill_2_status is not FillStatus.IN_RANGE:
        return VisionDecision(False, False, "VISION_CHANNEL_2_SEMANTIC_CONTRADICTION")
    if payload.leak_or_spill_detected and (payload.bottle_1_pass or payload.bottle_2_pass):
        return VisionDecision(False, False, "VISION_LEAK_PASS_CONTRADICTION")
    if payload.low_confidence and (payload.bottle_1_pass or payload.bottle_2_pass):
        return VisionDecision(False, False, "VISION_LOW_CONFIDENCE_PASS_CONTRADICTION")
    if payload.low_confidence:
        return VisionDecision(True, False, "VISION_LOW_CONFIDENCE")
    if payload.leak_or_spill_detected:
        return VisionDecision(True, False, "VISION_LEAK_OR_SPILL")
    if payload.fill_1_status is not FillStatus.IN_RANGE or payload.fill_2_status is not FillStatus.IN_RANGE:
        return VisionDecision(True, False, "VISION_FILL_OUT_OF_RANGE")
    if not payload.bottle_1_pass or not payload.bottle_2_pass:
        return VisionDecision(True, False, "VISION_QUALITY_REJECT")
    return VisionDecision(True, True, "VISION_ACCEPTED")


def _move(position: float, target: float, step: float) -> float:
    if position < target:
        return min(target, position + step)
    return max(target, position - step)


@dataclass
class FillingPlant:
    config: SimulationConfig
    power_available: bool = True
    air_ok: bool = True
    product_ok: bool = True
    hmi_comms_ok: bool = True
    conveyor_vfd_fault: bool = False
    pump_vfd_fault: bool = False
    bottles: list[bool] = field(default_factory=lambda: [True, True])
    sensor_stuck_on: bool = False
    sensor_stuck_off: bool = False
    gate_stuck: bool = False
    clamp_stuck: bool = False
    contradictory_gate_feedback: bool = False
    suppress_pulses: list[bool] = field(default_factory=lambda: [False, False])
    analog_scale: list[float] = field(default_factory=lambda: [1.0, 1.0])
    physical_flow_scale: list[float] = field(default_factory=lambda: [1.0, 1.0])
    valve_1_stuck_open: bool = False

    pair_position: float = 0.0
    gate_position: float = 0.0
    clamp_position: float = 0.0
    pump_speed: float = 0.0
    valve_position: list[float] = field(default_factory=lambda: [0.0, 0.0])
    pulse_accumulator: list[float] = field(default_factory=lambda: [0.0, 0.0])
    measured_pulses: list[int] = field(default_factory=lambda: [0, 0])
    analog_flow_ml_s: list[float] = field(default_factory=lambda: [0.0, 0.0])
    physical_volume_ml: list[float] = field(default_factory=lambda: [0.0, 0.0])
    valve_1_has_opened: bool = False

    @property
    def conveyor_ready(self) -> bool:
        return self.power_available and not self.conveyor_vfd_fault

    @property
    def pump_ready(self) -> bool:
        return self.power_available and not self.pump_vfd_fault

    @property
    def pump_running(self) -> bool:
        return self.pump_speed >= 0.75 and self.pump_ready

    @property
    def gate_closed_fb(self) -> bool:
        return self.contradictory_gate_feedback or self.gate_position >= 0.98

    @property
    def gate_open_fb(self) -> bool:
        return self.contradictory_gate_feedback or self.gate_position <= 0.02

    @property
    def clamp_engaged_fb(self) -> bool:
        return self.clamp_position >= 0.98

    @property
    def clamp_released_fb(self) -> bool:
        return self.clamp_position <= 0.02

    @property
    def valve_open_fb(self) -> tuple[bool, bool]:
        return self.valve_position[0] >= 0.10, self.valve_position[1] >= 0.10

    @property
    def bottle_sensors(self) -> tuple[bool, bool]:
        if self.sensor_stuck_on:
            return True, True
        if self.sensor_stuck_off:
            return False, False
        in_station = 0.98 <= self.pair_position < 1.45
        return self.bottles[0] and in_station, self.bottles[1] and in_station

    @property
    def capper_entry_sensor(self) -> bool:
        return self.pair_position >= 1.65 and any(self.bottles)

    def step(self, commands: Commands) -> None:
        dt_s = self.config.dt_ms / 1_000.0
        if commands.reset_flow_totals:
            self.pulse_accumulator[:] = [0.0, 0.0]
            self.measured_pulses[:] = [0, 0]
            self.physical_volume_ml[:] = [0.0, 0.0]

        powered_air = self.power_available and self.air_ok
        gate_target = 1.0 if powered_air and commands.gate_close else 0.0
        clamp_target = 1.0 if powered_air and commands.clamp else 0.0
        if not self.gate_stuck:
            self.gate_position = _move(
                self.gate_position,
                gate_target,
                self.config.dt_ms / self.config.gate_travel_ms,
            )
        if not self.clamp_stuck:
            self.clamp_position = _move(
                self.clamp_position,
                clamp_target,
                self.config.dt_ms / self.config.clamp_travel_ms,
            )

        pump_target = 1.0 if self.power_available and self.product_ok and commands.pump and self.pump_ready else 0.0
        self.pump_speed = _move(
            self.pump_speed,
            pump_target,
            self.config.dt_ms / self.config.pump_ramp_ms,
        )

        requested_valves = [commands.valve_1, commands.valve_2]
        if commands.valve_1:
            self.valve_1_has_opened = True
        for channel in range(2):
            requested = requested_valves[channel] and powered_air
            if channel == 0 and self.valve_1_stuck_open and self.valve_1_has_opened and self.power_available:
                requested = True
            target = 1.0 if requested else 0.0
            self.valve_position[channel] = _move(
                self.valve_position[channel],
                target,
                self.config.dt_ms / self.config.valve_travel_ms,
            )

        if commands.conveyor and self.conveyor_ready and self.gate_open_fb and self.clamp_released_fb:
            rate = self.config.bottle_index_rate_s * (1.15 if commands.transfer_mode else 1.0)
            self.pair_position += rate * dt_s

        for channel in range(2):
            metered_rate = (
                self.config.flow_rates_ml_s[channel]
                * self.pump_speed
                * self.valve_position[channel]
                if self.power_available and self.product_ok
                else 0.0
            )
            self.analog_flow_ml_s[channel] = metered_rate * self.analog_scale[channel]
            if not self.suppress_pulses[channel]:
                self.pulse_accumulator[channel] += metered_rate * self.config.pulses_per_ml * dt_s
                self.measured_pulses[channel] = math.floor(self.pulse_accumulator[channel] + 1e-9)
            self.physical_volume_ml[channel] += metered_rate * self.physical_flow_scale[channel] * dt_s


@dataclass
class VisionDevice:
    config: SimulationConfig
    scenario: str
    ready_configuration: bool = True
    heartbeat_frozen: bool = False
    suppress_result: bool = False
    stale_result_id: bool = False
    force_low_confidence: bool = False
    force_bottle_2_fail: bool = False
    busy: bool = False
    result_valid: bool = False
    result: VisionResultPayload | None = None
    heartbeat: int = 0
    fault: bool = False
    fault_reason: str = ""
    last_request_id: int = 0
    active_request: VisionRequest | None = None
    request_started_ms: int = 0
    now_ms: int = 0
    _last_heartbeat_ms: int = 0
    _last_plc_heartbeat: int | None = None
    _last_plc_change_ms: int = 0

    @property
    def ready(self) -> bool:
        return self.ready_configuration and not self.fault

    def receive_trigger(self, request: VisionRequest) -> bool:
        if not self.ready or self.busy:
            return False
        if request.inspection_id <= self.last_request_id:
            self.fault = True
            self.fault_reason = "NON_MONOTONIC_INSPECTION_ID"
            return False
        try:
            validate_request_fields(request.expected_bottles, request.target_fill_level)
        except ProtocolError:
            self.fault = True
            self.fault_reason = "INVALID_INSPECTION_REQUEST"
            return False
        self.last_request_id = request.inspection_id
        self.active_request = request
        self.request_started_ms = self.now_ms
        self.busy = True
        self.result_valid = False
        self.result = None
        return True

    def step(self, plant: FillingPlant, plc_heartbeat: int) -> None:
        self.now_ms += self.config.dt_ms
        if not self.heartbeat_frozen and self.now_ms - self._last_heartbeat_ms >= self.config.heartbeat_period_ms:
            self.heartbeat = (self.heartbeat + 1) & 0xFFFFFFFF
            self._last_heartbeat_ms = self.now_ms

        if self._last_plc_heartbeat is None or plc_heartbeat != self._last_plc_heartbeat:
            self._last_plc_heartbeat = plc_heartbeat
            self._last_plc_change_ms = self.now_ms
        elif self.now_ms - self._last_plc_change_ms > self.config.heartbeat_stale_ms:
            self.fault = True
            self.fault_reason = "PLC_HEARTBEAT_STALE"
            self.busy = False
            self.result_valid = False

        if not self.busy or self.active_request is None or self.suppress_result or self.fault:
            return
        inference_ms = 360
        if self.now_ms - self.request_started_ms < inference_ms:
            return

        def fill_status(volume: float) -> FillStatus:
            ratio = volume / self.config.target_volume_ml
            if ratio < 0.95:
                return FillStatus.UNDER
            if ratio > 1.05:
                return FillStatus.OVER
            return FillStatus.IN_RANGE

        statuses = [fill_status(value) for value in plant.physical_volume_ml]
        bottle_pass = [
            plant.bottles[index] and statuses[index] is FillStatus.IN_RANGE
            for index in range(2)
        ]
        if self.force_bottle_2_fail:
            bottle_pass[1] = False
        low_confidence = self.force_low_confidence
        if low_confidence:
            bottle_pass[:] = [False, False]
        result_id = self.active_request.inspection_id - 1 if self.stale_result_id else self.active_request.inspection_id
        self.result = VisionResultPayload(
            result_id=result_id,
            bottle_1_pass=bottle_pass[0],
            bottle_2_pass=bottle_pass[1],
            fill_1_status=statuses[0],
            fill_2_status=statuses[1],
            low_confidence=low_confidence,
            inference_time_ms=inference_ms,
        )
        self.busy = False
        self.result_valid = True


@dataclass
class CapperDevice:
    config: SimulationConfig
    ready: bool = True
    inhibit_busy: bool = False
    inject_fault: bool = False
    busy: bool = False
    complete: bool = False
    fault: bool = False
    _active: bool = False
    _request_started_ms: int = 0
    now_ms: int = 0

    def step(self, request: bool) -> None:
        self.now_ms += self.config.dt_ms
        if request and self.ready and not self.fault and not self._active:
            self._active = True
            self._request_started_ms = self.now_ms
            self.complete = False
        if not self._active:
            return
        age = self.now_ms - self._request_started_ms
        if self.inject_fault and age >= 300:
            self.fault = True
            self.busy = False
            return
        if not self.inhibit_busy and age >= 200:
            self.busy = True
        if self.busy and age >= 900:
            self.busy = False
            self.complete = True
            self._active = False


@dataclass
class ControllerModel:
    config: SimulationConfig
    state: MachineState = MachineState.UNINITIALIZED
    state_entered_ms: int = 0
    commands: Commands = field(default_factory=Commands)
    restart_inhibit: bool = True
    fault_latched: bool = False
    first_out_fault: str = ""
    hold_reason: str = ""
    released: bool = False
    automatic_restart: bool = False
    accepted_start_edges: int = 0
    inspection_id: int = 0
    active_request: VisionRequest | None = None
    transitions: list[tuple[int, str]] = field(default_factory=lambda: [(0, MachineState.UNINITIALIZED.value)])
    invariant_violations: list[str] = field(default_factory=list)
    _fill_complete: list[bool] = field(default_factory=lambda: [False, False])
    _fill_start_pulses: list[int] = field(default_factory=lambda: [0, 0])
    _last_pulses: list[int] = field(default_factory=lambda: [0, 0])
    _no_flow_ms: list[int] = field(default_factory=lambda: [0, 0])
    _analog_pulse_equivalent: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _valve_mismatch_ms: list[int] = field(default_factory=lambda: [0, 0])
    _last_vision_heartbeat: int | None = None
    _vision_heartbeat_changed_ms: int = 0
    plc_heartbeat: int = 0
    _last_plc_heartbeat_ms: int = 0

    def state_age(self, now_ms: int) -> int:
        return now_ms - self.state_entered_ms

    def _transition(self, state: MachineState, now_ms: int) -> None:
        if state is self.state:
            return
        self.state = state
        self.state_entered_ms = now_ms
        self.transitions.append((now_ms, state.value))

    def _record_fault(self, code: str) -> None:
        if not self.first_out_fault:
            self.first_out_fault = code
        self.fault_latched = True

    def _trip(self, code: str, now_ms: int) -> None:
        self._record_fault(code)
        self.commands = Commands(inspection_id=self.inspection_id)
        self._transition(MachineState.FAULTED, now_ms)

    def _hold(self, reason: str, now_ms: int) -> None:
        if not self.first_out_fault:
            self.first_out_fault = reason
        self.hold_reason = reason
        self.commands = Commands(inspection_id=self.inspection_id)
        self._transition(MachineState.HOLDING, now_ms)

    def _healthy_for_reset(self, plant: FillingPlant) -> bool:
        return (
            plant.power_available
            and plant.air_ok
            and plant.product_ok
            and plant.hmi_comms_ok
            and not plant.pump_vfd_fault
            and not plant.conveyor_vfd_fault
            and not (plant.gate_closed_fb and plant.gate_open_fb)
        )

    def _update_heartbeats(self, now_ms: int, vision: VisionDevice, freeze_plc: bool) -> None:
        if not freeze_plc and now_ms - self._last_plc_heartbeat_ms >= self.config.heartbeat_period_ms:
            self.plc_heartbeat = (self.plc_heartbeat + 1) & 0xFFFFFFFF
            self._last_plc_heartbeat_ms = now_ms
        if self._last_vision_heartbeat is None or vision.heartbeat != self._last_vision_heartbeat:
            self._last_vision_heartbeat = vision.heartbeat
            self._vision_heartbeat_changed_ms = now_ms

    def _vision_heartbeat_fresh(self, now_ms: int) -> bool:
        return now_ms - self._vision_heartbeat_changed_ms <= self.config.heartbeat_stale_ms

    def _global_faults(self, now_ms: int, plant: FillingPlant) -> bool:
        active = self.state not in {
            MachineState.UNINITIALIZED,
            MachineState.STOPPED,
            MachineState.FAULTED,
            MachineState.HOLDING,
            MachineState.CONTROLLED_STOPPING,
        }
        if plant.gate_closed_fb and plant.gate_open_fb:
            self._trip("GATE_FEEDBACK_CONTRADICTION", now_ms)
            return True
        if active and not plant.hmi_comms_ok:
            self._record_fault("HMI_COMMS_LOSS")
            self.restart_inhibit = True
            self._transition(MachineState.CONTROLLED_STOPPING, now_ms)
            return True
        if active and not plant.air_ok:
            self._trip("AIR_PRESSURE_LOSS", now_ms)
            return True
        if active and not plant.product_ok:
            self._trip("PRODUCT_SUPPLY_LOSS", now_ms)
            return True
        if plant.pump_vfd_fault and self.state is MachineState.FILLING:
            self._trip("PUMP_VFD_FAULT", now_ms)
            return True
        if plant.conveyor_vfd_fault and self.state in {MachineState.INDEXING, MachineState.TRANSFER}:
            self._trip("CONVEYOR_VFD_FAULT", now_ms)
            return True
        return False

    def step(
        self,
        now_ms: int,
        plant: FillingPlant,
        vision: VisionDevice,
        capper: CapperDevice,
        operator: OperatorEdges,
        *,
        freeze_plc_heartbeat: bool = False,
    ) -> Commands:
        self.commands = Commands(inspection_id=self.inspection_id)
        self._update_heartbeats(now_ms, vision, freeze_plc_heartbeat)

        if not plant.power_available:
            if self.state not in {MachineState.UNINITIALIZED, MachineState.STOPPED}:
                self._record_fault("POWER_LOSS_DURING_CYCLE")
            self.restart_inhibit = True
            self._transition(MachineState.UNINITIALIZED, now_ms)
            return self.commands

        if self.state is MachineState.UNINITIALIZED:
            self.restart_inhibit = True
            self._transition(MachineState.STOPPED, now_ms)
            return self.commands

        if self._global_faults(now_ms, plant):
            return self.commands

        age = self.state_age(now_ms)
        if self.state is MachineState.FAULTED:
            if operator.reset and self._healthy_for_reset(plant):
                self.fault_latched = False
                self.restart_inhibit = False
                self._transition(MachineState.STOPPED, now_ms)
            return self.commands

        if self.state is MachineState.HOLDING:
            return self.commands

        if self.state is MachineState.CONTROLLED_STOPPING:
            if age >= 250:
                self.restart_inhibit = True
                self._transition(MachineState.STOPPED, now_ms)
            return self.commands

        if self.state is MachineState.STOPPED:
            if operator.manual_pump or operator.manual_valve_1 or operator.manual_valve_2:
                self._trip("MANUAL_COMMAND_INTERLOCK", now_ms)
                return self.commands
            if operator.reset and self._healthy_for_reset(plant):
                self.fault_latched = False
                self.restart_inhibit = False
            if operator.start and operator.auto_mode and not self.restart_inhibit and not self.fault_latched:
                self.accepted_start_edges += 1
                self.released = False
                self._transition(MachineState.INITIALIZING, now_ms)
            return self.commands

        if self.state is MachineState.INITIALIZING:
            if age >= 300:
                self._transition(MachineState.READY, now_ms)
            return self.commands

        if self.state is MachineState.READY:
            if self.released:
                return self.commands
            if self.accepted_start_edges < 1:
                self.automatic_restart = True
                self._trip("UNAUTHORIZED_AUTOMATIC_START", now_ms)
                return self.commands
            self.commands.conveyor = True
            self._transition(MachineState.INDEXING, now_ms)
            return self.commands

        if self.state is MachineState.INDEXING:
            self.commands.conveyor = True
            sensors = plant.bottle_sensors
            if age <= 100 and any(sensors):
                self._trip("BOTTLE_SENSOR_STUCK_ON", now_ms)
            elif all(sensors):
                self.commands.conveyor = False
                self._transition(MachineState.GATE_CLOSING, now_ms)
            elif any(sensors):
                # Hold the first positioned bottle while waiting for its pair.
                self.commands.conveyor = False
                if age >= self.config.position_timeout_ms:
                    self._trip("SINGLE_BOTTLE_MISSING", now_ms)
            elif age >= self.config.position_timeout_ms:
                self._trip("BOTTLE_POSITION_TIMEOUT", now_ms)
            return self.commands

        if self.state is MachineState.GATE_CLOSING:
            self.commands.gate_close = True
            if plant.gate_closed_fb:
                self._transition(MachineState.CLAMPING, now_ms)
            elif age >= self.config.gate_timeout_ms:
                self._trip("GATE_CLOSE_TIMEOUT", now_ms)
            return self.commands

        if self.state is MachineState.CLAMPING:
            self.commands.gate_close = True
            self.commands.clamp = True
            if plant.clamp_engaged_fb:
                self._transition(MachineState.ZEROING, now_ms)
            elif age >= self.config.clamp_timeout_ms:
                self._trip("CLAMP_ENGAGE_TIMEOUT", now_ms)
            return self.commands

        if self.state is MachineState.ZEROING:
            self.commands.gate_close = True
            self.commands.clamp = True
            self.commands.reset_flow_totals = True
            if age >= max(2 * self.config.dt_ms, 40):
                self._fill_complete[:] = [False, False]
                self._fill_start_pulses[:] = list(plant.measured_pulses)
                self._last_pulses[:] = list(plant.measured_pulses)
                self._no_flow_ms[:] = [0, 0]
                self._analog_pulse_equivalent[:] = [0.0, 0.0]
                self._valve_mismatch_ms[:] = [0, 0]
                self._transition(MachineState.FILLING, now_ms)
            return self.commands

        if self.state is MachineState.FILLING:
            self.commands.gate_close = True
            self.commands.clamp = True
            self.commands.pump = True
            for channel in range(2):
                pulse_delta = plant.measured_pulses[channel] - self._fill_start_pulses[channel]
                if pulse_delta >= self.config.target_pulses[channel]:
                    self._fill_complete[channel] = True
                if not self._fill_complete[channel]:
                    if channel == 0:
                        self.commands.valve_1 = True
                    else:
                        self.commands.valve_2 = True

            valve_fb = plant.valve_open_fb
            for channel in range(2):
                commanded = self.commands.valve_1 if channel == 0 else self.commands.valve_2
                if self._fill_complete[channel] and not commanded and valve_fb[channel]:
                    self._valve_mismatch_ms[channel] += self.config.dt_ms
                else:
                    self._valve_mismatch_ms[channel] = 0
                if self._valve_mismatch_ms[channel] >= self.config.valve_mismatch_ms:
                    self._trip(f"VALVE_{channel + 1}_FAILS_TO_CLOSE", now_ms)
                    return self.commands

            for channel in range(2):
                commanded = self.commands.valve_1 if channel == 0 else self.commands.valve_2
                pulse_change = plant.measured_pulses[channel] - self._last_pulses[channel]
                if commanded and plant.pump_running and plant.analog_flow_ml_s[channel] > 25.0 and pulse_change <= 0:
                    self._no_flow_ms[channel] += self.config.dt_ms
                else:
                    self._no_flow_ms[channel] = 0
                if self._no_flow_ms[channel] >= self.config.no_flow_timeout_ms:
                    self._trip(f"FLOW_{channel + 1}_NO_PULSE", now_ms)
                    return self.commands
                self._analog_pulse_equivalent[channel] += (
                    plant.analog_flow_ml_s[channel]
                    * self.config.pulses_per_ml
                    * self.config.dt_ms
                    / 1_000.0
                )
                pulse_delta = plant.measured_pulses[channel] - self._fill_start_pulses[channel]
                if (
                    age >= self.config.flow_compare_delay_ms
                    and self._analog_pulse_equivalent[channel] >= 50.0
                    and pulse_delta >= 10
                ):
                    ratio = pulse_delta / self._analog_pulse_equivalent[channel]
                    if not 0.70 <= ratio <= 1.30:
                        self._trip(f"FLOW_{channel + 1}_ANALOG_PULSE_DISAGREEMENT", now_ms)
                        return self.commands
                if pulse_delta > self.config.target_pulses[channel] + 50:
                    self._trip(f"FLOW_{channel + 1}_OVERFILL", now_ms)
                    return self.commands
                self._last_pulses[channel] = plant.measured_pulses[channel]

            if all(self._fill_complete):
                self.commands.pump = False
                self.commands.valve_1 = False
                self.commands.valve_2 = False
                self._transition(MachineState.DRIP_SETTLE, now_ms)
            elif age >= self.config.fill_timeout_ms:
                self._trip("FILL_TIMEOUT", now_ms)
            return self.commands

        if self.state is MachineState.DRIP_SETTLE:
            self.commands.gate_close = True
            self.commands.clamp = True
            if age >= self.config.drip_settle_ms:
                self._transition(MachineState.VISION_REQUEST, now_ms)
            return self.commands

        if self.state is MachineState.VISION_REQUEST:
            self.commands.gate_close = True
            self.commands.clamp = True
            heartbeat_fresh = self._vision_heartbeat_fresh(now_ms)
            if not heartbeat_fresh:
                self._hold("VISION_HEARTBEAT_STALE", now_ms)
                return self.commands
            if vision.fault:
                reason = "VISION_REPORTED_" + (vision.fault_reason or "FAULT")
                self._hold(reason, now_ms)
                return self.commands
            if not vision.ready:
                if age >= self.config.vision_ready_timeout_ms:
                    self._hold("VISION_NOT_READY", now_ms)
                return self.commands
            self.inspection_id = (self.inspection_id + 1) & 0xFFFFFFFF
            if self.inspection_id == 0:
                self.inspection_id = 1
            self.active_request = VisionRequest(self.inspection_id)
            self.commands.inspection_id = self.inspection_id
            self.commands.inspection_trigger = True
            if not vision.receive_trigger(self.active_request):
                self._hold("VISION_TRIGGER_REJECTED", now_ms)
                return self.commands
            self._transition(MachineState.VISION_WAIT, now_ms)
            return self.commands

        if self.state is MachineState.VISION_WAIT:
            self.commands.gate_close = True
            self.commands.clamp = True
            self.commands.inspection_id = self.inspection_id
            if vision.fault:
                reason = "VISION_REPORTED_" + (vision.fault_reason or "FAULT")
                self._hold(reason, now_ms)
                return self.commands
            if not self._vision_heartbeat_fresh(now_ms):
                self._hold("VISION_HEARTBEAT_STALE", now_ms)
                return self.commands
            if vision.result_valid:
                decision = evaluate_vision_contract(
                    self.active_request or VisionRequest(self.inspection_id),
                    vision.result,
                    result_valid=vision.result_valid,
                    ready=vision.ready,
                    busy=vision.busy,
                    heartbeat_fresh=True,
                )
                if not decision.protocol_valid or not decision.quality_pass:
                    self._hold(decision.reason, now_ms)
                else:
                    self._transition(MachineState.TRANSFER, now_ms)
                return self.commands
            if age >= self.config.vision_result_timeout_ms:
                self._hold("VISION_RESULT_TIMEOUT", now_ms)
            return self.commands

        if self.state is MachineState.TRANSFER:
            self.commands.transfer_mode = True
            if not plant.clamp_released_fb or not plant.gate_open_fb:
                if age >= self.config.transfer_timeout_ms:
                    self._trip("TRANSFER_RELEASE_TIMEOUT", now_ms)
                return self.commands
            if not capper.ready:
                if age >= self.config.capper_ready_timeout_ms:
                    self._trip("CAPPER_NOT_READY", now_ms)
                return self.commands
            self.commands.conveyor = True
            if plant.capper_entry_sensor:
                self.commands.conveyor = False
                self.commands.capper_request = True
                self._transition(MachineState.CAPPER_WAIT_BUSY, now_ms)
            elif age >= self.config.transfer_timeout_ms:
                self._trip("TRANSFER_TIMEOUT", now_ms)
            return self.commands

        if self.state is MachineState.CAPPER_WAIT_BUSY:
            self.commands.capper_request = True
            if capper.fault:
                self._trip("CAPPER_FAULT", now_ms)
            elif capper.busy:
                self.commands.capper_request = False
                self._transition(MachineState.CAPPER_WAIT_COMPLETE, now_ms)
            elif age >= self.config.capper_busy_timeout_ms:
                self._trip("CAPPER_BUSY_TIMEOUT", now_ms)
            return self.commands

        if self.state is MachineState.CAPPER_WAIT_COMPLETE:
            if capper.fault:
                self._trip("CAPPER_FAULT", now_ms)
            elif capper.complete:
                self.released = True
                self._transition(MachineState.READY, now_ms)
            elif age >= self.config.capper_complete_timeout_ms:
                self._trip("CAPPER_COMPLETE_TIMEOUT", now_ms)
            return self.commands

        raise RuntimeError(f"unhandled controller state {self.state}")

    def check_invariants(self, now_ms: int, plant: FillingPlant, vision: VisionDevice, capper: CapperDevice) -> None:
        violations: list[str] = []
        if self.commands.pump and self.state is not MachineState.FILLING:
            violations.append("pump command outside FILLING")
        if (self.commands.valve_1 or self.commands.valve_2) and not self.commands.pump:
            violations.append("valve command without pump command")
        if self.commands.conveyor and (self.commands.clamp or self.commands.pump or self.commands.valve_1 or self.commands.valve_2):
            violations.append("conveyor command conflicts with retained/filling actuators")
        if not plant.power_available and any(
            (self.commands.conveyor, self.commands.gate_close, self.commands.clamp, self.commands.pump, self.commands.valve_1, self.commands.valve_2)
        ):
            violations.append("energized command during power loss")
        if self.released:
            accepted = self.transitions and any(state == MachineState.CAPPER_WAIT_COMPLETE.value for _, state in self.transitions)
            if not accepted or not capper.complete:
                violations.append("release without completed capper handshake")
        if self.state in {MachineState.FILLING, MachineState.DRIP_SETTLE, MachineState.VISION_REQUEST, MachineState.VISION_WAIT}:
            if not plant.gate_closed_fb or not plant.clamp_engaged_fb:
                violations.append("contained-process state without gate and clamp feedback")
        for violation in violations:
            record = f"{now_ms}:{violation}"
            if record not in self.invariant_violations:
                self.invariant_violations.append(record)


@dataclass
class ScenarioRuntime:
    name: str
    initial_reset_sent: bool = False
    initial_start_sent: bool = False
    manual_attempt_sent: bool = False
    dynamic_event_started_ms: int | None = None
    dynamic_event_complete: bool = False
    recovery_reset_sent: bool = False

    def configure(self, plant: FillingPlant, vision: VisionDevice, capper: CapperDevice) -> None:
        if self.name == "single_missing_bottle":
            plant.bottles[:] = [True, False]
        elif self.name == "both_bottles_missing":
            plant.bottles[:] = [False, False]
        elif self.name == "bottle_sensor_stuck_on":
            plant.sensor_stuck_on = True
        elif self.name == "bottle_sensor_stuck_off":
            plant.sensor_stuck_off = True
        elif self.name == "gate_timeout":
            plant.gate_stuck = True
        elif self.name == "clamp_timeout":
            plant.clamp_stuck = True
        elif self.name == "contradictory_actuator_feedback":
            plant.contradictory_gate_feedback = True
        elif self.name == "flow_channel_no_pulse":
            plant.suppress_pulses[0] = True
        elif self.name == "flow_analog_pulse_disagreement":
            plant.analog_scale[0] = 0.35
        elif self.name == "underfill":
            plant.physical_flow_scale[0] = 0.82
        elif self.name == "overfill":
            plant.physical_flow_scale[0] = 1.18
        elif self.name == "valve_fails_to_close":
            plant.valve_1_stuck_open = True
        elif self.name == "capper_not_ready":
            capper.ready = False
        elif self.name == "capper_busy_timeout":
            capper.inhibit_busy = True
        elif self.name == "capper_fault":
            capper.inject_fault = True
        elif self.name == "vision_not_ready":
            vision.ready_configuration = False
        elif self.name == "vision_result_timeout":
            vision.suppress_result = True
        elif self.name == "stale_inspection_id":
            vision.stale_result_id = True
        elif self.name == "low_confidence_inspection":
            vision.force_low_confidence = True
        elif self.name == "one_bottle_fails":
            vision.force_bottle_2_fail = True
        elif self.name == "vision_heartbeat_loss":
            vision.heartbeat_frozen = True
        elif self.name == "power_restoration":
            plant.power_available = False

    def apply_timed_faults(self, now_ms: int, controller: ControllerModel, plant: FillingPlant) -> bool:
        freeze_plc_heartbeat = self.name == "plc_heartbeat_loss"
        if self.name == "conveyor_vfd_fault" and controller.state is MachineState.INDEXING and controller.state_age(now_ms) >= 300:
            plant.conveyor_vfd_fault = True
        if self.name in {"pump_vfd_fault", "reset_no_restart"}:
            if controller.state is MachineState.FILLING and controller.state_age(now_ms) >= 300 and self.dynamic_event_started_ms is None:
                self.dynamic_event_started_ms = now_ms
            if self.dynamic_event_started_ms is not None:
                duration = 500 if self.name == "reset_no_restart" else 10_000
                plant.pump_vfd_fault = now_ms < self.dynamic_event_started_ms + duration
                self.dynamic_event_complete = not plant.pump_vfd_fault
        if self.name == "air_pressure_loss" and controller.state is MachineState.FILLING and controller.state_age(now_ms) >= 500:
            plant.air_ok = False
        if self.name == "product_supply_loss" and controller.state is MachineState.FILLING and controller.state_age(now_ms) >= 500:
            plant.product_ok = False
        if self.name == "hmi_communications_loss":
            if controller.state is MachineState.FILLING and controller.state_age(now_ms) >= 500 and self.dynamic_event_started_ms is None:
                self.dynamic_event_started_ms = now_ms
            if self.dynamic_event_started_ms is not None:
                plant.hmi_comms_ok = not (now_ms < self.dynamic_event_started_ms + 700)
                self.dynamic_event_complete = plant.hmi_comms_ok
        if self.name == "power_loss_during_filling":
            if controller.state is MachineState.FILLING and controller.state_age(now_ms) >= 500 and self.dynamic_event_started_ms is None:
                self.dynamic_event_started_ms = now_ms
            if self.dynamic_event_started_ms is not None:
                plant.power_available = not (now_ms < self.dynamic_event_started_ms + 700)
                self.dynamic_event_complete = plant.power_available
        if self.name == "power_restoration" and now_ms >= 1_000:
            plant.power_available = True
            self.dynamic_event_complete = True
        return freeze_plc_heartbeat

    def operator_edges(self, now_ms: int, controller: ControllerModel, plant: FillingPlant) -> OperatorEdges:
        age = controller.state_age(now_ms)
        if self.name == "power_restoration":
            return OperatorEdges()
        if self.name == "manual_mode_interlocks":
            if controller.state is MachineState.STOPPED and not self.initial_reset_sent and age >= 100:
                self.initial_reset_sent = True
                return OperatorEdges(reset=True, auto_mode=False)
            if controller.state is MachineState.STOPPED and self.initial_reset_sent and not self.manual_attempt_sent and age >= 300:
                self.manual_attempt_sent = True
                return OperatorEdges(auto_mode=False, manual_pump=True, manual_valve_1=True)
            return OperatorEdges(auto_mode=False)

        if controller.state is MachineState.STOPPED and not self.initial_reset_sent and age >= 100:
            self.initial_reset_sent = True
            return OperatorEdges(reset=True)
        if controller.state is MachineState.STOPPED and self.initial_reset_sent and not self.initial_start_sent and age >= 260:
            self.initial_start_sent = True
            return OperatorEdges(start=True)

        recoverable = {"reset_no_restart", "hmi_communications_loss", "power_loss_during_filling"}
        if (
            self.name in recoverable
            and self.initial_start_sent
            and self.dynamic_event_complete
            and not self.recovery_reset_sent
            and controller.state in {MachineState.FAULTED, MachineState.STOPPED}
            and controller.state_age(now_ms) >= 300
            and plant.hmi_comms_ok
            and plant.power_available
            and not plant.pump_vfd_fault
        ):
            self.recovery_reset_sent = True
            return OperatorEdges(reset=True)
        return OperatorEdges()


@dataclass(frozen=True)
class TraceSample:
    time_ms: int
    state: str
    state_age_ms: int
    power_available: bool
    hmi_comms_ok: bool
    conveyor_cmd: bool
    gate_close_cmd: bool
    clamp_cmd: bool
    pump_cmd: bool
    valve_1_cmd: bool
    valve_2_cmd: bool
    gate_closed_fb: bool
    gate_open_fb: bool
    clamp_engaged_fb: bool
    bottle_1_positioned: bool
    bottle_2_positioned: bool
    pulse_1: int
    pulse_2: int
    analog_flow_1_ml_s: float
    analog_flow_2_ml_s: float
    volume_1_ml: float
    volume_2_ml: float
    inspection_trigger: bool
    inspection_id: int
    vision_ready: bool
    vision_busy: bool
    result_valid: bool
    result_id: int
    plc_heartbeat: int
    vision_heartbeat: int
    capper_request: bool
    capper_ready: bool
    capper_busy: bool
    capper_complete: bool
    first_out_fault: str
    hold_reason: str
    restart_inhibit: bool
    released: bool

    def as_row(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class Result:
    scenario: str
    final_state: str
    released: bool
    pump_cmd: bool
    valve_1_cmd: bool
    valve_2_cmd: bool
    automatic_restart: bool
    evidence: str
    duration_ms: int
    transition_count: int
    fault_code: str
    hold_reason: str
    pulse_1: int
    pulse_2: int
    volume_1_ml: float
    volume_2_ml: float
    inspection_id: int
    result_id: int
    invariant_violations: tuple[str, ...]
    transitions: tuple[tuple[int, str], ...]
    trace: tuple[TraceSample, ...]

    def summary_row(self) -> dict[str, object]:
        row = asdict(self)
        row.pop("trace")
        row["invariant_violations"] = " | ".join(self.invariant_violations)
        row["transitions"] = " > ".join(f"{time_ms}:{state}" for time_ms, state in self.transitions)
        return row


SCENARIOS = (
    "normal_two_bottle_cycle",
    "single_missing_bottle",
    "both_bottles_missing",
    "bottle_sensor_stuck_on",
    "bottle_sensor_stuck_off",
    "gate_timeout",
    "clamp_timeout",
    "contradictory_actuator_feedback",
    "flow_channel_no_pulse",
    "flow_analog_pulse_disagreement",
    "underfill",
    "overfill",
    "valve_fails_to_close",
    "pump_vfd_fault",
    "conveyor_vfd_fault",
    "air_pressure_loss",
    "product_supply_loss",
    "capper_not_ready",
    "capper_busy_timeout",
    "capper_fault",
    "hmi_communications_loss",
    "vision_not_ready",
    "vision_result_timeout",
    "stale_inspection_id",
    "low_confidence_inspection",
    "one_bottle_fails",
    "vision_heartbeat_loss",
    "plc_heartbeat_loss",
    "power_loss_during_filling",
    "power_restoration",
    "reset_no_restart",
    "manual_mode_interlocks",
)


class FillingCellSimulator:
    """Run deterministic scenarios against an independent controller/plant model."""

    def __init__(self, config: SimulationConfig | None = None) -> None:
        self.config = config or SimulationConfig()

    def run(self, scenario: str) -> Result:
        if scenario not in SCENARIOS:
            raise KeyError(scenario)
        plant = FillingPlant(self.config)
        vision = VisionDevice(self.config, scenario)
        capper = CapperDevice(self.config)
        controller = ControllerModel(self.config)
        runtime = ScenarioRuntime(scenario)
        runtime.configure(plant, vision, capper)
        trace: list[TraceSample] = []
        final_time = 0

        for now_ms in range(0, self.config.max_time_ms + self.config.dt_ms, self.config.dt_ms):
            final_time = now_ms
            freeze_plc = runtime.apply_timed_faults(now_ms, controller, plant)
            operator = runtime.operator_edges(now_ms, controller, plant)
            commands = controller.step(
                now_ms,
                plant,
                vision,
                capper,
                operator,
                freeze_plc_heartbeat=freeze_plc,
            )
            plant.step(commands)
            vision.step(plant, controller.plc_heartbeat)
            capper.step(commands.capper_request)
            controller.check_invariants(now_ms, plant, vision, capper)
            sensors = plant.bottle_sensors
            result_id = vision.result.result_id if vision.result is not None else 0
            trace.append(
                TraceSample(
                    time_ms=now_ms,
                    state=controller.state.value,
                    state_age_ms=controller.state_age(now_ms),
                    power_available=plant.power_available,
                    hmi_comms_ok=plant.hmi_comms_ok,
                    conveyor_cmd=commands.conveyor,
                    gate_close_cmd=commands.gate_close,
                    clamp_cmd=commands.clamp,
                    pump_cmd=commands.pump,
                    valve_1_cmd=commands.valve_1,
                    valve_2_cmd=commands.valve_2,
                    gate_closed_fb=plant.gate_closed_fb,
                    gate_open_fb=plant.gate_open_fb,
                    clamp_engaged_fb=plant.clamp_engaged_fb,
                    bottle_1_positioned=sensors[0],
                    bottle_2_positioned=sensors[1],
                    pulse_1=plant.measured_pulses[0],
                    pulse_2=plant.measured_pulses[1],
                    analog_flow_1_ml_s=round(plant.analog_flow_ml_s[0], 3),
                    analog_flow_2_ml_s=round(plant.analog_flow_ml_s[1], 3),
                    volume_1_ml=round(plant.physical_volume_ml[0], 3),
                    volume_2_ml=round(plant.physical_volume_ml[1], 3),
                    inspection_trigger=commands.inspection_trigger,
                    inspection_id=controller.inspection_id,
                    vision_ready=vision.ready,
                    vision_busy=vision.busy,
                    result_valid=vision.result_valid,
                    result_id=result_id,
                    plc_heartbeat=controller.plc_heartbeat,
                    vision_heartbeat=vision.heartbeat,
                    capper_request=commands.capper_request,
                    capper_ready=capper.ready,
                    capper_busy=capper.busy,
                    capper_complete=capper.complete,
                    first_out_fault=controller.first_out_fault,
                    hold_reason=controller.hold_reason,
                    restart_inhibit=controller.restart_inhibit,
                    released=controller.released,
                )
            )

            terminal_age = controller.state_age(now_ms)
            if controller.released and controller.state is MachineState.READY and terminal_age >= 100:
                break
            if controller.state in {MachineState.FAULTED, MachineState.HOLDING} and terminal_age >= 500:
                if scenario not in {"reset_no_restart"}:
                    break
            if scenario == "power_restoration" and controller.state is MachineState.STOPPED and now_ms >= 2_000:
                break
            if (
                scenario in {"reset_no_restart", "hmi_communications_loss", "power_loss_during_filling"}
                and runtime.recovery_reset_sent
                and controller.state is MachineState.STOPPED
                and terminal_age >= 300
            ):
                break

        result_id = vision.result.result_id if vision.result is not None else 0
        if controller.released:
            evidence = "matched fresh vision result accepted; transfer and capper busy/complete handshake observed"
        elif controller.hold_reason:
            evidence = f"quality hold: {controller.hold_reason}"
        elif controller.first_out_fault:
            evidence = f"first-out {controller.first_out_fault}; commands de-energized; explicit new start required"
        else:
            evidence = "stopped with restart inhibit; no start edge accepted"
        return Result(
            scenario=scenario,
            final_state=controller.state.value,
            released=controller.released,
            pump_cmd=controller.commands.pump,
            valve_1_cmd=controller.commands.valve_1,
            valve_2_cmd=controller.commands.valve_2,
            automatic_restart=controller.automatic_restart,
            evidence=evidence,
            duration_ms=final_time,
            transition_count=len(controller.transitions) - 1,
            fault_code=controller.first_out_fault,
            hold_reason=controller.hold_reason,
            pulse_1=plant.measured_pulses[0],
            pulse_2=plant.measured_pulses[1],
            volume_1_ml=round(plant.physical_volume_ml[0], 3),
            volume_2_ml=round(plant.physical_volume_ml[1], 3),
            inspection_id=controller.inspection_id,
            result_id=result_id,
            invariant_violations=tuple(controller.invariant_violations),
            transitions=tuple(controller.transitions),
            trace=tuple(trace),
        )


def run_all(config: SimulationConfig | None = None, scenarios: Iterable[str] = SCENARIOS) -> list[Result]:
    simulator = FillingCellSimulator(config)
    return [simulator.run(name) for name in scenarios]
