from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from revision_d_generator import _csv, _doc, _write


REVISION = "G"
DATE = "2026-08-08"
NOTICE = "FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION."
SAFETY = (
    "CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, "
    "DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. "
    "NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
)
AI_BOUNDARY = (
    "THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF "
    "PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL."
)


def doc(title: str, body: str) -> str:
    return f"# {title}\n\n> {NOTICE}\n\n> {SAFETY}\n\n{body}"


GATES = [
    {
        "gate_id": "G0-01", "requirement": "Reviewable two-environment Google Cloud architecture",
        "current_evidence": "cloud/architecture.md and cloud/terraform", "current_status": "VERIFIED",
        "missing_input": "None for design", "responsible_agent": "Cloud/DevSecOps workstream",
        "planned_action": "Retain architecture under release control", "acceptance_evidence": "Revision-G static security verification",
        "external_dependency": "None", "final_disposition": "VERIFIED - design only; no resources created",
    },
    {
        "gate_id": "G0-02", "requirement": "Terraform format, native validate and non-destructive plan",
        "current_evidence": "Static HCL/security checks pass; Terraform CLI absent", "current_status": "BLOCKED BY EXTERNAL SYSTEM",
        "missing_input": "Approved Terraform/OpenTofu CLI, Google project, billing identity and ADC", "responsible_agent": "Cloud owner",
        "planned_action": "Run cloud/scripts/plan_cloud.ps1 after consolidated approval", "acceptance_evidence": "fmt/validate/plan logs and plan SHA-256",
        "external_dependency": "User cloud authorization and tool approval", "final_disposition": "BLOCKED - no plan or apply claimed",
    },
    {
        "gate_id": "G0-03", "requirement": "Cloud security, budget and shutdown controls",
        "current_evidence": "No external IPs, IAP-only ingress, separate service accounts, budgets, schedules and bucket controls encoded",
        "current_status": "IMPLEMENTABLE NOW", "missing_input": "Project-specific IAM principals, billing account and reviewed budget",
        "responsible_agent": "Cloud security owner", "planned_action": "Parameterize and plan only after approval",
        "acceptance_evidence": "Reviewed plan plus Security Command Center/IAM evidence after apply",
        "external_dependency": "Cloud project and billing access", "final_disposition": "DEPLOYABLE; NOT PROVISIONED",
    },
    {
        "gate_id": "G1-01", "requirement": "Authorized TIA Portal V20 native project and reopen",
        "current_evidence": "Portal executable 2000.0.9501.1 and Openness V20 assemblies installed; no genuine AP20",
        "current_status": "REQUIRES LICENCE", "missing_input": "Valid STEP 7/WinCC licences and Siemens TIA Openness group membership",
        "responsible_agent": "Licensed Siemens engineer", "planned_action": "Execute siemens_native handoff and import controlled sources",
        "acceptance_evidence": "Native AP20/ZAP20, reopen log and hashes", "external_dependency": "Licence, authorization and qualified operator",
        "final_disposition": "BLOCKED - no AP20/ZAP20 fabricated",
    },
    {
        "gate_id": "G1-02", "requirement": "Native PLC, hardware and HMI compile",
        "current_evidence": "99 source/simulator contract tests; import-ready SCL/HMI tables",
        "current_status": "REQUIRES LICENCE", "missing_input": "Authorized TIA session and catalog confirmation",
        "responsible_agent": "Licensed Siemens engineer", "planned_action": "Compile and disposition every warning",
        "acceptance_evidence": "Raw native compile logs and screenshots", "external_dependency": "TIA licence/authorization",
        "final_disposition": "BLOCKED - source tests are not native compilation",
    },
    {
        "gate_id": "G1-03", "requirement": "Startdrive and PLCSIM execution",
        "current_evidence": "Neither Startdrive nor PLCSIM is installed", "current_status": "REQUIRES LICENCE",
        "missing_input": "Approved installers/licences plus motor and pump data", "responsible_agent": "Drives/controls owner",
        "planned_action": "Install through approved Siemens channel, configure, compile and simulate",
        "acceptance_evidence": "Product inventory, native compile and PLCSIM traces", "external_dependency": "Software, licences and machine data",
        "final_disposition": "BLOCKED",
    },
    {
        "gate_id": "G2-01", "requirement": "Production-shaped fail-closed PLC-AI edge contract",
        "current_evidence": "47-node contract, encrypted asyncua integration and immutable ACK behavior; 86 edge and 17 harness tests",
        "current_status": "VERIFIED", "missing_input": "Production S7/Jetson endpoint for deployment acceptance",
        "responsible_agent": "NVIDIA/controls owners", "planned_action": "Retain software contract and repeat on target",
        "acceptance_evidence": "Automated unit/integration/fault evidence", "external_dependency": "Target endpoint for production validation",
        "final_disposition": "VERIFIED AS SOFTWARE-ONLY NON-SAFETY CONTRACT",
    },
    {
        "gate_id": "G2-02", "requirement": "Dataset provenance, taxonomy and split controls",
        "current_evidence": "Acquisition/labeling plans, empty controlled manifest and executable validation/split tooling",
        "current_status": "REQUIRES REAL DATA", "missing_input": "Approved representative multi-lot images and annotations",
        "responsible_agent": "Vision product owner", "planned_action": "Collect and double-review approved real data",
        "acceptance_evidence": "Hashed manifest, provenance, class balance, leakage/duplicate review",
        "external_dependency": "Real process samples, camera/lighting and data approval", "final_disposition": "PIPELINE READY; DATASET ABSENT",
    },
    {
        "gate_id": "G2-03", "requirement": "Real TAO training, independent evaluation and deployment artifacts",
        "current_evidence": "Pinned configuration templates and synthetic fail-closed smoke only",
        "current_status": "REQUIRES REAL DATA", "missing_input": "Approved dataset, Linux GPU runtime and selected architecture",
        "responsible_agent": "Vision/MLOps owner", "planned_action": "Train, evaluate, export ONNX and generate target TensorRT engine",
        "acceptance_evidence": "Raw logs, held-out metrics, model card, artifact hashes and target latency",
        "external_dependency": "Dataset, GPU environment and model approval", "final_disposition": "BLOCKED - no model or metric claimed",
    },
    {
        "gate_id": "G2-04", "requirement": "DeepStream/TAO/TensorRT native runtime",
        "current_evidence": "RTX 5060 driver 595.95 is present; nvcc, Docker, TAO, TensorRT and DeepStream absent",
        "current_status": "REQUIRES USER APPROVAL", "missing_input": "Approved Ubuntu 24.04/container runtime installation or cloud GPU plan",
        "responsible_agent": "NVIDIA platform owner", "planned_action": "Execute pinned environment runbook after approval",
        "acceptance_evidence": "Native version logs, container digest, SBOM and measured smoke/latency logs",
        "external_dependency": "Installation approval, registry terms and runtime", "final_disposition": "BLOCKED - GPU inventory only",
    },
    {
        "gate_id": "G3A-01", "requirement": "Controlled commissioning procedures and blank records",
        "current_evidence": "commissioning directory contains FAT/SAT, inspection, calibration, I/O and safety-review templates",
        "current_status": "VERIFIED", "missing_input": "None for controlled blank templates",
        "responsible_agent": "Commissioning preparation owner", "planned_action": "Issue to qualified execution team",
        "acceptance_evidence": "Revision-G consistency and schema verification", "external_dependency": "None for preparation",
        "final_disposition": "VERIFIED AS DOCUMENTATION ONLY",
    },
    {
        "gate_id": "G3A-02", "requirement": "Construction information reconciled to final site/equipment inputs",
        "current_evidence": "Deterministic fictional schedules exist; Revision-F vision electrical delta and site calculations remain provisional",
        "current_status": "REQUIRES REAL DATA", "missing_input": "Supply, earthing, fault current, motors, routes, ambient, enclosure and selected vision hardware",
        "responsible_agent": "Qualified electrical designer", "planned_action": "Finalize calculations and apply controlled QET/CAD change",
        "acceptance_evidence": "Approved calculations, updated native QET/CAD and construction review",
        "external_dependency": "Site/equipment data and qualified review", "final_disposition": "PARTIAL - not construction ready",
    },
    {
        "gate_id": "G3B-01", "requirement": "Physical FAT/SAT and commissioning evidence",
        "current_evidence": "Blank records only", "current_status": "REQUIRES HARDWARE",
        "missing_input": "Built panel/machine, calibrated instruments, site and qualified testers",
        "responsible_agent": "Commissioning manager", "planned_action": "Execute controlled procedures without prefilled values",
        "acceptance_evidence": "Signed raw measurements, punch closure and as-built redlines",
        "external_dependency": "Hardware and personnel", "final_disposition": "0% EXECUTED",
    },
    {
        "gate_id": "G3C-01", "requirement": "Qualified electrical and machinery-safety review",
        "current_evidence": "Conceptual boundary, hazard assumptions and validation template only",
        "current_status": "REQUIRES QUALIFIED PERSON", "missing_input": "Named competent electrical and machinery-safety engineers plus project risk assessment",
        "responsible_agent": "Project owner", "planned_action": "Submit qualified-review handoff",
        "acceptance_evidence": "Signed review, validated calculations and safety lifecycle records",
        "external_dependency": "Qualified people and organization approval", "final_disposition": "0% EXECUTED",
    },
]


def _write_csv_header(root: Path, rel: str, columns: list[str]) -> None:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerow(columns)


