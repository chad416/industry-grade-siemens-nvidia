from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_NAMES = {"manifest.json", "manifest.csv", ".DS_Store"}
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".cache", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp"}


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return (path.is_file() and path.name not in EXCLUDED_NAMES and
            not any(part in EXCLUDED_DIRS for part in rel.parts) and
            path.suffix.lower() not in EXCLUDED_SUFFIXES and
            not path.name.endswith(".inspect.ndjson"))


errors: list[str] = []
payload = json.loads((ROOT / "release/manifest.json").read_text(encoding="utf-8"))
with (ROOT / "release/manifest.csv").open(encoding="utf-8", newline="") as handle:
    csv_rows = list(csv.DictReader(handle))
rows = payload.get("files", [])
paths = [row["path"] for row in rows]
actual = {p.relative_to(ROOT).as_posix(): p for p in ROOT.rglob("*") if included(p)}
listed = set(paths)

if payload.get("revision") != "C": errors.append("manifest revision is not C")
if payload.get("file_count") != len(rows): errors.append(f"metadata count {payload.get('file_count')} != JSON rows {len(rows)}")
if len(paths) != len(listed): errors.append("duplicate manifest paths")
if len(csv_rows) != len(rows): errors.append(f"CSV rows {len(csv_rows)} != JSON rows {len(rows)}")
if {row["path"] for row in csv_rows} != listed: errors.append("CSV/JSON path sets differ")
csv_by_path = {row["path"]: row for row in csv_rows}
manifest_fields = ["path","bytes","sha256","category","role","revision","gate_status","blocker"]
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
    if int(row["bytes"]) != path.stat().st_size: errors.append(f"size mismatch: {rel}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if row["sha256"] != digest: errors.append(f"hash mismatch: {rel}")
    if row.get("revision") != "C": errors.append(f"row revision mismatch: {rel}")

print(f"manifest_count={len(rows)} actual_count={len(actual)} missing={len(listed-set(actual))} unlisted={len(set(actual)-listed)} mismatches={len(errors)}")
for error in errors: print(f"ERROR: {error}")
sys.exit(1 if errors else 0)
