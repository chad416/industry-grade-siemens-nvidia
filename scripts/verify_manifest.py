"""Verify a release manifest against authoritative Git or worktree bytes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from git_release_source import clean_state_errors, read_bytes, tracked_paths, untracked_paths
from manifest_policy import FIELDS, REVISION, classify, forbidden, included_rel, reparse_points

ROOT = Path(__file__).resolve().parents[1]
ARGS = argparse.ArgumentParser()
ARGS.add_argument("--source", choices=("head", "index", "worktree"), default="head")
ARGS.add_argument("--require-clean", action="store_true")
OPTIONS = ARGS.parse_args()

errors: list[str] = []
for rel in reparse_points(ROOT):
    errors.append(f"reparse/symlink path forbidden: {rel}")

try:
    payload = json.loads(read_bytes(OPTIONS.source, "release/manifest.json").decode("utf-8"))
    csv_rows = list(
        csv.DictReader(
            io.StringIO(read_bytes(OPTIONS.source, "release/manifest.csv").decode("utf-8"), newline="")
        )
    )
    source_paths = tracked_paths(OPTIONS.source)
except (OSError, RuntimeError, UnicodeError, json.JSONDecodeError) as exc:
    raise SystemExit(f"Unable to read manifest from {OPTIONS.source}: {exc}") from exc

actual = {rel for rel in source_paths if included_rel(rel)}
rows = payload.get("files", [])
paths = [row.get("path", "") for row in rows]
listed = set(paths)

if payload.get("revision") != REVISION:
    errors.append(f"manifest revision is not {REVISION}")
if payload.get("file_count") != len(rows):
    errors.append(f"metadata count {payload.get('file_count')} != JSON rows {len(rows)}")
if len(paths) != len(listed):
    errors.append("duplicate manifest paths")
if paths != sorted(paths):
    errors.append("JSON manifest paths are not sorted")
for rel in paths:
    pure = Path(rel)
    if pure.is_absolute() or ".." in pure.parts or "\\" in rel:
        errors.append(f"unsafe/non-POSIX manifest path: {rel}")
    if forbidden(rel):
        errors.append(f"superseded/forbidden path listed: {rel}")
for rel in source_paths:
    if forbidden(rel):
        errors.append(f"superseded/forbidden path present in {OPTIONS.source}: {rel}")

if len(csv_rows) != len(rows):
    errors.append(f"CSV rows {len(csv_rows)} != JSON rows {len(rows)}")
if [row.get("path", "") for row in csv_rows] != paths:
    errors.append("CSV/JSON ordered path lists differ")
if (list(csv_rows[0]) if csv_rows else []) != FIELDS:
    errors.append("CSV schema/order mismatch")
csv_by_path = {row.get("path", ""): row for row in csv_rows}
for row in rows:
    csv_row = csv_by_path.get(row.get("path", ""))
    if csv_row is None:
        continue
    for field in FIELDS:
        if str(csv_row.get(field, "")) != str(row.get(field, "")):
            errors.append(f"CSV/JSON {field} mismatch: {row.get('path', '')}")

missing = sorted(listed - actual)
unlisted = sorted(actual - listed)
for rel in missing:
    errors.append(f"missing file: {rel}")
for rel in unlisted:
    errors.append(f"unlisted controlled file: {rel}")

for row in rows:
    rel = row.get("path", "")
    if rel not in actual:
        continue
    content = read_bytes(OPTIONS.source, rel)
    if int(row.get("bytes", -1)) != len(content):
        errors.append(f"size mismatch: {rel}")
    if row.get("sha256") != hashlib.sha256(content).hexdigest():
        errors.append(f"hash mismatch: {rel}")
    if row.get("revision") != REVISION:
        errors.append(f"row revision mismatch: {rel}")
    expected = classify(rel)
    for field, value in zip(("category", "role", "gate_status", "blocker"), expected):
        if row.get(field) != value:
            errors.append(f"classification {field} mismatch: {rel}")

unexpected_worktree = untracked_paths()
for rel in unexpected_worktree:
    errors.append(f"untracked/unexpected worktree path: {rel}")
if OPTIONS.require_clean:
    errors.extend(clean_state_errors())

print(
    f"manifest_source={OPTIONS.source} manifest_count={len(rows)} actual_count={len(actual)} "
    f"missing={len(missing)} unlisted={len(unlisted)} unexpected={len(unexpected_worktree)} "
    f"discrepancies={len(errors)}"
)
for error in errors:
    print(f"ERROR: {error}")
raise SystemExit(1 if errors else 0)
