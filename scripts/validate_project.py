from __future__ import annotations

import csv
import configparser
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []
checks: list[str] = []


def ok(condition: bool, message: str) -> None:
    (checks if condition else errors).append(message)


model = json.loads((ROOT / "00_project_control/canonical_model.json").read_text(encoding="utf-8"))
required_dirs = [f"{i:02d}_{name}" for i, name in enumerate([
    "project_control", "requirements", "system_architecture", "electrical", "controls_siemens",
    "hmi", "drives", "nvidia_vision", "digital_twin", "panel_cad", "schedules", "simulation",
    "testing", "documentation", "qa"
])] + ["release"]
for directory in required_dirs:
    ok((ROOT / directory).is_dir(), f"required directory {directory}")

io = model["io"]
symbols = [row["symbol"] for row in io]
addresses = [row["address"] for row in io]
ok(len(symbols) == len(set(symbols)), "PLC symbols unique")
ok(len(addresses) == len(set(addresses)), "PLC addresses/module channels unique")
ok(sum(r["direction"] == "DI" for r in io) == 32, "32 DI channels allocated")
ok(sum(r["direction"] == "DO" for r in io) == 32, "32 DO channels allocated")
ok(sum(r["direction"] == "AI" for r in io) == 8, "8 AI channels allocated")
ok(sum(r["direction"] == "HSC" for r in io) == 2, "two independent HSC channels allocated")

required_io = {
    "BOTTLE_AT_NEST_1", "BOTTLE_AT_NEST_2", "CLAMP_ENGAGED_FB", "GATE_CLOSED_FB",
    "FLOW_1_MA_RAW", "FLOW_2_MA_RAW", "FLOW_1_PULSE", "FLOW_2_PULSE", "PUMP_FAULT",
    "FILL_VALVE_1_OPEN_CMD", "FILL_VALVE_2_OPEN_CMD", "CAPPER_READY", "CAPPER_BUSY",
    "CAPPER_COMPLETE", "CAPPER_FAULT", "CAPPER_REQUEST"
}
ok(required_io.issubset(symbols), "required two-bottle/fill/capper I/O present")

required_vision = {
    "VISION_ENABLE", "INSPECTION_TRIGGER", "INSPECTION_ID", "RECIPE_ID", "EXPECTED_BOTTLES",
    "TARGET_FILL_LEVEL", "PLC_HEARTBEAT", "VISION_READY", "VISION_BUSY", "RESULT_VALID",
    "RESULT_ID", "BOTTLE_1_PASS", "BOTTLE_2_PASS", "FILL_1_STATUS", "FILL_2_STATUS",
    "LEAK_OR_SPILL_DETECTED", "LOW_CONFIDENCE", "VISION_WARNING", "VISION_FAULT",
    "INFERENCE_TIME", "VISION_HEARTBEAT"
}
vision_names = {row["signal"] for row in model["vision_interface"]}
ok(vision_names == required_vision, "PLC-AI contract has exact required signal set")
ok(len({r["alarm_id"] for r in model["alarms"]}) == len(model["alarms"]), "alarm numbers unique")
ok(len(model["tests"]) == 32, "all 32 required regression scenarios controlled")
ok(len(model["states"]) == 10, "all ten required operating states controlled")

deepstream = configparser.ConfigParser()
deepstream.read(ROOT / "07_nvidia_vision/deepstream_app_config.txt", encoding="utf-8")
ok({"application", "source0", "streammux", "primary-gie", "sink0"}.issubset(deepstream.sections()), "DeepStream design configuration parses with required sections")
infer = configparser.ConfigParser()
infer.read(ROOT / "07_nvidia_vision/config_infer_primary.txt", encoding="utf-8")
ok({"property", "class-attrs-all"}.issubset(infer.sections()), "DeepStream inference design configuration parses")
annotation = json.loads((ROOT / "07_nvidia_vision/annotation_schema.json").read_text(encoding="utf-8"))
ok(annotation["status"] == "NO DATASET - SCHEMA ONLY" and len(annotation["classes"]) == 7, "annotation schema is explicit, parseable and untrained")

for csv_path in sorted(ROOT.rglob("*.csv")):
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        ok(bool(rows and rows[0]), f"CSV parses and has header: {csv_path.relative_to(ROOT)}")
    except Exception as exc:
        errors.append(f"CSV parse failed {csv_path.relative_to(ROOT)}: {exc}")

notice = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"
safety = "CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
for path in [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "00_project_control/design_basis.md", ROOT / "14_qa/acceptance_gate_status.md", ROOT / "release/RELEASE_NOTES.md"]:
    text = path.read_text(encoding="utf-8")
    ok(notice in text, f"notice present: {path.relative_to(ROOT)}")
    ok(safety in text, f"safety boundary present: {path.relative_to(ROOT)}")