def apply_revision_g(root: Path) -> None:
    _csv(root, "00_project_control/revision_g_gap_matrix.csv", GATES)
    _csv(root, "10_schedules/revision_g_gap_matrix.csv", GATES)
    _write(root, "00_project_control/revision_g_charter.md", doc("Revision G execution charter", """Revision G is an evidence-driven execution programme. It preserves the verified Revision-F Git-object and native-CAD baseline while adding a disabled-by-default cloud foundation, an exact Siemens licence/access handoff, a data-gated NVIDIA execution pipeline and commissioning-ready blank records.

No paid cloud resource, licence acceptance, native Siemens project, model, metric, physical result or professional approval is created by this revision. A task closes only when it produces genuine execution evidence, removes a blocker, implements reproducible closure automation or gives the external owner one exact handoff.

## Controlled completion language

- G0: cloud-ready, not provisioned.
- G1: source-tested and native-execution-ready, not natively compiled.
- G2: software-pipeline validated with synthetic controls, not production-model validated.
- G3A: commissioning documentation issued but site-dependent construction information remains provisional.
- G3B/G3C: not executed.
"""))
    _write(root, "00_project_control/revision_g_decision_log.md", doc("Revision G decision log", """| Decision | Disposition | Engineering rationale |
|---|---|---|
| DG-001 | Use two isolated cloud environments | Siemens does not need a GPU; NVIDIA training/runtime has different OS, driver and cost controls. |
| DG-002 | Keep all VM creation flags false by default | Repository validation must not create billable infrastructure. |
| DG-003 | Prefer a dedicated supported Windows workstation/Siemens-supported hypervisor for G1; retain ordinary GCE only as an explicitly unsupported-lab candidate pending written Siemens confirmation | Siemens V20 documentation names VMware vSphere/Workstation/Player and Hyper-V, not Google Compute Engine. |
| DG-004 | Use Ubuntu 24.04 and DeepStream 9.1 planning baseline for NVIDIA dGPU/Jetson work | Current NVIDIA DeepStream 9.1 documentation specifies Ubuntu 24.04, CUDA 13.2 and TensorRT 10.16 for dGPU, with JetPack 7.2 for Jetson. |
| DG-005 | Never let a synthetic backend assert service READY | Synthetic evidence can test plumbing but cannot support production disposition. |
| DG-006 | Do not re-author QET/CAD in G without a hardware/tag/envelope change | Revision-E native CAD remains valid; the known Revision-F electrical delta remains an explicit construction-readiness blocker rather than being hidden. |
| DG-007 | Requalify artifact-tool 2.8.39 instead of weakening the old lock | The private 2.8.31 package is unavailable; a lock change requires two full deterministic builds and complete visual review. |
"""))
    _write(root, "00_project_control/revision_g_dependency_graph.mmd", """flowchart TD
  A[Revision-F verified Git baseline] --> G0[G0 cloud and execution foundation]
  G0 --> CRED[One controlled cloud approval]
  CRED --> WVM[Windows engineering environment]
  CRED --> GPU[Linux GPU environment]
  WVM --> LIC[Siemens licences and Openness authorization]
  LIC --> G1[G1 native TIA, WinCC, Startdrive and PLCSIM]
  GPU --> DATA[Representative controlled dataset]
  DATA --> G2[G2 train, evaluate, export and target inference]
  G1 --> G3A[G3A commissioning documentation]
  G2 --> G3A
  SITE[Site and equipment inputs] --> G3A
  G3A --> G3B[G3B physical FAT, SAT and commissioning]
  QUAL[Qualified electrical and machinery-safety personnel] --> G3C[G3C qualified review]
  G3B --> RELEASE[Industry validation decision]
  G3C --> RELEASE
""")
    _write(root, "00_project_control/revision_g_gate_status.md", doc("Revision G gate status", """| Stage | Completion | Supported description | Principal evidence | Open boundary |
|---|---:|---|---|---|
| G0 | 78% | Cloud-ready | Reviewable disabled-by-default IaC, security model, cost controls and runbooks | Terraform/OpenTofu native validate/plan, credentials, approval and provisioning not available |
| G1 | 45% | Native-execution-ready | Installed TIA V20/Openness inventory plus import-ready source and exact handoff | No licence/authorization, AP20/ZAP20, compile, Startdrive or PLCSIM |
| G2 | 55% | Software-pipeline validated | Fail-closed OPC UA service, data tooling, synthetic smoke and GPU inventory | No representative data, trained model, CUDA/TAO/TensorRT/DeepStream or target latency |
| G3A | 80% | Commissioning-documentation-ready | Controlled procedures and blank measurement/signature records | Site calculations and Revision-F electrical delta incorporation remain open |
| G3B | 0% | Not physically executed | Blank controlled records only | Hardware, calibrated instruments and qualified execution team |
| G3C | 0% | Not qualified/reviewed | Conceptual risk and validation handoff only | Qualified electrical and machinery-safety engineers |

Overall supported description: **cloud-ready and native-execution-ready engineering package with software-only NVIDIA pipeline validation**. It is not Siemens natively compiled, production-model validated, construction ready, physically commissioned or qualified/approved.
"""))
    _write(root, "00_project_control/revision_g_external_handoffs.md", doc("Revision G consolidated external handoff", """Use this single handoff only when the project owner elects to continue external execution. Do not provide secrets in chat.

## 1. Cloud approval

Approve only a non-destructive Terraform plan first. Provide the Google project ID, billing account ID, approved IAM principals and Application Default Credentials through the local Google CLI/OS credential store. Set an approved monthly budget after checking the current Google Cloud Pricing Calculator. No apply is authorized by this handoff. Pricing is uncertain until region, quotas, Windows licensing, sustained-use/Spot policy and storage are selected. The plan is reversible; no resource exists until a separate apply approval. Stop/removal controls are instance schedules plus the deprovisioning runbook; disks, snapshots and buckets can continue to cost money while VMs are stopped.

## 2. Siemens native access

On a supported Windows engineering host, add the named engineer to the local **Siemens TIA Openness** group, sign out/in, assign valid STEP 7 Professional V20 and WinCC Unified licences through Automation License Manager, and install/authorise Startdrive and PLCSIM/PLCSIM Advanced. Do not send licence keys. Then execute `siemens_native/preflight.ps1` and the native runbook. This changes local security membership and licensed software state and may require administrator approval/restart.

## 3. NVIDIA runtime and data

Approve either the reviewed Linux GPU cloud plan or a local Ubuntu 24.04/container installation and any NVIDIA registry terms. Provide representative bottle/process images through controlled storage, not chat. The owner must approve the label taxonomy before training. Keep the GPU stopped outside active work.

## 4. Physical and qualified execution

Provide the confirmed supply/earthing/fault-current/site/environment data, motor and pump nameplates, selected camera/lens/light/carrier data, built equipment and calibrated instruments. Appoint qualified electrical and machinery-safety engineers and a commissioning manager. They own measurements, signatures, construction release, safety lifecycle and final acceptance.
"""))
    _csv(root, "00_project_control/revision_g_change_register.csv", [
        {"ecr":"ECR-G-001","reason":"Add disabled-by-default secure cloud foundation","affected":"cloud; 00_project_control","compatibility":"No existing runtime or network changed","test_impact":"Static HCL/security/secret checks","risk":"Provider-native validation and plan remain external","migration":"Run one approved plan; apply only under separate approval"},
        {"ecr":"ECR-G-002","reason":"Capture actual native-tool and licence boundary","affected":"siemens_native; nvidia_native; 14_qa","compatibility":"No native artifact fabricated","test_impact":"Inventory schema and executable/hash checks","risk":"Installed software does not prove usable licence","migration":"Execute consolidated handoff"},
        {"ecr":"ECR-G-003","reason":"Issue reproducible data/model/container execution scaffolding","affected":"nvidia_native","compatibility":"47-node PLC-AI contract unchanged","test_impact":"Synthetic fail-closed smoke and configuration checks","risk":"Synthetic evidence is non-production","migration":"Replace only through approved real-data/model ECR"},
        {"ecr":"ECR-G-004","reason":"Issue controlled blank commissioning and qualified-review records","affected":"commissioning","compatibility":"No measured result or signature prefilled","test_impact":"CSV schemas, safety text and blank-evidence checks","risk":"Templates could be misread as execution evidence","migration":"Only signed measured records may close G3B/G3C"},
        {"ecr":"ECR-G-005","reason":"Requalify current artifact runtime and refresh Revision-G release artifacts","affected":"scripts; workbook; PDF; release","compatibility":"Revision-F engineering authorities retained","test_impact":"Two builds, formula scan, all-sheet/page render review and manifest","risk":"Runtime drift could alter rendering","migration":"Lock only after identical builds and visual acceptance"},
    ])

    _write_cloud(root)
    _write_siemens(root)
    _write_nvidia(root)
    _write_commissioning(root)
    _update_controls(root)
    _write_release(root)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _update_controls(root: Path) -> None:
    for rel in ("AGENTS.md", "00_project_control/design_basis.md"):
        source_lines = (root / rel).read_text(encoding="utf-8").splitlines()
        normalized = []
        for line in source_lines:
            if line.startswith("> FICTIONAL ENGINEERING PROJECT"):
                line = f"> {NOTICE}"
            elif line.startswith("> CONCEPTUAL SAFETY ARCHITECTURE"):
                line = f"> {SAFETY}"
            normalized.append(line)
        _write(root, rel, "\n".join(normalized))

    model_path = root / "00_project_control/canonical_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["project"].update({
        "revision": "G", "date": DATE, "notice": NOTICE, "safety_boundary": SAFETY,
        "status": "CONTROLLED NVIDIA IMPLEMENTATION-READINESS RELEASE CANDIDATE - REVISION G CLOUD/NATIVE-EXECUTION READY; NATIVE SIEMENS, REAL DATA/MODEL, SITE, PHYSICAL AND QUALIFIED GATES REMAIN OPEN",
    })
    gates = _read_csv(root / "00_project_control/acceptance_gates.csv")
    updates = {
        "1": ("PARTIAL", "Revision-G requirements, execution gates and evidence are traceable; owner and qualified-human approvals remain absent"),
        "2": ("PARTIAL", "Core authorities reconcile; the Revision-F NVIDIA electrical delta remains provisional and outside final QET/CAD/construction authorities"),
        "3": ("PARTIAL", "TIA V20/Openness installation is inventoried exactly; authorized native catalog confirmation and delivered hardware remain open"),
        "4": ("BLOCKED", "TIA V20 exists but no licensed/Openness-authorized session or genuine AP20 project was available"),
        "5": ("BLOCKED", "No genuine ZAP20 archive exists; no native archive was fabricated"),
        "6": ("BLOCKED", "99 Siemens/source/simulator contract tests pass; native TIA compile was not run"),
        "7": ("BLOCKED", "HMI definitions are controlled; native WinCC Unified compile/usability review was not run"),
        "8": ("BLOCKED", "Startdrive is absent and motor/pump/site data remain unconfirmed"),
        "9": ("BLOCKED", "PLCSIM/PLCSIM Advanced are absent; Python evidence is independent and explicitly non-native"),
        "10": ("PARTIAL", "Inherited exact-hash 26-folio QET reopen remains valid; executable was not found for a new Revision-G execution and automatic cross-references remain unsupported"),
        "11": ("PARTIAL", "Inherited 26-page native export was reviewed; folio 25 clipping/density limitation remains open"),
        "12": ("PASS", "FreeCADCmd 1.1.3 re-executed in Revision G: 165 objects, 148 solids, zero invalid shapes"),
        "13": ("PASS", "Revision-G FreeCAD execution reimported STEP/IGES/DXF and reconciled 30 mounting holes"),
        "14": ("PARTIAL", "Revision-E CAD remains natively verified; final selected vision envelopes and electrical delta incorporation remain open"),
        "15": ("BLOCKED", "Supply, earthing, fault current, motor/pump, routes, installation, ambient and enclosure inputs remain absent"),
        "16": ("BLOCKED", "Dataset acquisition/labeling/schema tooling is controlled; representative real data is absent"),
        "17": ("BLOCKED", "Training/evaluation configuration is ready; no approved dataset, training run, model or metric exists"),
        "18": ("BLOCKED", "RTX 5060 driver query passed; CUDA, Docker, TAO, TensorRT, DeepStream and target Jetson/cloud runtime are absent"),
        "19": ("PARTIAL", "Fail-closed edge/OPC UA/harness/synthetic-authorization tests pass; production S7/Jetson endpoint and physical timing remain unverified"),
        "20": ("OPEN", "G3A procedures and blank records are issued; no FAT, SAT or commissioning measurement was executed"),
        "21": ("BLOCKED", "Conceptual boundary and handoff exist; qualified machinery-safety/electrical verification and validation were not performed"),
        "22": ("PARTIAL", "Revision-G candidate manifest, final commit and post-push fresh-clone reproduction are pending release freeze"),
    }
    published_path = root / "release/revision_g_published_evidence.json"
    if published_path.is_file():
        published = json.loads(published_path.read_text(encoding="utf-8"))
        candidate = str(published.get("candidate_commit", ""))
        if published.get("result") == "PASS" and len(candidate) == 40 and published.get("manifest", {}).get("discrepancies") == 0:
            updates["22"] = ("PASS", f"Published candidate {candidate} reproduced from a fresh GitHub clone: manifest 504/504, zero discrepancies; see DOC-G-015")
    for row in gates:
        row["status"], row["evidence_or_blocker"] = updates[row["gate"]]
    model["acceptance_gates"] = gates
    _write(root, "00_project_control/canonical_model.json", json.dumps(model, indent=2))
    _csv(root, "00_project_control/acceptance_gates.csv", gates)
    _csv(root, "10_schedules/acceptance_gates.csv", gates)
    lines = ["# Acceptance gate status - Revision G", "", f"> {NOTICE}", "", f"> {SAFETY}", ""]
    lines.extend(f"- Gate {row['gate']}: **{row['status']}** - {row['acceptance_gate']}: {row['evidence_or_blocker']}" for row in gates)
    _write(root, "14_qa/acceptance_gate_status.md", "\n".join(lines))

    revisions = _read_csv(root / "00_project_control/revision_history.csv")
    revisions = [row for row in revisions if row["revision"] != "G"]
    revisions.append({"revision":"G","date":DATE,"status":"Cloud/native-execution-ready release candidate","description":"Disabled-by-default secure cloud foundation, exact Siemens/NVIDIA inventories, data-gated native pipeline, commissioning records and requalified release evidence"})
    _csv(root, "00_project_control/revision_history.csv", revisions)

    docs = _read_csv(root / "10_schedules/document_register.csv")
    docs = [row for row in docs if not row["document_id"].startswith("DOC-G-")]
    additions = [
        ("DOC-G-001", "Revision-G charter", "00_project_control/revision_g_charter.md", "Lead systems"),
        ("DOC-G-002", "Revision-G gap matrix", "00_project_control/revision_g_gap_matrix.csv", "Lead systems"),
        ("DOC-G-003", "Secure cloud architecture", "cloud/architecture.md", "Cloud security"),
        ("DOC-G-004", "Cloud Terraform source", "cloud/terraform/README.md", "Cloud security"),
        ("DOC-G-005", "Siemens native report", "siemens_native/native_execution_report.md", "Controls"),
        ("DOC-G-006", "NVIDIA native report", "nvidia_native/native_execution_report.md", "Vision"),
        ("DOC-G-007", "Commissioning package", "commissioning/README.md", "Commissioning"),
        ("DOC-G-008", "Revision-G limitations", "release/REVISION_G_KNOWN_LIMITATIONS.md", "Release"),
        ("DOC-G-009", "Revision-G evidence PDF", "release/FC01_release_evidence.pdf", "Release"),
        ("DOC-G-010", "Revision-G engineering workbook", "10_schedules/FC01_engineering_schedules.xlsx", "Release"),
        ("DOC-G-011", "Revision-G adversarial self-audit", "14_qa/revision_g_audit_report.md", "Release"),
        ("DOC-G-012", "NVIDIA model/runtime evidence status", "nvidia_native/model_card.md", "Vision"),
        ("DOC-G-013", "Qualified safety-review preparation", "commissioning/qualified_review_handoff.md", "Safety boundary"),
        ("DOC-G-014", "Cloud plan status", "cloud/plan_status.md", "Cloud security"),
    ]
    if published_path.is_file():
        additions.append(("DOC-G-015", "Revision-G post-push reproduction", "14_qa/revision_g_post_push_reproduction.md", "Configuration management"))
    docs.extend({"document_id":i,"title":t,"path":p,"revision":"G","owner":o,"status":"Controlled"} for i,t,p,o in additions)
    _csv(root, "10_schedules/document_register.csv", docs)

    historical_hashes = {
        "RR-F-004": "e71d99d01c63889d229b1cd3d76e558bca6387d3df9174c428d5a6bd5a3922c5",
        "RR-F-006": "885c50a543f3600abcd182b5f744cb10e22613d5e7bf5811ab86997c0b13746b",
        "RR-F-007": "e5213d5fec0919ee242246fe56ab1b2727472d3e4bb3f4ebc4dc9ff97bdf9a6a",
        "RR-F-008": "b9bcec7510f2de1d157a4b5dcc27f968be9fcc0c71c03e0e9510db3688129d82",
    }
    reviews = _read_csv(root / "14_qa/review_records.csv")
    reviews = [row for row in reviews if not row["review_record_id"].startswith("RR-G-")]
    for row in reviews:
        if row["review_record_id"] in historical_hashes:
            row["evidence_sha256"] = historical_hashes[row["review_record_id"]]
    def digest(paths: list[str]) -> str:
        value = hashlib.sha256()
        for rel in paths:
            value.update(rel.encode("utf-8")); value.update(b"\0"); value.update((root / rel).read_bytes()); value.update(b"\0")
        return value.hexdigest()
    audit_specs = [
        ("RR-G-001", "Siemens controls/native-execution adversarial self-audit", ["siemens_native/environment_inventory/inventory.json","siemens_native/native_execution_report.md","04_controls_siemens/tia_v20_revision_f_runbook.md"], "No native compile/project/licence or organizationally independent Siemens reviewer"),
        ("RR-G-002", "Electrical construction/documentation adversarial self-audit", ["commissioning/FAT_procedure.md","commissioning/SAT_procedure.md","03_electrical/revision_f_nvidia_electrical_delta.md"], "Site calculations, delta incorporation, construction check and qualified electrical review remain open"),
        ("RR-G-003", "NVIDIA/MLOps/data-quality adversarial self-audit", ["nvidia_native/data_acquisition_plan.md","nvidia_native/data_card.md","nvidia_native/native_execution_report.md"], "No representative data, model, target runtime or production endpoint"),
        ("RR-G-004", "Safety-boundary/claims adversarial self-audit", ["00_project_control/revision_g_gate_status.md","commissioning/qualified_review_handoff.md","release/REVISION_G_KNOWN_LIMITATIONS.md"], "Conceptual review only; no qualified machinery-safety engineer"),
        ("RR-G-005", "Release reproducibility/cybersecurity adversarial self-audit", ["cloud/threat_model.md","cloud/scripts/validate_cloud_iac.py","scripts/verify_revision_g.py"], "Same software worker authored and audited; provider-native cloud plan and final fresh clone still required"),
    ]
    for record_id, scope, paths, limitations in audit_specs:
        reviews.append({"review_record_id":record_id,"reviewer_task":"/root/revision_g_execution","review_type":"Lead software-agent adversarial self-audit; NOT independent professional approval","scope":scope,"method":"Read-only claims/evidence countercheck plus executable Revision-G static verifier","evidence_sha256":digest(paths),"limitations":limitations,"actual_qualification":"Software agent; same worker as author; not an identified qualified human engineer","human_approval_required":"Yes","disposition":"ACCEPT FOR CONTINUED RELEASE VERIFICATION; external/native/physical/qualified gates remain open exactly as stated"})
    _csv(root, "14_qa/review_records.csv", reviews)

    _write(root, "14_qa/revision_g_audit_report.md", doc("Revision G adversarial audit report", """This report records five **self-audit perspectives by the same software worker that authored Revision G**. It is not an independent organizational review, professional certification or qualified-human approval.

| Perspective | Finding | Disposition |
|---|---|---|
| Siemens controls/native | Installed TIA/Openness is not licence/compile evidence; no AP20/ZAP20 exists | External G1 gates remain BLOCKED |
| Electrical/construction | Blank commissioning records are honest; site calculations and vision delta incorporation remain incomplete | G3A remains PARTIAL; G3B 0% |
| NVIDIA/MLOps/data | Synthetic authorization refusal is valid plumbing evidence; no data/model/metric/runtime claim is supportable | G2 production gates remain BLOCKED |
| Safety/claims | Required conceptual boundary is present and no PL/SIL/category/CE/UKCA claim exists | G3C 0%; qualified review required |
| Release/cybersecurity | IaC is disabled by default and statically fail-closed; no secrets or cloud resources found | Native Terraform plan and final fresh clone remain mandatory |

No P0/P1 claim defect was found in the generated Revision-G scope. Open items are explicit external gates, not waived findings.
"""))


