"""Deterministic Revision-F NVIDIA implementation-readiness overlay."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from revision_d_generator import NOTICE, SAFETY, _csv, _doc, _rationales, _write
from revision_e_generator import _append_row, _digest


REVISION = "F"
DATE = "2026-08-03"
AI_BOUNDARY = (
    "THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF "
    "PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL."
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _upsert(rows: list[dict], key: str, row: dict) -> list[dict]:
    return [item for item in rows if str(item.get(key)) != str(row[key])] + [row]


def _vision_row(signal: str, data_type: str, owner: str, meaning: str, *, timeout_ms: int = 0) -> dict:
    opcua = {
        "BOOL": "Boolean", "USINT": "Byte", "UINT": "UInt16", "UDINT": "UInt32",
        "DWORD": "UInt32", "ULINT": "UInt64", "REAL": "Float", "STRING[32]": "String",
        "STRING[64]": "String",
    }[data_type]
    return {
        "signal": signal,
        "data_type": data_type,
        "owner": owner,
        "meaning": meaning,
        "transport": f"OPC UA ns=3;s=FC01.Vision.{signal}",
        "timeout_ms": timeout_ms,
        "opcua_type": opcua,
        "byte_order": "OPC UA typed scalar; no application byte swapping",
        "update_rule": "PLC writes request/configuration; immutable while active" if owner == "PLC" else "Edge writes payload before RESULT_VALID; immutable until exact ACK",
        "invalid_action": "Edge refuses request and remains not ready/faulted" if owner == "PLC" else "PLC rejects publication and enters deterministic HOLD/FAULT",
    }


ADDITIONAL_SIGNALS = [
    _vision_row("MAINTENANCE_MODE", "BOOL", "PLC", "Permission-scoped maintenance request; never quality acceptance or actuator bypass"),
    _vision_row("EXPECTED_DATASET_ID", "STRING[32]", "PLC", "Approved validation/dataset baseline expected for the active recipe"),
    _vision_row("EXPECTED_CALIBRATION_ID", "STRING[32]", "PLC", "Approved optics/calibration identity expected for the active recipe"),
    _vision_row("CAPTURE_ACK_ID", "UDINT", "NVIDIA", "Inspection ID whose image acquisition has been accepted"),
    _vision_row("PROCESSING_STATE", "USINT", "NVIDIA", "0 not ready; 1 ready; 2 capture acknowledged; 3 processing; 4 complete; 5 fault"),
    _vision_row("SERVICE_HEALTHY", "BOOL", "NVIDIA", "Edge process, configuration, storage and watchdog health"),
    _vision_row("CAMERA_HEALTHY", "BOOL", "NVIDIA", "Camera connection/acquisition health; not optical-quality proof"),
    _vision_row("MODEL_LOADED", "BOOL", "NVIDIA", "Configured model adapter loaded with approved identity"),
    _vision_row("MAINTENANCE_ACTIVE", "BOOL", "NVIDIA", "Edge is in controlled maintenance state and cannot publish production PASS"),
    _vision_row("RESULT_DISPOSITION", "USINT", "NVIDIA", "0 none; 1 pass; 2 hold; 3 fail; 4 fault"),
    _vision_row("REASON_BITS", "DWORD", "NVIDIA", "Structured quality/fault reason mask; PASS requires zero"),
    _vision_row("CONFIDENCE", "REAL", "NVIDIA", "Normalized quality confidence; threshold remains PLC/recipe controlled"),
    _vision_row("DATASET_ID", "STRING[32]", "NVIDIA", "Validation/dataset baseline identity bound to the result"),
    _vision_row("CALIBRATION_ID", "STRING[32]", "NVIDIA", "Optics/calibration identity bound to the result"),
    _vision_row("CAPTURE_TIMESTAMP_UTC_MS", "ULINT", "NVIDIA", "Diagnostic UTC image-acquisition timestamp in milliseconds"),
    _vision_row("INFERENCE_TIMESTAMP_UTC_MS", "ULINT", "NVIDIA", "Diagnostic UTC inference-completion timestamp in milliseconds"),
    _vision_row("PUBLICATION_TIMESTAMP_UTC_MS", "ULINT", "NVIDIA", "Diagnostic UTC immutable-publication timestamp in milliseconds"),
    _vision_row("PROCESSING_TIME_MS", "UDINT", "NVIDIA", "Measured capture-to-publication processing time", timeout_ms=1000),
    _vision_row("DIAGNOSTIC_CODE", "UDINT", "NVIDIA", "Edge first-out diagnostic code independent of PLC VISION_DIAG_REASON"),
    _vision_row("QUEUE_DEPTH", "UINT", "NVIDIA", "Bounded inspection queue depth; saturation fails closed"),
]


VISION_REQUIREMENTS = [
    (26, "Keep NVIDIA non-safety and unable to command actuators or bypass PLC interlocks", "02_system_architecture/revision_f_vision_integration_architecture.md", "VFS-002; VFS-004"),
    (27, "Support camera, recorded-directory and explicitly synthetic non-production acquisition adapters", "07_nvidia_vision/edge_service", "EDGE-PIPELINE"),
    (28, "Validate versioned configuration schema, reject unknown keys and publish configuration hashes", "07_nvidia_vision/edge_service", "EDGE-CONFIG"),
    (29, "Correlate capture acknowledgement and processing state to the immutable inspection identity", "04_controls_siemens/scl/FB_VisionInterface.scl; 07_nvidia_vision/edge_service", "EDGE-V3; SCL-V3"),
    (30, "Publish explicit PASS HOLD FAIL or FAULT disposition with structured reason bits", "02_system_architecture/interface_control_document.md", "EDGE-V3; SCL-V3"),
    (31, "Bind model, dataset and calibration identities to each accepted result", "07_nvidia_vision/plc_ai_interface_v3.md", "EDGE-V3"),
    (32, "Provide diagnostic UTC timestamps while retaining PLC monotonic timing as acceptance authority", "02_system_architecture/revision_f_vision_integration_architecture.md", "EDGE-V3; VFS-020"),
    (33, "Expose service, camera, model, maintenance, queue and diagnostic health", "05_hmi; 07_nvidia_vision/plc_ai_node_map.csv", "EDGE-V3; HMI-V3"),
    (34, "Fail closed when durable inspection audit records cannot be written", "07_nvidia_vision/edge_service", "EDGE-AUDIT; VFS-021"),
    (35, "Version and hash dataset records and split by production lot to prevent leakage", "07_nvidia_vision", "DATASET-TOOLS"),
    (36, "Provide reproducible evaluation, FAR/FRR, threshold and latency tooling without fabricated results", "07_nvidia_vision", "EVAL-TOOLS"),
    (37, "Define optical resolution, exposure, motion-blur, glare, focus and calibration acceptance methods", "07_nvidia_vision; 12_testing/AI_commissioning_procedure.md", "DOC-LINK"),
    (38, "Apply least-privilege certificate-based OPC UA across the controlled quality zone", "13_documentation/network_cybersecurity.md", "OPCUA-INTEGRATION"),
    (39, "Retain bounded deployment rollback and independent model/configuration/calibration identities", "13_documentation/ai_maintenance_backup.md", "DOC-LINK"),
    (40, "Do not retain raw production images by default and require an approved retention/privacy policy", "02_system_architecture/revision_f_vision_integration_architecture.md", "DOC-LINK"),
    (41, "Reserve separately protected edge, camera, lighting and maintenance electrical branches", "03_electrical/revision_f_nvidia_electrical_delta.md", "NED-CHECK"),
    (42, "Reject queue saturation, concurrent transaction reuse and results for unknown IDs", "11_simulation/vision_fault_scenarios.json", "EDGE-V3; VFS-012; VFS-025"),
    (43, "Invalidate an active inspection on recipe change or unacceptable clock discontinuity", "07_nvidia_vision/edge_service/opcua_adapter.py; 11_simulation/vision_fault_scenarios.json", "EDGE-V3; VFS-019; VFS-020"),
    (44, "Require explicit recovery and a new start following PLC or edge restart", "11_simulation/revision_f_vision_sil.py", "VFS-017; VFS-018; VFS-027"),
    (45, "Keep flow and level instrumentation as the primary deterministic filling measurement", "02_system_architecture/revision_f_vision_integration_architecture.md", "ARCH-OWNER"),
]

TRACEABILITY_TESTS = [
    ("EDGE-PIPELINE", "Acquisition/preprocessing authorization boundaries", "Python unit tests", "Recorded input is hash-bound/exactly-once and cannot authorize production READY", "07_nvidia_vision/edge_service/tests/test_revision_f_readiness.py"),
    ("EDGE-CONFIG", "Configuration schema and hash publication", "Python unit/static tests", "Unknown keys rejected; runtime/contract/schema SHA-256 values are structured-log fields", "07_nvidia_vision/edge_service/tests/test_revision_f_readiness.py; 07_nvidia_vision/edge_service/opcua_adapter.py"),
    ("EDGE-V3", "47-node edge contract", "Python unit and encrypted OPC UA integration tests", "Type/owner/node parity, exact identity, terminal-before-valid ordering and fail-closed behavior", "07_nvidia_vision/edge_service/tests"),
    ("SCL-V3", "Revision-F PLC source contract", "Static Siemens source contracts", "Additive interface, PLC ownership and fail-closed guards present; native compile remains blocked", "11_simulation/tests/test_revision_d1_siemens_contracts.py"),
    ("EDGE-AUDIT", "Durable audit interlock", "Injected storage-failure unit test", "fsync-backed write is required before publication; failure holds RESULT_VALID low and requires reset", "07_nvidia_vision/edge_service/tests/test_service.py"),
    ("DATASET-TOOLS", "Dataset hash/split/leakage controls", "Python unit tests", "Manifest hashes, grouped splits and leakage rejection execute without claiming a dataset", "07_nvidia_vision/edge_service/tests/test_revision_f_readiness.py"),
    ("EVAL-TOOLS", "Evaluation tooling", "Python unit tests", "FAR/FRR arithmetic and invalid-score rejection execute on synthetic fixtures only", "07_nvidia_vision/edge_service/tests/test_revision_f_readiness.py"),
    ("DOC-LINK", "Controlled engineering method", "Document/traceability review", "Method and blocker are linked; procedure execution remains external", "00_project_control/document_register.csv"),
    ("OPCUA-INTEGRATION", "Certificate-backed OPC UA integration", "Local asyncua server/client integration tests", "Basic256Sha256 SignAndEncrypt and named X.509 user path pass locally", "07_nvidia_vision/edge_service/tests/test_opcua_adapter.py"),
    ("HMI-V3", "HMI contract coverage", "Static source-parity verification", "All 47 transport bindings have a read-only HMI diagnostic source; native WinCC compile remains blocked", "05_hmi/vision_tags_revision_f.csv"),
    ("NED-CHECK", "NVIDIA electrical delta", "CSV/document consistency verification", "Ten provisional records, unique cables, 100 W allowance and standalone-delta boundary reconcile", "10_schedules/nvidia_electrical_delta.csv"),
    ("ARCH-OWNER", "PLC/edge ownership boundary", "Architecture/source review", "PLC retains sequence, filling measurement, disposition and hazardous-output authority", "02_system_architecture/revision_f_vision_integration_architecture.md"),
]


def _gate_rows(model: dict, root: Path) -> list[dict]:
    rows = [dict(row) for row in model["acceptance_gates"]]
    qet_native = root / "03_electrical/revision_f_native_qet/native_reopen_export_evidence.json"
    qet = json.loads(qet_native.read_text(encoding="utf-8")) if qet_native.is_file() else {}
    qet_reopen = str(qet.get("native_reopen", {}).get("status", "BLOCKED")).upper()
    qet_export = str(qet.get("native_pdf_export", {}).get("status", "BLOCKED")).upper()
    updates = {
        "1": ("PARTIAL", "Revision-F requirements and evidence are traceable; identified owner approval remains absent"),
        "2": ("PARTIAL", "Core canonical/interface schedules reconcile; the standalone Revision-F NVIDIA electrical delta is internally consistent but is not yet incorporated into canonical BOM/terminal/cable/P2P/QET/CAD authorities"),
        "6": ("BLOCKED", "Expanded import-ready SCL/source contracts pass locally; native TIA V20 compile was not run"),
        "7": ("BLOCKED", "Expanded HMI definitions are source-controlled; native WinCC Unified compile/usability review was not run"),
        "10": ("PARTIAL", "Exact controlled Revision-E QET hash reopened natively with 26/26 folios; automatic cross-reference resolution remains unsupported" if qet_reopen == "PASS" else "Corrected QET remains source-verified; exact-hash native reopen evidence is incomplete"),
        "11": ("PARTIAL" if qet_export == "PASS" else "BLOCKED", "Native 26-page PDF export completed; all pages were reviewed, with one clipped in-body statement on folio 25 and dense text noted" if qet_export == "PASS" else "Native complete PDF export/all-page visual review remains incomplete"),
        "14": ("PARTIAL", "Revision-E panel CAD remains natively verified; Revision-F electrical delta uses provisional carrier/camera/light envelopes and is not incorporated into QET/CAD"),
        "16": ("BLOCKED", "Dataset tooling, schema, collection matrix and leakage-safe split checks are ready; no representative labeled dataset exists"),
        "17": ("BLOCKED", "Training/evaluation tooling is ready; no approved dataset, training run, model or defensible production metrics exist"),
        "18": ("BLOCKED", "DeepStream 9.1/TAO 7.0.1 policy is documented; CUDA/TAO/TensorRT/DeepStream/Docker and target hardware are absent"),
        "19": ("PARTIAL", "Source, edge, durable-audit, encrypted OPC UA and interface tests pass locally; native SCL enum binding, production S7/Jetson endpoint and physical timing remain unverified"),
        "22": ("PARTIAL", "Manifest and clean-clone release-integrity gate closes only after the final Revision-F commit is pushed and reproduced"),
    }
    for row in rows:
        key = str(row["gate"])
        if key in updates:
            row["status"], row["evidence_or_blocker"] = updates[key]
    return rows


def apply_revision_f(root: Path) -> None:
    model_path = root / "00_project_control/canonical_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["project"].update({
        "revision": REVISION,
        "date": DATE,
        "status": "CONTROLLED NVIDIA IMPLEMENTATION-READINESS RELEASE CANDIDATE; NATIVE SIEMENS, REAL DATA/MODEL, SITE, PHYSICAL AND QUALIFIED GATES REMAIN OPEN",
        "nvidia_non_safety_boundary": AI_BOUNDARY,
    })

    normalized = []
    for row in model["vision_interface"]:
        normalized.append(_vision_row(row["signal"], row["data_type"], row["owner"], row["meaning"], timeout_ms=int(row.get("timeout_ms", 0))))
    by_signal = {row["signal"]: row for row in normalized}
    for row in ADDITIONAL_SIGNALS:
        by_signal[row["signal"]] = row
    model["vision_interface"] = list(by_signal.values())
    if len(model["vision_interface"]) != 47:
        raise ValueError(f"Revision-F PLC-AI contract must contain 47 nodes, got {len(model['vision_interface'])}")

    requirements = [row for row in model["requirements"] if int(row["requirement_id"].split("-")[1]) < 26]
    for number, requirement, artifact, tests in VISION_REQUIREMENTS:
        requirements.append({
            "requirement_id": f"SYS-{number:03d}", "requirement": requirement,
            "verification": "Review plus deterministic source tests and structured behavioral fault injection where applicable",
            "status": "Implemented locally where possible; external native/data/hardware acceptance remains explicit",
            "design_artifact": artifact, "test_ids": tests,
            "evidence": "Revision-F controlled source, schedule, test and review records",
        })
    for row in requirements:
        if row["requirement_id"] == "SYS-024":
            row["design_artifact"] = row["design_artifact"].replace("backup_restore.md", "backup_recovery.md")
        if row["requirement_id"] == "SYS-022":
            row["evidence"] = (
                "32 deterministic process scenarios plus 99 source/simulator/native-contract tests, "
                "28 deterministic vision-fault scenarios, 86 edge-service tests and 17 interface-harness tests; "
                "see the executed report"
            )
    model["requirements"] = requirements

    scenarios = json.loads((root / "11_simulation/vision_fault_scenarios.json").read_text(encoding="utf-8"))
    tests = []
    for row in model["tests"]:
        if not str(row.get("test_id", "")).startswith("TC-"):
            continue
        normalized_test = dict(row)
        normalized_test["test_type"] = "DETERMINISTIC_PROCESS_SIMULATOR"
        tests.append(normalized_test)
    for index, row in enumerate(scenarios, 1):
        tests.append({
            "test_id": f"VFS-{index:03d}", "scenario": row["scenario"],
            "method": "Revision-F deterministic structured behavioral fault injection",
            "expected": f"{row['expected_state']}; no process-output command; no automatic restart; diagnostic {row['diagnostic']}",
            "native_plcsim": "NOT RUN", "evidence": "11_simulation/outputs/vision_fault_results.csv",
            "test_type": "BEHAVIORAL_FAULT_INJECTION_MODEL",
        })
    for test_id, scenario, method, expected, evidence in TRACEABILITY_TESTS:
        tests.append({
            "test_id": test_id, "scenario": scenario, "method": method,
            "expected": expected, "native_plcsim": "NOT APPLICABLE OR NOT RUN",
            "evidence": evidence, "test_type": "SOURCE_OR_INTEGRATION_VERIFICATION",
        })
    model["tests"] = tests

    split_loads = [
        {"load":"Vision edge compute allowance","voltage":"24 VDC","nominal_w":60,"demand_factor":1.0,"demand_w":60,"basis":"Provisional branch -F220; carrier/input/inrush unconfirmed"},
        {"load":"Vision camera allowance","voltage":"24 VDC","nominal_w":12,"demand_factor":1.0,"demand_w":12,"basis":"Provisional branch -F221; PoE not assumed"},
        {"load":"Vision lighting allowance","voltage":"24 VDC","nominal_w":20,"demand_factor":1.0,"demand_w":20,"basis":"Provisional branch -F222; pulse duty/inrush unconfirmed"},
        {"load":"Vision service/network allowance","voltage":"24 VDC","nominal_w":8,"demand_factor":1.0,"demand_w":8,"basis":"Provisional branch -F223; maintenance-only service"},
    ]
    revision_f_load_names = {row["load"] for row in split_loads}
    revision_f_load_names.add("Vision edge + camera + lighting")
    model["load_budget"] = [row for row in model["load_budget"] if row["load"] not in revision_f_load_names]
    subtotal = next((i for i, row in enumerate(model["load_budget"]) if row["load"] == "24 VDC subtotal"), len(model["load_budget"]))
    model["load_budget"][subtotal:subtotal] = split_loads

    new_inputs = [
        {"request_id":"IR-023","required_input":"Maximum line speed, bottle/carrier geometry and available camera working envelope","owner":"Machine/process owner","blocks":"Final camera count, FOV, pixels/mm and motion-blur design","status":"OPEN","date_requested":DATE,"evidence_required":"Approved drawings, timing study and representative product samples"},
        {"request_id":"IR-024","required_input":"Representative labeled multi-lot bottle/liquid/foam/glare/spill dataset","owner":"Quality/process owner","blocks":"Model training, threshold selection and performance claims","status":"OPEN","date_requested":DATE,"evidence_required":"Controlled dataset manifest, labels, lot/session metadata and approval"},
        {"request_id":"IR-025","required_input":"Selected industrial Jetson carrier, camera, lens, lighting, enclosure and target software image","owner":"Vision/electrical owner","blocks":"Procurement, thermal/electrical finalization and target runtime validation","status":"OPEN","date_requested":DATE,"evidence_required":"Approved vendor data, lifecycle, compatibility and environmental records"},
        {"request_id":"IR-026","required_input":"Site PKI, authenticated time, log retention, privacy and vulnerability-response policy","owner":"OT cybersecurity owner","blocks":"Production OPC UA trust and audit deployment","status":"OPEN","date_requested":DATE,"evidence_required":"Approved certificates, rules, retention and incident workflow"},
        {"request_id":"IR-027","required_input":"Confirmed edge/camera/light loads, inrush, routes, ambient and protection coordination","owner":"Electrical/site engineer","blocks":"Final vision branch protection, cables, voltage drop and thermal release","status":"OPEN","date_requested":DATE,"evidence_required":"Manufacturer data, site conditions and approved calculations"},
        {"request_id":"IR-028","required_input":"Quality cost/risk basis and approved false-accept/false-reject acceptance limits","owner":"Quality/process owner","blocks":"Threshold selection and model promotion","status":"OPEN","date_requested":DATE,"evidence_required":"Approved acceptance protocol and product-disposition economics"},
    ]
    for row in new_inputs:
        model["input_requests"] = _upsert(model["input_requests"], "request_id", row)

    model["acceptance_gates"] = _gate_rows(model, root)
    model["rationales"] = _rationales(model)
    _write(root, "00_project_control/canonical_model.json", json.dumps(model, indent=2, ensure_ascii=False))
    for path, rows in [
        ("00_project_control/acceptance_gates.csv", model["acceptance_gates"]),
        ("10_schedules/acceptance_gates.csv", model["acceptance_gates"]),
        ("10_schedules/nvidia_interface_tags.csv", model["vision_interface"]),
        ("10_schedules/requirements_traceability.csv", model["requirements"]),
        ("10_schedules/test_coverage.csv", model["tests"]),
        ("10_schedules/load_budget.csv", model["load_budget"]),
        ("00_project_control/input_request_register.csv", model["input_requests"]),
        ("10_schedules/input_request_register.csv", model["input_requests"]),
        ("10_schedules/component_rationale.csv", model["rationales"]),
    ]:
        _csv(root, path, rows)
    _csv(root, "10_schedules/vision_requirements.csv", [row for row in model["requirements"] if int(row["requirement_id"].split("-")[1]) >= 26])
    _csv(root, "10_schedules/vision_fault_matrix.csv", scenarios)
    _csv(root, "10_schedules/revision_f_gap_matrix.csv", _read_csv(root / "00_project_control/revision_f_requirements_gap_matrix.csv"))
    _csv(root, "10_schedules/nvidia_version_baseline.csv", [
        {"domain":"DeepStream target","version":"9.1","platform":"Jetson Orin/Thor or supported x86","status":"OFFICIAL CURRENT; target image not selected","source":"https://docs.nvidia.com/metropolis/deepstream/9.1/text/DS_Release_notes.html"},
        {"domain":"Jetson installation","version":"JetPack 7.2 GA","platform":"Jetson","status":"PLANNING BASELINE","source":"https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Installation.html"},
        {"domain":"DeepStream Jetson TensorRT","version":"10.16.1.7","platform":"Jetson","status":"PLATFORM-SPECIFIC COMPATIBILITY","source":"https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Migration_guide.html"},
        {"domain":"TAO skill bank","version":"7.0.1","platform":"Approved Linux/container backend","status":"NOT INSTALLED OR EXECUTED","source":"https://docs.nvidia.com/tao/tao-toolkit/latest/text/release_notes.html"},
        {"domain":"Generic TensorRT","version":"11.1","platform":"Generic supported platforms","status":"CURRENT GENERIC; NOT JETSON TARGET EVIDENCE","source":"https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/release-notes-11/11.1.0.html"},
    ])

    revisions = _read_csv(root / "00_project_control/revision_history.csv")
    revisions = _upsert(revisions, "revision", {"revision":REVISION,"date":DATE,"status":"NVIDIA implementation-readiness release candidate","description":"Expanded 47-node PLC-AI contract, production-structured acquisition/configuration/dataset tooling, 28-case behavioral fault-injection model, electrical delta and refreshed evidence"})
    _csv(root, "00_project_control/revision_history.csv", revisions)

    ecr = _read_csv(root / "00_project_control/engineering_change_register.csv")
    for row in [
        {"ecr":"ECR-F-001","reason":"Expand the PLC-AI contract from 27 to 47 typed nodes","affected":"Canonical model; Siemens SCL/HMI; edge adapter; schedules/ICD","compatibility":"Existing nodes and immutable session/ID/ACK rules retained","test_impact":"Source parity, 47-node mapping, OPC UA integration and negative contract tests","risk":"Native TIA/WinCC compile and production endpoint remain unverified","migration":"Import all Revision-F Siemens sources and deploy the matching edge/node map atomically"},
        {"ecr":"ECR-F-002","reason":"Complete locally executable edge, configuration, dataset and evaluation foundations","affected":"07_nvidia_vision","compatibility":"No-model and synthetic modes remain explicitly non-production","test_impact":"Unit, schema, dataset, event-store, adapter and synthetic-fixture tests","risk":"No real dataset/model/target runtime performance evidence","migration":"Replace mock adapters only through approved model/configuration change control"},
        {"ecr":"ECR-F-003","reason":"Add the 28-case NVIDIA structured behavioral fault-injection matrix","affected":"11_simulation; test schedule; CI","compatibility":"Existing 32 machine scenarios retained","test_impact":"Every injected invalid observation proves no release, safe outputs, exact identity and explicit recovery in the software-only model","risk":"The behavioral model is not PLCSIM, HIL or physical evidence","migration":"Repeat applicable cases in native and physical test stages"},
        {"ecr":"ECR-F-004","reason":"Issue a controlled NVIDIA electrical delta without corrupting the released QET source","affected":"03_electrical; load budget; delta schedule","compatibility":"Revision-E QET/CAD native evidence retained","test_impact":"Load total, branch, terminal/cable/port and document checks","risk":"Selected devices, protection, thermal/site data and native QET update remain open","migration":"Apply the delta natively using the recorded QET procedure after device selection"},
        {"ecr":"ECR-F-005","reason":"Refresh CI, workbook, PDF, manifest and clean-clone release evidence","affected":"scripts; .github; 10_schedules; 14_qa; release","compatibility":"D.1 Git-object authority model retained","test_impact":"Determinism, formulas, renders, manifest and clean-clone reproduction","risk":"Self-hosted native CI requires the controlled runner","migration":"Accept only the final pushed SHA after fresh-clone reproduction"},
    ]:
        ecr = _upsert(ecr, "ecr", row)
    _csv(root, "00_project_control/engineering_change_register.csv", ecr)

    decisions = _read_csv(root / "00_project_control/decision_register.csv")
    for row in [
        {"decision_id":"ADR-F-001","decision":"Use hybrid calibrated deterministic vision plus learned segmentation/detection/anomaly scoring","rationale":"Transparent bottles, fill lines, glare, foam and spills need geometry and localized evidence; global classification alone obscures failure cause","consequence":"Final method and thresholds require physical optical feasibility and representative data"},
        {"decision_id":"ADR-F-002","decision":"Transport 47 typed PLC-AI nodes while deriving result age in the PLC","rationale":"PLC monotonic timing is authoritative; edge UTC timestamps remain diagnostics and cannot overcome clock discontinuity","consequence":"No RESULT_AGE_MS edge node; HMI reads the PLC-derived value"},
        {"decision_id":"ADR-F-003","decision":"Tie target compatibility to DeepStream/JetPack rather than the latest generic TensorRT","rationale":"NVIDIA platform matrices differ between Jetson DeepStream and generic releases","consequence":"DeepStream 9.1/JetPack 7.2 remains provisional; TAO 7.0.1 and TensorRT 11.1 are tracked separately"},
        {"decision_id":"ADR-F-004","decision":"Synthetic fixtures validate software plumbing only","rationale":"Generated or mock data cannot establish production optical/model performance","consequence":"All accuracy, threshold and latency gates remain blocked until approved real data and target hardware exist"},
    ]:
        decisions = _upsert(decisions, "decision_id", row)
    _csv(root, "00_project_control/decision_register.csv", decisions)

    issues = _read_csv(root / "00_project_control/open_issues.csv")
    for row in issues:
        if row["issue_id"] == "OI-003":
            row.update({"severity":"High","issue":"Exact-hash Revision-E QET reopen and 26-page native export passed; automatic cross-reference graph, folio-25 clipping and Revision-F electrical-delta incorporation remain open","closure_evidence":"Native linked master/slave cross-reference evidence, corrected folio-25 layout, all-page re-review and approved Revision-F native delta"})
        if row["issue_id"] == "OI-004":
            row.update({"severity":"High","issue":"Revision-E selected-architecture CAD is natively verified; final edge carrier/cooling, vendor clearances and construction review remain open","closure_evidence":"Approved carrier/vendor dimensions, thermal/EMC data, updated native CAD if required and qualified construction review"})
    _csv(root, "00_project_control/open_issues.csv", issues)

    _write(root, "README.md", _doc("FC01 Siemens/NVIDIA compact filling cell - Revision F", f"""Revision F advances the verified Revision-E native-engineering baseline into NVIDIA implementation readiness. It adds a 47-node typed PLC-AI contract, production-structured acquisition/configuration/model-adapter foundations, dataset and evaluation tooling, durable audit behavior, 28 named structured behavioral fault injections, expanded Siemens/HMI import artifacts, a controlled electrical delta, current NVIDIA version policy and refreshed release evidence.

