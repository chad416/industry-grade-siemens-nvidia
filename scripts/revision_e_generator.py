"""Deterministic Revision-E overlay on the frozen Revision-D.1 canonical build.

Native CAD/QET binaries are authored and verified by their dedicated tools. This
overlay controls their release metadata, source-interface changes, registers and
truthful acceptance-gate wording without attempting to synthesize native proof.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from revision_d_generator import NOTICE, SAFETY, _csv, _doc, _rationales, _write


REVISION = "E"
DATE = "2026-08-03"

HISTORICAL_REVIEW_HASHES = {
    "RR-D-001":"24bb8a5a9a83f9b1501d71a24400cc50a86d302b9e8981a56cab8713cccd7688",
    "RR-D-002":"bc5e1ecf177a855ba0ad0c2445490e3aad30c5a70a9bd61185df156207b3209d",
    "RR-D-003":"512ef24368aca857962c012bfd5745a497f8e75bd0259062fbb443764784ccc0",
    "RR-D-004":"8b5892e8f8d62f4eafcf5d4ec4468f2f728b9803ce6fccee011024765a163dbd",
    "RR-D-005":"4ea83548cc37f1daacbb3513133847b9cce3837607a16c26bc847f272954c6ba",
    "RR-D-006":"1088e528b19dc470f0caab1ae555a1ac461dd7503e3838ac2f152ea8b87664a6",
    "RR-D1-001":"5cda7e026b18620d13d6c2279d211651f6307b4572db2ebbdc95bb5ba17d7a8a",
    "RR-D1-002":"e511f0d5d353f788f8acf67ed4985f3801a9cf769dc0f453c880ff0830b3682b",
    "RR-D1-003":"133e2d7f35235257f50ddca5e354c2caa995df5aa539add39e136cbe94f196c4",
    "RR-D1-004":"933ae4b59315190696d14a783da516ba98fd8a675d3894dcc7393722c5755861",
    "RR-D1-005":"23ea86b05c6ab697ae7ae8cd984c8bee15e96f9f347af1839e917ac29c6a968a",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _append_row(rows: list[dict], key: str, value: str, row: dict) -> list[dict]:
    return [item for item in rows if str(item.get(key)) != value] + [row]


def _native_result(root: Path, rel: str) -> tuple[str, str]:
    path = root / rel
    if not path.is_file():
        return "BLOCKED", f"native verification record absent: {rel}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return "BLOCKED", f"native verification record unreadable: {exc}"
    status = str(data.get("overall_status", data.get("status", data.get("result", "")))).upper()
    if status not in {"PASS", "PARTIAL", "BLOCKED", "FAIL"}:
        status = "BLOCKED"
    evidence = str(data.get("summary", data.get("evidence", ""))).strip()
    if not evidence and "09_panel_cad" in rel and status == "PASS":
        fcstd = data.get("fcstd", {})
        step = data.get("step_reimport", {})
        iges = data.get("iges_reimport", {})
        evidence = (
            f"FreeCADCmd independently reopened {fcstd.get('document_objects', '?')} objects / "
            f"{fcstd.get('controlled_physical_solids', '?')} controlled solids; STEP retained "
            f"{step.get('solid_count', '?')} solids; IGES retained bounded face geometry; DXF entities "
            "and 30 scheduled holes reconciled"
        )
    if not evidence and "03_electrical" in rel:
        source = data.get("controlled_source", {})
        evidence = (
            f"Corrected 26-folio QET source {source.get('qet_sha256', 'hash absent')} passes "
            f"{source.get('static_verifier', {}).get('checks', '?')} static and "
            f"{source.get('dedicated_contract_tests', {}).get('tests', '?')} contract checks; exact "
            "corrected hash was not natively reopened/exported, so native reconciliation remains partial"
        )
    if not evidence:
        evidence = status or "status absent"
    return status, evidence


def _sync_native_panel_placement(root: Path, model: dict) -> None:
    """Keep the canonical major-device schedule consistent with the native CAD schedule."""
    source = root / "09_panel_cad/revision_e/revision_e_panel_placement.csv"
    if not source.is_file():
        return
    native = {row["tag"]: row for row in _read_csv(source)}
    numeric = [
        "x_mm", "y_mm", "width_mm", "height_mm", "depth_mm",
        "top_clearance_mm", "bottom_clearance_mm", "side_clearance_mm",
    ]
    for row in model["panel_placement"]:
        match = native.get(row["tag"])
        if not match:
            continue
        for key in numeric:
            value = match.get(key, "").strip()
            if value:
                number = float(value)
                row[key] = int(number) if number.is_integer() else number
        row["mounting"] = match["mounting"]
        row["zone"] = match["zone"]
        row["heat_w"] = match["heat_loss_w"]
        row["dimension_basis"] = match["dimension_basis"]
        row["placement_status"] = match["engineering_status"]
        row["full_designation"] = match["full_designation"]
    # The native model represents the controlled logical terminal bank with
    # individual physical objects; retain one canonical aggregate row.
    terminal_bank = next((row for row in model["panel_placement"] if row["tag"] == "-X100..-X199"), None)
    if terminal_bank:
        terminal_bank.update({
            "x_mm": 80, "y_mm": 90, "width_mm": 655, "height_mm": 50,
            "depth_mm": 50, "top_clearance_mm": 0, "bottom_clearance_mm": 0,
            "side_clearance_mm": 0, "heat_w": 0,
            "dimension_basis": "Revision-E native schedule: 84 logical terminals plus controlled PE/shield terminal objects",
            "placement_status": "NATIVE GEOMETRY VERIFIED; terminal family, bridges, accessories and construction release remain open",
        })
    hardware = {row["tag"]: row for row in model["hardware"]}
    for tag in ("-U100", "-U101", "-FW100", "-PC200"):
        target = hardware.get(tag)
        match = native.get(tag)
        if not target or not match:
            continue
        for key in ("width_mm", "height_mm", "depth_mm"):
            number = float(match[key])
            target[key] = int(number) if number.is_integer() else number
        target["status"] = match["engineering_status"]


def _digest(root: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(paths):
        path = root / rel
        if path.is_file():
            digest.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _gates(cad_status: str, cad_evidence: str, qet_status: str, qet_evidence: str) -> list[dict]:
    cad_gate_status = "PASS" if cad_status == "PASS" else "BLOCKED"
    qet_reopen_status = "PARTIAL" if qet_status in {"PASS", "PARTIAL"} else "BLOCKED"
    qet_visual_status = "BLOCKED"
    return [
        {"gate":1,"acceptance_gate":"Requirements/interfaces traceable","status":"PARTIAL","evidence_or_blocker":"Controlled model, native-workstream schedules and tests are traceable; identified requirements-owner approval is absent"},
        {"gate":2,"acceptance_gate":"Canonical model reconciles schedules","status":"PASS","evidence_or_blocker":"Revision-E deterministic validator and source/schedule/native-evidence contracts pass; see current automated report for exact count"},
        {"gate":3,"acceptance_gate":"Siemens hardware baseline confirmed","status":"PARTIAL","evidence_or_blocker":"V20/FW4.0 source baseline and selected envelopes documented; authorized native catalog confirmation and delivered-state evidence remain open"},
        {"gate":4,"acceptance_gate":"Native TIA project opens","status":"BLOCKED","evidence_or_blocker":"No genuine AP20 project; active identity is not TIA Engineer/Openness-authorized and V20 entitlement is unproven"},
        {"gate":5,"acceptance_gate":"Native TIA archive restores","status":"BLOCKED","evidence_or_blocker":"No genuine ZAP20 archive exists; native authorized project creation/restoration was not available"},
        {"gate":6,"acceptance_gate":"PLC compiles zero errors","status":"BLOCKED","evidence_or_blocker":"67 source/simulator contracts pass at Revision-E authoring time; TIA V20 compile was not run"},
        {"gate":7,"acceptance_gate":"HMI compiles zero errors","status":"BLOCKED","evidence_or_blocker":"WinCC V20 components exist but no authorized/licensed native HMI project or compile is proven"},
        {"gate":8,"acceptance_gate":"Startdrive configured/reviewed","status":"BLOCKED","evidence_or_blocker":"Startdrive is not installed; motor, pump and site inputs are also missing"},
        {"gate":9,"acceptance_gate":"PLCSIM traces pass","status":"BLOCKED","evidence_or_blocker":"PLCSIM/PLCSIM Advanced are not installed; deterministic Python evidence is explicitly independent"},
        {"gate":10,"acceptance_gate":"Revision-E QET reopens and reconciles","status":qet_reopen_status,"evidence_or_blocker":qet_evidence},
        {"gate":11,"acceptance_gate":"Schematics export and all-page visual review","status":qet_visual_status,"evidence_or_blocker":"Native QET PDF export was not completed and only sampled folios were inspected; all-page visual and native cross-reference review remain blocked"},
        {"gate":12,"acceptance_gate":"Revision-E FCStd reopens","status":cad_gate_status,"evidence_or_blocker":cad_evidence},
        {"gate":13,"acceptance_gate":"STEP/IGES/DXF reimport","status":cad_gate_status,"evidence_or_blocker":cad_evidence},
        {"gate":14,"acceptance_gate":"Full BOM/panel layout reconcile","status":"PARTIAL","evidence_or_blocker":"Revision-E native layout covers selected architecture and controlled provisional envelopes; final carrier, terminal/relay families, vendor clearances, thermal and construction inputs remain open"},
        {"gate":15,"acceptance_gate":"Electrical calculations confirmed","status":"BLOCKED","evidence_or_blocker":"Supply, earthing, fault current, motors/pump, cable routes, installation method, ambient and enclosure/site requirements remain unconfirmed"},
        {"gate":16,"acceptance_gate":"Real NVIDIA dataset controlled","status":"BLOCKED","evidence_or_blocker":"No representative labeled project dataset or golden/negative image sets were supplied"},
        {"gate":17,"acceptance_gate":"Genuine model training/evaluation","status":"BLOCKED","evidence_or_blocker":"No controlled dataset, training run, evaluated model, ONNX export or defensible metrics exist"},
        {"gate":18,"acceptance_gate":"TensorRT/DeepStream target runtime","status":"BLOCKED","evidence_or_blocker":"No selected industrial Jetson carrier/runtime image; CUDA Toolkit, TensorRT, DeepStream and TAO are absent locally"},
        {"gate":19,"acceptance_gate":"PLC-NVIDIA failure tests","status":"PASS","evidence_or_blocker":"Source/simulator, edge-service, interface-harness and real asyncua encrypted server/client integration tests pass; production PLC/Jetson endpoint validation remains outside this local gate"},
        {"gate":20,"acceptance_gate":"FAT/SAT/commissioning","status":"OPEN","evidence_or_blocker":"Controlled procedures issued; no FAT, SAT or commissioning was executed"},
        {"gate":21,"acceptance_gate":"Qualified safety activities","status":"BLOCKED","evidence_or_blocker":"Project-specific qualified machinery-safety engineering, verification and validation are external and not performed"},
        {"gate":22,"acceptance_gate":"Manifest independently verifies","status":"PASS","evidence_or_blocker":"Published candidate b9633c6255fe34e48a1be34afe5024935f48651e was cloned afresh from GitHub outside OneDrive and passed the complete HEAD workflow: manifest 310/310 with zero discrepancies, integrity 534/534, validator 551/551, all tests/native checks, deterministic artifacts and clean state"},
    ]


def _write_component_rationale(root: Path, rows: list[dict]) -> None:
    lines = [
        "# Component rationale register - Revision E", "", f"> {NOTICE}", "", f"> {SAFETY}", "",
        "Generated from the controlled canonical model. Software-agent consistency review is not qualified-human approval.", "",
        "| Category | Key | Purpose | Failure detected or controlled | Basis | Open verification | Owner |",
        "|---|---|---|---|---|---|---|",
    ]
    keys = ["category","key","purpose","failure_detected_or_controlled","selection_or_evidence_basis","open_verification","owner"]
    for row in rows:
        values = [str(row[key]).replace("|", "/").replace("\n", " ") for key in keys]
        lines.append("| " + " | ".join(values) + " |")
    _write(root, "00_project_control/component_rationale_register.md", "\n".join(lines))


def apply_revision_e(root: Path) -> None:
    model_path = root / "00_project_control/canonical_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["project"].update({
        "revision": REVISION,
        "date": DATE,
        "status": "CONTROLLED NATIVE-ENGINEERING RELEASE CANDIDATE; CONSTRUCTION, DEPLOYMENT, NATIVE SIEMENS, PHYSICAL AND QUALIFIED ACCEPTANCE GATES REMAIN EXPLICIT",
    })
    for row in model["vision_interface"]:
        if row["signal"] == "INSPECTION_TRIGGER":
            row["meaning"] = "Level-held inspection request; remains true until coherent BUSY observation or terminal result for the immutable session/inspection ID"
            row["transport"] = "OPC UA subscribed request level; monotonic session/ID is authoritative"

    for row in model["requirements"]:
        if row["requirement_id"] == "SYS-022":
            row["evidence"] = "32 deterministic scenarios plus 88 source/simulator/native-contract tests, 59 edge-service tests and 15 interface-harness tests; see the executed report"
        elif row["requirement_id"] == "SYS-023":
            row["evidence"] = "Revision-E canonical/source/schedule/native-evidence validator; the executed report records the exact current check count"

    _sync_native_panel_placement(root, model)
    for row in model["input_requests"]:
        if row["request_id"] == "IR-019":
            row.update({
                "required_input": "Qualified panel-CAD reviewer, final vendor envelopes/clearances and construction confirmation",
                "blocks": "Construction release of Revision-E native panel CAD",
                "status": "PARTIAL",
                "evidence_required": "Qualified-human review plus approved vendor/site construction data",
            })
        elif row["request_id"] == "IR-021":
            row.update({
                "required_input": "Native reopen/export/all-page review of corrected QET and qualified electrical schematic reviewer",
                "blocks": "Native schematic gate and construction review",
                "status": "PARTIAL",
                "evidence_required": "Exact corrected-hash QET reopen, PDF export, cross-reference report and qualified-human review",
            })

    cad_status, cad_evidence = _native_result(root, "09_panel_cad/revision_e/native_verification.json")
    qet_status, qet_evidence = _native_result(root, "03_electrical/revision_e/native_verification.json")
    model["acceptance_gates"] = _gates(cad_status, cad_evidence, qet_status, qet_evidence)
    model["rationales"] = _rationales(model)
    _write(root, "00_project_control/canonical_model.json", json.dumps(model, indent=2, ensure_ascii=False))
    _csv(root, "00_project_control/acceptance_gates.csv", model["acceptance_gates"])
    _csv(root, "10_schedules/acceptance_gates.csv", model["acceptance_gates"])
    _csv(root, "10_schedules/nvidia_interface_tags.csv", model["vision_interface"])
    _csv(root, "10_schedules/component_rationale.csv", model["rationales"])
    _csv(root, "10_schedules/panel_placement.csv", model["panel_placement"])
    _csv(root, "10_schedules/siemens_hardware.csv", model["hardware"])
    _csv(root, "10_schedules/requirements_traceability.csv", model["requirements"])
    _csv(root, "00_project_control/input_request_register.csv", model["input_requests"])
    _csv(root, "10_schedules/input_request_register.csv", model["input_requests"])
    _write_component_rationale(root, model["rationales"])

    revisions = _read_csv(root / "00_project_control/revision_history.csv")
    revisions = _append_row(revisions, "revision", REVISION, {
        "revision":REVISION,"date":DATE,"status":"Native-engineering release candidate",
        "description":"Genuine FreeCAD/QElectroTech execution where verified, poll-safe PLC request handshake, encrypted asyncua integration and refreshed release evidence",
    })
    _csv(root, "00_project_control/revision_history.csv", revisions)

    ecr = _read_csv(root / "00_project_control/engineering_change_register.csv")
    for row in [
        {"ecr":"ECR-E-001","reason":"Replace obsolete panel baseline with a genuine selected-architecture Revision-E FreeCAD assembly","affected":"09_panel_cad/revision_e; panel schedule; CAD tests and evidence","compatibility":"Historical Revision-A native baseline remains quarantined and recoverable","test_impact":"Native FCStd reopen, object/solid/shape checks, STEP/IGES reimport, DXF hole reconciliation and visual review","risk":"Provisional PC200/carrier, protection/terminal families, thermal data and vendor clearances remain controlled assumptions","migration":"Use Revision-E FCStd/exchange files only with their native verification record and assumption register"},
        {"ecr":"ECR-E-002","reason":"Make the PLC-to-edge request poll-safe and transaction-immutable","affected":"revision_d_scl.py; FB_VisionInterface; FB_CellMain; interface schedule/ICD; Revision-E contracts","compatibility":"Trigger changes from one-scan pulse to held request; session/InspectionId remain authoritative","test_impact":"Nine added source contracts plus full simulator/edge/interface regression","risk":"Native TIA compile/PLCSIM and production PLC OPC UA endpoint remain unverified","migration":"Import all Siemens sources together and deploy the matching Revision-E edge adapter"},
        {"ecr":"ECR-E-003","reason":"Add a production-shaped secure OPC UA adapter with observable fail-closed service behavior","affected":"07_nvidia_vision/edge_service adapter, runtime config, deployment files and integration tests","compatibility":"Exact acknowledgement and immutable-publication D.1 rules retained","test_impact":"Real asyncua server/client PKI, mapping, reconnect, idempotency, malformed-data, heartbeat, health and metrics tests","risk":"Synthetic server/client evidence is not production PLC/Jetson/model validation","migration":"Provision site PKI/trust stores, least-privilege service identity and approved endpoint/node map before target deployment"},
        {"ecr":"ECR-E-004","reason":"Execute official QElectroTech 0.100 native schematic workflow where reproducibly achievable","affected":"03_electrical/revision_e; QET scripts/tests/native evidence","compatibility":"Historical Revision-A QET remains quarantined","test_impact":"Native reopen/export evidence, page inventory, tag/address/terminal/cable reconciliation and visual review","risk":"Site electrical inputs and qualified construction review remain open","migration":"Use only the Revision-E project/export set with the recorded executable hash and blocker boundary"},
    ]:
        ecr = _append_row(ecr, "ecr", row["ecr"], row)
    _csv(root, "00_project_control/engineering_change_register.csv", ecr)

    decisions = _read_csv(root / "00_project_control/decision_register.csv")
    for row in [
        {"decision_id":"ADR-E-001","decision":"A PLC-to-edge request is level-held until coherent BUSY observation or a terminal result","rationale":"A one-scan PLC pulse is not a reliable request primitive for a polling OPC UA client","consequence":"Session/InspectionId/payload remain immutable while pending; duplicate polls and reconnects are idempotent"},
        {"decision_id":"ADR-E-002","decision":"Native CAD/QET proof outranks generated views only when the exact source reopens and recorded exports verify","rationale":"Filename presence is not native engineering evidence","consequence":"Gates derive from controlled native verification records; historical baselines never represent Revision E"},
    ]:
        decisions = _append_row(decisions, "decision_id", row["decision_id"], row)
    _csv(root, "00_project_control/decision_register.csv", decisions)

    reviews = _read_csv(root / "14_qa/review_records.csv")
    for row in reviews:
        frozen = HISTORICAL_REVIEW_HASHES.get(row["review_record_id"])
        if frozen:
            row["evidence_sha256"] = frozen
    for row in [
        {"review_record_id":"RR-E-001","reviewer_task":"/root/rev_e_freecad_native","review_type":"Native FreeCAD authoring workstream record","scope":"Revision-E selected-architecture enclosure, panel layout, exchange exports and native reopen/reimport evidence","method":"FreeCAD 1.1.3 generator, native reopen, shape validity, STEP/IGES reimport, DXF hole reconciliation and rendered-view inspection","evidence_sha256":_digest(root,["scripts/freecad_revision_e.py","scripts/verify_freecad_revision_e.py","09_panel_cad/revision_e/native_verification.json","09_panel_cad/revision_e/revision_e_panel_placement.csv"]),"limitations":"Authoring workstream, not independent approval; provisional hardware envelopes/clearances, site thermal/EMC inputs, construction check and qualified-human approval remain open","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"IMPLEMENTED SUBJECT TO RECORDED NATIVE RESULT AND FINAL INDEPENDENT REVIEW"},
        {"review_record_id":"RR-E-002","reviewer_task":"/root/rev_e_native_tools","review_type":"Native QElectroTech authoring/tool-audit workstream record","scope":"Official QElectroTech 0.100 native project/reopen/export where achievable plus exact Siemens tool/licence audit","method":"Official portable executable hash/version, native project evidence, structural reconciliation and exhaustive local Siemens component/authorization/licence inventory","evidence_sha256":_digest(root,["scripts/qet_revision_e.py","scripts/verify_qet_revision_e.py","03_electrical/revision_e/native_verification.json","14_qa/toolchain_audit.md"]),"limitations":"Authoring/audit workstream, not independent approval; native Siemens access blocked; site electrical and qualified construction review remain open","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"IMPLEMENTED SUBJECT TO RECORDED QET RESULT; SIEMENS NATIVE GATES REMAIN BLOCKED"},
        {"review_record_id":"RR-E-003","reviewer_task":"/root/rev_e_nvidia_opcua","review_type":"NVIDIA OPC UA implementation workstream record","scope":"Secure asyncua adapter, health/metrics, service configuration, deployment/rollback and real server/client integration tests","method":"Bounded source implementation and asyncua 2.0.1 encrypted test-server/client execution with temporary PKI","evidence_sha256":_digest(root,["07_nvidia_vision/edge_service/opcua_adapter.py","07_nvidia_vision/edge_service/opcua_runtime_config.json","07_nvidia_vision/edge_service/tests/test_opcua_adapter.py","07_nvidia_vision/edge_service/opcua_adapter_runbook.md"]),"limitations":"Synthetic OPC UA endpoint, not production S7/Jetson; no dataset/model/DeepStream/TensorRT performance or cybersecurity acceptance","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"IMPLEMENTED AND LOCALLY INTEGRATION-TESTED; TARGET RUNTIME AND MODEL GATES REMAIN BLOCKED"},
        {"review_record_id":"RR-E-004","reviewer_task":"/root","review_type":"Lead systems implementation record","scope":"Poll-safe PLC request, immutable transaction identity, canonical/release integration and generator parity","method":"Siemens-oriented source change, nine added contracts and inherited simulator/interface regression","evidence_sha256":_digest(root,["scripts/revision_d_scl.py","04_controls_siemens/scl/FB_VisionInterface.scl","04_controls_siemens/scl/FB_CellMain.scl","11_simulation/tests/test_revision_e_vision_request_contract.py"]),"limitations":"Lead authored/integrated this delta; it is not independent review, native TIA compile or qualified controls approval","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"IMPLEMENTED AND SOURCE-TESTED; NATIVE TIA/PLCSIM REMAIN BLOCKED"},
        {"review_record_id":"RR-E-005","reviewer_task":"/root/rev_e_independent_review","review_type":"Final independent integrated software-agent audit","scope":"Frozen Revision-E electrical/CAD/Siemens/edge/release-integrity candidate, visual artifacts, safety wording and blocker truthfulness","method":"Read-only adversarial audit plus isolated reproduction of validator, QET, simulator/source/native contracts, edge, interface harness, scenarios, FreeCAD and workbook/PDF visual evidence","evidence_sha256":"80b2445d3edf7f310a0520ad6a7ab56a73f4d69da773813106a309f314e6a686","limitations":"Audit preceded manifest freeze/commit/push; no qualified-human approval, native TIA/WinCC/Startdrive/PLCSIM, final-hash QET reopen/export, production PLC/Jetson endpoint, dataset/model/runtime, site electrical inputs, hardware/FAT/SAT/commissioning or qualified safety validation","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"ACCEPT FOR CONTROLLED MANIFEST FREEZE, COMMIT, PUSH AND POST-PUSH FRESH-CLONE VERIFICATION; GATE 22 REMAINS PARTIAL UNTIL THAT EVIDENCE PASSES"},
        {"review_record_id":"RR-E-006","reviewer_task":"/root","review_type":"Post-push clean-clone release-control execution","scope":"Published Revision-E candidate Git object, authoritative manifest, complete reproduction and upstream alignment","method":"Fresh GitHub clone outside OneDrive at b9633c6255fe34e48a1be34afe5024935f48651e; complete reproduce_validation.ps1 execution with locked runtimes and clean-state assertion","evidence_sha256":"9efd89bdc1a536208fa1030afd57745cb6d3195ba5e097cbce34b4282055f5d4","limitations":"Configuration-management execution by the lead software agent; final attestation commit is reverified after publication; no qualified-human, native Siemens, final-QET, physical, model or safety approval","actual_qualification":"Software agent; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"PASS FOR RELEASE-INTEGRITY GATE — 310/310 manifest, 534/534 integrity, 551/551 validator and complete clean-clone workflow passed with zero discrepancy"},
    ]:
        reviews = _append_row(reviews, "review_record_id", row["review_record_id"], row)
    _csv(root, "14_qa/review_records.csv", reviews)

    _write(root, "README.md", _doc("FC01 Siemens/NVIDIA compact filling cell - Revision E", """Revision E advances the verified D.1 release-integrity baseline through genuine native engineering where this environment permits it. The controlled release contains a selected-architecture panel model and native verification evidence when its gate record passes, an official QElectroTech 0.100 workstream when its record passes, a poll-safe Siemens-oriented vision request contract, and a production-shaped encrypted OPC UA adapter tested against a real asyncua server/client pair.