def _write_cloud(root: Path) -> None:
    _write(root, "cloud/architecture.md", doc("Revision G secure execution architecture", """Two laboratory environments are separated from each other and from any plant/OT network.

## Environment A - Siemens engineering

A Windows engineering host provides TIA Portal V20, STEP 7 Professional, WinCC Unified, Startdrive, PLCSIM/PLCSIM Advanced and TIA Openness. The primary recommendation is a dedicated always-on engineering workstation or a Siemens-supported VMware/Hyper-V environment. Ordinary Google Compute Engine is retained only as a technically plausible **unsupported laboratory candidate** pending written Siemens confirmation; Siemens V20 installation documentation explicitly names VMware vSphere 8+, Workstation/Player 17+ and Hyper-V Server 2019+, not GCE.

## Environment B - NVIDIA engineering

A separate Ubuntu 24.04 GPU host is provisioned only after approval. DeepStream 9.1 currently requires Ubuntu 24.04, driver 595.58.03, CUDA 13.2 and TensorRT 10.16.0.72 on dGPU. A G2/L4-class VM is a capacity and price candidate, not a selected or provisioned target. Jetson deployment must use the exact DeepStream/JetPack platform matrix and regenerate TensorRT engines for the intended runtime/hardware.

## Network and evidence flow

- Dedicated VPC/subnet; no VM external IP.
- IAP TCP forwarding is the only administrative ingress; firewall source is `35.235.240.0/20` to RDP/SSH tags.
- Cloud NAT provides bounded installation egress; egress firewall permits DNS, NTP and TLS only.
- Separate keyless service accounts; no project-owner grants.
- Versioned, uniform-access, public-access-prevented evidence bucket; no secrets in objects or Terraform state.
- Project audit logging plus optional CPU alert policies; notification-channel IDs remain operator-supplied variables.
- OPC UA and PLC traffic are laboratory-only. No direct conduit to a real plant is created.

Official sources:

- https://support.industry.siemens.com/cs/attachments/109963850/Install_STEP7_WinCC_V20_enUS.pdf
- https://cloud.google.com/iap/docs/tcp-forwarding-overview
- https://cloud.google.com/compute/docs/instances/schedule-instance-start-stop
- https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Installation.html
"""))
    _write(root, "cloud/threat_model.md", doc("Cloud threat model", """| Threat | Control | Residual risk / verification |
|---|---|---|
| Public RDP/SSH exposure | No external IP; IAP-only ingress rule | Verify plan and effective firewall after apply |
| Overprivileged workload identity | Separate keyless service accounts; bucket-level object role only | Review effective IAM; organization policies may add grants |
| Credential disclosure | No key files or secrets in Git; ADC/Secret Manager only | Terraform state and screenshots still require access control |
| Unbounded cost | VM creation false by default, schedules, budget alerts, GPU stopped when idle | Budget alerts do not cap spend; disks/snapshots/storage persist |
| Malicious dependency/image | Require approved image digest, SBOM and vulnerability scan before container build | No container was built in Revision G |
| OT pivot | Lab-only VPC, no plant route/VPN/interconnect | Future OT connection requires separate zone/conduit design |
| Dataset exfiltration | Restricted bucket, versioning, no public access, retention decision | Privacy/provenance approval remains absent |
| Untrusted OPC UA peer | Site PKI, named identities, SignAndEncrypt, least-privilege nodes | Production S7/Jetson PKI integration remains untested |
| Accidental apply/destroy | All create flags false; scripts separate validate/plan from apply; deletion protection | An authorized operator can still override controls |
"""))
    _write(root, "cloud/cost_assumptions.md", doc("Cloud cost assumptions", """No cloud resource was created and actual cost is **EUR/USD 0.00 from this Revision-G execution**.

The estimate is intentionally formula-driven because project region, quota, current price, Windows licence treatment, discounts and run hours are not approved:

`monthly estimate = Windows VM hourly rate * approved hours + GPU VM hourly rate * active training hours + persistent-disk GB-month + snapshot GB-month + object-storage GB-month + network/NAT/logging charges`.

Before plan approval, the owner must record a dated Google Cloud Pricing Calculator export for the selected region and a maximum monthly budget. Budget alerts are notifications and do not automatically cap ordinary Compute Engine spend. Stopping a VM stops vCPU/GPU runtime charges but does not remove persistent disk, snapshot, IP/NAT, Data Access logging, monitoring or storage charges. The Terraform defaults keep both VMs disabled and configure weekday shutdown schedules if enabled. Audit-log volume and retention must be priced before apply.

Official sources: https://cloud.google.com/products/calculator, https://cloud.google.com/billing/docs/how-to/budgets, https://cloud.google.com/compute/docs/instances/schedule-instance-start-stop.
"""))
    _write(root, "cloud/plan_status.md", doc("Cloud plan status", """**Status: NOT RUN / NO RESOURCES CREATED.** Terraform/OpenTofu and Google Cloud CLI are not installed in the inspected environment, and no project/billing credentials or expenditure approval were supplied. Revision G performs deterministic static HCL/security validation only. A provider-native `terraform fmt -check`, `terraform init -backend=false`, `terraform validate` and saved non-destructive plan are required before G0 native validation can close.
"""))
    _write(root, "cloud/windows_tia_build_runbook.md", doc("Windows TIA build runbook", """1. Confirm the selected host/virtualization route is supported by Siemens or obtain written support confirmation.
2. Provision only after approved Terraform plan and cost/security review.
3. Connect through IAP; do not add an external IP or public RDP rule.
4. Patch Windows; install Git/evidence tooling from approved sources.
5. Install TIA V20, STEP 7 Professional, WinCC Unified, Startdrive, PLCSIM and TIA Openness under the organisation licence process.
6. Assign licences without placing keys in Git/logs. Add the engineer to Siemens TIA Openness and re-authenticate.
7. Clone the exact Revision-G commit, run `siemens_native/preflight.ps1`, then follow the existing TIA/WinCC/Startdrive runbooks.
8. Store raw native logs/screenshots/archives only in the controlled evidence path; hash every artifact.
9. Stop the VM after exporting evidence; retain only approved disks/snapshots.
"""))
    _write(root, "cloud/nvidia_gpu_build_runbook.md", doc("NVIDIA GPU build runbook", """1. Confirm current DeepStream/TAO compatibility and selected model requirements before selecting G2/L4 or another GPU.
2. Require an approved plan, quota and price record. Use Spot only for resumable jobs.
3. Provision Ubuntu 24.04 with no external IP; connect through IAP SSH.
4. Install the NVIDIA driver/container stack strictly from official repositories; record version/digest and licence acceptance owner.
5. Pull only an approved digest-pinned DeepStream/TAO image. Generate SBOM and vulnerability report before execution.
6. Mount controlled dataset/artifact storage least-privilege; never embed credentials in an image.
7. Run data validation, synthetic smoke, then approved real training/evaluation. Record raw logs and hashes.
8. Stop the GPU immediately after each job; verify instance state and continuing storage costs.
"""))
    _write(root, "cloud/backup_restore_runbook.md", doc("Cloud backup and restore runbook", """Use versioned object storage for source/evidence and dated disk snapshots only after malware/secret review. Record source disk, snapshot ID, encryption mode, operator, time, retention and restore-test result. Quarterly, restore into an isolated lab project/subnet, verify hashes and delete the test resources. A snapshot is not a substitute for a portable TIA archive, Git history, dataset manifest or model artifact registry.
"""))
    _write(root, "cloud/deprovisioning_runbook.md", doc("Cloud deprovisioning runbook", """1. Export and hash approved evidence; confirm no secrets are included.
2. Stop both VMs and verify status.
3. Review persistent disks, snapshots, buckets, NAT, logging sinks and reserved addresses with owners.
4. Run a saved Terraform destroy plan; require a second reviewer before apply.
5. Preserve only approved retention artifacts; `force_destroy` is disabled.
6. Remove IAM grants/service accounts, then network resources.
7. Confirm Billing export shows no continuing compute/storage/network resource and record final cost.

Revision G does not execute these destructive actions.
"""))

    _write(root, "cloud/terraform/versions.tf", '''terraform {
  required_version = ">= 1.6.0, < 2.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}
''')
    _write(root, "cloud/terraform/variables.tf", '''variable "project_id" {
  type = string
}
variable "billing_account_id" {
  type    = string
  default = null
}
variable "region" {
  type    = string
  default = "europe-west4"
}
variable "zone" {
  type    = string
  default = "europe-west4-a"
}
variable "name_prefix" {
  type    = string
  default = "fc01-lab"
}
variable "subnet_cidr" {
  type    = string
  default = "10.71.0.0/24"
}
variable "admin_principals" {
  type    = set(string)
  default = []
}
variable "operator_principals" {
  type    = set(string)
  default = []
}
variable "create_windows_vm" {
  type    = bool
  default = false
}
variable "create_gpu_vm" {
  type    = bool
  default = false
}
variable "windows_machine_type" {
  type    = string
  default = "n2-standard-8"
}
variable "gpu_machine_type" {
  type    = string
  default = "g2-standard-4"
}
variable "windows_boot_image" {
  type    = string
  default = "projects/windows-cloud/global/images/family/windows-2022"
}
variable "gpu_boot_image" {
  type    = string
  default = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2404-lts-amd64"
}
variable "artifact_bucket_name" {
  type = string
}
variable "monthly_budget_amount" {
  type    = number
  default = 250
}
variable "schedule_time_zone" {
  type    = string
  default = "Europe/Berlin"
}
variable "monitoring_notification_channels" {
  type    = list(string)
  default = []
}
variable "labels" {
  type = map(string)
  default = {
    system      = "fc01"
    environment = "engineering-lab"
    managed_by  = "terraform"
  }
}
''')
    _write(root, "cloud/terraform/observability.tf", '''resource "google_project_iam_audit_config" "all_services" {
  project = var.project_id
  service = "allServices"
  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

resource "google_monitoring_alert_policy" "windows_high_cpu" {
  count                = var.create_windows_vm ? 1 : 0
  display_name         = "${var.name_prefix} Windows sustained high CPU"
  combiner             = "OR"
  notification_channels = var.monitoring_notification_channels
  conditions {
    display_name = "Windows VM CPU above 90 percent for 15 minutes"
    condition_threshold {
      filter          = "resource.type = \\"gce_instance\\" AND resource.labels.instance_id = \\"${google_compute_instance.windows[0].instance_id}\\" AND metric.type = \\"compute.googleapis.com/instance/cpu/utilization\\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.9
      duration        = "900s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  documentation {
    content   = "Investigate the FC01 Windows engineering workload; stop the VM if it is not under an approved active session."
    mime_type = "text/markdown"
  }
}

resource "google_monitoring_alert_policy" "gpu_high_cpu" {
  count                = var.create_gpu_vm ? 1 : 0
  display_name         = "${var.name_prefix} GPU host sustained high CPU"
  combiner             = "OR"
  notification_channels = var.monitoring_notification_channels
  conditions {
    display_name = "GPU host CPU above 90 percent for 15 minutes"
    condition_threshold {
      filter          = "resource.type = \\"gce_instance\\" AND resource.labels.instance_id = \\"${google_compute_instance.gpu[0].instance_id}\\" AND metric.type = \\"compute.googleapis.com/instance/cpu/utilization\\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.9
      duration        = "900s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  documentation {
    content   = "Investigate the FC01 NVIDIA workload and stop the GPU VM when no approved job is active. GPU utilization requires the approved Ops Agent/NVIDIA telemetry setup."
    mime_type = "text/markdown"
  }
}
''')
    _write(root, "cloud/terraform/main.tf", '''locals {
  required_apis = toset([
    "billingbudgets.googleapis.com", "compute.googleapis.com", "iap.googleapis.com",
    "iam.googleapis.com", "logging.googleapis.com", "monitoring.googleapis.com",
    "serviceusage.googleapis.com", "storage.googleapis.com"
  ])
}

resource "google_project_service" "required" {
  for_each           = local.required_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "lab" {
  name                    = "${var.name_prefix}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
  depends_on              = [google_project_service.required]
}

resource "google_compute_subnetwork" "lab" {
  name                     = "${var.name_prefix}-subnet"
  region                   = var.region
  network                  = google_compute_network.lab.id
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = true
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_router" "lab" {
  name    = "${var.name_prefix}-router"
  region  = var.region
  network = google_compute_network.lab.id
}
resource "google_compute_router_nat" "lab" {
  name                               = "${var.name_prefix}-nat"
  router                             = google_compute_router.lab.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  subnetwork {
    name                    = google_compute_subnetwork.lab.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_compute_firewall" "iap_admin" {
  name      = "${var.name_prefix}-iap-admin"
  network   = google_compute_network.lab.name
  direction = "INGRESS"
  priority  = 1000
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["fc01-iap-admin"]
  allow {
    protocol = "tcp"
    ports    = ["22", "3389"]
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "egress_dns" {
  name               = "${var.name_prefix}-egress-dns"
  network            = google_compute_network.lab.name
  direction          = "EGRESS"
  priority           = 900
  destination_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "udp"
    ports    = ["53", "123"]
  }
  allow {
    protocol = "tcp"
    ports    = ["53"]
  }
}
resource "google_compute_firewall" "egress_tls" {
  name               = "${var.name_prefix}-egress-tls"
  network            = google_compute_network.lab.name
  direction          = "EGRESS"
  priority           = 910
  destination_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}
resource "google_compute_firewall" "egress_deny" {
  name               = "${var.name_prefix}-egress-deny"
  network            = google_compute_network.lab.name
  direction          = "EGRESS"
  priority           = 65534
  destination_ranges = ["0.0.0.0/0"]
  deny {
    protocol = "all"
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_storage_bucket" "artifacts" {
  name                        = var.artifact_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  versioning {
    enabled = true
  }
  lifecycle_rule {
    condition {
      age        = 365
      with_state = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }
  labels = var.labels
}
''')
    _write(root, "cloud/terraform/iam.tf", '''resource "google_service_account" "windows" {
  account_id   = "${var.name_prefix}-windows"
  display_name = "FC01 Windows engineering VM"
  description  = "Keyless workload identity; no project-owner grant"
}
resource "google_service_account" "nvidia" {
  account_id   = "${var.name_prefix}-nvidia"
  display_name = "FC01 NVIDIA engineering VM"
  description  = "Keyless workload identity; no project-owner grant"
}

resource "google_project_iam_member" "windows_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.windows.email}"
}
resource "google_project_iam_member" "windows_metrics" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.windows.email}"
}
resource "google_project_iam_member" "nvidia_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.nvidia.email}"
}
resource "google_project_iam_member" "nvidia_metrics" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.nvidia.email}"
}
resource "google_storage_bucket_iam_member" "windows_artifacts" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.windows.email}"
}
resource "google_storage_bucket_iam_member" "nvidia_artifacts" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.nvidia.email}"
}

resource "google_project_iam_member" "iap_admin" {
  for_each = var.admin_principals
  project  = var.project_id
  role     = "roles/iap.tunnelResourceAccessor"
  member   = each.value
}

resource "google_project_iam_custom_role" "vm_operator" {
  role_id     = "fc01LabVmOperator"
  title       = "FC01 Lab VM Operator"
  description = "Start, stop and inspect FC01 lab VMs without broad instance administration"
  permissions = ["compute.instances.get", "compute.instances.list", "compute.instances.start", "compute.instances.stop", "compute.zoneOperations.get"]
}
resource "google_project_iam_member" "vm_operator" {
  for_each = var.operator_principals
  project  = var.project_id
  role     = google_project_iam_custom_role.vm_operator.name
  member   = each.value
}
''')
    _write(root, "cloud/terraform/compute.tf", '''resource "google_compute_resource_policy" "weekday_schedule" {
  name   = "${var.name_prefix}-weekday-schedule"
  region = var.region
  instance_schedule_policy {
    vm_start_schedule {
      schedule = "0 8 * * MON-FRI"
    }
    vm_stop_schedule {
      schedule = "0 18 * * MON-FRI"
    }
    time_zone = var.schedule_time_zone
  }
}

resource "google_compute_disk" "windows_data" {
  count                     = var.create_windows_vm ? 1 : 0
  name                      = "${var.name_prefix}-windows-data"
  type                      = "pd-balanced"
  zone                      = var.zone
  size                      = 200
  physical_block_size_bytes = 4096
  labels                    = var.labels
}
resource "google_compute_disk" "gpu_data" {
  count                     = var.create_gpu_vm ? 1 : 0
  name                      = "${var.name_prefix}-gpu-data"
  type                      = "pd-balanced"
  zone                      = var.zone
  size                      = 500
  physical_block_size_bytes = 4096
  labels                    = var.labels
}

resource "google_compute_instance" "windows" {
  count               = var.create_windows_vm ? 1 : 0
  name                = "${var.name_prefix}-windows"
  machine_type        = var.windows_machine_type
  zone                = var.zone
  deletion_protection = true
  tags                = ["fc01-iap-admin", "fc01-windows"]
  labels              = var.labels
  boot_disk {
    initialize_params {
      image = var.windows_boot_image
      size  = 150
      type  = "pd-balanced"
    }
  }
  attached_disk {
    source = google_compute_disk.windows_data[0].id
    mode   = "READ_WRITE"
  }
  network_interface {
    subnetwork = google_compute_subnetwork.lab.id
  }
  service_account {
    email  = google_service_account.windows.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  resource_policies = [google_compute_resource_policy.weekday_schedule.id]
  metadata = {
    enable-osconfig    = "TRUE"
    serial-port-enable = "FALSE"
  }
  lifecycle {
    prevent_destroy = true
  }
}

resource "google_compute_instance" "gpu" {
  count               = var.create_gpu_vm ? 1 : 0
  name                = "${var.name_prefix}-gpu"
  machine_type        = var.gpu_machine_type
  zone                = var.zone
  deletion_protection = true
  tags                = ["fc01-iap-admin", "fc01-nvidia"]
  labels              = var.labels
  boot_disk {
    initialize_params {
      image = var.gpu_boot_image
      size  = 100
      type  = "pd-balanced"
    }
  }
  attached_disk {
    source = google_compute_disk.gpu_data[0].id
    mode   = "READ_WRITE"
  }
  network_interface {
    subnetwork = google_compute_subnetwork.lab.id
  }
  service_account {
    email  = google_service_account.nvidia.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = false
    preemptible          = false
  }
  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  resource_policies = [google_compute_resource_policy.weekday_schedule.id]
  metadata = {
    enable-osconfig       = "TRUE"
    install-nvidia-driver = "TRUE"
    serial-port-enable    = "FALSE"
  }
  lifecycle {
    prevent_destroy = true
  }
}
''')
    _write(root, "cloud/terraform/safety_checks.tf", '''check "approved_access_before_compute" {
  assert {
    condition     = !(var.create_windows_vm || var.create_gpu_vm) || length(var.admin_principals) > 0
    error_message = "At least one approved IAP administrator principal is required before VM creation."
  }
}

check "budget_before_compute" {
  assert {
    condition     = !(var.create_windows_vm || var.create_gpu_vm) || var.billing_account_id != null
    error_message = "A billing account and budget resource are required before paid compute can be enabled."
  }
}

check "alert_route_before_compute" {
  assert {
    condition     = !(var.create_windows_vm || var.create_gpu_vm) || length(var.monitoring_notification_channels) > 0
    error_message = "At least one approved Monitoring notification channel is required before VM creation."
  }
}
''')
    _write(root, "cloud/terraform/budget.tf", '''data "google_project" "current" {
  project_id = var.project_id
}

resource "google_billing_budget" "monthly" {
  count           = var.billing_account_id == null ? 0 : 1
  billing_account = var.billing_account_id
  display_name    = "${var.name_prefix}-monthly-budget"
  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(floor(var.monthly_budget_amount))
    }
  }
  budget_filter {
    projects = ["projects/${data.google_project.current.number}"]
  }
  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.8
  }
  threshold_rules {
    threshold_percent = 1.0
  }
  all_updates_rule {
    disable_default_iam_recipients = false
  }
}
''')
    _write(root, "cloud/terraform/outputs.tf", '''output "vpc_name" { value = google_compute_network.lab.name }
output "subnet_name" { value = google_compute_subnetwork.lab.name }
output "artifact_bucket" { value = google_storage_bucket.artifacts.name }
output "windows_vm_name" { value = try(google_compute_instance.windows[0].name, null) }
output "gpu_vm_name" { value = try(google_compute_instance.gpu[0].name, null) }
output "cost_warning" { value = "Budget alerts do not cap spend; stopped VMs can retain disk/snapshot/storage/NAT/logging costs." }
''')
    _write(root, "cloud/terraform/terraform.tfvars.example", '''project_id              = "replace-with-approved-project-id"
billing_account_id      = null
artifact_bucket_name    = "replace-with-globally-unique-approved-bucket"
admin_principals        = ["group:approved-cloud-admins@example.invalid"]
operator_principals     = ["group:approved-fc01-operators@example.invalid"]
monitoring_notification_channels = []
monthly_budget_amount   = 250
create_windows_vm       = false
create_gpu_vm           = false
''')
    _write(root, "cloud/terraform/backend.tf.example", '''terraform {
  backend "gcs" {
    bucket = "replace-with-approved-restricted-state-bucket"
    prefix = "fc01/revision-g"
  }
}
''')
    _write(root, "cloud/terraform/README.md", doc("Terraform operator boundary", """The module is reviewable source, not a recorded cloud plan. Both VM creation flags default to false. Copy the variable example outside Git, replace placeholders and authenticate with Application Default Credentials. Run `cloud/scripts/plan_cloud.ps1`; inspect every IAM, firewall, image, GPU, schedule, disk and budget change. Do not apply without separate explicit expenditure/security approval. Provider lock and saved plan files must not be committed if they contain project-sensitive data.
"""))
    _write(root, "cloud/scripts/validate_cloud_iac.py", r'''from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / "cloud" / "terraform"
required = {"versions.tf", "variables.tf", "main.tf", "iam.tf", "compute.tf", "observability.tf", "safety_checks.tf", "budget.tf", "outputs.tf", "terraform.tfvars.example"}
failures = []
paths = {p.name: p for p in TF.glob("*.tf")} | {"terraform.tfvars.example": TF / "terraform.tfvars.example"}
for name in sorted(required):
    if name not in paths or not paths[name].is_file(): failures.append(f"missing {name}")
text = "\n".join(p.read_text(encoding="utf-8") for p in sorted(TF.glob("*.tf")))
checks = {
    "vm create defaults false": text.count('default = false') >= 2,
    "no access_config external IP": "access_config" not in text,
    "IAP source constrained": '35.235.240.0/20' in text,
    "RDP/SSH not world ingress": not re.search(r'source_ranges\s*=\s*\["0\\.0\\.0\\.0/0"\][\s\S]{0,200}ports\s*=\s*\["(?:22|3389)', text),
    "separate service accounts": 'google_service_account" "windows' in text and 'google_service_account" "nvidia' in text,
    "no owner/editor role": "roles/owner" not in text and "roles/editor" not in text,
    "bucket public access prevention": 'public_access_prevention    = "enforced"' in text,
    "bucket force destroy disabled": "force_destroy               = false" in text,
    "shielded secure boot": len(re.findall(r"enable_secure_boot\s*=\s*true", text)) == 2,
    "GPU does not auto restart": bool(re.search(r"automatic_restart\s*=\s*false", text)),
    "instance schedule present": "instance_schedule_policy" in text,
    "budget thresholds present": all(x in text for x in ("0.5", "0.8", "1.0")),
    "egress default deny": bool(re.search(r"deny\s*\{\s*protocol\s*=\s*\"all\"\s*\}", text)),
    "serial ports disabled": len(re.findall(r"serial-port-enable\s*=\s*\"FALSE\"", text)) == 2,
    "HCL braces balanced": text.count("{") == text.count("}"),
    "no comma-separated HCL block assignments": not re.search(r",\s*[A-Za-z_][A-Za-z0-9_-]*\s*=", text),
}
for label, passed in checks.items():
    if not passed: failures.append(label)
for path in TF.rglob("*"):
    if path.is_file() and re.search(r'(?i)(private[_ -]?key|client[_ -]?secret|password)\s*[=:]\s*["\'][^"\']+', path.read_text(encoding="utf-8", errors="ignore")):
        failures.append(f"possible secret in {path.relative_to(ROOT)}")
print(json.dumps({"checks": len(checks) + len(required), "failures": failures, "status": "PASS" if not failures else "FAIL", "scope": "deterministic static controls only; not terraform fmt/validate/plan or cloud evidence"}, indent=2, sort_keys=True))
raise SystemExit(1 if failures else 0)
''')
    _write(root, "cloud/scripts/plan_cloud.ps1", r'''param([Parameter(Mandatory=$true)][string]$VarFile, [string]$OutputDirectory = "")
$ErrorActionPreference = 'Stop'
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) { throw 'Terraform CLI is not installed or approved' }
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\terraform')).Path
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path.TrimEnd('\') + '\'
if (-not (Test-Path -LiteralPath $VarFile -PathType Leaf)) { throw "Variable file does not exist: $VarFile" }
$resolvedVarFile = (Resolve-Path -LiteralPath $VarFile).Path
if (-not $OutputDirectory) { $OutputDirectory = Join-Path ([IO.Path]::GetTempPath()) ('fc01-cloud-plan-' + [Guid]::NewGuid().ToString('N')) }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$outputRoot = (Resolve-Path -LiteralPath $OutputDirectory).Path
if (($outputRoot.TrimEnd('\') + '\').StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Cloud plan output must remain outside the controlled release tree'
}
$workRoot = Join-Path $outputRoot 'terraform-work'
if (Test-Path -LiteralPath $workRoot) { throw "Refusing to overwrite existing work directory: $workRoot" }
New-Item -ItemType Directory -Path $workRoot | Out-Null
Copy-Item -Path (Join-Path $sourceRoot '*') -Destination $workRoot -Recurse
Push-Location $workRoot
try {
  terraform fmt -check -recursive
  terraform init -backend=false -input=false
  terraform validate
  $plan = Join-Path $outputRoot 'fc01-revision-g.tfplan'
  terraform plan -input=false -refresh=false -lock=false -var-file=$resolvedVarFile -out=$plan
  $planText = Join-Path $outputRoot 'fc01-revision-g-plan.txt'
  terraform show -no-color $plan | Set-Content -Encoding utf8 $planText
  Get-FileHash -Algorithm SHA256 $plan,$planText
} finally { Pop-Location }
Write-Output 'NO APPLY WAS RUN. Review the plan and cost separately.'
''')