The PLC remains authoritative for sequence, interlocks, outputs, disposition and transfer. {AI_BOUNDARY}

Run `powershell -ExecutionPolicy Bypass -File scripts/reproduce_validation.ps1` only from a clean clone outside synchronization folders. No native Siemens compile, representative dataset, trained model, CUDA/TAO/TensorRT/DeepStream execution, GPU latency, physical optics, electrical measurement, FAT/SAT, safety validation or construction readiness is claimed."""))

    _write(root, "00_project_control/design_basis.md", _doc("Design basis - Revision F", f"""The canonical owner is `00_project_control/canonical_model.json`. Revision F overlays the frozen Revision-E baseline without weakening Git-object byte authority or native evidence boundaries. The 47-node OPC UA contract preserves the original 27 nodes and immutable session/inspection/ACK lifecycle. Result age is calculated by the PLC from monotonic transaction time; edge UTC timestamps are diagnostic.

The edge service is a non-safety quality subsystem. {AI_BOUNDARY} Flow and level instrumentation remains the primary deterministic fill measurement. Representative data, target hardware and native/physical evidence remain controlled external gates."""))

    _write(root, "02_system_architecture/interface_control_document.md", _doc("PLC-NVIDIA interface control document - Revision F", f"""## Ownership and transaction

The PLC freezes session epoch, inspection ID, recipe, bottle count, fill target and expected model/dataset/calibration identities before raising the level-held request. The edge validates the complete snapshot, publishes capture acknowledgement and processing state, then writes one complete immutable result before `RESULT_VALID`. The PLC accepts only the exact current session/ID, coherent capture acknowledgement, healthy service/camera/model, approved identities, allowed disposition/reasons/confidence and PLC-derived age. Exact acknowledgement clears the result but never authorizes transfer.

