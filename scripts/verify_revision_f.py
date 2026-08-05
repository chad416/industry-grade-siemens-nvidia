"""Independent deterministic Revision-F NVIDIA-readiness consistency checks."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTICE = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"
SAFETY = (
    "CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, "
    "VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, "
    "SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
)
AI_BOUNDARY = (
    "THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF "
    "PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL."
)
PARSER = argparse.ArgumentParser()
PARSER.add_argument("--check", action="store_true", help="Do not rewrite the controlled report")
OPTIONS = PARSER.parse_args()
passed: list[str] = []
failed: list[str] = []


def check(condition: bool, description: str) -> None:
    (passed if condition else failed).append(description)


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


model = json.loads(text("00_project_control/canonical_model.json"))
vision = model["vision_interface"]
signals = [row["signal"] for row in vision]
check(model["project"]["revision"] == "F", "canonical model identifies Revision F")
check(len(vision) == len(set(signals)) == 47, "PLC-AI contract contains 47 unique signals")
check(sum(row["owner"] == "PLC" for row in vision) == 13, "PLC owns exactly 13 contract signals")
check(sum(row["owner"] == "NVIDIA" for row in vision) == 34, "NVIDIA owns exactly 34 contract signals")
check("RESULT_AGE_MS" not in signals, "result age is not transported from the edge")
check("ResultAgeMs" in text("04_controls_siemens/scl/DB_Global.scl"), "PLC exposes its derived result age")
check("#Vision.ResultAgeMs" in text("04_controls_siemens/scl/FB_CellMain.scl"), "PLC result age comes from the transaction FB")

required_additive = {
    "MAINTENANCE_MODE", "EXPECTED_DATASET_ID", "EXPECTED_CALIBRATION_ID", "CAPTURE_ACK_ID",
    "PROCESSING_STATE", "SERVICE_HEALTHY", "CAMERA_HEALTHY", "MODEL_LOADED",
    "MAINTENANCE_ACTIVE", "RESULT_DISPOSITION", "REASON_BITS", "CONFIDENCE", "DATASET_ID",
    "CALIBRATION_ID", "CAPTURE_TIMESTAMP_UTC_MS", "INFERENCE_TIMESTAMP_UTC_MS",
    "PUBLICATION_TIMESTAMP_UTC_MS", "PROCESSING_TIME_MS", "DIAGNOSTIC_CODE", "QUEUE_DEPTH",
}
check(required_additive <= set(signals), "all 20 Revision-F additive transport signals are controlled")
check(all(row["opcua_type"] and row["update_rule"] and row["invalid_action"] for row in vision), "every contract row defines type, update and invalid behavior")

schedule = rows("10_schedules/nvidia_interface_tags.csv")
node_map = rows("07_nvidia_vision/plc_ai_node_map.csv")
bindings = rows("04_controls_siemens/opcua_symbol_bindings_revision_f.csv")
configuration = json.loads(text("07_nvidia_vision/edge_service/service_config.json"))
check(schedule == [{key: str(value) for key, value in row.items()} for row in vision], "canonical and schedule contract rows match exactly")
check([row["signal"] for row in node_map] == signals, "edge CSV node order matches the canonical contract")
check([row["signal"] for row in bindings] == signals, "Siemens symbol bindings cover the canonical contract exactly")
check(configuration["namespace_version"] == "FC01.Vision.v3", "edge configuration uses the versioned v3 namespace")
check(configuration["signal_count"] == 47 and set(configuration["nodes"]) == set(signals), "edge configuration controls all 47 nodes")
check(all(configuration["nodes"][row["signal"]] == row["node_id"] for row in node_map), "edge JSON and CSV node identifiers match exactly")

schema = json.loads(text("07_nvidia_vision/edge_service/service_config.schema.json"))
check(schema.get("additionalProperties") is False, "service configuration schema rejects unknown top-level keys")
check({"status", "namespace_version", "nodes"} <= set(schema.get("required", [])), "service schema requires identity and node map")
check(json.loads(text("07_nvidia_vision/model_bundle.schema.json")).get("additionalProperties") is False, "model-bundle schema rejects unknown top-level keys")

for relative in (
    "07_nvidia_vision/edge_service/vision_runtime.py",
    "07_nvidia_vision/dataset_tool.py",
    "07_nvidia_vision/edge_service/benchmark_harness.py",
    "07_nvidia_vision/edge_service/dependency_inventory.py",
    "07_nvidia_vision/dataset_model_engineering_specification.md",
    "07_nvidia_vision/vision_architecture_trade_study.md",
    "07_nvidia_vision/vision_commissioning_cybersecurity_runbook.md",
    "13_documentation/ai_maintenance_backup.md",
    "13_documentation/ai_troubleshooting_guide.md",
):
    check((ROOT / relative).is_file(), f"Revision-F implementation artifact exists: {relative}")

runtime = text("07_nvidia_vision/edge_service/vision_runtime.py")
check(all(token in runtime for token in ("RecordedDirectorySource", "MockModelAdapter", "OnnxAdapterStructure", "production_authorized")), "runtime has recorded, mock and authorization-gated model boundaries")
check("DEVELOPMENT_BACKEND_PROHIBITED" in text("07_nvidia_vision/edge_service/service.py"), "development backend cannot authorize production readiness")
check("SignAndEncrypt" in text("07_nvidia_vision/edge_service/opcua_runtime_config.json"), "OPC UA runtime requires signed and encrypted transport")
check("_validate_contract_document" in text("07_nvidia_vision/edge_service/opcua_adapter.py") and "configuration_sha256" in text("07_nvidia_vision/edge_service/observability.py"), "configuration schema executes and hashes are structured-log fields")
check("DurableJsonlAuditSink" in text("07_nvidia_vision/edge_service/observability.py") and "AUDIT_STORAGE_FAILURE" in text("07_nvidia_vision/edge_service/service.py"), "durable audit failure has a publication interlock")
check("await self._publish_status()\n                await self._publish_result(result)" in text("07_nvidia_vision/edge_service/opcua_adapter.py"), "terminal status is published before RESULT_VALID")

manifest = rows("07_nvidia_vision/dataset_manifest.csv")
check(len(manifest) == 0, "controlled dataset manifest remains empty and makes no data claim")
annotation = json.loads(text("07_nvidia_vision/annotation_schema.json"))
check("NO REPRESENTATIVE DATASET" in annotation["status"], "annotation schema explicitly states that representative data are absent")
check("NOT TRAINED" in text("07_nvidia_vision/model_card.md"), "model card explicitly states that no model is trained")
check("NOT TARGET PERFORMANCE" in text("07_nvidia_vision/edge_service/benchmark_harness.py"), "benchmark harness cannot be presented as target performance")

vision_sil = json.loads(text("11_simulation/vision_fault_scenarios.json"))
results = rows("11_simulation/outputs/vision_fault_results.csv")
check(len(vision_sil) == len({row["scenario"] for row in vision_sil}) == 28, "vision behavioral injection matrix contains 28 unique named cases")
check(len(results) == 28, "vision behavioral injection output contains 28 results")
check(sum(row["product_released"] == "True" for row in results) == 1, "only the exact normal-pass behavioral injection releases product")
check(all(row["pump_cmd"] == row["valve_1_cmd"] == row["valve_2_cmd"] == "False" for row in results), "all vision behavioral injection results leave process outputs decommanded")
check(all(row["automatic_restart"] == "False" for row in results), "no vision behavioral injection result initiates automatic restart")

requirements = rows("10_schedules/vision_requirements.csv")
tests = rows("10_schedules/test_coverage.csv")
check(len(requirements) == 20 and requirements[0]["requirement_id"] == "SYS-026" and requirements[-1]["requirement_id"] == "SYS-045", "twenty Revision-F vision requirements are traceable")
check(len(tests) == 72 and sum(row["test_type"] == "BEHAVIORAL_FAULT_INJECTION_MODEL" for row in tests) == 28 and sum(row["test_type"] == "SOURCE_OR_INTEGRATION_VERIFICATION" for row in tests) == 12, "test schedule retains 32 process, 28 behavioral vision injections and 12 source/integration records")
controlled_test_ids = {row["test_id"] for row in tests}
unresolved_test_ids = sorted({test_id.strip() for row in requirements for test_id in row["test_ids"].split(";") if test_id.strip() not in controlled_test_ids})
check(not unresolved_test_ids, f"every Revision-F requirement test reference resolves: {unresolved_test_ids}")

hmi_tags = rows("05_hmi/vision_tags_revision_f.csv")
reason_bits = rows("05_hmi/vision_reason_bits_revision_f.csv")
state_texts = rows("05_hmi/vision_state_texts_revision_f.csv")
alarms = rows("05_hmi/vision_alarms_revision_f.csv")
faceplate = rows("05_hmi/vision_faceplate_revision_f.csv")
check(len(hmi_tags) == len({row["name"] for row in hmi_tags}) == 60, "Revision-F HMI schedule contains 60 unique tags")
check({row["plc_binding"] for row in bindings} <= {row["plc_source"] for row in hmi_tags}, "HMI diagnostics cover all 47 PLC-AI contract bindings")
check(len(reason_bits) == 16 and len({row["mask"] for row in reason_bits}) == 16, "HMI has 16 unique reason-bit definitions")
check(len(state_texts) == 35, "HMI has 35 controlled state and diagnostic texts")
check(len(alarms) == 6 and len(faceplate) == 18, "HMI has 6 vision alarms and 18 faceplate objects")
check(not any("Write" in row["access"] and not row["plc_source"].startswith("DB_HMI.") for row in hmi_tags), "HMI has no direct writable edge or process-output path")

pzd = rows("06_drives/pzd_map_revision_f.csv")
parameters = rows("06_drives/startdrive_parameter_baseline_revision_f.csv")
check(len(pzd) == 8, "drive PZD schedule contains the two four-word telegram maps")
check(len(parameters) == 18, "Startdrive parameter baseline contains 18 controlled rows")
check(not any("NVIDIA" in " ".join(row.values()).upper() for row in pzd), "NVIDIA has no drive PZD ownership")

electrical = rows("10_schedules/nvidia_electrical_delta.csv")
load_rows = [row for row in model["load_budget"] if row["load"].startswith("Vision ") and row["load"] != "Vision edge + camera + lighting"]
check(len(electrical) == 10, "NVIDIA electrical delta controls ten branch, terminal, network and grounding records")
check(abs(sum(float(row["allowance_w"]) for row in electrical) - 100.0) < 1e-9, "NVIDIA electrical delta retains the 100 W provisional allowance")
check(abs(sum(float(row["demand_w"]) for row in load_rows) - 100.0) < 1e-9, "canonical load split reconciles to the 100 W allowance")
check(all(row["status"] in {"PROVISIONAL", "RESERVED", "SPARE"} for row in electrical), "electrical delta does not misstate provisional selections as final")
check(all(row.get("rationale", "").strip() for row in electrical), "every NVIDIA electrical-delta item has explicit rationale")
delta_cables = [row["cable_id"] for row in electrical if row["cable_id"]]
check(len(delta_cables) == len(set(delta_cables)), "NVIDIA electrical-delta cable identifiers are unique")
check(all("+FS01-" not in row["designation"] for row in electrical), "NVIDIA field designations use the canonical FLD location")

versions = {row["domain"]: row for row in rows("10_schedules/nvidia_version_baseline.csv")}
check(versions["DeepStream target"]["version"] == "9.1", "DeepStream planning baseline is 9.1")
check(versions["TAO skill bank"]["version"] == "7.0.1", "TAO planning baseline is 7.0.1")
check(versions["Generic TensorRT"]["version"] == "11.1" and "NOT JETSON" in versions["Generic TensorRT"]["status"], "generic TensorRT is not misrepresented as a Jetson target lock")

gates = rows("00_project_control/acceptance_gates.csv")
gate_by_id = {row["gate"]: row for row in gates}
for gate in ("4", "5", "6", "7", "8", "9", "16", "17", "18", "21"):
    check(gate_by_id[gate]["status"] == "BLOCKED", f"external/native gate {gate} remains BLOCKED")
check(gate_by_id["20"]["status"] == "OPEN", "FAT/SAT/commissioning gate remains OPEN")
check(gate_by_id["2"]["status"] == gate_by_id["19"]["status"] == "PARTIAL", "integration and software gates retain truthful PARTIAL boundaries")

boundary = "THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL."
for relative in (
    "README.md", "00_project_control/design_basis.md", "02_system_architecture/revision_f_vision_integration_architecture.md",
    "07_nvidia_vision/plc_ai_interface_v3.md", "12_testing/AI_commissioning_procedure.md", "release/RELEASE_NOTES.md",
    "04_controls_siemens/plc_nvidia_interface_revision_f.md", "05_hmi/wincc_unified_revision_f_runbook.md",
    "07_nvidia_vision/dataset_model_engineering_specification.md", "07_nvidia_vision/nvidia_platform_version_policy.md",
    "07_nvidia_vision/vision_architecture_trade_study.md", "07_nvidia_vision/vision_commissioning_cybersecurity_runbook.md",
    "12_testing/AI_fault_injection_procedure.md", "13_documentation/ai_maintenance_backup.md",
    "13_documentation/ai_troubleshooting_guide.md", "13_documentation/nvidia_version_compatibility.md",
):
    check(boundary in text(relative), f"NVIDIA non-safety boundary is explicit: {relative}")

uncontrolled = sorted(
    path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*")
    if path.is_file() and (
        path.suffix.lower() in {".pyc", ".pyo"}
        or path.name.endswith(".inspect.ndjson")
        or "__pycache__" in path.parts
        or "node_modules" in path.parts
    )
)
check(not uncontrolled, f"release tree contains no ignored runtime/generated artifacts: {uncontrolled}")

banned = {".ap20", ".zap20", ".onnx", ".engine", ".plan", ".etlt", ".trt"}
unexpected = sorted(path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in banned)
check(not unexpected, f"no fabricated Siemens/model/runtime artifacts exist: {unexpected}")
check(json.loads(text("release/reproduction_toolchain_lock.json"))["release"] == "F", "artifact toolchain lock identifies Revision F")
check((ROOT / ".github/workflows/revision-f-reproduce.yml").is_file(), "Revision-F fresh-clone CI workflow is controlled")

report = ROOT / "14_qa/revision_f_verification_report.md"
lines = [
    "# Revision-F NVIDIA-readiness verification", "", f"Result: **{'PASS' if not failed else 'FAIL'}**", "",
    f"> {NOTICE}", "", f"> {SAFETY}", "",
    AI_BOUNDARY, "",
    "This is software-agent static, source and deterministic structured behavioral fault-injection verification. It is not native Siemens compilation, production NVIDIA runtime/model evidence, physical testing, qualified safety validation or human approval.",
    "", "## Passed checks", "", *[f"- {item}" for item in sorted(passed)],
]
if failed:
    lines.extend(("", "## Failed checks", "", *[f"- {item}" for item in sorted(failed)]))
if not OPTIONS.check:
    report.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(f"REVISION_F_PASS={len(passed)} REVISION_F_FAIL={len(failed)}")
for item in failed:
    print(f"ERROR: {item}")
sys.exit(1 if failed else 0)