def _write_siemens(root: Path) -> None:
    inventory = {
        "captured_utc": "2026-08-08T20:48:00Z",
        "host_scope": "Local Windows host through Codex sandbox identity; inventory only",
        "portal": {"path": "C:/Program Files/Siemens/Automation/Portal V20/Bin/Siemens.Automation.Portal.exe", "file_version": "2000.0.9501.1", "sha256": "4ab4c76cfa956956187b4e1401dd11eed3473fe60ca121c13698f6918da4354f", "installed": True},
        "openness": {"v20_assembly": "C:/Program Files/Siemens/Automation/Portal V20/PublicAPI/V20/Siemens.Engineering.dll", "file_version": "2000.0.9501.1", "installed": True, "active_identity_authorized": False, "evidence": "Active identity is CodexSandboxOffline and is not a member of Siemens TIA Openness"},
        "automation_license_manager": {"version": "6.2 SP1 / 602.100.0.34", "installed": True, "licence_entitlement": "UNPROVEN - no key data collected"},
        "step7_v20": {"installed": True, "registry_version": "20.00.0000", "licence": "UNPROVEN"},
        "wincc_v20": {"installed": True, "registry_version": "20.00.0000", "licence": "UNPROVEN"},
        "startdrive": {"installed": False},
        "plcsim": {"installed": False},
        "plcsim_advanced": {"installed": False},
        "native_execution": "NOT RUN - authorization/licence gate",
    }
    _write(root, "siemens_native/environment_inventory/inventory.json", json.dumps(inventory, indent=2, sort_keys=True))
    _write(root, "siemens_native/licence_status.md", doc("Siemens licence and authorization status", """Automation License Manager 6.2 SP1 is installed, but no STEP 7 Professional V20 or WinCC Unified entitlement was proven and no licence key value was queried or recorded. The active sandbox identity is not a member of **Siemens TIA Openness**. Installed binaries do not prove licence availability. Startdrive and PLCSIM/PLCSIM Advanced are absent. Native execution remains blocked.
"""))
    _write(root, "siemens_native/native_execution_report.md", doc("Siemens native execution report", """**Result: BLOCKED BEFORE PROJECT CREATION.** TIA Portal V20 executable and V20 Openness assemblies were found and hashed. No AP20/ZAP20 was created, no hardware catalog was opened, and no PLC/hardware/HMI/drive compile or PLCSIM execution occurred. The exact external closure is in `00_project_control/revision_g_external_handoffs.md`.

The controlled source tests prove deterministic source generation, state-machine/AI fail-closed contracts and schedule parity. They do not prove Siemens syntax acceptance, catalog/order-number availability, firmware compatibility, compile quality, download, timing or runtime behavior.
"""))
    _write(root, "siemens_native/openness_execution_runbook.md", doc("TIA Openness execution runbook", """After licence/group authorization, run `siemens_native/preflight.ps1` under the named engineering identity. Create a new V20 project only through TIA Portal/Openness; import the controlled SCL and tag/alarm/HMI tables, configure the exact catalog hardware and PROFINET topology, then compile hardware/software/HMI/drives. Export raw compiler messages without filtering. Classify every warning as corrected, accepted with rationale, blocking or tool limitation. Run PLCSIM scenarios and archive through supported Siemens mechanisms. Hash AP20/ZAP20, logs and screenshots. Never use file renaming or fabricated XML as a native artifact.
"""))
    _write(root, "siemens_native/preflight.ps1", r'''$ErrorActionPreference = 'Stop'
$portal = 'C:\Program Files\Siemens\Automation\Portal V20\Bin\Siemens.Automation.Portal.exe'
$openness = 'C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20\Siemens.Engineering.dll'
$alm = 'C:\Program Files\Siemens\Automation\Automation License Manager\almapp\almapp64x.exe'
$groups = whoami /groups | Out-String
$result = [ordered]@{
  captured_utc = [DateTime]::UtcNow.ToString('o')
  identity = (whoami)
  portal_present = Test-Path -LiteralPath $portal
  portal_version = if (Test-Path -LiteralPath $portal) { (Get-Item $portal).VersionInfo.FileVersion } else { $null }
  openness_present = Test-Path -LiteralPath $openness
  openness_group = $groups -match 'Siemens TIA Openness'
  alm_present = Test-Path -LiteralPath $alm
  startdrive_present = [bool](Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object DisplayName -Match 'Startdrive')
  plcsim_present = [bool](Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object DisplayName -Match 'PLCSIM')
  licence_entitlement = 'MUST BE VERIFIED INTERACTIVELY IN ALM; KEYS MUST NOT BE EXPORTED'
}
$result | ConvertTo-Json -Depth 3
if (-not $result.portal_present -or -not $result.openness_present -or -not $result.openness_group) { exit 2 }
''')