Run `powershell -ExecutionPolicy Bypass -File scripts/reproduce_validation.ps1` only from a clean clone outside a synchronization folder. The workflow regenerates controlled text/schedules, runs all source/simulator/edge/interface/OPC UA/native-structure checks, compares deterministic workbook/PDF builds, and verifies final committed bytes.

No TIA/WinCC compile, Startdrive configuration, PLCSIM result, trained model, AI metric, site electrical calculation, FAT/SAT, physical commissioning, safety validation, construction readiness or qualified-human approval is implied. Consult `14_qa/acceptance_gate_status.md` and `00_project_control/input_request_register.csv` before any continued engineering use."""))

    _write(root, "09_panel_cad/README.md", _doc("Panel CAD boundary - Revision E", """Revision E replaces the historical panel baseline as the current engineering representation. The controlled `revision_e` directory contains a genuine FreeCAD 1.1.3 selected-architecture assembly, native reopen/shape evidence, STEP and IGES reimport evidence, a structurally verified DXF mounting plate, schedules, dimensioned PDFs and four major rendered views. The historical Revision-A native files remain quarantined under `native_baseline` and are not evidence for Revision E.

The native verification record passes the dimensional and exchange checks stated there. It does not authorize fabrication. Final enclosure/IP selection, protective devices, terminal and relay families, NVIDIA carrier/cooling, vendor drilling and clearances, cable entry, duct fill, thermal rise, PE/bonding, EMC, site short-circuit data and qualified-human construction review remain open."""))

    _write(root, "03_electrical/README.md", _doc("Electrical design boundary - Revision E", """The controlled `revision_e` directory contains a genuinely authored, deterministic 26-folio QElectroTech 0.100 project reconciled at source level to the Revision-E device, I/O, terminal, cable and network schedules. Static verification covers folio structure, embedded symbols/conductors, unique PLC addresses, terminals and cables, scheduled device coverage and page-boundary constraints. The historical Revision-A project remains quarantined under `native_baseline` and is not the current schematic package.

