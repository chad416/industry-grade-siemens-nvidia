"""Verify the frozen exact-hash native QElectroTech reopen/export evidence."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "03_electrical/revision_f_native_qet/native_reopen_export_evidence.json"
errors: list[str] = []
checks: list[str] = []


def check(condition: bool, description: str) -> None:
    (checks if condition else errors).append(description)


evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
source = ROOT / evidence["controlled_source"]["path"]
export = ROOT / evidence["native_pdf_export"]["path"]
source_sha = hashlib.sha256(source.read_bytes()).hexdigest().upper()
export_sha = hashlib.sha256(export.read_bytes()).hexdigest().upper()

check(evidence["status"] == "PARTIAL", "overall QET evidence is truthfully PARTIAL")
check(evidence["native_reopen"]["status"] == "PASS", "exact-hash native reopen is PASS")
check(evidence["native_reopen"]["observed_folio_count"] == 26, "native project tree exposed 26 folios")
check(len(evidence["native_reopen"]["folio_tree"]) == 26, "evidence records all 26 folio titles")
check(source_sha == evidence["controlled_source"]["sha256_before_and_after"], "controlled QET source hash matches native evidence")
check(source.stat().st_size == evidence["controlled_source"]["bytes"], "controlled QET source byte count matches native evidence")
check(evidence["controlled_source"]["modified_by_workstream"] is False, "native execution did not claim to modify the controlled source")
check(evidence["native_pdf_export"]["status"] == "PASS", "native QET PDF export is PASS")
check(export_sha == evidence["native_pdf_export"]["sha256"], "native QET PDF hash matches evidence")
check(export.stat().st_size == evidence["native_pdf_export"]["bytes"], "native QET PDF byte count matches evidence")

pdf = PdfReader(export)
check(len(pdf.pages) == evidence["native_pdf_export"]["pages"] == 26, "pypdf independently confirms 26 native export pages")
check(not pdf.is_encrypted and evidence["native_pdf_export"]["encrypted"] is False, "native QET PDF is unencrypted")
metadata = pdf.metadata or {}
check("QElectroTech 0.100.0" in str(metadata.get("/Creator", "")), "PDF metadata identifies QElectroTech 0.100.0")
check("Qt 5.15.18" in str(metadata.get("/Producer", "")), "PDF metadata identifies Qt 5.15.18")

renders = sorted((ROOT / "14_qa/qet_revision_f_rendered").glob("page-*.png"))
check(len(renders) == 26, "controlled native QET visual-review set contains 26 page renders")
check(evidence["visual_review"]["rendered_pages_reviewed"] == 26, "visual evidence records review of all 26 pages")
check(evidence["visual_review"]["status"] == "PARTIAL", "visual status remains PARTIAL for the recorded clipping finding")
check(evidence["cross_references"]["status"] == "BLOCKED", "automatic cross-reference proof remains BLOCKED")
check(evidence["gate_disposition"]["overall_native_qet_gate"] == "PARTIAL", "overall native QET gate remains PARTIAL")

print(f"QET_REVISION_F_PASS={len(checks)} QET_REVISION_F_FAIL={len(errors)}")
for item in errors:
    print(f"ERROR: {item}")
sys.exit(1 if errors else 0)