The 47 typed nodes, OPC UA types, owner, update rule and invalid action are controlled in `10_schedules/nvidia_interface_tags.csv`. OPC UA typed scalars abstract byte order; no application byte swapping is permitted. Disconnect, restart, recipe change, clock jump, stale/duplicate/future ID, malformed/contradictory payload, low confidence, fault, queue saturation or maintenance state fails closed.

{AI_BOUNDARY}

Local encrypted asyncua tests are not production S7/Jetson/PKI evidence. Native TIA/WinCC compilation and target endpoint commissioning remain blocked."""))

    _write(root, "14_qa/acceptance_gate_status.md", _doc("Acceptance gate status - Revision F", "\n".join(f"- Gate {row['gate']}: **{row['status']}** - {row['acceptance_gate']}: {row['evidence_or_blocker']}" for row in model["acceptance_gates"])))
    _write(root, "14_qa/validation_matrix.md", _doc("Validation matrix - Revision F", """| Domain | Local evidence | Boundary |
|---|---|---|
| Canonical/interface | 47-node ownership/type/schedule/source parity | Native TIA/production endpoint external |
| Edge service | Acquisition/configuration/adapters/audit plus encrypted OPC UA tests | Synthetic/mock inputs are non-production |
| Dataset/evaluation tools | Hash/split/QA/metrics/threshold harnesses with synthetic fixtures | Real dataset/model metrics blocked |
| Process and vision behavioral simulation | Existing 32 process scenarios plus 28 structured vision fault injections | Software-only model; not PLCSIM, HIL, FAT or physical evidence |
| Electrical/CAD/QET | Revision-E native CAD retained; controlled Revision-F electrical delta | Final devices/site calculations/native delta/qualified review open |
| Workbook/PDF/release | Deterministic build, formula scan, page/sheet renders, manifest and clean clone | Final evidence recorded after freeze/push |"""))
    _write(root, "14_qa/toolchain_audit.md", _doc("Toolchain audit - Revision F", """The Revision-E Siemens, FreeCAD and QElectroTech tool evidence remains controlled. TIA V20 components are installed but the active identity lacks proven Engineering/Openness authorization; Startdrive and PLCSIM remain absent. FreeCAD 1.1.3 native CAD evidence remains valid. Official QElectroTech 0.100.0 is available for the exact-hash reopen/export attempt recorded separately.