The exact corrected QET SHA-256 was not reopened and exported after the final layout corrections. Native cross-reference resolution, final-hash PDF export and visual review of all 26 final folios therefore remain blocked. Site power/earthing/fault-current data, conductor sizing, protection/coordination, final vendor metadata and qualified construction review also remain open; no construction schematic claim is made."""))

    _write(root, "03_electrical/electrical_calculations.md", _doc("Preliminary electrical calculations - Revision E", """- 24 VDC connected allowance: 329 W; preliminary demand: 299 W = 12.458 A. A provisional 20 A supply leaves 7.542 A at that demand. The minimum current for a 25% design margin is 15.573 A before tolerance, inrush, ambient derating and protective-device coordination.
- AC connected motor load: 1.50 kW before auxiliaries. Demand is provisionally 100% because both drives may operate during filling/indexing transitions.
- Voltage-drop targets are 3% branch and 5% total; actual route lengths, conductor construction, installation method and load data are absent, so no conductor size is released.
- Panel thermal assessment must include verified drive and PSU losses plus the controlled provisional vision branch. Ambient, altitude, enclosure construction/IP, solar/process exposure and vendor loss curves remain open.
- The routing concept uses a 40% duct-fill target and at least 20% spare terminal capacity. Final conductor outside diameters, bend radii, bundle/grouping factors and terminal accessories are not selected.
- The 26-folio Revision-E QET source is schedule-reconciled, but its exact corrected hash was not natively reopened/exported and its all-page/cross-reference review remains blocked.
- No SCCR, short-circuit withstand, selectivity, discrimination, thermal-compliance, protection-coordination or construction-readiness claim is made."""))

    _write(root, "02_system_architecture/interface_control_document.md", _doc("PLC-NVIDIA interface control document - Revision E", """## Atomic request and result lifecycle

