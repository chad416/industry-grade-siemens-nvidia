from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTICE = "FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION."
SAFETY = (
    "CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, "
    "VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, "
    "SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
)


passed = 0
failures: list[str] = []


def check(condition: bool, label: str) -> None:
    global passed
    if condition:
        passed += 1
    else:
        failures.append(label)


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


required = [
    "00_project_control/revision_g_charter.md",
    "00_project_control/revision_g_gap_matrix.csv",
    "00_project_control/revision_g_decision_log.md",
    "00_project_control/revision_g_dependency_graph.mmd",
    "00_project_control/revision_g_gate_status.md",
    "00_project_control/revision_g_external_handoffs.md",
    "cloud/architecture.md", "cloud/threat_model.md", "cloud/cost_assumptions.md",
    "cloud/terraform/main.tf", "cloud/terraform/iam.tf", "cloud/terraform/compute.tf",
    "cloud/scripts/validate_cloud_iac.py", "cloud/scripts/plan_cloud.ps1",
    "siemens_native/environment_inventory/inventory.json", "siemens_native/native_execution_report.md",
    "nvidia_native/environment_inventory/inventory.json", "nvidia_native/dataset_manifest.csv",
    "nvidia_native/container/Dockerfile", "nvidia_native/container/Dockerfile.dockerignore",
    "nvidia_native/container/README.md", "nvidia_native/synthetic_smoke.py",
    "nvidia_native/model_card.md", "nvidia_native/confusion_matrix_status.md",
    "nvidia_native/latency_results_status.md", "nvidia_native/dependency_vulnerability_status.json",
    "commissioning/FAT_procedure.md", "commissioning/SAT_procedure.md",
    "commissioning/physical_test_records.csv", "commissioning/io_checkout.csv",
    "commissioning/qualified_review_handoff.md", "commissioning/hazard_and_safety_input_register.csv",
    "commissioning/safety_function_list.csv", "commissioning/standards_applicability_register.csv",
    "commissioning/open_safety_decisions.csv", "commissioning/qualified_review_signature_block.md",
    "release/REVISION_G_KNOWN_LIMITATIONS.md",
    "release/REVISION_G_FINAL_CHECKLIST.md",
    "release/revision_g_published_evidence.json",
    "14_qa/revision_g_post_push_reproduction.md",
]
for rel in required:
    check((ROOT / rel).is_file() and (ROOT / rel).stat().st_size > 0, f"required artifact: {rel}")

policy_text = text("scripts/manifest_policy.py")
check('REVISION = "G"' in policy_text, "manifest policy identifies Revision G")
check('14_qa/pdf_renders/release_f/' in policy_text and not (ROOT / "14_qa/pdf_renders/release_f").exists(), "superseded Revision-F release render directory cannot re-enter")

model = json.loads(text("00_project_control/canonical_model.json"))
check(model["project"]["revision"] == "G", "canonical revision is G")
check(model["project"]["date"] == "2026-08-08", "canonical Revision-G date")
check("CLOUD/NATIVE-EXECUTION READY" in model["project"]["status"], "truthful supported release state")
check("CE/UKCA" in model["project"]["safety_boundary"], "canonical safety boundary includes CE/UKCA")

gap = rows("00_project_control/revision_g_gap_matrix.csv")
expected_columns = ["gate_id","requirement","current_evidence","current_status","missing_input","responsible_agent","planned_action","acceptance_evidence","external_dependency","final_disposition"]
check(list(gap[0]) == expected_columns, "gap matrix exact schema")
check(len(gap) == 14, "gap matrix has 14 material gates")
allowed = {"VERIFIED","IMPLEMENTABLE NOW","REQUIRES USER APPROVAL","REQUIRES LICENCE","REQUIRES REAL DATA","REQUIRES HARDWARE","REQUIRES QUALIFIED PERSON","BLOCKED BY EXTERNAL SYSTEM","NOT APPLICABLE"}
check(all(row["current_status"] in allowed for row in gap), "gap statuses are controlled vocabulary")
check(len({row["gate_id"] for row in gap}) == len(gap), "gap IDs unique")
check(all(row["acceptance_evidence"] and row["responsible_agent"] for row in gap), "every gap has owner and evidence")
check(rows("10_schedules/revision_g_gap_matrix.csv") == gap, "workbook gap matrix matches project control")

gates = rows("00_project_control/acceptance_gates.csv")
check(rows("10_schedules/acceptance_gates.csv") == gates, "acceptance gate authorities agree")
check(len(gates) == 22 and len({r["gate"] for r in gates}) == 22, "22 unique acceptance gates")
check(next(r for r in gates if r["gate"] == "4")["status"] == "BLOCKED", "TIA project gate remains blocked")
check(next(r for r in gates if r["gate"] == "18")["status"] == "BLOCKED", "NVIDIA runtime gate remains blocked")
check(next(r for r in gates if r["gate"] == "20")["status"] == "OPEN", "physical commissioning remains open")
check(next(r for r in gates if r["gate"] == "21")["status"] == "BLOCKED", "qualified safety remains blocked")