The inspected NVIDIA environment contains an RTX 5060 Laptop GPU, driver 595.95, 8,151 MiB and compute capability 12.0. `nvcc`, TensorRT, DeepStream, TAO, Docker, OpenUSD and Omniverse were not found. WSL distribution enumeration was access denied. Official current policy is DeepStream 9.1, TAO 7.0.1 and generic TensorRT 11.1, with target compatibility tied to the selected DeepStream/JetPack matrix. No native NVIDIA runtime result is claimed."""))
    _write(root, "release/RELEASE_NOTES.md", _doc("Revision F release notes", f"""Revision F completes locally achievable NVIDIA implementation-readiness foundations without claiming unavailable real-data, target-runtime or physical evidence. Principal changes are the 47-node PLC-AI contract, acquisition/configuration/model-adapter and audit foundations, dataset/evaluation tools, 28-case structured behavioral fault-injection matrix, expanded Siemens/HMI source definitions, optics/system documentation, controlled electrical delta and current NVIDIA version policy.

{AI_BOUNDARY}

Native Siemens, final Revision-F QET incorporation, site electrical, representative dataset/model, target Jetson/DeepStream performance, FAT/SAT/commissioning and qualified safety/human approval remain open exactly as recorded."""))

    toolchain_path = root / "release/reproduction_toolchain_lock.json"
    toolchain = json.loads(toolchain_path.read_text(encoding="utf-8"))
    toolchain["release"] = REVISION
    toolchain["python"]["packages"]["pypdf"] = "6.10.0"
    _write(root, "release/reproduction_toolchain_lock.json", json.dumps(toolchain, indent=2))

    _write(root, "03_electrical/electrical_calculations.md", _doc("Preliminary electrical calculations - Revision F", """- 24 VDC connected allowance: 329 W; preliminary demand: 299 W = 12.458 A. A provisional 20 A supply leaves 7.542 A at that demand. The minimum current for a 25% design margin is 15.573 A before tolerance, inrush, ambient derating and protective-device coordination.