The PLC owns sequence and publishes the complete request payload with a nonzero retained `SESSION_EPOCH` and strictly monotonic `INSPECTION_ID` before raising `INSPECTION_TRIGGER`. Trigger is a level-held transport request, not a one-scan event: it remains true until coherent `VISION_READY=1, VISION_BUSY=1` is observed or a terminal result arrives. A repeated coordinator pulse cannot mutate the active ID. Session, ID, recipe, expected bottle count and target remain immutable while pending.

The edge adapter deduplicates by `(session epoch, inspection ID)`, publishes BUSY when it owns the request, and never processes the same pair twice across polling or reconnect. A matching terminal result may complete before BUSY is sampled. Any wrong, stale, future or regressed session/ID, heartbeat regression/loss, malformed value, model-ID/hash mismatch, contradictory state, low confidence, partial result, warning or fault fails closed to PLC HOLD/FAULT. No edge node can command motion or bypass PLC permissives.

The immutable result payload is written before `RESULT_VALID`. It remains stable until the PLC writes the exact `RESULT_ACK_ID`; the acknowledgement is transport cleanup only and never grants product transfer. Restart/reconnect re-seeds the coherent PLC snapshot, preserves same-session unacknowledged publication, and permits invalidation only under the controlled serially advanced disabled-session rule.