def _write_nvidia(root: Path) -> None:
    inv = {
        "captured_utc": "2026-08-08T20:48:00Z", "scope": "Local inventory; no cloud or target Jetson execution",
        "gpu": {"name": "NVIDIA GeForce RTX 5060 Laptop GPU", "driver": "595.95", "memory_mib": 8151, "compute_capability": "12.0", "evidence": "nvidia-smi query"},
        "cuda_nvcc": {"installed": False}, "docker": {"installed": False}, "nvidia_container_toolkit": {"installed": False},
        "tensorrt": {"installed": False}, "deepstream": {"installed": False}, "tao": {"installed": False},
        "openusd_omniverse": {"installed": False}, "cloud_resources": [], "runtime_smoke": "DRIVER QUERY ONLY",
    }
    _write(root, "nvidia_native/environment_inventory/inventory.json", json.dumps(inv, indent=2, sort_keys=True))
    _write(root, "nvidia_native/data_acquisition_plan.md", doc("Vision data acquisition plan", """## Inspection questions

The initial taxonomy separates: bottle present/positioned, correct bottle type, fill level per channel, gross foam/overflow/leak indication and cap/transfer observation. PLC flow and level measurement remains authoritative for deterministic filling; vision is a non-safety quality device.

## Controlled acquisition

Use a fixed camera/lens/light enclosure, locked focus/exposure/white balance and a calibration target. Capture multiple production lots, sessions, operators, expected ambient variation, bottle positions and difficult negative cases. Record camera/lens/light IDs, recipe, lot/session, timestamps, dimensions and SHA-256. Keep train/validation/test groups separated by lot and session. Do not collect people or confidential labels unless privacy approval and retention rules exist.

## Acceptance before training

The product owner approves taxonomy/tolerances; a data steward approves provenance/licence/privacy; two reviewers adjudicate safety-relevant false-pass candidates. An empty manifest is valid pipeline state but is not dataset evidence.
"""))
    _write(root, "nvidia_native/labeling_guide.md", doc("Vision labeling guide", """Annotators shall label each bottle channel independently: `PRESENT_OK`, `MISSING`, `MISPOSITIONED`, `WRONG_TYPE`; fill `UNDER`, `WITHIN_TOLERANCE`, `OVER`, `OBSCURED`; leakage `NONE`, `PRESENT`, `UNCERTAIN`; cap/transfer `NOT_OBSERVED`, `OK`, `FAIL`, `UNCERTAIN`. `UNCERTAIN`, occluded or contradictory labels can never be mapped to automatic PASS. Record annotator and review state outside image filenames. Double review and adjudicate all test/challenge data and every candidate false pass. Lot/session groups may not cross dataset splits.
"""))
    _write_csv_header(root, "nvidia_native/dataset_manifest.csv", ["image_id","uri","sha256","provenance","split","production_lot","acquisition_session","recipe_id","bottle_sku","annotation_uri","annotation_sha256","review_status","synthetic_or_real","camera_id","lens_id","lighting_id","width_px","height_px"])
    _write(root, "nvidia_native/data_card.md", doc("Dataset card", """**State: EMPTY / NO REPRESENTATIVE DATA.** The controlled manifest contains only its schema header. Provenance, licence, privacy, class balance, acquisition variation, annotation agreement, duplicate/leakage analysis and production representativeness therefore remain unassessed. Synthetic smoke inputs are excluded from model-performance evidence.
"""))
    _write(root, "nvidia_native/training_config.yaml", '''schema: FC01.training.v1
status: BLOCKED_NO_APPROVED_DATASET
seed: 41601
task: multi_attribute_quality_inspection
framework: NVIDIA_TAO_7_PLANNING_BASELINE
architecture: UNSELECTED
dataset_manifest: nvidia_native/dataset_manifest.csv
split_policy: grouped_by_production_lot_and_acquisition_session
epochs: null
batch_size: null
precision: FP16_CANDIDATE_NOT_EXECUTED
output_dir: MUST_BE_OUTSIDE_GIT
''')
    _write(root, "nvidia_native/evaluation_config.yaml", '''schema: FC01.evaluation.v1
status: BLOCKED_NO_MODEL_OR_TEST_SET
primary_risk: false_pass
required_outputs:
  - per_class_precision_recall_f1
  - confusion_matrices
  - false_accept_and_false_reject_analysis
  - robustness_by_lighting_position_fill_and_lot
  - threshold_selection_with_untouched_test_set
  - end_to_end_latency_on_target
automatic_pass_policy: prohibited_until_formally_approved
''')
    _write(root, "nvidia_native/deepstream_config.txt", '''# TEMPLATE ONLY - DO NOT EXECUTE WITHOUT APPROVED DIGEST/MODEL
[application]
enable-perf-measurement=1
perf-measurement-interval-sec=5

[primary-gie]
enable=0
# model-engine-file must be generated on the intended compatible architecture.

[sink0]
enable=0
''')
    _write(root, "nvidia_native/container/Dockerfile", '''# Build requires an explicitly approved immutable DeepStream base digest.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
ARG APP_UID=10001
RUN test -n "${BASE_IMAGE}" && useradd --uid ${APP_UID} --create-home --shell /usr/sbin/nologin fc01edge
WORKDIR /opt/fc01
COPY 07_nvidia_vision/edge_service/requirements-opcua.txt /tmp/requirements-opcua.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements-opcua.txt
COPY 07_nvidia_vision/edge_service /opt/fc01/edge_service
USER fc01edge
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/opt/fc01/edge_service/main.py"]
CMD ["--config", "/run/fc01/opcua_runtime_config.json"]
''')
    _write(root, "nvidia_native/container/Dockerfile.dockerignore", '''.git
**/__pycache__
**/*.pyc
release
14_qa
09_panel_cad
03_electrical
''')
    _write(root, "nvidia_native/container/README.md", doc("Container build and rollback boundary", """No container was built in Revision G. From the repository root, after selecting an official compatible DeepStream image by immutable digest and approving network/package access, run:

`docker build --file nvidia_native/container/Dockerfile --build-arg BASE_IMAGE=<approved-registry/image@sha256:digest> --tag fc01-edge:<approved-version> .`

The adjacent `Dockerfile.dockerignore` limits the repository-root build context. Record the base digest, requirements hash, build command, image digest, SBOM and vulnerability report. Do not tag `latest`. Deploy by immutable image digest; rollback by restoring the last approved configuration/model/container tuple. Mount the runtime OPC UA configuration and certificates read-only, and provide writable log/audit paths explicitly. The service has no model backend and must remain not-ready until a separately approved production adapter is injected.
"""))
    _write(root, "nvidia_native/container/sbom_status.json", json.dumps({"status":"NOT_GENERATED","reason":"No approved container runtime/base digest was available","required_tool":"syft or equivalent on the approved Linux build host","production_claim":False}, indent=2))
    _write(root, "nvidia_native/dependency_vulnerability_status.json", json.dumps({"status":"NOT_EXECUTED","reason":"No approved container/base digest and no Docker/SBOM/vulnerability scanner were available","pinned_python_requirements":"07_nvidia_vision/edge_service/requirements-opcua.txt","required_evidence":["container digest","SBOM","scanner name/version/database timestamp","raw findings","severity disposition"],"production_claim":False}, indent=2))
    _write(root, "nvidia_native/model_card.md", doc("Revision G model card status", """**STATUS: NOT TRAINED / NO DEPLOYABLE MODEL.** No representative approved dataset, training run, checkpoint, ONNX export, TensorRT engine, threshold, metric or model approval exists. The controlled taxonomy, data card, manifests and training/evaluation configurations are execution prerequisites only. A production model card must identify data/model hashes, training environment, untouched-test results, false-pass/false-reject analysis, approved threshold, target-runtime measurements, limitations, owners and change approval.
"""))
    _write(root, "nvidia_native/confusion_matrix_status.md", doc("Confusion-matrix evidence status", """No confusion matrix exists because no representative labeled dataset, trained model or untouched test run exists. Synthetic plumbing output is not converted into a matrix or accuracy claim. The production gate requires raw predictions and labels, per-class matrices, class definitions, split-manifest hash and independent review.
"""))
    _write(root, "nvidia_native/latency_results_status.md", doc("Latency and throughput evidence status", """No production latency or throughput measurement exists. Local synthetic timing and the RTX driver query do not represent camera acquisition, preprocessing, model inference, publication, PLC scan timing or target Jetson/cloud execution. Record monotonic end-to-end distributions, warm-up policy, batch size, input dimensions, target hardware, power mode, container/model/config hashes and process-timeout comparison only after native execution.
"""))
    _write(root, "nvidia_native/raw_logs/README.md", doc("Native NVIDIA raw-log status", """No training, evaluation, ONNX, TensorRT, DeepStream, container-build or target-runtime log was produced. Future raw logs must be stored unchanged, hashed and referenced from the model/container release record; sanitized summaries must never replace raw evidence.
"""))
    _write(root, "nvidia_native/interface_harness_summary.md", doc("PLC-AI interface harness summary", """Revision G re-executed the inherited software suites: 86 edge/OPC UA tests and 17 PLC-AI harness tests pass, including certificate-backed local asyncua transport and fail-closed transaction behavior. The deterministic synthetic smoke separately proves the mock backend cannot authorize `VISION_READY`. These results prove source/local laboratory contract behavior only. They do not prove a production S7 endpoint, camera, target runtime, model, physical timing or safe commissioning.
"""))
    _write(root, "nvidia_native/native_execution_report.md", doc("NVIDIA native execution report", """The local RTX 5060 driver query executed successfully. CUDA toolkit (`nvcc`), Docker, NVIDIA Container Toolkit, TAO, TensorRT, DeepStream, OpenUSD and Omniverse were not found. No cloud GPU resource exists. The deterministic synthetic smoke exercises the existing acquisition/preprocess/mock boundary and proves the mock backend is refused by `VisionService`; it does not decode representative images, train a model, create ONNX/TensorRT artifacts, measure latency or validate production OPC UA.

Current official planning baseline is DeepStream 9.1 on Ubuntu 24.04; dGPU prerequisites include driver 595.58.03, CUDA 13.2 and TensorRT 10.16.0.72. TAO-trained engines must be regenerated for their exact TensorRT/CUDA/hardware environment. Sources: https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Installation.html and https://docs.nvidia.com/tao/tao-toolkit/latest/text/ds_tao/deepstream_tao_integration.html.
"""))
    _write(root, "nvidia_native/synthetic_smoke.py", r'''from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "07_nvidia_vision" / "edge_service"))
from protocol import InspectionRequest, ResultDisposition
from service import VisionService
from vision_runtime import BytePreprocessor, MockModelAdapter, ModelDecision, RecordedDirectorySource, VisionPipelineBackend

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="fc01-revg-synthetic-") as directory:
        root = Path(directory)
        image = root / "synthetic.png"
        image.write_bytes(b"\\x89PNG\\r\\n\\x1a\\nFC01-SYNTHETIC-NOT-AN-IMAGE-METRIC")
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        manifest = root / "manifest.csv"
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["inspection_id","path","sha256","provenance","width_px","height_px","captured_utc_ms"], lineterminator="\n")
            writer.writeheader(); writer.writerow({"inspection_id":1,"path":image.name,"sha256":digest,"provenance":"SYNTHETIC","width_px":640,"height_px":480,"captured_utc_ms":0})
        backend = VisionPipelineBackend(RecordedDirectorySource(root, manifest), BytePreprocessor(), MockModelAdapter(ModelDecision(True, True, 2, 2, False, 0.99, 0)), dataset_id="SYNTHETIC-NO-DATASET", calibration_id="SYNTHETIC-NO-CALIBRATION", confidence_threshold=0.9)
        result = backend.infer(InspectionRequest(inspection_id=1, recipe_id=1, expected_bottles=2, target_fill_level=0.5, plc_heartbeat=1, session_epoch=1))
        service = VisionService(backend=backend)
        service.reset(disabled=True, session_epoch=1, observed_plc_heartbeat=1)
        checks = {
            "synthetic_pipeline_executed": result.disposition == int(ResultDisposition.PASS),
            "backend_never_production_authorized": backend.production_authorized is False,
            "service_refuses_synthetic_ready": service.state.ready is False,
            "diagnostic_is_explicit": service.state.diagnostic_code == "DEVELOPMENT_BACKEND_PROHIBITED",
        }
        print(json.dumps({"status":"PASS" if all(checks.values()) else "FAIL", "checks":checks, "scope":"synthetic plumbing/fail-closed authorization only; no image decoding, model, metric or latency evidence"}, indent=2, sort_keys=True))
        return 0 if all(checks.values()) else 1
if __name__ == "__main__": raise SystemExit(main())
''')