required_scl = {"00_types.scl", "FB_VFD.scl", "FB_Actuator2Pos.scl", "FB_FillChannel.scl", "FB_VisionInterface.scl", "FB_RecipeManager.scl", "FB_AlarmManager.scl", "FB_MachineCoordinator.scl", "OB1_Call_Structure.scl"}
scl_dir = ROOT / "04_controls_siemens/scl"
ok(required_scl.issubset({p.name for p in scl_dir.glob("*.scl")}), "modular Siemens SCL source set present")
for path in scl_dir.glob("*.scl"):
    text = path.read_text(encoding="utf-8")
    ok("ILLUSTRATIVE PSEUDOCODE" not in text.upper(), f"no pseudocode claim: {path.name}")

# Quarantined native baselines must exactly match the audited primary package.
expected_hashes = {
    "03_electrical/native_baseline/filling_cell.qet": "d817036497afbf0f48379da4dbce81cd1d7b7cca28bfc8341d5b437d2421660b",
    "09_panel_cad/native_baseline/filling_cell_panel.FCStd": "306b7376fd2b870b879cf78171e51b02b68fe23678fe15c61c81d48bcc90cf31",
    "09_panel_cad/native_baseline/filling_cell_panel.step": "6340777b10172ba7cae5b1749cb5611d00f5dc2f8371ac249a0dd921e96db36a",
    "09_panel_cad/native_baseline/filling_cell_panel.iges": "ad6447e85e81e4960e3e2b8f68287dafe0554401b24169f4ffde34d47fe26630",
    "09_panel_cad/native_baseline/mounting_plate.dxf": "9ddd38069e43c74c92393bf7f2d3dda729dfce041cedcd16fcdfca0dd433828d",
}
for rel, expected in expected_hashes.items():
    payload = (ROOT / rel).read_bytes()
    ok(hashlib.sha256(payload).hexdigest() == expected, f"audited baseline hash retained: {rel}")
try:
    qet = ROOT / "03_electrical/native_baseline/filling_cell.qet"
    ElementTree.parse(qet)
    ok(True, "QET baseline is well-formed XML")
except Exception as exc:
    errors.append(f"QET XML parse failed: {exc}")
try:
    with zipfile.ZipFile(ROOT / "09_panel_cad/native_baseline/filling_cell_panel.FCStd") as zf:
        ok(len(zf.namelist()) == 76, "FCStd baseline ZIP has audited 76 entries")
except Exception as exc:
    errors.append(f"FCStd container failed: {exc}")
ok((ROOT / "09_panel_cad/native_baseline/filling_cell_panel.step").read_text(encoding="latin-1", errors="ignore").startswith("ISO-10303-21"), "STEP exchange header valid")

# No fabricated native outputs may appear outside the explicitly audited baseline.
banned = {".ap", ".ap15_1", ".ap16", ".ap17", ".ap18", ".ap19", ".ap20", ".zap", ".zap15_1", ".zap16", ".zap17", ".zap18", ".zap19", ".zap20", ".onnx", ".engine", ".plan", ".usd", ".usda", ".usdc"}
bad_files = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in banned]
ok(not bad_files, "no fabricated TIA/model/engine/USD native file delivered")

# Cross-file schedule equality with canonical source.
with (ROOT / "10_schedules/plc_io.csv").open(encoding="utf-8-sig", newline="") as handle:
    schedule_io = list(csv.DictReader(handle))
ok(schedule_io == [{k: str(v) for k, v in row.items()} for row in io], "PLC I/O schedule exactly derives from canonical model")

report = ROOT / "14_qa/automated_validation_report.md"
lines = ["# Automated validation report", "", f"Result: **{'PASS' if not errors else 'FAIL'}**", "", "## Passed checks", ""]
lines.extend(f"- {item}" for item in checks)
if errors:
    lines.extend(["", "## Errors", ""] + [f"- {item}" for item in errors])
report.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Hash manifest excludes itself and temporary render folders.
manifest_rows = []
for path in sorted(ROOT.rglob("*")):
    if (not path.is_file() or path.name in {"manifest.json", "manifest.csv"} or
            "qa_renders" in path.parts or "__pycache__" in path.parts or
            path.suffix.lower() in {".pyc", ".pyo"} or path.name.endswith(".inspect.ndjson")):
        continue
    rel = path.relative_to(ROOT).as_posix()
    manifest_rows.append({"path": rel, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT / "release/manifest.json").write_text(json.dumps({"project":"FC01","revision":"B","status":"PARTIALLY COMPLETE","files":manifest_rows}, indent=2), encoding="utf-8")
with (ROOT / "release/manifest.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"]); writer.writeheader(); writer.writerows(manifest_rows)

print(f"PASS={len(checks)} FAIL={len(errors)} manifest_files={len(manifest_rows)}")
if errors:
    for item in errors: print(f"ERROR: {item}")
    sys.exit(1)