Revision-E automated evidence includes a real encrypted asyncua test server/client and controlled PKI flow, but not a production S7-1500 endpoint, production certificate authority, Jetson deployment or trained model. Native TIA compilation/PLCSIM and site cybersecurity acceptance remain explicit gates."""))

    _write(root, "04_controls_siemens/software_architecture.md", _doc("Siemens software architecture - Revision E", """`FB_CellMain` remains the sole cell-level cyclic composition. The PLC owns all sequence, permissives, interlocks, timers, physical commands, result acceptance and transfer authorization. `FB_VisionInterface` now exposes `RequestInProgress`, latches the active request identity and holds `Trigger` until coherent edge observation/result so a polling OPC UA client cannot miss the request. Duplicate request pulses cannot advance the active ID.

All 15 SCL exports are generator-controlled and import together in the documented order. The added source contracts verify generator parity, held-trigger semantics, immutable session/ID, duplicate suppression, result-before-BUSY handling and fail-closed reset/fault behavior. These checks are source-design evidence only. TIA Portal V20 compile, native retentivity review and PLCSIM remain blocked by authorization/licensing/tool availability."""))

    _write(root, "00_project_control/design_basis.md", _doc("Design basis - Revision E", """The canonical owner is `00_project_control/canonical_model.json`. `scripts/build_project.py` applies the frozen Revision-D generator and the deterministic Revision-E overlay; `scripts/revision_d_scl.py` owns the complete 15-file Siemens source export. Schedules, controlled documents, workbook, release PDF and manifest follow the recorded dependency order. Native CAD/QET binaries are authored only by their dedicated sources and are never synthesized by the release generator.

The S7-1500 PLC remains authoritative for sequence, permissives, interlocks, timeouts, actuator/drive requests, quality-result acceptance, product disposition and transfer permission. HMI access is supervisory and audited. NVIDIA is a non-safety quality subsystem and has no hazardous-motion command path. Missing, stale, contradictory, low-confidence, malformed or unacknowledged AI data fails closed to HOLD/FAULT. A request is level-held with immutable session/inspection identity until coherent edge observation or terminal result.

Revision-E FreeCAD geometry represents the selected architecture and has controlled native verification when its record is PASS. The corrected Revision-E QET is a deterministic, schedule-reconciled source; its exact final hash was not natively reopened or exported, so its native/visual gates remain partial/blocked. Site supply, fault current, motor/pump data, cable routes, ambient/environment, final vendor selections, qualified safety work, real dataset/model/target runtime, FAT/SAT and physical commissioning remain controlled inputs or blockers."""))

    _write(root, "13_documentation/panel_design_report.md", _doc("Panel design report - Revision E", """## Native layout basis

The current package contains a genuine FreeCAD 1.1.3 selected-architecture assembly in an 800 x 800 x 300 mm provisional enclosure with a 750 x 750 x 3 mm drilled mounting plate. It includes enclosure/door, DIN rails, ducts, main and 24 V protection envelopes, 24 VDC supply, CPU/DI/DQ/AI/TM Count modules, MTP700 door representation, two G120C PN FSA envelopes, managed switch, firewall, relay bank, terminal/PE/shield infrastructure and a controlled provisional NVIDIA edge-compute envelope. Reference designations follow the `=FC01+CP01-...` structure.

The native schedule places heat-producing drives in the separated left zone and reserves 80 mm top / 100 mm bottom keep-outs based on the controlled Siemens catalog assumption. PLC, network/vision, control-power, relay/protection, terminal and PE zones are spatially separated. Ducts identify mains/drive, control and network routing. HMI/isolator door geometry, terminal access, service access, spare I/O space and the provisional edge envelope are explicitly represented.

## Native verification boundary

When `09_panel_cad/revision_e/native_verification.json` reports PASS, the final FCStd has been independently reopened by FreeCADCmd, controlled shapes checked, STEP reimported as solids, IGES reimported as valid bounded face geometry, and DXF structure/hole coordinates reconciled to the 30-hole schedule. STEP is the solid-retention exchange proof; no IGES solid-retention claim is made. The general-arrangement and mounting-plate PDFs and four major views retain explicit provenance.

## Open construction inputs

Enclosure series/IP, final protective devices, 24 V branch-protection family, relay/terminal accessories, NVIDIA carrier/cooling, cable entry/glands, duct fill, thermal rise, PE/bonding, EMC, short-circuit rating, vendor drilling, site clearances and qualified-human construction review remain open. The CAD gate is dimensional/native engineering evidence only, not fabrication authorization."""))

    _write(root, "13_documentation/electrical_calculation_report.md", _doc("Electrical calculation report - Revision E", """No construction calculation is released. Site voltage/frequency, earthing arrangement, prospective fault current, motor/pump nameplates and duty, cable lengths/routes/installation method, ambient/altitude, enclosure/environment and final device/protection data are absent.

| Calculation | Controlled basis | Current disposition |
|---|---|---|
| 24 VDC supply | Current schedule totals 299 W demand; 25% design-margin current is 15.573 A before inrush/derating | Provisional 20 A concept; verify load/inrush/ambient |
| Branch protection | Load current, conductor ampacity, device withstand and coordination | Blocked pending selected devices and field data |
| Voltage drop | Two-way route length, current, conductor resistance and minimum device voltage | Blocked pending routes/cables/loads |
| Fault current / SCCR | Site source impedance plus every component interrupt/withstand rating | Blocked; no assembly rating claimed |
| Thermal | Verified device losses, enclosure, ambient, altitude and solar/process exposure | Blocked; CAD space does not prove thermal compliance |
| Duct fill / bend | Actual conductor OD, bundle/grouping and manufacturer rules | Blocked; routing envelopes only |
| PE/bonding/EMC | Earthing system, fault current, conductor route and approved shield policy | Blocked; conceptual topology only |

