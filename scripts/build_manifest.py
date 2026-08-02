from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_NAMES = {"manifest.json", "manifest.csv", ".DS_Store"}
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".cache", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp"}


def controlled(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return (path.is_file() and path.name not in EXCLUDED_NAMES and
            not any(part in EXCLUDED_DIRS for part in rel.parts) and
            path.suffix.lower() not in EXCLUDED_SUFFIXES and
            not path.name.endswith(".inspect.ndjson"))


def classify(rel: str) -> tuple[str, str, str, str]:
    top = rel.split("/", 1)[0]
    category = {
        "00_project_control":"Project control","01_requirements":"Requirements","02_system_architecture":"Architecture",
        "03_electrical":"Electrical baseline","04_controls_siemens":"Siemens sources","05_hmi":"HMI","06_drives":"Drives",
        "07_nvidia_vision":"Vision","08_digital_twin":"Digital twin","09_panel_cad":"Panel baseline","10_schedules":"Schedules",
        "11_simulation":"Simulation","12_testing":"Testing","13_documentation":"Documentation","14_qa":"QA","release":"Release","scripts":"Reproduction"
    }.get(top, "Repository control")
    if top in {"03_electrical","09_panel_cad"}: return category,"Historical controlled baseline","OPEN","Revision-C native replacement blocked"
    if top in {"04_controls_siemens","05_hmi","06_drives"}: return category,"Design source/specification","OPEN","Native compile/configuration not executed"
    if top in {"07_nvidia_vision","08_digital_twin"}: return category,"Architecture/source","OPEN","Real dataset/target runtime unavailable"
    if top == "11_simulation": return category,"Independent design evidence","PASS","Not Siemens/physical evidence"
    return category,"Controlled artifact","PASS",""


rows = []
for path in sorted((p for p in ROOT.rglob("*") if controlled(p)), key=lambda p: p.relative_to(ROOT).as_posix()):
    rel = path.relative_to(ROOT).as_posix()
    category, role, gate, blocker = classify(rel)
    rows.append({"path":rel,"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"category":category,"role":role,"revision":"C","gate_status":gate,"blocker":blocker})

payload = {"project":"FC01","revision":"C","status":"PARTIALLY COMPLETE","generated":"2026-08-02","file_count":len(rows),"files":rows}
(ROOT / "release/manifest.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
with (ROOT / "release/manifest.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
print(f"manifest_files={len(rows)}")
