from __future__ import annotations
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