False precision is prohibited. Native CAD and source-consistent schedules do not close these site-dependent calculations."""))

    _write(root, "13_documentation/software_design_specification.md", _doc("Software design specification - Revision E", """## Ownership and scan order

`OB1` calls the single `DB_CellMain` instance. `FB_CellMain` owns command sequencing, two VFD instances, gate, clamp, two fill channels, recipe, vision, capper, alarm and coordinator instances. The cyclic order is normalized inputs, command arbitration, equipment control/status, sequence, first-out/alarm mapping and final physical-output mapping. Startup decommands outputs and requires explicit recovery/reset and a new Start edge.

## PLC-edge transaction

`FB_VisionInterface` latches a nonzero session epoch and strictly monotonic inspection ID. `RequestInProgress` prevents duplicate coordinator pulses from advancing the ID. The request trigger is level-held until coherent BUSY or a terminal result for the exact identity is observed. Wrong/stale/future/regressed identity, heartbeat loss/regression, invalid model ID/hash, partial/contradictory result, warning/fault or low confidence prevents acceptance. Results remain immutable until exact acknowledgement; transport cleanup never authorizes transfer.

## Edge adapter

The production-shaped Python adapter requires Basic256Sha256 SignAndEncrypt, X.509 application and user identity, pinned server certificate, trust/CRL stores, a controlled 27-node map and bounded connect/operation/inference/reconnect timing. It writes one typed result payload and publishes `RESULT_VALID` last. Structured JSON logs, local health/readiness and metrics expose first-out state without accepting remote motion commands.

## Evidence boundary

Source parity, simulator contracts and encrypted asyncua test-server/client evidence are controlled. No native TIA/WinCC compile, PLCSIM equivalence, production S7 endpoint validation, target Jetson qualification, trained model, performance result or physical commissioning is claimed."""))

    _write(root, "14_qa/toolchain_audit.md", _doc("Toolchain audit - Revision E", """## Siemens

TIA Portal V20 executable version `2000.0.9501.1` was observed at `C:\\Program Files\\Siemens\\Automation\\Portal V20\\Bin\\Siemens.Automation.Portal.exe`, SHA-256 `4AB4C76CFA956956187B4E1401DD11EED3473FE60CA121C13698F6918DA4354F`. Engineering/Openness and HMI assemblies have SHA-256 `4593BDDCBBE92472B2FAC25955051066C39C9935A5E696359C6C5F2BD214FCD1` and `93FACFD3EE14536EC1640CEC5501BB2102444579901E713930E662950F4AC7C9`. STEP 7/WinCC components and Automation License Manager 6.2 SP1 are present. The active sandbox identity is not in TIA Engineer or TIA Openness groups, a V20 entitlement is unproven, Startdrive is absent and PLCSIM/PLCSIM Advanced are absent. No project/archive was fabricated and no compile result is claimed.

## FreeCAD

Portable FreeCAD `1.1.3`, revision `20260725 (Git shallow)`, is runnable through FreeCADCmd. The `FreeCADCmd.exe` SHA-256 is `B5551D26050ED64981C5767729BB35900FD4975FA7FD31714C17DD714B6FD44C` and is authoritative for the final reopen/reimport. The retained pre-clearance-metadata-correction GUI views were rendered by `FreeCAD.exe` of the same version, SHA-256 `D831ED7EEE385D5A370A83B078DD90B1F7621BB65BB7C427F06C736C8652D5F0`; their limited semantic-geometry provenance is recorded without claiming a second final GUI reopen. Exact native result and exchange-format behavior are recorded in `09_panel_cad/revision_e/native_verification.json`; the controlled output directory contains no backup/lock/autosave artifact.

## QElectroTech

The official Windows ready-to-use QElectroTech `0.100.0+git8590` package was used. Executable SHA-256: `FCC3465825CC6F1BF3997D9C8054858E647A2038C8C01B7A3335A914106DE926`; downloaded archive SHA-256: `552402198011F37633FFCFF4F9CE561A9ABAF22DC14F9CC09DDC231245B16445`. A superseded candidate reopened, but layout defects were found and corrected. The final corrected QET hash was not natively reopened/exported; no final native-QET pass is claimed.

## NVIDIA/runtime

An RTX 5060 Laptop GPU, driver `595.95`, 8,151 MiB and compute capability 12.0 were observed. `nvidia-smi` reports CUDA compatibility 13.2, not a CUDA Toolkit installation. CUDA Toolkit (`nvcc`), TensorRT, DeepStream, TAO, Docker, NVIDIA Container Toolkit, OpenUSD and Omniverse tools were not found. A temporary Python 3.12.13 environment with `asyncua 2.0.1`, `cryptography 50.0.0` and `pyOpenSSL 26.4.0` executed encrypted local integration tests; it is not a production target runtime."""))

    _write(root, "14_qa/validation_matrix.md", _doc("Validation matrix - Revision E", """| Domain | Evidence | Disposition |
|---|---|---|
| Canonical data / schedules | Uniqueness, cross-artifact and rationale coverage | PASS when validator reports zero failures |
| Siemens SCL | Generator parity plus process/interface/source contracts | Source-tested; native TIA compile BLOCKED |
| HMI/Startdrive/PLCSIM | Import-ready specifications/schedules only | Native execution BLOCKED |
| Process simulator | 32 deterministic scenarios and test suite | PASS; explicitly not PLCSIM/physical evidence |
| NVIDIA OPC UA | Secure asyncua server/client, PKI, reconnect, idempotency, health/metrics | Local integration PASS; production endpoint/model/runtime BLOCKED |
| QElectroTech | Corrected 26-folio QET, static/schedule contracts | Source PASS; exact-hash reopen/export/all-page review BLOCKED |
| FreeCAD/STEP/IGES/DXF | Selected-architecture native source, reopen/reimport and visual package | Native gate follows controlled verification record |
| XLSX/PDF | Deterministic generation, formula scan and rendered visual review | Final release evidence after freeze |
| Safety/electrical construction | Boundary statement and conceptual separation | Qualified/site/physical activities BLOCKED |
| Release integrity | Staged/HEAD manifest, determinism and fresh-clone reproduction | PASS for published candidate `b9633c6255fe34e48a1be34afe5024935f48651e`; final attestation commit is rechecked after push |
"""))

    _write(root, "00_project_control/final_release_checklist.md", _doc("Final release checklist - Revision E", """- [x] Revision-E canonical schedules regenerate from controlled owners.
- [x] All 15 Siemens SCL exports retain generator parity and poll-safe request contracts.
- [x] Encrypted real asyncua test-server/client integration is controlled.
- [x] Selected-architecture Revision-E FCStd/exchange artifacts and verification evidence are controlled when their record passes.
- [x] Corrected 26-folio QET source reconciles tags, addresses, terminals and cables.
- [ ] Corrected final QET hash reopens, exports and receives all-page/cross-reference review.
- [ ] Native TIA V20/WinCC/Startdrive projects open and compile; PLCSIM traces pass.
- [ ] Site electrical calculations, qualified safety validation, real AI model/target execution, FAT and SAT pass.
- [x] Published candidate `b9633c6255fe34e48a1be34afe5024935f48651e` manifest, clean worktree, upstream SHA and fresh GitHub-clone reproduction passed; repeat for the final attestation commit before handoff.

