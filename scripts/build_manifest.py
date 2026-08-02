from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path
from manifest_policy import FIELDS, classify, included, reparse_points

ROOT = Path(__file__).resolve().parents[1]


def read_stable(path: Path) -> bytes:
    for attempt in range(20):
        try:
            return path.read_bytes()
        except (OSError, PermissionError):
            if attempt == 19:
                raise
            time.sleep(0.25)


points = reparse_points(ROOT)
if points:
    raise SystemExit(f"reparse/symlink paths are forbidden during manifest build: {points}")


rows = []
for path in sorted((p for p in ROOT.rglob("*") if included(ROOT, p)), key=lambda p: p.relative_to(ROOT).as_posix()):
    rel = path.relative_to(ROOT).as_posix()
    category, role, gate, blocker = classify(rel)
    content = read_stable(path)
    rows.append({"path":rel,"bytes":len(content),"sha256":hashlib.sha256(content).hexdigest(),"category":category,"role":role,"revision":"D","gate_status":gate,"blocker":blocker})

payload = {"project":"FC01","revision":"D","status":"PROFESSIONAL CONTROLLED ENGINEERING-DEVELOPMENT PACKAGE","generated":"2026-08-02","file_count":len(rows),"files":rows}
(ROOT / "release/manifest.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
with (ROOT / "release/manifest.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader(); writer.writerows(rows)
print(f"manifest_files={len(rows)}")