published = json.loads(text("release/revision_g_published_evidence.json"))
candidate = published.get("candidate_commit", "")
check(published.get("result") == "PASS", "published-candidate reproduction passed")
check(isinstance(candidate, str) and bool(re.fullmatch(r"[0-9a-f]{40}", candidate)), "published candidate has full Git SHA")
check(published.get("branch") == "codex/revision-g-native-cloud-execution", "published candidate is Revision-G branch")
check(published.get("source") == "fresh GitHub clone outside the development worktree", "published evidence identifies uncontaminated source")
check(published.get("manifest") == {"controlled_files": 504, "discrepancies": 0}, "published candidate manifest result")
check(published.get("release_integrity") == {"passed": 871, "failed": 0}, "published candidate release-integrity result")
check(published.get("determinism") == {"controlled_outputs": 350, "missing": 0, "extra": 0, "mismatched": 0}, "published candidate deterministic-build result")
check(published.get("workbook", {}).get("sheets") == 27 and published.get("pdf", {}).get("pages") == 6, "published candidate workbook/PDF review scope")
check(next(r for r in gates if r["gate"] == "22")["status"] == "PASS", "published-candidate manifest/reproduction gate passes")

cloud_text = "\n".join(text(f"cloud/terraform/{name}") for name in ("versions.tf","variables.tf","main.tf","iam.tf","compute.tf","observability.tf","safety_checks.tf","budget.tf","outputs.tf"))
check(cloud_text.count("default = false") >= 2, "cloud VMs disabled by default")
check("access_config" not in cloud_text, "cloud VMs have no external IP configuration")
check("35.235.240.0/20" in cloud_text, "IAP source range encoded")
check("roles/owner" not in cloud_text and "roles/editor" not in cloud_text, "no broad owner/editor role")
check(len(re.findall(r"enable_secure_boot\s*=\s*true", cloud_text)) == 2, "secure boot for both candidate VMs")
check(bool(re.search(r"automatic_restart\s*=\s*false", cloud_text)), "GPU automatic restart disabled")
check("force_destroy               = false" in cloud_text, "artifact bucket force destroy disabled")
check('public_access_prevention    = "enforced"' in cloud_text, "artifact bucket public access prevented")
check(bool(re.search(r'deny\s*\{\s*protocol\s*=\s*"all"\s*\}', cloud_text)), "egress default deny")
check("google_billing_budget" in cloud_text and "instance_schedule_policy" in cloud_text, "budget and shutdown controls encoded")
check("google_project_iam_audit_config" in cloud_text and cloud_text.count("google_monitoring_alert_policy") == 2, "audit logging and candidate VM alert policies encoded")
check(all(name in cloud_text for name in ("approved_access_before_compute","budget_before_compute","alert_route_before_compute")), "compute enablement is gated by access, budget and alert route")
check("guest_accelerator" not in cloud_text and 'default = "g2-standard-4"' in cloud_text, "G2 machine type supplies its included L4 without duplicate accelerator attachment")
check(cloud_text.count("{") == cloud_text.count("}"), "Terraform source has balanced braces")
check(not re.search(r",\s*[A-Za-z_][A-Za-z0-9_-]*\s*=", cloud_text), "Terraform source has no comma-separated block assignments")

plan_script = text("cloud/scripts/plan_cloud.ps1")
check("..\\terraform" in plan_script and "\t" not in plan_script, "cloud plan script resolves the Terraform source without escaped-tab corruption")
check("terraform-work" in plan_script and "outside the controlled release tree" in plan_script, "cloud plan executes in an isolated external work directory")

cloud = subprocess.run([sys.executable, str(ROOT / "cloud/scripts/validate_cloud_iac.py")], cwd=ROOT, capture_output=True, text=True)
check(cloud.returncode == 0 and '"status": "PASS"' in cloud.stdout, "cloud static validator executes")

siemens = json.loads(text("siemens_native/environment_inventory/inventory.json"))
check(siemens["portal"]["file_version"] == "2000.0.9501.1", "actual TIA executable version captured")
check(siemens["portal"]["sha256"] == "4ab4c76cfa956956187b4e1401dd11eed3473fe60ca121c13698f6918da4354f", "actual TIA executable hash captured")
check(siemens["openness"]["installed"] and not siemens["openness"]["active_identity_authorized"], "Openness installed but active identity blocked")
check(not siemens["startdrive"]["installed"] and not siemens["plcsim"]["installed"], "Startdrive and PLCSIM absence captured")
check(siemens["native_execution"].startswith("NOT RUN"), "no Siemens native execution claimed")