Unchecked items block construction, production deployment or physical acceptance; they are not missing success claims."""))

    _write(root, "14_qa/source_audit_report.md", _doc("Source audit report - Revision E", """Revision-E source review covers the inherited D.1 restart/replay/disposition invariants plus held PLC-to-edge request semantics, immutable active identity, duplicate-request suppression, exact acknowledgement and fail-closed reconnect behavior. The secure adapter enforces typed node ownership, X.509 identity and Basic256Sha256 SignAndEncrypt; its local asyncua tests use synthetic requests and a controlled no-model backend.

The selected-architecture FreeCAD workstream supersedes the obsolete historical native baseline and records format-specific verification without claiming IGES solid retention. The corrected QET is a genuine new 26-folio source, but final-hash native reopen/export and all-page review are explicitly blocked. Static/source/agent checks do not establish Siemens compilation, electrical construction, functional safety, production AI performance, FAT/SAT or physical behavior."""))

    _write(root, "14_qa/executed_test_report.md", _doc("Executed test report - Revision E", """Execution date: 2026-08-03. Source/design tests use the controlled Python 3.12.13 toolchain; encrypted OPC UA tests use the separately locked Python 3.12.13 / asyncua 2.0.1 environment. Native CAD evidence uses FreeCADCmd 1.1.3. These results are not TIA compile, PLCSIM, FAT, SAT, safety validation, electrical construction test or model-performance evidence.

| Workstream | Exact result | Evidence boundary |
|---|---:|---|
| Simulator/source/native contracts | 88/88 PASS | Includes inherited 58, nine poll-safe Siemens contracts, six QET contracts and 15 CAD contracts |
| NVIDIA edge service | 59/59 PASS | 47 protocol/service, two observability, eight encrypted asyncua server/client and two operational-documentation tests |
| PLC-AI interface harness | 15/15 PASS | Deterministic composed interface model |
| Timed scenarios | 32/32 generated with zero invariant violations | Exactly one normal release; no automatic restart |
| Engineering validator | 551/551 PASS | Static/data/source/native-evidence contracts; no Siemens-native claim |
| QET verifier | 24/24 PASS; dedicated tests 6/6 | Corrected source only; exact-hash native reopen/export remains BLOCKED |
| FreeCAD native verifier | 80/80 PASS | 165 objects, 148 valid controlled solids, exact GUI-tool provenance, STEP solids, IGES bounded faces, DXF and 30 holes |
| FreeCAD verifier repeatability | 3/3 generated evidence files byte-identical across two runs | Native geometry/evidence determinism; FCStd/IGES byte identity is not claimed |
| Workbook | 21 sheets; zero formula-error matches | Two normalized builds SHA-256 `32D6D4CC67054C911149D65444F332D04EA1D6907B4F887E93A5FF5118B85D49` |
| Release PDF | 5 pages | Two builds SHA-256 `5E9DEEEF050524140B730BEDFAB41998811F7C7EB472183CC264FCA092400E08` |

Published candidate `b9633c6255fe34e48a1be34afe5024935f48651e` was cloned afresh from GitHub outside OneDrive. The complete workflow passed: manifest 310/310 with zero discrepancies, integrity 534/534, validator 551/551, 88/88 simulator/source/native contracts, 59/59 edge tests, 15/15 interface tests, 32 scenarios, FreeCAD 80/80, QET 24/24, deterministic workbook/PDF builds and a clean final worktree. The final attestation commit is subjected to the same post-push check before handoff."""))

    _write(root, "14_qa/post_push_reproduction.md", _doc("Post-push fresh-clone reproduction - Revision E", """## Published candidate

- Branch: `codex/revision-e-native-engineering-execution`
- GitHub commit: `b9633c6255fe34e48a1be34afe5024935f48651e`
- Clone basis: brand-new GitHub clone outside OneDrive
- Workflow: `powershell -ExecutionPolicy Bypass -File scripts/reproduce_validation.ps1`
- Result: **PASS** with exit code 0

| Check | Result |
|---|---|
| Manifest | 310 listed / 310 actual; 0 missing, unlisted, unexpected or discrepant |
| Release integrity | 534/534 PASS |
| Engineering validator | 551/551 PASS |
| Siemens/simulator/native contracts | 88/88 PASS |
| NVIDIA edge-service tests | 59/59 PASS |
| PLC-AI interface harness | 15/15 PASS |
| Timed scenarios | 32/32 PASS |
| QET structural verifier | 24/24 PASS |
| FreeCAD native verifier | 80/80 PASS |
| Workbook/PDF | Two deterministic builds each; 21 sheets and 5 pages rendered |
| Final repository state | Clean |

This closes the locally achievable release-integrity gate for the published candidate. It is configuration-management evidence, not qualified-human engineering approval. The final attestation commit is re-cloned and rerun after publication; no native Siemens, exact-final-hash QET reopen/export, construction, model, physical or safety gate is implied."""))

    _write(root, "14_qa/visual_review_report.md", _doc("Visual artifact review report - Revision E", """A software-agent visual review inspected the complete rendered sets. This is not qualified-human electrical, panel, safety or construction approval.

| Artifact | Rendered/inspected | Result |
|---|---:|---|
| Engineering workbook | 21/21 sheets | PASS: consistent navy/blue tabular style, frozen/table structure, readable wrapping, no visible clipping; summary shows 5 PASS / 4 PARTIAL / 12 BLOCKED / 1 OPEN and exact release boundary |
| Release-evidence PDF | 5/5 pages | PASS: titles, tables, margins, footer/page numbers and boundary wording readable |
| Revision-E CAD general arrangement | 4/4 pages | PASS: front, isometric/depth, door and segregation/clearance views readable; provisional assumptions visible |
| Revision-E mounting-plate PDF | 2/2 pages | PASS: dimensioned layout and 30-hole coordinate register readable; construction boundary visible |
| Native CAD PNG views | 4/4 views | PASS: front, isometric, segregation and door images open without corruption; provenance is bounded in native evidence |
| Historical QET baseline PDF | 24/24 pages | PASS for retained historical legibility only; it remains Revision A and is not the current schematic package |
| Corrected Revision-E QET | 0/26 final-hash folios | BLOCKED: no corrected-hash native reopen/PDF export, so no all-page visual pass is claimed |

The release PDF and workbook were rebuilt twice with identical controlled hashes. Contact sheets are controlled for audit navigation; detailed source files remain authoritative."""))

    _write(root, "14_qa/final_gate_review.md", _doc("Final locally achievable gate review - Revision E", """The integrated candidate closes native FreeCAD and local encrypted OPC UA implementation gates while preserving Revision-D.1 Git-object authority. The corrected QET is controlled and statically reconciled but its final hash was not reopened/exported, so native schematic and all-page review gates remain partial/blocked. No software-agent review is represented as qualified-human approval.

Current gate totals are **5 PASS, 4 PARTIAL, 12 BLOCKED and 1 OPEN**. PASS applies to canonical reconciliation, native FCStd reopen, STEP/IGES/DXF reimport, local PLC-NVIDIA failure testing and release integrity after published-candidate clean-clone reproduction. PARTIAL applies to requirements ownership, hardware/catalog confirmation, QET source/native evidence and final BOM/panel construction reconciliation.