- The prior 100 W aggregate vision allowance is partitioned provisionally into 60 W edge compute, 12 W camera, 20 W lighting and 8 W service/network branches. No final protection, cable, voltage-drop or thermal claim is made.
- The exact controlled Revision-E QET SHA-256 `BCA022BE0B9F65AA061F9731C1EE0BD0399947F04C94EE596D4AD231BB47AAD5` reopened in QElectroTech 0.100.0+git8590 and exported to 26 pages. The overall native QET gate remains PARTIAL because automatic linked cross-references are unsupported, folio 25 has one clipped in-body statement and the Revision-F electrical delta is not incorporated.
- Site supply, earthing, prospective fault current, motor/pump nameplates, cable routes/installation method, ambient/altitude, enclosure/environment and final device data remain mandatory external inputs.

No short-circuit rating, coordination, voltage-drop, thermal, cable-ampacity, SCCR, construction or regulatory-compliance result is released."""))

    _write(root, "14_qa/visual_review_report.md", _doc("Visual artifact review report - Revision F", f"""A software-agent visual review inspected the complete rendered sets. This is not qualified-human electrical, panel, safety or construction approval.

| Artifact | Rendered/inspected | Result |
|---|---:|---|
| Engineering workbook | 26/26 sheets | PASS: consistent navy/blue style, formula-error scan clean, readable wrapping and no visible clipping; summary shows 2 PASS / 8 PARTIAL / 11 BLOCKED / 1 OPEN |
| Release-evidence PDF | 6/6 pages | PASS: titles, tables, margins, footer/page numbers, safety and NVIDIA non-safety wording are readable |
| Revision-E CAD general arrangement | 4/4 pages | PASS for retained native evidence; provisional assumptions remain visible |
| Revision-E mounting-plate PDF | 2/2 pages | PASS for retained native evidence; dimensioned layout and 30-hole register are readable |
| Native CAD PNG views | 4/4 views | PASS; provenance remains bounded in native evidence |
| Exact-hash native QET export | 26/26 pages | PARTIAL: native reopen/export passed; folio 25 clips one in-body statement and dense schedule pages are small; complete safety text remains readable in the footer |