nvidia = json.loads(text("nvidia_native/environment_inventory/inventory.json"))
check(nvidia["gpu"]["name"] == "NVIDIA GeForce RTX 5060 Laptop GPU", "actual GPU name captured")
check(nvidia["gpu"]["driver"] == "595.95" and nvidia["gpu"]["memory_mib"] == 8151, "actual GPU driver/memory captured")
check(all(not nvidia[key]["installed"] for key in ("cuda_nvcc","docker","nvidia_container_toolkit","tensorrt","deepstream","tao")), "absent NVIDIA runtime stack captured")
check(nvidia["cloud_resources"] == [], "no cloud resources claimed")

manifest_path = ROOT / "nvidia_native/dataset_manifest.csv"
with manifest_path.open("r", encoding="utf-8", newline="") as handle:
    dataset_rows = list(csv.reader(handle))
check(len(dataset_rows) == 1 and len(dataset_rows[0]) == 18, "dataset manifest is controlled empty schema")
check("EMPTY / NO REPRESENTATIVE DATA" in text("nvidia_native/data_card.md"), "data card explicitly states data absence")
check("BLOCKED_NO_APPROVED_DATASET" in text("nvidia_native/training_config.yaml"), "training configuration fails closed")
check("BASE_IMAGE" in text("nvidia_native/container/Dockerfile") and "USER fc01edge" in text("nvidia_native/container/Dockerfile"), "container requires selected base and nonroot user")
check(json.loads(text("nvidia_native/container/sbom_status.json"))["status"] == "NOT_GENERATED", "SBOM absence truthful")
check(json.loads(text("nvidia_native/dependency_vulnerability_status.json"))["status"] == "NOT_EXECUTED", "dependency/vulnerability scan absence truthful")
check("NOT TRAINED / NO DEPLOYABLE MODEL" in text("nvidia_native/model_card.md"), "model card cannot imply a trained model")

smoke = subprocess.run([sys.executable, str(ROOT / "nvidia_native/synthetic_smoke.py")], cwd=ROOT, capture_output=True, text=True)
check(smoke.returncode == 0 and '"service_refuses_synthetic_ready": true' in smoke.stdout, "synthetic smoke executes and cannot authorize READY")

blank_records = {
    "commissioning/physical_test_records.csv": 13,
    "commissioning/calibration_records_template.csv": 16,
    "commissioning/io_checkout.csv": 13,
    "commissioning/punch_list.csv": 11,
    "commissioning/as_built_redline_register.csv": 10,
}
for rel, count in blank_records.items():
    with (ROOT / rel).open("r", encoding="utf-8", newline="") as handle:
        data = list(csv.reader(handle))
    check(len(data) == 1 and len(data[0]) == count, f"blank controlled record schema: {rel}")

safety_rows = rows("commissioning/safety_function_list.csv")
check(len(safety_rows) == 4 and not any(re.search(r"\bPL\s*[a-e]\b|\bSIL\s*[1-4]\b", " ".join(row.values()), re.I) for row in safety_rows), "conceptual safety-function list has no validated PL/SIL claim")
check(len(rows("commissioning/hazard_and_safety_input_register.csv")) == 5, "hazard/input register has five controlled conceptual hazards")
check(len(rows("commissioning/open_safety_decisions.csv")) == 5, "open safety decisions remain explicit")

for rel in [
    "00_project_control/revision_g_charter.md", "00_project_control/revision_g_gate_status.md",
    "cloud/architecture.md", "siemens_native/native_execution_report.md",
    "nvidia_native/native_execution_report.md", "commissioning/README.md",
    "commissioning/qualified_review_handoff.md", "release/REVISION_G_KNOWN_LIMITATIONS.md",
    "README.md", "release/RELEASE_NOTES.md",
]:
    value = text(rel)
    check(NOTICE in value and SAFETY in value, f"mandatory boundaries in {rel}")

prohibited_extensions = ["*.ap20", "*.zap20", "*.onnx", "*.engine", "*.plan"]
prohibited = [p.relative_to(ROOT).as_posix() for pattern in prohibited_extensions for p in ROOT.rglob(pattern)]
check(not prohibited, f"no fabricated native/model artifacts: {prohibited}")

secret_pattern = re.compile(r"(?i)(api[_-]?key|client[_-]?secret|private[_-]?key|password)\s*[=:]\s*[\"'][^\"']{8,}")
secret_hits = []
for base in (ROOT / "cloud", ROOT / "siemens_native", ROOT / "nvidia_native"):
    for path in base.rglob("*"):
        if path.is_file() and path.suffix.lower() not in {".png", ".pdf", ".xlsx"}:
            if secret_pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                secret_hits.append(path.relative_to(ROOT).as_posix())
check(not secret_hits, f"no embedded secrets: {secret_hits}")

toolchain = json.loads(text("release/reproduction_toolchain_lock.json"))
check(toolchain["release"] == "G", "toolchain lock is Revision G")
check(toolchain["node"]["packages"]["@oai/artifact-tool"] == "2.8.39", "artifact-tool 2.8.39 controlled requalification lock")

print(f"REVISION_G_PASS={passed} REVISION_G_FAIL={len(failures)}")
for failure in failures:
    print(f"ERROR: {failure}")
raise SystemExit(1 if failures else 0)