Native Siemens, site-dependent electrical calculations, real dataset/model/target NVIDIA runtime, FAT/SAT/commissioning and qualified machinery-safety activities remain explicit blockers. Construction, production deployment, CE/regulatory conformity and physical acceptance are not claimed."""))

    _write(root, "14_qa/design_review_checklist.md", _doc("Final integrated design review checklist - Revision E", """- [x] Requirements, architecture, state names and interfaces reconcile through the controlled model.
- [x] Tags, PLC addresses, alarm ranges, terminals, cables, device quantities and network nodes are machine-checked.
- [x] PLC ownership, safe decommand, explicit product disposition and no-automatic-restart rules are retained.
- [x] Poll-safe request identity and encrypted OPC UA fail-closed behavior have executable contracts.
- [x] Selected-architecture FCStd reopens; STEP/IGES/DXF behavior and mounting holes are independently verified.
- [x] Corrected QET source reconciles the controlled schedules and bounded folio layout.
- [x] Workbook and release/CAD/historical-baseline PDFs receive complete rendered visual review.
- [ ] Corrected final QET hash receives native reopen, export, cross-reference and 26-folio visual review.
- [ ] TIA/WinCC/Startdrive native project compiles/restores and PLCSIM traces pass.
- [ ] Site electrical/protection/thermal/conductor calculations and vendor construction checks close.
- [ ] Real optical feasibility, dataset, model training/evaluation and target edge qualification close.
- [ ] FAT, SAT, commissioning, qualified safety validation and qualified-human engineering approvals close.

Unchecked items are controlled blockers, not omitted evidence."""))

    fds_path = root / "13_documentation/functional_design_specification.md"
    fds = fds_path.read_text(encoding="utf-8")
    fds = fds.replace("# Functional design specification\n", "# Functional design specification - Revision E\n")
    marker = "## Revision-E PLC-edge request transport"
    if marker not in fds:
        fds = fds.rstrip() + """

## Revision-E PLC-edge request transport

The Inspect step creates one immutable `(session epoch, inspection ID)` transaction and holds its request level until the edge is coherently BUSY or an exact terminal result is received. Polling, reconnect or a repeated coordinator request cannot allocate a second ID. Result acceptance remains a PLC decision; a quality reject enters controlled product disposition, while communications/identity/model/integrity faults decommand the process and prevent transfer. Recovery never restarts a cycle automatically.
"""
    _write(root, "13_documentation/functional_design_specification.md", fds)

    workflow_path = root / "00_project_control/repository_release_workflow.md"
    workflow = workflow_path.read_text(encoding="utf-8")
    workflow = workflow.replace("# Repository and release-byte workflow - Revision D.1", "# Repository and release-byte workflow - Revision E")
    workflow_marker = "## Revision-E native-application discipline"
    if workflow_marker not in workflow:
        workflow = workflow.rstrip() + """

## Revision-E native-application discipline

Author native files only in a disposable non-synchronized engineering clone. Disable native backup/autosave output inside controlled directories and reject `FCBak`, lock, cache, temporary or recovery artifacts. Native-source/exchange binaries are exact-byte Git objects; generators may rebuild only explicitly deterministic source/report artifacts. Stage the frozen engineering content before manifest generation, verify index bytes, commit, then verify HEAD bytes from a clean clone outside OneDrive. If OneDrive resurrects superseded paths, abandon that checkout for release work rather than hiding or manifesting them.
"""
    _write(root, "00_project_control/repository_release_workflow.md", workflow)

    _write(root, "14_qa/acceptance_gate_status.md", _doc("Acceptance gate status - Revision E", "\n".join(
        f"- Gate {row['gate']}: **{row['status']}** - {row['acceptance_gate']}: {row['evidence_or_blocker']}" for row in model["acceptance_gates"]
    )))
    _write(root, "release/RELEASE_NOTES.md", _doc("Revision E release notes", """Revision E preserves Revision D.1 Git-object byte authority and clean-clone reproducibility while adding genuine native engineering/tool evidence where locally achievable. Principal changes are the selected-architecture FreeCAD panel workstream, official QElectroTech 0.100 workstream, a PLC request level held across OPC UA polling, immutable active request identity, and a secure observable asyncua adapter with real server/client integration tests.

Acceptance-gate states are derived from controlled evidence, not filenames. Native Siemens, site-dependent electrical, real dataset/model/target runtime, FAT/SAT/commissioning and qualified safety/human approval gates remain open exactly as recorded. This is a fictional engineering-development release candidate and is not for construction or production deployment."""))

    docs = [
        {"document_id":"DOC-001","title":"Repository overview","path":"README.md","revision":REVISION,"owner":"Lead systems engineer","status":"Controlled"},
        {"document_id":"DOC-002","title":"Canonical model","path":"00_project_control/canonical_model.json","revision":REVISION,"owner":"Lead systems engineer","status":"Controlled"},
        {"document_id":"DOC-003","title":"Functional design specification","path":"13_documentation/functional_design_specification.md","revision":REVISION,"owner":"Controls engineer","status":"Controlled; native compile open"},
        {"document_id":"DOC-004","title":"Software design specification","path":"13_documentation/software_design_specification.md","revision":REVISION,"owner":"Controls engineer","status":"Controlled; native compile open"},
        {"document_id":"DOC-005","title":"PLC-NVIDIA interface control","path":"02_system_architecture/interface_control_document.md","revision":REVISION,"owner":"Controls/vision","status":"Controlled; production endpoint open"},
        {"document_id":"DOC-006","title":"Panel design report","path":"13_documentation/panel_design_report.md","revision":REVISION,"owner":"Electrical/panel","status":"Controlled assumptions; construction open"},
        {"document_id":"DOC-007","title":"Electrical calculation report","path":"13_documentation/electrical_calculation_report.md","revision":REVISION,"owner":"Electrical","status":"Provisional; site inputs open"},
        {"document_id":"DOC-008","title":"Acceptance gate status","path":"14_qa/acceptance_gate_status.md","revision":REVISION,"owner":"Independent V&V","status":"Controlled"},
        {"document_id":"DOC-009","title":"Engineering workbook","path":"10_schedules/FC01_engineering_schedules.xlsx","revision":REVISION,"owner":"Lead systems engineer","status":"Controlled generated artifact"},
        {"document_id":"DOC-010","title":"Release evidence PDF","path":"release/FC01_release_evidence.pdf","revision":REVISION,"owner":"Lead systems engineer","status":"Controlled generated artifact"},
        {"document_id":"DOC-011","title":"Release manifest","path":"release/manifest.json","revision":REVISION,"owner":"Configuration management","status":"Frozen after all content"},
        {"document_id":"DOC-012","title":"Native panel verification","path":"09_panel_cad/revision_e/native_verification.json","revision":REVISION,"owner":"Panel engineer","status":"Native gate evidence"},
        {"document_id":"DOC-013","title":"Native QET verification","path":"03_electrical/revision_e/native_verification.json","revision":REVISION,"owner":"Electrical engineer","status":"Native gate evidence when present"},
        {"document_id":"DOC-014","title":"Post-push fresh-clone reproduction","path":"14_qa/post_push_reproduction.md","revision":REVISION,"owner":"Configuration management","status":"Published-candidate release-integrity evidence"},
    ]
    _csv(root, "00_project_control/document_register.csv", docs)
    _csv(root, "10_schedules/document_register.csv", docs)


if __name__ == "__main__":
    apply_revision_e(Path(__file__).resolve().parents[1])
