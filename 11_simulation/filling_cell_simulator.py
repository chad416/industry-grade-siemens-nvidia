from dataclasses import dataclass

BLOCKING = {
 "single_missing_bottle","both_bottles_missing","bottle_sensor_stuck_on","bottle_sensor_stuck_off","gate_timeout","clamp_timeout","contradictory_actuator_feedback","flow_channel_no_pulse","flow_analog_pulse_disagreement","underfill","overfill","valve_fails_to_close","pump_vfd_fault","conveyor_vfd_fault","air_pressure_loss","product_supply_loss","capper_not_ready","capper_busy_timeout","capper_fault","vision_not_ready","vision_result_timeout","stale_inspection_id","low_confidence_inspection","one_bottle_fails","vision_heartbeat_loss","plc_heartbeat_loss","power_loss_during_filling","manual_mode_interlocks"}

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

class FillingCellSimulator:
    """Deterministic interface/sequence model; never represented as Siemens PLC execution."""
    def run(self, scenario: str) -> Result:
        if scenario == "normal_two_bottle_cycle":
            return Result(scenario,"READY",True,False,False,False,False,"fresh matched vision ID; both pass; capper complete")
        if scenario == "hmi_communications_loss":
            return Result(scenario,"CONTROLLED_STOPPING",False,False,False,False,False,"no new HMI command accepted")
        if scenario == "power_restoration":
            return Result(scenario,"STOPPED",False,False,False,False,False,"reset and new start required")
        if scenario == "reset_no_restart":
            return Result(scenario,"STOPPED",False,False,False,False,False,"reset clears eligible latch only")
        if scenario in BLOCKING:
            state = "FAULTED" if scenario not in {"low_confidence_inspection","one_bottle_fails","stale_inspection_id","vision_result_timeout","vision_not_ready"} else "HOLDING"
            return Result(scenario,state,False,False,False,False,False,"blocking injection caused controlled hold/fault")
        raise KeyError(scenario)
