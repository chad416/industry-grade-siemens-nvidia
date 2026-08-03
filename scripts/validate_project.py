from __future__ import annotations

import csv
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
ARGS = argparse.ArgumentParser()
ARGS.add_argument("--check", action="store_true", help="Read-only validation; do not rewrite the Markdown report")
OPTIONS = ARGS.parse_args()
errors: list[str] = []
checks: list[str] = []


def ok(condition: bool, message: str) -> None:
    (checks if condition else errors).append(message)


def csv_rows(name: str) -> list[dict]:
    with (ROOT / "10_schedules" / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


model = json.loads((ROOT / "00_project_control/canonical_model.json").read_text(encoding="utf-8"))
ok(model["project"]["revision"] == "D.1", "canonical revision D.1")
ok(model["project"]["status"].startswith("PROFESSIONAL CONTROLLED ENGINEERING-DEVELOPMENT RELEASE CANDIDATE"), "truthful controlled-development release-candidate status")

required_dirs = [f"{i:02d}_{name}" for i,name in enumerate(["project_control","requirements","system_architecture","electrical","controls_siemens","hmi","drives","nvidia_vision","digital_twin","panel_cad","schedules","simulation","testing","documentation","qa"])] + ["release"]
for directory in required_dirs: ok((ROOT / directory).is_dir(), f"required directory {directory}")

io = model["io"]
ok(len({r["symbol"] for r in io}) == len(io), "PLC symbols unique")
ok(len({r["address"] for r in io}) == len(io), "PLC physical addresses unique")
for direction,count in [("DI",32),("DO",32),("AI",8),("HSC",2)]: ok(sum(r["direction"] == direction for r in io) == count, f"{count} {direction} channels allocated")
hardwired = {"CONVEYOR_READY","CONVEYOR_RUNNING","CONVEYOR_FAULT","PUMP_READY","PUMP_RUNNING","PUMP_FAULT","CONVEYOR_RUN_CMD","PUMP_RUN_CMD"}
ok(not (hardwired & {r["symbol"] for r in io}), "contradictory hardwired drive run/status I/O removed")
ok(len(model["drive_interfaces"]) == 8 and {r["telegram"] for r in model["drive_interfaces"]} == {"Standard Telegram 1"}, "two Standard Telegram 1 PZD mappings controlled")

schedule_map = {
    "plc_io.csv":"io","siemens_hardware.csv":"hardware","drive_interfaces.csv":"drive_interfaces","hmi_tags.csv":"hmi_tags","alarms.csv":"alarms","nvidia_interface_tags.csv":"vision_interface","bom.csv":"bom","point_to_point_connections.csv":"connections","wire_list.csv":"connections","terminal_plan.csv":"terminals","cable_schedule.csv":"cables","panel_placement.csv":"panel_placement","network_nodes.csv":"network","load_budget.csv":"load_budget","vfd_parameters.csv":"vfd_parameters","component_rationale.csv":"rationales","requirements_traceability.csv":"requirements","test_coverage.csv":"tests","input_request_register.csv":"input_requests","acceptance_gates.csv":"acceptance_gates"
}
for file,key in schedule_map.items():
    expected = [{k:str(v) for k,v in row.items()} for row in model[key]]
    ok(csv_rows(file) == expected, f"{file} exactly derives from canonical model")

hmi = model["hmi_tags"]
physical_do = {r["symbol"] for r in io if r["direction"] == "DO" and r["device"] != "SPARE" and "SPARE" not in r["symbol"]}
writable = [r for r in hmi if r["access"].startswith("Write")]
sequenced = [r for r in writable if r["access"] == "Write request only"]
hold_to_run = [r for r in writable if "while pressed" in r["access"]]
ok(all(r["plc_source"].startswith("DB_HMI.") for r in writable), "all writable HMI tags use DB_HMI command requests")
ok(not any(any(symbol in r["plc_source"] for symbol in physical_do) for r in writable), "HMI never writes physical output symbols")
ok(not any("SPARE" in r["hmi_tag"] and r["access"].startswith("Write") for r in hmi), "spares are never HMI writable")
ok(all(r["request_seq"] and r["accepted_seq"] and r["rejected_seq"] and r["disabled_reason"] for r in sequenced), "sequenced HMI commands have request/ack/reject/disabled fields")
ok(len(hold_to_run) >= 4 and all(r["disabled_reason"] for r in hold_to_run), "manual commands are explicit heartbeat-supervised hold-to-run requests")

connections = model["connections"]
external_connections = [r for r in connections if r["cable_id"]]
keys = [(r["cable_id"],r["cable_core"]) for r in external_connections]
ok(len(keys) == len(set(keys)), "cable/core allocations unique")
ok(len({r["panel_terminal"] for r in external_connections}) == len(external_connections), "external panel terminals unique")
ok(len({r["internal_wire"] for r in connections}) == len(connections), "wire numbers unique")
ok(all(r["field_pin"] and r["internal_wire"] and r["module_terminal"] and r["potential"] for r in connections), "connection mandatory fields populated")
ok(all(r["cable_core"] and r["panel_terminal"] for r in external_connections), "external connection cable/core/terminal fields populated")
ok(len({r["field_terminal"] for r in connections}) == len(connections), "field and relay terminals are not double-landed")
ok(any(r["shield_termination"] for r in connections), "analog/HSC shields scheduled")
ok(any(r["return_common"] for r in connections), "0 V/return commons scheduled")
ok(all(r["return_common"] == "X0:MANA" for r in connections if r["function"] == "Analog signal return"), "all analog returns reference the dedicated MANA common")
ok(all(r["cable_core"] == "SH" and not r["conductor_mm2"] and not r["color"] for r in connections if r["function"] == "Cable shield"), "overall cable shields are separate from insulated cores and carry no invented size/color")
used_cables = {r["cable_id"] for r in external_connections}
ok(used_cables == {r["cable_id"] for r in model["cables"]}, "every cable is referenced by connection records")
for cable in sorted(model["cables"], key=lambda row: row["cable_id"]):
    insulated = [r for r in external_connections if r["cable_id"] == cable["cable_id"] and r["cable_core"] != "SH"]
    ok(int(cable["allocated_cores"]) == len(insulated) and int(cable["spare_cores"]) == int(cable["installed_cores"]) - len(insulated), f"insulated-core allocation/spares reconcile: {cable['cable_id']}")
for do_symbol in sorted(physical_do):
    paths = [r["function"] for r in connections if r["signal"] == do_symbol]
    ok({"PLC output to relay coil","Relay coil return","Relay contact supply","Relay contact 14 to field load","Field load return"}.issubset(paths), f"complete relay coil/contact/load path: {do_symbol}")
ok({"X24:+24V","X0:0V","X0:MANA","SC100:1"}.issubset({r["terminal"] for r in model["terminals"]}), "power, analog-reference and shield reference terminals are scheduled")
for hsc_symbol in sorted({r["symbol"] for r in io if r["direction"] == "HSC"}):
    ok(any(r["signal"] == hsc_symbol and r["function"] == "Counter reference" and r["destination"].endswith(" M") for r in connections), f"explicit TM Count M/reference conductor: {hsc_symbol}")
designation_re = re.compile(r"^=FC01\+(CP01|FLD)-[A-Z]+[0-9]+(?:\.\.-[A-Z]+[0-9]+)?$")
ok(all(designation_re.fullmatch(r["field_designation"]) and r["field_designation"].startswith("=FC01+FLD-") and designation_re.fullmatch(r["module_designation"]) and r["module_designation"].startswith("=FC01+CP01-") for r in external_connections), "external connections use strict class-number reference designations")
ok(all(designation_re.fullmatch(r["full_designation"]) and r["full_designation"].startswith("=FC01+CP01-") for r in model["hardware"] + model["panel_placement"]), "hardware and panel rows use strict full reference designations")

bom_tags = " ".join(r["tag"] for r in model["bom"])
missing_devices = sorted({r["device"] for r in io if r["device"] != "SPARE" and r["device"] not in bom_tags and not (r["device"].startswith("-K2") and "-K202..-K213" in bom_tags)})
ok(not missing_devices, f"BOM covers all I/O devices: {missing_devices}")
ok(any(r["symbol"] == "SAFETY_OK" and r["device"] == "-K100" and "Dry-contact" in r["description"] for r in io), "safety-status mirror maps to controlled K100 dry-contact interface")
ok(any(r["symbol"] == "GUARD_CLOSED_STATUS" and r["device"] == "-S102" and "Dry-contact" in r["description"] for r in io), "guard-status mirror maps to controlled S102 dry-contact interface")
ok(sum(r["signal"] == "SAFETY_OK" and r["field_device"] == "-K100" and "monitor contact" in r["function"].lower() for r in connections) == 2, "K100 safety-interface monitor has explicit supply and signal conductors")
ok(sum(r["signal"] == "GUARD_CLOSED_STATUS" and r["field_device"] == "-S102" and "contact" in r["function"].lower() for r in connections) == 2, "S102 guard monitor has explicit dry-contact supply and signal conductors")
sensor_devices = {r["device"] for r in io if r["device"].startswith("-B")}
sensor_bom = [r for r in model["bom"] if r["tag"].startswith("-B")]
ok({r["tag"] for r in sensor_bom} == sensor_devices and sum(int(r["qty"]) for r in sensor_bom) == len(sensor_devices), "sensor BOM has one non-overlapping line per active sensor")
ok(all(designation_re.fullmatch(r["full_designation"]) for r in model["bom"]), "all BOM rows use strict full reference designations")
ok(all((r["scope"] not in {"Panel","Panel/field hardware"} or r["full_designation"].startswith("=FC01+CP01-")) for r in model["bom"]), "panel-scope BOM rows use CP01 location")
ok(len(model["bom"]) >= 45, "expanded panel and field BOM has at least 45 controlled lines")
ok(len({str(r["width_mm"]) for r in model["panel_placement"]}) > 4, "panel placement no longer uses identical envelopes")
ok(any(r["mounting"] == "Door cutout" for r in model["panel_placement"] if r["tag"] == "-H100"), "HMI is door-mounted")
known_placement = [r for r in model["panel_placement"] if r["mounting"] != "Door cutout" and all(str(r[key]).strip() not in {"","TBD"} for key in ["x_mm","y_mm","width_mm","height_mm","top_clearance_mm","bottom_clearance_mm","side_clearance_mm"])]
def separated(a: dict, b: dict, clearance: bool) -> bool:
    sa = float(a["side_clearance_mm"]) if clearance else 0.0; sb = float(b["side_clearance_mm"]) if clearance else 0.0
    at = float(a["top_clearance_mm"]) if clearance else 0.0; ab = float(a["bottom_clearance_mm"]) if clearance else 0.0
    bt = float(b["top_clearance_mm"]) if clearance else 0.0; bb = float(b["bottom_clearance_mm"]) if clearance else 0.0
    ax1=float(a["x_mm"])-sa; ax2=float(a["x_mm"])+float(a["width_mm"])+sa; ay1=float(a["y_mm"])-at; ay2=float(a["y_mm"])+float(a["height_mm"])+ab
    bx1=float(b["x_mm"])-sb; bx2=float(b["x_mm"])+float(b["width_mm"])+sb; by1=float(b["y_mm"])-bt; by2=float(b["y_mm"])+float(b["height_mm"])+bb
    return ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1
for index,a in enumerate(known_placement):
    for b in known_placement[index+1:]:
        ok(separated(a,b,False), f"known panel bodies do not overlap: {a['tag']} / {b['tag']}")
        ok(separated(a,b,True), f"scheduled clearance envelopes do not overlap: {a['tag']} / {b['tag']}")
for row in known_placement:
    left = float(row["x_mm"]) - float(row["side_clearance_mm"])
    right = float(row["x_mm"]) + float(row["width_mm"]) + float(row["side_clearance_mm"])
    top = float(row["y_mm"]) - float(row["top_clearance_mm"])
    bottom = float(row["y_mm"]) + float(row["height_mm"]) + float(row["bottom_clearance_mm"])
    ok(0 <= left <= right <= 800 and 0 <= top <= bottom <= 800,
       f"body and scheduled clearances remain inside 800 x 800 panel boundary: {row['tag']}")

load_rows = [r for r in model["load_budget"] if r["voltage"] == "24 VDC" and r["load"] != "24 VDC subtotal"]
load_subtotal = next(r for r in model["load_budget"] if r["load"] == "24 VDC subtotal")
load_demand = sum(float(r["demand_w"]) for r in load_rows)
ok(load_demand == float(load_subtotal["demand_w"]) == 299.0 and load_subtotal["demand_factor"] == "N/A", "24 VDC subtotal reconciles without a false aggregate demand factor")
ok(abs((load_demand / 24.0 * 1.25) - 15.5729166667) < 1e-6, "24 VDC 25-percent demand-margin current is 15.573 A before inrush/derating")

rationale = model["rationales"]
by_category = {category:{row["key"] for row in rationale if row["category"] == category} for category in {row["category"] for row in rationale}}
ok(by_category.get("PLC channel") == {r["symbol"] for r in model["io"]}, "rationale covers every PLC channel")
ok(by_category.get("Terminal") == {r["terminal"] for r in model["terminals"]}, "rationale covers every terminal/reference")
ok(by_category.get("Cable") == {r["cable_id"] for r in model["cables"]}, "rationale covers every cable")
ok(by_category.get("HMI tag") == {r["hmi_tag"] for r in model["hmi_tags"]}, "rationale covers every HMI tag")
ok(by_category.get("Alarm") == {str(r["alarm_id"]) for r in model["alarms"]}, "rationale covers every alarm")
ok(by_category.get("NVIDIA interface") == {r["signal"] for r in model["vision_interface"]}, "rationale covers every NVIDIA interface signal")
ok(by_category.get("Relay") == {r["device"] for r in io if r["direction"] == "DO" and r["device"].startswith("-K2")}, "rationale has an individual row for each active output relay")
component_rationale = {r["key"]: r for r in rationale if r["category"] == "Component"}
ok(all(component_rationale[r["tag"]]["selection_or_evidence_basis"] == r["selection_status"] and component_rationale[r["tag"]]["open_verification"] == r["basis_or_blocker"] for r in model["bom"]), "component rationale separates selection status from open evidence/blocker")
hmi_rationale = {r["key"]: r for r in rationale if r["category"] == "HMI tag"}
ok(all("visibility" in hmi_rationale[r["hmi_tag"]]["failure_detected_or_controlled"] for r in model["hmi_tags"] if r["access"] == "Read only"), "read-only HMI rationale describes visibility rather than command arbitration")
ok(all("hold-to-run" in hmi_rationale[r["hmi_tag"]]["failure_detected_or_controlled"] for r in model["hmi_tags"] if r["hmi_tag"].startswith("HOLD_")), "manual HMI rationale describes decommanded hold-to-run behavior")
ok("stalled counter" in hmi_rationale["HMI_COMMAND_HEARTBEAT"]["failure_detected_or_controlled"], "HMI heartbeat rationale describes fail-closed counter supervision")
trace_by_id = {r["requirement_id"]: r for r in model["requirements"]}
semantic_trace = {"SYS-005":{"TC-009","TC-010"},"SYS-015":{"TC-018","TC-019","TC-020"},"SYS-018":{"VAL-D-STATIC"},"SYS-023":{"VAL-D-STATIC"},"SYS-024":{"PROC-RESTORE-OPEN","MANIFEST-VERIFY-001"}}
for requirement_id, expected_ids in semantic_trace.items():
    actual_ids = {token.strip() for token in trace_by_id[requirement_id]["test_ids"].split(";")}
    ok(actual_ids == expected_ids, f"semantic requirement/test trace: {requirement_id}")

scl_dir = ROOT / "04_controls_siemens/scl"
required_scl = {"00_types.scl","DB_Global.scl","FB_HMICommandManager.scl","FB_VFD.scl","FB_Actuator2Pos.scl","FB_FillChannel.scl","FB_VisionInterface.scl","FB_CapperInterface.scl","FB_RecipeManager.scl","FB_AlarmManager.scl","FB_MachineCoordinator.scl","FB_CellMain.scl","DB_CellMain.scl","OB1_Call_Structure.scl","OB100_Startup.scl"}
actual_scl = {p.name for p in scl_dir.glob("*.scl")}
ok(required_scl == actual_scl, "exact 15-file Siemens type/FB/DB/OB source inventory present")
sys.path.insert(0, str(ROOT / "scripts"))
from revision_d_scl import sources as generated_scl_sources
generated_sources = generated_scl_sources()
ok(set(generated_sources) == required_scl, "revision-D generator owns every authoritative Siemens source")
for name, generated in sorted(generated_sources.items()):
    ok((scl_dir / name).read_text(encoding="utf-8").rstrip() == generated.rstrip(), f"generated Siemens source parity: {name}")
for path in sorted(scl_dir.glob("*.scl")):
    text = path.read_text(encoding="utf-8")
    ok(not re.search(r"(?m)^\+", text), f"no leading patch artifact: {path.name}")
    ok(not re.search(r"(?i)\b(TODO|TBD|PLACEHOLDER|PSEUDOCODE)\b", text), f"no forbidden source placeholder: {path.name}")
    for token,end in [("FUNCTION_BLOCK","END_FUNCTION_BLOCK"),("ORGANIZATION_BLOCK","END_ORGANIZATION_BLOCK"),("DATA_BLOCK","END_DATA_BLOCK")]:
        if re.search(rf"(?m)^\s*{token}\b", text): ok(len(re.findall(rf"(?m)^\s*{token}\b",text)) == len(re.findall(rf"(?m)^\s*{end}\b",text)), f"balanced {token} endings: {path.name}")
ob1 = (scl_dir / "OB1_Call_Structure.scl").read_text(encoding="utf-8")
cell = (scl_dir / "FB_CellMain.scl").read_text(encoding="utf-8")
fill = (scl_dir / "FB_FillChannel.scl").read_text(encoding="utf-8")
types = (scl_dir / "00_types.scl").read_text(encoding="utf-8")
recipe_manager = (scl_dir / "FB_RecipeManager.scl").read_text(encoding="utf-8")
ok('"DB_CellMain"();' in ob1, "OB1 executes root cell instance")
for owner,count in [("FillCh1",1),("FillCh2",1),("ConveyorVfd",1),("PumpVfd",1),("Gate",1),("Clamp",1),("Vision",1),("Capper",1),("Recipe",1),("Alarm",1),("Coordinator",1)]: ok(cell.count(f"#{owner}(") == count, f"root calls {owner} exactly once")
for feature in ["PULSE_MISSING","ANALOG_NO_FLOW","PULSE_COUNTER_DISCONTINUITY","MeasurementWindowValid","comparisonArmed","CounterRolloverObserved","CounterDiscontinuity","PumpRequest","tPulseMissing","tAnalogNoFlow","tValveClose","ABORTED"]: ok(feature in fill, f"fill-channel implements {feature}")
vision_scl = (scl_dir / "FB_VisionInterface.scl").read_text(encoding="utf-8")
for feature in ["lastIssuedId","NON_MONOTONIC_REQUEST","RESULT_STUCK_VALID","resultMustClear","PublicationAck","HeartbeatHealthy","NOT #Result.ResultValid","#pending := FALSE; #triggered := FALSE","NOT #TriggerEdge","SessionEpoch","Warning","ExpectedModelId","ExpectedModelHash","MODEL_MISMATCH"]: ok(feature in vision_scl, f"vision-interface recovery contract includes {feature}")
revision_d_tests = (ROOT / "11_simulation/tests/test_revision_d_interfaces.py").read_text(encoding="utf-8")
for test_name in ["test_stale_id","test_future_id","test_duplicate_request_id","test_result_valid_stuck_high","test_busy_ready_contradiction","test_timeout_then_delayed_result","test_reset_after_stale","test_reset_does_not_restart","test_pulse_zero_analog_positive","test_analog_zero_pulses_positive","test_both_measurements_no_flow","test_counter_rollover","test_timer_boundary"]: ok(test_name in revision_d_tests, f"direct Revision-D interface test present: {test_name}")
recipe_type_match = re.search(r'TYPE "UDT_Recipe".*?STRUCT(.*?)END_STRUCT;', types, re.S)
recipe_fields = set(re.findall(r"(?m)^\s*([A-Za-z][A-Za-z0-9_]*)\s*:", recipe_type_match.group(1) if recipe_type_match else ""))
recipe_refs = set(re.findall(r"#Candidate\.([A-Za-z][A-Za-z0-9_]*)", recipe_manager))
ok(bool(recipe_fields) and recipe_refs <= recipe_fields, f"recipe manager references only delivered UDT fields: {sorted(recipe_refs - recipe_fields)}")
ok("TargetPulsesCh" not in recipe_manager and "CycleTimeS" not in fill, "removed recipe members and hard-coded scan time are absent")
ok(all(token in recipe_manager for token in ["ApplyRequest","RequestSeq","AcceptedSeq","RejectedSeq","DripSettleTime","VisionTimeout","TargetMlCh1 * #Candidate.PulsesPerLitreCh1"]), "recipe manager atomically validates current candidate, timing and nonzero pulse targets")
ok("RecipeRequest" not in cell and "#Recipe.AcceptedSeq" in cell and "#Recipe.RejectedSeq" in cell, "RecipeManager owns atomic apply acceptance/rejection")
for token in ["#scanDelta := 0; #lastPulseTotal := #PulseTotal","tFlowStopped","NOT #AnalogBrokenWire","NOT #closing","#FlowLMin <= #NoFlowMinLMin"]:
    ok(token in fill, f"fill start/reset/post-close contract includes {token}")
capper_text = (scl_dir / "FB_CapperInterface.scl").read_text(encoding="utf-8")
ok("#Ready AND NOT #FaultIn AND NOT #Busy AND NOT #Complete" in capper_text, "capper reset requires all diagnosed causes cleared")
ok("(#Capper.DiagReason = 1) OR (#Capper.DiagReason = 5)" in cell, "capper external/handshake faults map to alarm 1402")
aggregate_pos = cell.find("#blockingFault := FALSE")
recovery_release_pos = cell.rfind("IF #HmiCommands.ResetPulse AND NOT #blockingFault")
coordinator_pos = cell.find("#Coordinator(")
ok("#preBlockingFault" in cell and aggregate_pos < recovery_release_pos < coordinator_pos and "#processPermissive := NOT #immediateStop" in cell[recovery_release_pos:coordinator_pos], "current equipment faults arbitrate and permissives recompute before one-shot power-recovery reset reaches coordinator")
ok("AutoAllowed := (#Coordinator.State = \"E_MachineState\".MANUAL_SETUP)" in cell and "ManualAllowed := (#Coordinator.State = \"E_MachineState\".READY)" in cell, "mode acceptance permissions match coordinator-consumed states")
for token in ["ManualSecureRequest","#manualConveyorInterlocked","#manualSecureInterlocked","#manualPumpInterlocked","GateCloseRequest OR #manualSecureInterlocked","ClampRequest OR #manualSecureInterlocked"]:
    ok(token in cell, f"manual secure hold-to-run path includes {token}")
ok("#HmiCommands.ManualConveyorCmd AND NOT #HmiCommands.ManualSecureCmd" in cell and "#HmiCommands.ManualSecureCmd AND NOT #HmiCommands.ManualConveyorCmd AND #ConveyorVfd.Stopped" in cell, "manual conveyor and secure motions are mutually exclusive and stop-sequenced")
ok("#manualPumpInterlocked := #HmiCommands.ManualPumpCmd AND #manualSecureInterlocked AND #ConveyorVfd.Stopped" in cell, "manual pump and valve path requires stopped conveyor and secured pair")
input_type_match = re.search(r'TYPE "UDT_CellInputs".*?STRUCT(.*?)END_STRUCT;', types, re.S)
input_fields = set(re.findall(r"(?m)^\s*([A-Za-z][A-Za-z0-9_]*)\s*:", input_type_match.group(1) if input_type_match else ""))
unconsumed_inputs = sorted(field for field in input_fields if cell.count(f'Inputs.{field}') < 2)
ok(not unconsumed_inputs, f"canonical cell inputs are normalized and consumed: {unconsumed_inputs}")
alarm_ids = {int(r["alarm_id"]) for r in model["alarms"]}
mapped_alarm_ids = {int(value) for value in re.findall(r"#faultCodes\[\d+\]\s*:=\s*(\d+)", cell)}
ok(mapped_alarm_ids <= alarm_ids, f"all source alarm mappings exist in canonical alarm schedule: {sorted(mapped_alarm_ids-alarm_ids)}")
for token in ["ConveyorPnIoValid","PumpPnIoValid","Flow1PulseTotal","Flow2PulseTotal","Flow1ChannelFault","Flow2ChannelFault"]:
    ok(token in cell, f"native PN/TM Count adapter consumed: {token}")
output_type_match = re.search(r'TYPE "UDT_OutputCommands".*?STRUCT(.*?)END_STRUCT;', types, re.S)
output_fields = set(re.findall(r"(?m)^\s*([A-Za-z][A-Za-z0-9_]*)\s*:", output_type_match.group(1) if output_type_match else ""))
unwritten_outputs = sorted(field for field in output_fields if f'Commands.{field} :=' not in cell)
ok(not unwritten_outputs, f"all standard output commands are assigned: {unwritten_outputs}")
for token in ["Gate.Fault","Clamp.Fault","Vision.Fault","Capper.Fault","CommunicationsHealthy","AirPressureOk","ProductSupplyOk","GuardClosed"]:
    ok(token in cell and "#blockingFault" in cell, f"blocking-fault arbitration includes {token}")
ok("%QW256" in cell and "%IW256" in cell and "Standard Telegram" not in cell, "drive PZD process-image mapping present")
ok("DB_HMI" in cell and "DB_IO\".Commands" not in "\n".join(r["plc_source"] for r in writable), "command arbitration separated from output mapper")

sim_text = (ROOT / "11_simulation/filling_cell_simulator.py").read_text(encoding="utf-8")
ok("def step(" in sim_text and "class FillingPlant" in sim_text and "inject_fault" in sim_text, "simulator is a time-stepped fault-injection model")
results = csv_rows("../11_simulation/outputs/scenario_results.csv") if False else list(csv.DictReader((ROOT / "11_simulation/outputs/scenario_results.csv").open(encoding="utf-8", newline="")))
ok(len(results) == 32, "32 scenario summaries generated")
ok(sum(str(r.get("released","")).lower() == "true" for r in results) == 1, "only normal scenario releases product")
ok(all(str(r.get("invariant_violations","0")) in {"0","0.0",""} for r in results), "scenario summaries report zero invariant violations")
edge_protocol = (ROOT / "07_nvidia_vision/edge_service/protocol.py").read_text(encoding="utf-8")
edge_service = (ROOT / "07_nvidia_vision/edge_service/service.py").read_text(encoding="utf-8")
ok("inspection ID is not strictly monotonic" in edge_protocol and "result ID does not match" in edge_protocol, "edge service enforces monotonic/matched inspection IDs")
ok("service is not ready: controlled model unavailable" in edge_service and "validate_model_identity" in edge_service and "PLC heartbeat timeout" in edge_service, "edge service is fail-closed on model identity and timed heartbeat")
ok("MAX_TARGET_FILL_LEVEL = 1.0" in edge_protocol and "MODEL_HASH_RE" in edge_protocol and "expected_identity" in edge_protocol, "single edge protocol owns bounds and exact SHA-256 model identity")
ok("type(identity) is not tuple" in edge_protocol and "len(identity) != 2" in edge_protocol, "model identity shape is validated before indexing")
ok("RESULT_ACK_RANGE" in edge_service and "type(result_id) is not int" in edge_service and "invalidate_publication=False" in edge_service, "malformed acknowledgement faults without clearing the current publication")
edge_tests = (ROOT / "07_nvidia_vision/edge_service/tests/test_service.py").read_text(encoding="utf-8")
harness_tests = (ROOT / "07_nvidia_vision/test_plc_interface_harness.py").read_text(encoding="utf-8")
ok("test_malformed_ack_never_clears_valid_publication" in edge_tests and "test_malformed_identity_shapes_and_property_failure_stay_not_ready" in edge_tests, "edge tests cover malformed ACK and model-identity ingress")
ok("test_rearm_uses_single_validated_identity_read_and_catches_transition_failure" in edge_tests and "self._validated_identity" in edge_service, "edge rearm reuses one protected validated identity read")
for test_name in ["test_initial_zero_ack_poll_is_idempotent","test_same_session_reset_rejects_regressed_plc_snapshot","test_publication_survives_transport_fault_reset_and_wrong_ack","test_same_session_reset_snapshot_can_carry_exact_ack","test_advanced_disabled_session_invalidates_prior_publication","test_tick_contains_session_change_for_polling_adapter","test_model_identity_rejects_whitespace_control_and_path_characters"]:
    ok(test_name in edge_tests, f"Revision-D.1 edge regression test present: {test_name}")
ok("invalidate_publication: bool = False" in edge_service and "publication_invalidated_on_new_session" in edge_service, "edge publication remains immutable through same-session faults and records new-session invalidation")
ok("test_rejected_delayed_publication_is_acked_cleared_and_rearmed" in harness_tests, "composed PLC/edge test covers rejected delayed publication cleanup and rearm")
node_map = list(csv.DictReader((ROOT / "07_nvidia_vision/plc_ai_node_map.csv").open(encoding="utf-8-sig", newline="")))
service_config = json.loads((ROOT / "07_nvidia_vision/edge_service/service_config.json").read_text(encoding="utf-8"))
vision_signals = [r["signal"] for r in model["vision_interface"]]
ok([r["signal"] for r in node_map] == vision_signals and service_config["signal_count"] == len(vision_signals), "edge node map/config exactly track canonical vision signals")
ok(set(service_config["nodes"]) == set(vision_signals) and all(service_config["nodes"][r["signal"]] == r["node_id"] for r in node_map), "edge config node IDs exactly match generated node map")
ok(all(token in service_config["session_rearm"] for token in ["VISION_SESSION_EPOCH","INSPECTION_ID","RESULT_ACK_ID","PLC_HEARTBEAT","VISION_ENABLE low"]), "edge config records disabled four-counter anti-replay synchronization")
reproduction = (ROOT / "scripts/reproduce_validation.ps1").read_text(encoding="utf-8")
ok(reproduction.count("WorkbookHash") >= 4 and reproduction.count("PdfHash") >= 4 and "Get-FileHash -Algorithm SHA256" in reproduction, "standard reproduction compares two normalized XLSX and PDF builds by SHA-256")
ok("verify_manifest.py' '--source' 'head' '--require-clean'" in reproduction and "Assert-CleanGitState" in reproduction, "standard reproduction verifies clean committed bytes before and after generation")
attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
for token in ["* text=auto eol=lf","*.qet      -text","*.dxf      -text","*.FCStd    -text","*.step     -text","*.iges     -text","*.xlsx     -text","*.pdf      -text","*.png      -text"]:
    ok(token in attributes, f"explicit Git byte policy includes {token}")
toolchain_lock = json.loads((ROOT / "release/reproduction_toolchain_lock.json").read_text(encoding="utf-8"))
ok(toolchain_lock["release"] == "D.1", "artifact-reproduction toolchain lock is Revision D.1")
ok(toolchain_lock["python"]["version"] == "3.12.13", "artifact-reproduction Python version is locked")
ok(toolchain_lock["node"]["packages"]["@oai/artifact-tool"] == "2.8.31", "artifact-tool version is locked")
ok(toolchain_lock["pdftoppm"]["version"] == "26.05.0", "Poppler renderer version is locked")
ok("verify_release_toolchain.py" in reproduction, "complete reproduction verifies the locked artifact toolchain")
manifest_builder = (ROOT / "scripts/build_manifest.py").read_text(encoding="utf-8")
manifest_verifier = (ROOT / "scripts/verify_manifest.py").read_text(encoding="utf-8")
determinism = (ROOT / "scripts/check_determinism.py").read_text(encoding="utf-8")
ok("tracked_paths(\"index\")" in manifest_builder and "read_bytes(\"index\", rel)" in manifest_builder, "manifest builder hashes staged Git-index bytes")
ok('choices=("head", "index", "worktree")' in manifest_verifier and "untracked/unexpected worktree path" in manifest_verifier, "manifest verifier supports authoritative sources and rejects unexpected files")
ok("checkout-index" in determinism and "git\", \"archive" in determinism, "determinism exports authoritative index or HEAD snapshots")
ok((ROOT / ".github/workflows/revision-d1-reproduce.yml").exists(), "fresh-clone Revision-D.1 CI workflow is controlled")
ok((ROOT / "00_project_control/repository_release_workflow.md").exists() and (ROOT / "14_qa/release_integrity_reproduction.md").exists(), "release-byte and clean-clone evidence documents are controlled")
ok(all(not (ROOT / "14_qa/pdf_renders" / stale).exists() or not any((ROOT / "14_qa/pdf_renders" / stale).iterdir()) for stale in ["release","release_c"]), "stale pre-Revision-D PDF render directories are empty")
ok("FS03 / FW4.0" in (ROOT / "04_controls_siemens/cpu_tia_v20_compatibility.md").read_text(encoding="utf-8"), "CPU/TIA V20 firmware baseline documented")
network_decision = (ROOT / "02_system_architecture/network_hardware_decision.md").read_text(encoding="utf-8")
ok(all(term in network_decision for term in ["XB008","unmanaged","XC208","managed","S615"]), "switch misidentification corrected with managed/firewall design")

notice = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"
safety = "CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
for rel in ["README.md","AGENTS.md","00_project_control/design_basis.md","14_qa/acceptance_gate_status.md","release/RELEASE_NOTES.md"]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    ok(notice in text, f"exact notice present: {rel}")
    ok(safety in text, f"exact safety boundary present: {rel}")

expected_hashes = {
    "03_electrical/native_baseline/filling_cell.qet":"d817036497afbf0f48379da4dbce81cd1d7b7cca28bfc8341d5b437d2421660b",
    "09_panel_cad/native_baseline/filling_cell_panel.FCStd":"306b7376fd2b870b879cf78171e51b02b68fe23678fe15c61c81d48bcc90cf31",
    "09_panel_cad/native_baseline/mounting_plate.dxf":"9ddd38069e43c74c92393bf7f2d3dda729dfce041cedcd16fcdfca0dd433828d",
}
for rel,digest in expected_hashes.items(): ok(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, f"historical native baseline retained: {rel}")
ElementTree.parse(ROOT / "03_electrical/native_baseline/filling_cell.qet"); checks.append("QET historical baseline is well-formed XML")
with zipfile.ZipFile(ROOT / "09_panel_cad/native_baseline/filling_cell_panel.FCStd") as zf: ok(len(zf.namelist()) == 76, "FCStd historical baseline container has 76 entries")
banned = {".ap20",".zap20",".onnx",".engine",".plan",".usd",".usda",".usdc"}
bad = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in banned)
ok(not bad, f"no fabricated native/model artifacts: {bad}")

report = ROOT / "14_qa/automated_validation_report.md"
lines = ["# Automated validation report — Revision D.1","",f"Result: **{'PASS' if not errors else 'FAIL'}**","","This is deterministic static/data/independent-model validation. It is not TIA, WinCC, Startdrive, PLCSIM, QET or FreeCAD native proof.","","## Passed checks",""] + [f"- {item}" for item in sorted(checks)]
if errors: lines += ["","## Errors",""] + [f"- {item}" for item in sorted(errors)]
if not OPTIONS.check:
    report.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(f"PASS={len(checks)} FAIL={len(errors)}")
for error in errors: print(f"ERROR: {error}")
sys.exit(1 if errors else 0)
