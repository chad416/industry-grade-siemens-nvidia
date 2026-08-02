import csv
from pathlib import Path
from filling_cell_simulator import FillingCellSimulator
SCENARIOS = ['normal_two_bottle_cycle', 'single_missing_bottle', 'both_bottles_missing', 'bottle_sensor_stuck_on', 'bottle_sensor_stuck_off', 'gate_timeout', 'clamp_timeout', 'contradictory_actuator_feedback', 'flow_channel_no_pulse', 'flow_analog_pulse_disagreement', 'underfill', 'overfill', 'valve_fails_to_close', 'pump_vfd_fault', 'conveyor_vfd_fault', 'air_pressure_loss', 'product_supply_loss', 'capper_not_ready', 'capper_busy_timeout', 'capper_fault', 'hmi_communications_loss', 'vision_not_ready', 'vision_result_timeout', 'stale_inspection_id', 'low_confidence_inspection', 'one_bottle_fails', 'vision_heartbeat_loss', 'plc_heartbeat_loss', 'power_loss_during_filling', 'power_restoration', 'reset_no_restart', 'manual_mode_interlocks']
root=Path(__file__).resolve().parents[1]
out=root/"11_simulation"/"outputs"/"scenario_results.csv"
out.parent.mkdir(parents=True,exist_ok=True)
sim=FillingCellSimulator(); rows=[sim.run(s).__dict__ for s in SCENARIOS]
with out.open("w",newline="",encoding="utf-8") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(f"Wrote {len(rows)} scenario results to {out}")
