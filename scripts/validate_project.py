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
ok(model["project"]["revision"] == "C", "canonical revision C")
ok(model["project"]["status"].startswith("PARTIALLY COMPLETE"), "truthful partial release status")

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
    "plc_io.csv":"io","siemens_hardware.csv":"hardware","drive_interfaces.csv":"drive_interfaces","hmi_tags.csv":"hmi_tags","alarms.csv":"alarms","nvidia_interface_tags.csv":"vision_interface","bom.csv":"bom","point_to_point_connections.csv":"connections","wire_list.csv":"connections","terminal_plan.csv":"terminals","cable_schedule.csv":"cables","panel_placement.csv":"panel_placement","network_nodes.csv":"network","load_budget.csv":"load_budget","vfd_parameters.csv":"vfd_parameters","requirements_traceability.csv":"requirements","test_coverage.csv":"tests","input_request_register.csv":"input_requests","acceptance_gates.csv":"acceptance_gates"
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
used_cables = {r["cable_id"] for r in external_connections}
ok(used_cables == {r["cable_id"] for r in model["cables"]}, "every cable is referenced by connection records")
for do_symbol in physical_do:
    paths = [r["function"] for r in connections if r["signal"] == do_symbol]
    ok({"PLC output to relay coil","Relay coil return","Relay contact supply","Relay contact 14 to field load","Field load return"}.issubset(paths), f"complete relay coil/contact/load path: {do_symbol}")
ok({"X24:+24V","X0:0V","X0:MANA","SC100:1"}.issubset({r["terminal"] for r in model["terminals"]}), "power, analog-reference and shield reference terminals are scheduled")
for hsc_symbol in {r["symbol"] for r in io if r["direction"] == "HSC"}:
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
trace_by_id = {r["requirement_id"]: r for r in model["requirements"]}
semantic_trace = {"SYS-005":{"TC-009","TC-010"},"SYS-015":{"TC-018","TC-019","TC-020"},"SYS-018":{"VAL-C-STATIC"},"SYS-023":{"VAL-C-STATIC"},"SYS-024":{"PROC-RESTORE-OPEN","MANIFEST-VERIFY-001"}}
for requirement_id, expected_ids in semantic_trace.items():
    actual_ids = {token.strip() for token in trace_by_id[requirement_id]["test_ids"].split(";")}
    ok(actual_ids == expected_ids, f"semantic requirement/test trace: {requirement_id}")

scl_dir = ROOT / "04_controls_siemens/scl"
required_scl = {"00_types.scl","DB_Global.scl","FB_HMICommandManager.scl","FB_VFD.scl","FB_Actuator2Pos.scl","FB_FillChannel.scl","FB_VisionInterface.scl","FB_CapperInterface.scl","FB_RecipeManager.scl","FB_AlarmManager.scl","FB_MachineCoordinator.scl","FB_CellMain.scl","DB_CellMain.scl","OB1_Call_Structure.scl","OB100_Startup.scl"}
actual_scl = {p.name for p in scl_dir.glob("*.scl")}
ok(required_scl == actual_scl, "exact 15-file Siemens type/FB/DB/OB source inventory present")
sys.path.insert(0, str(ROOT / "scripts"))
from revision_c_scl import sources as generated_scl_sources
generated_sources = generated_scl_sources()
ok(set(generated_sources) == required_scl, "revision-C generator owns every authoritative Siemens source")
for name, generated in generated_sources.items():
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
for feature in ["UDINT#4294967295","AnalogBrokenWire","NoFlow","ContinuedFlow","PulseAnalogDisagreement","Underfill :=","Overfill :=","tValveClose","ABORTED"]: ok(feature in fill, f"fill-channel implements {feature}")
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
ok("FS03 / FW4.0" in (ROOT / "04_controls_siemens/cpu_tia_v20_compatibility.md").read_text(encoding="utf-8"), "CPU/TIA V20 firmware baseline documented")
network_decision = (ROOT / "02_system_architecture/network_hardware_decision.md").read_text(encoding="utf-8")
ok("XB008 unmanaged" in network_decision and "XC208 managed" in network_decision and "S615" in network_decision, "switch misidentification corrected with managed/firewall design")

notice = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"
safety = "CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
for rel in ["README.md","AGENTS.md","00_project_control/design_basis.md","14_qa/acceptance_gate_status.md","release/RELEASE_NOTES.md"]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    ok(notice in text, f"exact notice present: {rel}")
    ok(safety in text, f"exact safety boundary present: {rel}")

expected_hashes = {
    "03_electrical/native_baseline/filling_cell.qet":"d817036497afbf0f48379da4dbce81cd1d7b7cca28bfc8341d5b437d2421660b",
    "09_panel_cad/native_baseline/filling_cell_panel.FCStd":"306b7376fd2b870b879cf78171e51b02b68fe23678fe15c61c81d48bcc90cf31",
}
for rel,digest in expected_hashes.items(): ok(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, f"historical native baseline retained: {rel}")
ElementTree.parse(ROOT / "03_electrical/native_baseline/filling_cell.qet"); checks.append("QET historical baseline is well-formed XML")
with zipfile.ZipFile(ROOT / "09_panel_cad/native_baseline/filling_cell_panel.FCStd") as zf: ok(len(zf.namelist()) == 76, "FCStd historical baseline container has 76 entries")
banned = {".ap20",".zap20",".onnx",".engine",".plan",".usd",".usda",".usdc"}
bad = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in banned]
ok(not bad, f"no fabricated native/model artifacts: {bad}")

report = ROOT / "14_qa/automated_validation_report.md"
lines = ["# Automated validation report — Revision C","",f"Result: **{'PASS' if not errors else 'FAIL'}**","","This is static/data/dynamic-source validation. It is not TIA, WinCC, Startdrive, PLCSIM, QET or FreeCAD native proof.","","## Passed checks",""] + [f"- {item}" for item in checks]
if errors: lines += ["","## Errors",""] + [f"- {item}" for item in errors]
if not OPTIONS.check:
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"PASS={len(checks)} FAIL={len(errors)}")
for error in errors: print(f"ERROR: {error}")
sys.exit(1 if errors else 0)