def _write_commissioning(root: Path) -> None:
    _write(root, "commissioning/README.md", doc("Commissioning package boundary", """These procedures and records are controlled **blank templates**. They do not prove construction, FAT, SAT, calibration, energization, commissioning or approval. Actual values require calibrated instruments, named testers/witnesses and project authorization. Do not prefill pass/fail, actual values, serial numbers, dates or signatures.
"""))
    _write(root, "commissioning/FAT_procedure.md", doc("Factory acceptance test procedure", """Hold points: approved drawings/BOM; mechanical inspection; point-to-point wiring; PE continuity; insulation resistance under an approved isolation method; polarity/short-circuit inspection; torque/protection verification; controlled power-up; PLC diagnostics; I/O checkout; drives/motors; dosing calibration; HMI/alarms; communications/AI failure behavior; backup/restore; punch closure. Each test records instrument, serial/calibration status, point, expected/actual result, pass/fail, tester, witness, date and comments. Safety circuits and energised tests require competent persons and approved risk controls.
"""))
    _write(root, "commissioning/SAT_procedure.md", doc("Site acceptance test procedure", """Confirm site supply/earthing/fault-current/environment and as-installed routes before energization. Repeat safety-critical electrical inspections, network names/IPs, field I/O, sensor alignment, motor direction, pump calibration, fill repeatability, alarm/communications failures, AI timeout/uncertainty holds, recovery without automatic restart, backup/restore and owner training. SAT acceptance requires signed measured records and punch closure; this template contains none.
"""))
    _write(root, "commissioning/qualified_review_handoff.md", doc("Qualified electrical and machinery-safety review handoff", """Provide the functional design, hazard list, risk assumptions, electrical/QET/CAD sources, protective-device basis, calculations, safety-function list, reset/restart philosophy, commissioning records and open decisions to named competent reviewers. The qualified machinery-safety engineer owns risk assessment, safety design, PL/SIL/category determination if applicable, verification and validation. The qualified electrical engineer owns site/construction calculations and inspection acceptance. Software-agent review is not certification or approval.
"""))
    _write(root, "commissioning/safety_validation_plan_template.md", doc("Safety validation plan template", """Record project scope, standards applicability, hazards, required safety functions, specification references, test methods, independence/competence, calibrated instruments, normal/fault/environmental cases, reset/restart behavior, discrepancy handling, configuration identity, signatures and final disposition. No value, performance level, SIL or category is predetermined here.
"""))
    _write(root, "commissioning/guarding_reset_restart_philosophy.md", doc("Conceptual guarding, reset and restart philosophy", """Guards, emergency-stop devices and hazardous-energy isolation are external conceptual safety provisions and are not implemented by the standard PLC or NVIDIA subsystem. Loss of power, safety status, communications or AI availability removes or withholds process commands. Restoration never starts motion. A reset clears only eligible diagnostics and returns the coordinator to STOPPED; a separate authorized start request plus all validated permissives is required. Guard reset location, visibility, escape prevention, unexpected-start risk, energy isolation and drive stop behavior require project-specific qualified design.
"""))
    _csv(root, "commissioning/hazard_and_safety_input_register.csv", [
        {"hazard_id":"HZ-001","hazard_source":"Conveyor and capping motion","hazardous_event":"Crush, shear or entanglement during access","exposed_persons":"Operator/maintenance","conceptual_direction":"Guarding, access control, emergency stop and hazardous-energy isolation external to standard PLC","required_input":"Machine geometry, access tasks, stopping behavior and risk assessment","owner":"Qualified machinery-safety engineer","status":"OPEN - NO RISK ESTIMATE OR SAFETY DESIGN CLAIM"},
        {"hazard_id":"HZ-002","hazard_source":"Pump, valves and pressurised/liquid process","hazardous_event":"Unexpected discharge, pressure or chemical exposure","exposed_persons":"Operator/maintenance","conceptual_direction":"Isolation, containment, compatible materials and controlled depressurisation","required_input":"Fluid/SDS, pressure, temperature, pump/valve data and cleaning method","owner":"Process owner and qualified safety engineer","status":"OPEN - SITE/PROCESS INPUT ABSENT"},
        {"hazard_id":"HZ-003","hazard_source":"Electrical supply and drives","hazardous_event":"Shock, arc, fire or stored energy","exposed_persons":"Electrical/maintenance personnel","conceptual_direction":"Qualified electrical design, isolation, PE/bonding, protection and verification","required_input":"Supply, earthing, fault current, coordination, environment and equipment ratings","owner":"Qualified electrical engineer","status":"OPEN - SITE INPUT ABSENT"},
        {"hazard_id":"HZ-004","hazard_source":"Automatic restart after restoration","hazardous_event":"Unexpected motion or filling","exposed_persons":"All exposed persons","conceptual_direction":"PLC returns to STOPPED; reset is not start; separate start and permissives required","required_input":"Qualified validation of real safety and control implementation","owner":"Controls engineer plus qualified safety validator","status":"CONCEPT IMPLEMENTED / PHYSICAL VALIDATION OPEN"},
        {"hazard_id":"HZ-005","hazard_source":"NVIDIA misclassification or communications fault","hazardous_event":"Incorrect quality disposition","exposed_persons":"Product/process only; not personnel protection","conceptual_direction":"Non-safety fail-closed HOLD/reject, immutable transaction and explicit disposition","required_input":"Representative data, process acceptance rules, target runtime and commissioning results","owner":"Product owner and vision engineer","status":"SOFTWARE CONTRACT VERIFIED / PRODUCTION VALIDATION OPEN"},
    ])
    _csv(root, "commissioning/safety_function_list.csv", [
        {"function_id":"SF-001","conceptual_function":"Emergency stop","required_behavior":"Stop hazardous motion/energy according to qualified risk assessment; prevent automatic restart","implementation_owner":"Qualified machinery-safety engineer","standard_plc_role":"Monitor status only; no safety claim","status":"UNSPECIFIED / EXTERNAL"},
        {"function_id":"SF-002","conceptual_function":"Guard/access interlocking","required_behavior":"Prevent or stop hazardous operation when protected access is open","implementation_owner":"Qualified machinery-safety engineer","standard_plc_role":"Monitor validated aggregate status only","status":"UNSPECIFIED / EXTERNAL"},
        {"function_id":"SF-003","conceptual_function":"Drive hazardous-torque removal","required_behavior":"Use an approved architecture and validated stop behavior where risk assessment requires it","implementation_owner":"Qualified machinery-safety and drive engineers","standard_plc_role":"No direct safety authority","status":"STO INTERFACE CONCEPT ONLY"},
        {"function_id":"SF-004","conceptual_function":"Prevention of unexpected restart","required_behavior":"Restoration/reset returns to STOPPED; separate deliberate start and valid permissives required","implementation_owner":"Controls plus qualified machinery-safety engineer","standard_plc_role":"Deterministic non-safety restart inhibition implemented in source model","status":"SOURCE TESTED / NATIVE AND PHYSICAL VALIDATION OPEN"},
    ])
    _csv(root, "commissioning/standards_applicability_register.csv", [
        {"reference_family":"ISO 12100","topic":"Machinery risk assessment and risk reduction","edition":"TO BE CONFIRMED","applicability":"REQUIRES QUALIFIED DETERMINATION","owner":"Qualified machinery-safety engineer"},
        {"reference_family":"IEC 60204-1","topic":"Electrical equipment of machines","edition":"TO BE CONFIRMED","applicability":"REQUIRES SITE/JURISDICTION REVIEW","owner":"Qualified electrical engineer"},
        {"reference_family":"ISO 13849-1/-2 or IEC 62061","topic":"Safety-related control-system design and validation","edition":"TO BE CONFIRMED","applicability":"ROUTE NOT SELECTED; NO PL/SIL CLAIM","owner":"Qualified machinery-safety engineer"},
        {"reference_family":"ISO 13850","topic":"Emergency-stop principles","edition":"TO BE CONFIRMED","applicability":"REQUIRES QUALIFIED DETERMINATION","owner":"Qualified machinery-safety engineer"},
        {"reference_family":"IEC 61800-5-2","topic":"Functional safety of drive systems","edition":"TO BE CONFIRMED","applicability":"ONLY IF SELECTED ARCHITECTURE USES DRIVE SAFETY FUNCTIONS","owner":"Qualified drive/safety engineer"},
        {"reference_family":"Local electrical/building/product rules","topic":"Supply, installation, inspection and conformity route","edition":"JURISDICTION UNKNOWN","applicability":"REQUIRES PROJECT LOCATION AND AHJ/OWNER INPUT","owner":"Project owner and qualified electrical engineer"},
    ])
    _csv(root, "commissioning/open_safety_decisions.csv", [
        {"decision_id":"SD-001","decision":"Machine limits, intended use and foreseeable misuse","required_input":"Process/equipment/use specification","owner":"Project owner plus qualified safety engineer","status":"OPEN"},
        {"decision_id":"SD-002","decision":"Guarding type, access points, reset locations and escape prevention","required_input":"Mechanical layout and task-based risk assessment","owner":"Qualified machinery-safety engineer","status":"OPEN"},
        {"decision_id":"SD-003","decision":"Emergency-stop coverage and stop category/behavior","required_input":"Hazard analysis, drive/mechanical stopping data","owner":"Qualified machinery-safety/drive engineers","status":"OPEN - NO CATEGORY CLAIM"},
        {"decision_id":"SD-004","decision":"Required PL/SIL and architecture","required_input":"Completed risk assessment and standards route","owner":"Qualified machinery-safety engineer","status":"OPEN - NO PL/SIL CLAIM"},
        {"decision_id":"SD-005","decision":"Electrical conformity and inspection route","required_input":"Jurisdiction, site supply/environment and owner requirements","owner":"Qualified electrical engineer","status":"OPEN"},
    ])
    _write(root, "commissioning/qualified_review_signature_block.md", doc("Blank qualified-review signature block", """This page is intentionally unsigned and records no approval.

| Role | Name / organisation | Qualification basis | Scope reviewed | Evidence / findings reference | Disposition | Signature | Date |
|---|---|---|---|---|---|---|---|
| Qualified machinery-safety engineer |  |  |  |  |  |  |  |
| Qualified electrical engineer |  |  |  |  |  |  |  |
| Project/design authority |  |  |  |  |  |  |  |

Completion requires identified competent humans, their actual findings, controlled closure evidence and signatures under the owner organisation's process. Software-agent entries are prohibited.
"""))
    columns = ["record_id","test_category","test_point","expected_result","instrument","instrument_serial","calibration_status","actual_result","pass_fail","tester","witness","date","comments"]
    _write_csv_header(root, "commissioning/physical_test_records.csv", columns)
    _write_csv_header(root, "commissioning/calibration_records_template.csv", ["record_id","device_tag","measurand","reference_standard","instrument","instrument_serial","calibration_due","setpoint","actual","error","tolerance","pass_fail","technician","witness","date","comments"])
    _write_csv_header(root, "commissioning/io_checkout.csv", ["record_id","plc_address","symbol","device_tag","terminal","stimulus","expected_state","actual_state","pass_fail","tester","witness","date","comments"])
    _write_csv_header(root, "commissioning/punch_list.csv", ["punch_id","source","description","severity","owner","target_date","closure_evidence","status","closed_by","witness","closed_date"])
    _write_csv_header(root, "commissioning/as_built_redline_register.csv", ["redline_id","document","sheet_or_location","change_description","reason","author","checker","date","incorporated_revision","status"])
    _write(root, "commissioning/inspection_forms.md", doc("Inspection forms index", """Use `physical_test_records.csv` for incoming/BOM, mechanical, point-to-point, PE continuity, insulation, polarity, short-circuit, torque, protection, power-up, diagnostics, I/O, sensor, solenoid, motor/VFD, dosing, HMI, alarm, network/AI failure and backup/restore evidence. Use dedicated calibration, I/O, punch and redline registers for traceability. Every actual/result/signature field is intentionally blank at issue.
"""))


