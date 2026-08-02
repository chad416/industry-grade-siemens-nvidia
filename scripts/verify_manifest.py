from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from manifest_policy import EXCLUDED_DIRS, EXCLUDED_NAMES, FIELDS, classify, included, reparse_points

ROOT = Path(__file__).resolve().parents[1]


def read_stable(path: Path) -> bytes:
    for attempt in range(20):
        try:
            return path.read_bytes()
        except (OSError, PermissionError):
            if attempt == 19:
                raise
            time.sleep(0.25)


errors: list[str] = []
for rel in reparse_points(ROOT): errors.append(f"reparse/symlink path forbidden: {rel}")
payload = json.loads(read_stable(ROOT / "release/manifest.json").decode("utf-8"))
csv_rows = list(csv.DictReader(io.StringIO(read_stable(ROOT / "release/manifest.csv").decode("utf-8"), newline="")))
rows = payload.get("files", [])
paths = [row["path"] for row in rows]
actual = {p.relative_to(ROOT).as_posix(): p for p in ROOT.rglob("*") if included(ROOT, p)}
listed = set(paths)

if payload.get("revision") != "D": errors.append("manifest revision is not D")
if payload.get("file_count") != len(rows): errors.append(f"metadata count {payload.get('file_count')} != JSON rows {len(rows)}")
if len(paths) != len(listed): errors.append("duplicate manifest paths")
if paths != sorted(paths): errors.append("JSON manifest paths are not sorted")
for rel in paths:
    pure = Path(rel)
    if pure.is_absolute() or ".." in pure.parts or "\\" in rel: errors.append(f"unsafe/non-POSIX manifest path: {rel}")
if len(csv_rows) != len(rows): errors.append(f"CSV rows {len(csv_rows)} != JSON rows {len(rows)}")
if [row["path"] for row in csv_rows] != paths: errors.append("CSV/JSON ordered path lists differ")
csv_by_path = {row["path"]: row for row in csv_rows}
manifest_fields = FIELDS
if list(csv_rows[0]) != FIELDS if csv_rows else True: errors.append("CSV schema/order mismatch")
for row in rows:
    csv_row = csv_by_path.get(row["path"])
    if csv_row is None:
        continue
    for field in manifest_fields:
        if str(csv_row.get(field, "")) != str(row.get(field, "")):
            errors.append(f"CSV/JSON {field} mismatch: {row['path']}")
for path in sorted(listed - set(actual)): errors.append(f"missing file: {path}")
for path in sorted(set(actual) - listed): errors.append(f"unlisted controlled file: {path}")
for row in rows:
    rel = row["path"]
    if any(part in EXCLUDED_DIRS for part in Path(rel).parts) or Path(rel).name in EXCLUDED_NAMES: errors.append(f"excluded cache/self path listed: {rel}")
    path = actual.get(rel)
    if path is None: continue
    content = read_stable(path)
    if int(row["bytes"]) != len(content): errors.append(f"size mismatch: {rel}")
    digest = hashlib.sha256(content).hexdigest()
    if row["sha256"] != digest: errors.append(f"hash mismatch: {rel}")
    if row.get("revision") != "D": errors.append(f"row revision mismatch: {rel}")
    expected_category, expected_role, expected_gate, expected_blocker = classify(rel)
    for field, expected in (
        ("category", expected_category), ("role", expected_role),
        ("gate_status", expected_gate), ("blocker", expected_blocker),
    ):
        if row.get(field) != expected:
            errors.append(f"classification {field} mismatch: {rel}")

print(f"manifest_count={len(rows)} actual_count={len(actual)} missing={len(listed-set(actual))} unlisted={len(set(actual)-listed)} mismatches={len(errors)}")
for error in errors: print(f"ERROR: {error}")
sys.exit(1 if errors else 0)