The workbook and release PDF were each rebuilt twice with identical normalized SHA-256 hashes. Contact sheets are controlled for audit navigation; detailed native/source files remain authoritative.

{AI_BOUNDARY}"""))

    _write(root, "14_qa/final_gate_review.md", _doc("Final locally achievable gate review - Revision F", f"""Revision F implements the locally achievable NVIDIA source, deterministic integration and standalone electrical-delta work while preserving Revision-D.1 Git-object authority and the Revision-E native CAD baseline. The exact controlled QET hash reopens and exports natively, but its overall gate remains PARTIAL because an automatic linked cross-reference graph is unsupported and folio 25 has one clipped in-body statement.

Current gate totals are **2 PASS, 8 PARTIAL, 11 BLOCKED and 1 OPEN**. PASS applies only to native FCStd reopen and STEP/IGES/DXF reimport. Canonical/electrical reconciliation and PLC-NVIDIA failure testing remain PARTIAL because the standalone delta is not in every authority and native/production endpoint behavior remains external. Release-manifest gate 22 remains PARTIAL until final committed/pushed bytes reproduce from GitHub.

Native TIA/WinCC/Startdrive/PLCSIM, site-dependent electrical calculations, real dataset/model/target NVIDIA runtime, FAT/SAT/commissioning and qualified machinery-safety activities remain external blockers. Construction, production deployment, CE/regulatory conformity, model performance and physical acceptance are not claimed.

{AI_BOUNDARY}"""))

    _write(root, "14_qa/executed_test_report.md", _doc("Executed test report - Revision F", f"""Execution date: 2026-08-03. Source/design tests use Python 3.12.13; encrypted OPC UA tests use Python 3.12.13 / asyncua 2.0.1. Native CAD evidence uses FreeCADCmd 1.1.3 and schematic evidence uses QElectroTech 0.100.0+git8590. These are not TIA compile, PLCSIM, FAT, SAT, safety validation, construction test, model performance or production NVIDIA runtime results.

| Workstream | Exact result | Evidence boundary |
|---|---:|---|
| Simulator/Siemens/source/native contracts | 99/99 PASS | Includes inherited contracts plus eleven Revision-F behavioral fault-injection tests |
| NVIDIA edge service | 86/86 PASS | Includes 10/10 certificate-backed local asyncua cases; synthetic endpoint |
| PLC-AI interface harness | 17/17 PASS | Deterministic composed 47-node acceptance model |
| Process scenarios | 32/32 PASS | Exactly one normal release; no invariant violation/automatic restart |
| Vision behavioral fault injections | 28/28 PASS | Exactly one normal pass releases; outputs decommanded; no automatic restart; software-only evidence |
| Engineering validator | 551/551 PASS | Static/data/source/native-evidence contracts |
| Revision-F verifier | 96/96 PASS | Contract, HMI, electrical, traceability, hygiene, data/model honesty, gates and version policy |
| QET source / dedicated contracts | 24/24 and 6/6 PASS | Corrected source contracts |
| QET exact-hash native verifier | 19/19 PASS | Reopen/export/hash/page metadata; overall gate PARTIAL |
| FreeCAD native verifier | 80/80 PASS | 165 objects, 148 controlled solids, STEP/IGES/DXF and 30 holes |
| Workbook | 26 sheets; 12 stored formula cells; zero formula-error matches | Two builds SHA-256 `F7B326032B630B551B87A2882BB65FFD3867A250C2BF7AACD047B54F2B31534A` |
| Release PDF | 6 pages | Two builds SHA-256 `DF06D0C5E5C19E567FF277EB84B9284295C4BF2944FAD38172186A9827BED702` |

Final manifest, release-integrity, authoritative-snapshot determinism and post-push fresh-clone results are recorded separately after candidate freeze/commit. No software-agent record constitutes qualified-human approval.

{AI_BOUNDARY}"""))

    _write(root, "14_qa/source_audit_report.md", _doc("Source audit report - Revision F", f"""Revision-F source review covers the inherited restart/replay/disposition invariants plus the additive 47-node contract, exact capture acknowledgement, processing state, health, model/dataset/calibration identity, immutable result publication, PLC-derived result age, confidence/reason/disposition checks and fail-closed restart/reconnect behavior.

The edge foundation executes its bounded configuration schema, records the runtime/contract/schema SHA-256 values in structured logs, requires an append/flush/fsync inspection-audit write before result publication, publishes terminal state before RESULT_VALID, rejects active recipe/context change and excessive clock discontinuity, and keeps the unimplemented ONNX/recorded-input path permanently unauthorized. Dataset split/hash/leakage checks, evaluation math, local health/metrics and certificate-backed asyncua tests are controlled. Synthetic fixtures prove plumbing only.

Native TIA/WinCC/Startdrive/PLCSIM, production PLC/Jetson/PKI, representative data, trained model, target CUDA/TensorRT/DeepStream/TAO runtime, physical optics, site electrical inputs and qualified safety review remain external.

The first GitHub clean-clone reproduction of candidate a036620c5332997647625b510675345a33a16261 exposed an intermittent secure-session disconnect: asyncua transport supervision was incorrectly tied to the 10 ms PLC poll cadence and used a 50 ms server-state probe timeout. Revision F now gives the transport watchdog at least the configured OPC UA operation budget and a one-second floor. The added regression check plus eight repeated two-test secure runs and the complete 86-test edge suite passed after correction.

{AI_BOUNDARY}"""))

    _write(root, "13_documentation/software_design_specification.md", _doc("Software design specification - Revision F", f"""## Ownership and scan order

The S7-1500 PLC owns machine sequence, permissives, interlocks, timeouts, actuator commands and disposition authorization. The non-safety NVIDIA service transports quality evidence only. `FB_CellMain` retains the established deterministic scan order and safe final output mapping.

## PLC-edge transaction

The controlled interface contains 47 typed OPC UA nodes. Session epoch, monotonic inspection ID, capture acknowledgement, terminal processing state, immutable payload, exact result acknowledgement and result-clear are separate invariants. The edge publishes BUSY false and state 4 before setting RESULT_VALID. The PLC derives result age from its monotonic timer and never trusts edge wall-clock time for release.

## Verification boundary

Source/static, deterministic simulator and certificate-backed local asyncua evidence is controlled. Native TIA/WinCC compilation, production endpoint behavior, target-runtime timing, hardware and physical commissioning remain blocked. The `E_VisionDiag` to UA UInt16 exposure requires confirmation during native TIA/OPC UA configuration.

{AI_BOUNDARY}"""))

    _write(root, "13_documentation/panel_design_report.md", _doc("Panel design report - Revision F", f"""## Native layout basis

The inherited Revision-E FreeCAD 1.1.3 selected-architecture assembly remains the current natively reopened CAD authority: 800 x 800 x 300 mm provisional enclosure, drilled mounting plate, separated drive/power/control/network zones, Siemens PLC/I/O/HMI/drive envelopes and a provisional NVIDIA edge-compute envelope.