def _write_release(root: Path) -> None:
    toolchain_path = root / "release/reproduction_toolchain_lock.json"
    toolchain = json.loads(toolchain_path.read_text(encoding="utf-8"))
    toolchain["release"] = "G"
    toolchain["node"]["packages"]["@oai/artifact-tool"] = "2.8.39"
    toolchain["policy"] = "Revision G requalifies the available artifact-tool 2.8.39 through complete two-build hash, formula, all-sheet render and fresh-clone verification. Any later tool change requires the same controlled requalification."
    _write(root, "release/reproduction_toolchain_lock.json", json.dumps(toolchain, indent=2))

    _write(root, "release/REVISION_G_KNOWN_LIMITATIONS.md", doc("Revision G known limitations", """Revision G is cloud-ready and native-execution-ready but not provisioned, Siemens-compiled, production-model validated, construction ready, physically commissioned or qualified. The original Revision-F artifact-tool 2.8.31 runtime is unavailable; Revision G must complete full requalification on the available 2.8.39 runtime before release freeze. QET native evidence is inherited and the known folio-25 clipping/automatic-cross-reference limitation remains. The Revision-F vision electrical delta is still provisional and not incorporated into every QET/CAD/construction authority. Site electrical data, licences, software, data, target hardware and qualified people remain external.
"""))
    published = (root / "release/revision_g_published_evidence.json").is_file()
    mark = "x" if published else " "
    _write(root, "release/REVISION_G_FINAL_CHECKLIST.md", doc("Revision G final release checklist", f"""- [{mark}] Native-tool inventory evidence contains no secrets.
- [{mark}] Static cloud IaC/security verification passes; native Terraform plan remains truthfully blocked.
- [{mark}] Siemens native status does not imply compile/project evidence.
- [{mark}] Synthetic NVIDIA evidence cannot authorize production READY.
- [{mark}] Commissioning records contain no invented values or signatures.
- [{mark}] All inherited and Revision-G tests pass.
- [{mark}] Workbook formula scan and every-sheet visual review pass.
- [{mark}] PDF text/page and every-page visual review pass.
- [{mark}] Two deterministic builds match.
- [{mark}] Manifest reports zero missing, modified, unlisted or unexpected files.
- [{mark}] A published Revision-G candidate reproduces from a fresh GitHub clone.
- [ ] The attestation commit containing this checklist must be reverified after publication; record that external result without rewriting the commit being verified.
"""))
    _write(root, "release/RELEASE_NOTES.md", doc("Revision G release notes", f"""Revision G adds a secure, disabled-by-default Google Cloud foundation; exact installed Siemens/NVIDIA inventories and closure handoffs; official-current DeepStream 9.1 planning; a data-gated container/training/evaluation package with deterministic synthetic fail-closed smoke; and controlled blank commissioning/qualified-review records. It does not create cloud resources, a native TIA project, a model, model metrics, physical evidence or professional approval.

{AI_BOUNDARY}
"""))
    _write(root, "README.md", doc("FC01 Siemens/NVIDIA compact filling cell - Revision G", f"""Revision G is an evidence-driven execution release candidate. It preserves the verified Revision-F PLC/AI, QET and FreeCAD baseline while adding a disabled-by-default secure cloud foundation, exact Siemens native-access handoff, current NVIDIA execution pipeline, and commissioning-ready blank records.

Supported description: **cloud-ready and native-execution-ready with software-only NVIDIA pipeline validation**. Native TIA/WinCC/Startdrive/PLCSIM compile, representative data/model/target runtime, site electrical calculations, physical FAT/SAT/commissioning and qualified safety/electrical review remain open exactly as recorded in `00_project_control/revision_g_gate_status.md`.

No cloud resources were created. The PLC remains authoritative; NVIDIA is non-safety and any missing, stale, malformed, contradictory, uncertain or low-confidence result holds product and never commands hazardous outputs.

{AI_BOUNDARY}
"""))


if __name__ == "__main__":
    apply_revision_g(Path(__file__).resolve().parents[1])