## Revision-F electrical delta boundary

`03_electrical/revision_f_nvidia_electrical_delta.md` reserves provisional protected edge, camera, lighting and service branches plus unique C200-C206 power/network cable identifiers. It is a standalone delta and has not been incorporated into the native FCStd, QET, canonical BOM, terminal/cable/P2P or panel-placement authorities. Gate 14 therefore remains PARTIAL.

## Open construction inputs

Selected carrier/camera/light hardware, enclosure series/IP, branch protection, cable entry, duct fill, thermal rise, PE/bonding, EMC, fault-current/SCCR data, vendor drilling, site clearances and qualified-human review remain open.

{AI_BOUNDARY}"""))

    _write(root, "14_qa/design_review_checklist.md", _doc("Final integrated design review checklist - Revision F", f"""- [x] Revision-F canonical/interface schedules regenerate deterministically.
- [x] Exact-hash QET source reopens and exports 26 pages; overall gate remains PARTIAL for folio-25 clipping, automatic cross-references and unapplied delta.
- [x] FreeCAD source/exchange artifacts retain the inherited native verification evidence.
- [x] PLC-AI publication ordering, durable audit failure and active request-context change have executable checks.
- [x] Relevant documents carry the conceptual-safety and NVIDIA non-safety boundaries.
- [ ] Native TIA/WinCC/Startdrive/PLCSIM compilation and execution are completed.
- [ ] Revision-F electrical delta is incorporated into QET/CAD/canonical schedules.
- [ ] Real dataset/model/target runtime, site electrical, FAT/SAT, physical and qualified-safety gates are closed.

Reviewers are software agents, not qualified-human approvers. {AI_BOUNDARY}"""))

    boundary_documents = (
        "04_controls_siemens/tia_v20_revision_f_runbook.md",
        "04_controls_siemens/plc_nvidia_interface_revision_f.md",
        "05_hmi/wincc_unified_revision_f_runbook.md",
        "07_nvidia_vision/dataset_model_engineering_specification.md",
        "07_nvidia_vision/nvidia_platform_version_policy.md",
        "07_nvidia_vision/vision_architecture_trade_study.md",
        "07_nvidia_vision/vision_commissioning_cybersecurity_runbook.md",
        "12_testing/AI_commissioning_procedure.md",
        "12_testing/AI_fault_injection_procedure.md",
        "13_documentation/ai_maintenance_backup.md",
        "13_documentation/ai_troubleshooting_guide.md",
        "13_documentation/nvidia_version_compatibility.md",
    )
    for relative in boundary_documents:
        path = root / relative
        current = path.read_text(encoding="utf-8")
        body = current.split("\n", 1)[1].lstrip() if current.startswith("# ") else current
        title = current.splitlines()[0].removeprefix("# ") if current.startswith("# ") else Path(relative).stem.replace("_", " ").title()
        for marker in (f"> {NOTICE}", f"> {SAFETY}", AI_BOUNDARY):
            body = body.replace(marker, "").strip()
        body = "\n".join(line for line in body.splitlines() if line.strip() != ">")
        _write(root, relative, _doc(title, f"{body}\n\n{AI_BOUNDARY}"))

    reviews = _read_csv(root / "14_qa/review_records.csv")
    revision_f_reviews = [
        {"review_record_id":"RR-F-001","reviewer_task":"/root/rev_f_nvidia_impl","review_type":"NVIDIA implementation workstream software-agent record","scope":"47-node OPC UA contract, production-structured edge service, dataset/evaluation tooling and deployment controls","method":"Bounded source implementation plus unit, protocol, ten certificate-backed asyncua and negative-behavior tests","evidence_sha256":_digest(root,["07_nvidia_vision/edge_service/opcua_adapter.py","07_nvidia_vision/edge_service/service.py","07_nvidia_vision/edge_service/protocol.py","07_nvidia_vision/edge_service/tests/test_opcua_adapter.py","07_nvidia_vision/edge_service/tests/test_service.py","07_nvidia_vision/edge_service/tests/test_revision_f_readiness.py"]),"limitations":"Authoring workstream; no production S7/Jetson endpoint, representative dataset, trained model, target runtime, physical test or qualified cybersecurity approval","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"IMPLEMENTED AND LOCALLY TESTED; production endpoint, model/runtime, physical and human gates remain blocked"},
        {"review_record_id":"RR-F-002","reviewer_task":"/root/rev_f_siemens_hmi","review_type":"Siemens/HMI implementation workstream software-agent record","scope":"Revision-F PLC interface, SCL source contracts, OPC UA symbol bindings, HMI tags/alarms and native runbooks","method":"Bounded source implementation and static/source-contract regression","evidence_sha256":_digest(root,["scripts/revision_f_scl.py","04_controls_siemens/scl/FB_VisionInterface.scl","04_controls_siemens/scl/FB_CellMain.scl","04_controls_siemens/plc_nvidia_interface_revision_f.md","05_hmi/hmi_tags.csv","05_hmi/alarms.csv"]),"limitations":"Authoring workstream; no native TIA/WinCC compile, Startdrive, PLCSIM, hardware or qualified controls-engineer approval","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"IMPLEMENTED AND SOURCE-TESTED; native Siemens and human gates remain blocked"},
        {"review_record_id":"RR-F-003","reviewer_task":"/root/rev_f_qet_native","review_type":"QElectroTech/electrical workstream software-agent record","scope":"Exact-hash QET reopen/export evidence and standalone NVIDIA electrical delta reconciliation","method":"Native QET reopen/export evidence review plus schedule and rendered-page checks","evidence_sha256":_digest(root,["03_electrical/revision_f_native_qet/native_reopen_export_evidence.json","03_electrical/revision_f_nvidia_electrical_delta.md","10_schedules/nvidia_electrical_delta.csv","scripts/verify_qet_revision_f.py"]),"limitations":"Authoring/review workstream; Revision-F delta is not incorporated into canonical QET/CAD/BOM/terminal/cable authorities; folio 25 clipping and automatic cross-reference limitation remain","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"NATIVE REOPEN/EXPORT VERIFIED; overall electrical/QET gate remains PARTIAL"},
        {"review_record_id":"RR-F-004","reviewer_task":"/root","review_type":"Lead systems integration software-agent record","scope":"Cross-workstream integration, generator authority, behavioral fault injection, workbook/PDF and release controls","method":"Central reconciliation, clean-clone counterexample correction, deterministic builds, visual inspection and complete local regression","evidence_sha256":_digest(root,["scripts/revision_f_generator.py","scripts/verify_revision_f.py","scripts/validate_project.py","14_qa/executed_test_report.md","14_qa/source_audit_report.md"]),"limitations":"Lead authored/integrated changes; not independent review, qualified-human approval, native Siemens, production model/runtime or physical evidence","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"INTEGRATED AND LOCALLY VERIFIED; external native, physical, model and human gates remain open"},
        {"review_record_id":"RR-F-005","reviewer_task":"/root/rev_f_final_audit_controls_ai","review_type":"Final independent controls/NVIDIA software-agent re-audit","scope":"Corrected PLC-edge behavior, secure OPC UA transport supervision, timeout/rearm concurrency, malformed terminal results, evidence classification and release hygiene","method":"Read-only adversarial source/test re-review after the GitHub clean-clone watchdog finding; 99/86/17 regression, ten secure asyncua cases and 96-check Revision-F verification","evidence_sha256":_digest(root,["07_nvidia_vision/edge_service/opcua_adapter.py","07_nvidia_vision/edge_service/tests/test_opcua_adapter.py","14_qa/executed_test_report.md","scripts/verify_revision_f.py"]),"limitations":"No native Siemens, production PLC/Jetson endpoint, real dataset/model/runtime, physical test or qualified-human approval","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"ACCEPT FOR CORRECTED-CANDIDATE FREEZE AFTER CACHE CLEANUP AND INDEX-AUTHORITY VERIFICATION; P0 0, P1 0"},
        {"review_record_id":"RR-F-006","reviewer_task":"/root/rev_f_final_audit_release_electrical","review_type":"Final independent release/electrical software-agent re-audit","scope":"Corrected release integrity, QET/FreeCAD boundaries, schedules, workbook/PDF, evidence hashes, terminology and blocker truthfulness","method":"Read-only adversarial reconciliation, namespace-aware workbook formula scan and rendered-artifact re-review after the GitHub clean-clone watchdog finding","evidence_sha256":_digest(root,["10_schedules/FC01_engineering_schedules.xlsx","release/FC01_release_evidence.pdf","14_qa/visual_review_report.md","03_electrical/revision_f_nvidia_electrical_delta.md","scripts/revision_f_generator.py"]),"limitations":"No Revision-F native QET/CAD delta incorporation, site electrical inputs, physical construction test, qualified electrical/safety review or final post-push evidence at audit time","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"ACCEPT FOR CORRECTED-CANDIDATE MANIFEST FREEZE; P0 0, P1 0; external gates remain blocked or partial"},
    ]
    for row in revision_f_reviews:
        reviews = _append_row(reviews, "review_record_id", row["review_record_id"], row)
    _csv(root, "14_qa/review_records.csv", reviews)

    _write(root, "00_project_control/final_release_checklist.md", _doc("Final release checklist - Revision F", """- [x] Revision-F canonical schedules regenerate from controlled owners.
- [x] 47-node PLC-AI map reconciles across canonical, Siemens bindings, HMI, edge CSV/JSON and tests.
- [x] 32 process cases and 28 structured vision behavioral injections execute with fail-closed invariants.
- [x] Revision-E FCStd/exchange native evidence remains controlled and unchanged.
- [x] Exact-hash QET native reopen/export evidence is controlled; PARTIAL visual/xref status remains explicit.
- [x] 26-sheet workbook and six-page PDF rebuild deterministically and have complete rendered review sets.
- [ ] Final Revision-F manifest/commit/push/fresh-clone reproduction and upstream alignment are recorded.
- [ ] Native Siemens, real dataset/model/runtime, site electrical, physical and qualified-safety gates are closed externally."""))

    rationale_register = (root / "00_project_control/component_rationale_register.md").read_text(encoding="utf-8")
    rationale_register = rationale_register.replace("# Component rationale register - Revision E", "# Component rationale register - Revision F")
    _write(root, "00_project_control/component_rationale_register.md", rationale_register)

    release_workflow = (root / "00_project_control/repository_release_workflow.md").read_text(encoding="utf-8")
    release_workflow = release_workflow.replace("# Repository and release-byte workflow - Revision E", "# Repository and release-byte workflow - Revision F")
    if "## Revision-F NVIDIA/native discipline" not in release_workflow:
        release_workflow += f"""\n## Revision-F NVIDIA/native discipline\n\nThe 47-node transport, Siemens source templates and NVIDIA generator overlays must regenerate byte-identically before manifest freeze. Native applications write only to explicit controlled evidence directories and must not leave locks, caches or autosaves. QET reopen/export evidence is accepted only at the recorded exact source hash. Synthetic fixtures cannot authorize production READY or support model-performance claims. {AI_BOUNDARY}\n"""
    _write(root, "00_project_control/repository_release_workflow.md", release_workflow)

    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    agents = agents.replace(
        "QElectroTech portable baseline is 0.100.1-dev",
        "QElectroTech portable baseline is 0.100.0+git8590",
    )
    _write(root, "AGENTS.md", agents)

    _write(root, "14_qa/post_push_reproduction.md", _doc("Post-push fresh-clone reproduction - Revision F", """Status: **PENDING FINAL REVISION-F PUSH**.

The previous Revision-E published evidence remains available in Git history. This controlled file is intentionally replaced so the current release cannot inherit a stale SHA or result. After the candidate is pushed, record the exact branch/SHA, fresh-clone path, manifest/integrity/validator/test counts, workbook/PDF hashes, upstream equality and final clean state; then issue the attestation commit and reverify it."""))

    docs = _read_csv(root / "00_project_control/document_register.csv")
    additions = [
        (15,"Revision-F vision integration architecture","02_system_architecture/revision_f_vision_integration_architecture.md","Systems/vision","Controlled"),
        (16,"Revision-F NVIDIA electrical delta","03_electrical/revision_f_nvidia_electrical_delta.md","Electrical","Provisional; native delta open"),
        (17,"Revision-F requirements gap matrix","00_project_control/revision_f_requirements_gap_matrix.csv","Lead systems","Controlled"),
        (18,"Revision-F vision fault matrix","11_simulation/vision_fault_scenarios.json","Verification","Structured behavioral fault-injection model"),
        (19,"NVIDIA version compatibility","13_documentation/nvidia_version_compatibility.md","Vision","Official sources checked"),
        (20,"AI commissioning procedure","12_testing/AI_commissioning_procedure.md","Vision/controls","Issued; not executed"),
        (21,"AI fault-injection procedure","12_testing/AI_fault_injection_procedure.md","Verification","Issued; software-only behavioral fault injection executed"),
        (22,"AI maintenance backup and rollback","13_documentation/ai_maintenance_backup.md","Vision/OT","Controlled"),
        (23,"AI troubleshooting guide","13_documentation/ai_troubleshooting_guide.md","Vision/maintenance","Controlled"),
        (24,"Dataset and model engineering specification","07_nvidia_vision/dataset_model_engineering_specification.md","Vision/quality","Controlled; real data open"),
        (25,"PLC-AI interface v3","07_nvidia_vision/plc_ai_interface_v3.md","Controls/vision","Controlled; native endpoint open"),
        (26,"Vision architecture trade study","07_nvidia_vision/vision_architecture_trade_study.md","Systems/vision","Controlled assumptions"),
        (27,"QET exact-hash native evidence","03_electrical/revision_f_native_qet/native_reopen_export_evidence.json","Electrical","PARTIAL overall gate"),
        (28,"QET native export","03_electrical/revision_f_native_qet/FC01_revision_e_native_export.pdf","Electrical","Native 26-page export; PARTIAL review"),
        (29,"Python runtime SBOM","release/python_runtime_sbom.csv","Configuration management","Controlled inventory"),
        (30,"Third-party licence review","release/third_party_licence_review.md","Configuration management","Engineering inventory; legal approval open"),
        (31,"Revision-F verification report","14_qa/revision_f_verification_report.md","Independent verification","Software-agent evidence"),
    ]
    for number, title, path, owner, status in additions:
        docs = _upsert(docs, "document_id", {"document_id":f"DOC-{number:03d}","title":title,"path":path,"revision":REVISION,"owner":owner,"status":status})
    for row in docs:
        row["revision"] = REVISION
    _csv(root, "00_project_control/document_register.csv", docs)
    _csv(root, "10_schedules/document_register.csv", docs)


if __name__ == "__main__":
    apply_revision_f(Path(__file__).resolve().parents[1])
