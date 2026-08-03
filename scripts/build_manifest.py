"""Build the release manifest exclusively from staged Git-index bytes."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from git_release_source import assert_index_inputs_staged, read_bytes, tracked_paths
from manifest_policy import FIELDS, REVISION, classify, forbidden, included_rel, reparse_points

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = {"release/manifest.json", "release/manifest.csv"}


points = reparse_points(ROOT)
if points:
    raise SystemExit(f"reparse/symlink paths are forbidden during manifest build: {points}")

try:
    assert_index_inputs_staged(allow_unstaged=MANIFESTS)
except RuntimeError as exc:
    raise SystemExit(str(exc)) from exc

paths = [rel for rel in tracked_paths("index") if included_rel(rel)]
blocked = [rel for rel in paths if forbidden(rel)]
if blocked:
    raise SystemExit(f"superseded/forbidden controlled paths are staged: {blocked}")

rows = []
for rel in paths:
    category, role, gate, blocker = classify(rel)
    content = read_bytes("index", rel)
    rows.append(
        {
            "path": rel,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "category": category,
            "role": role,
            "revision": REVISION,
            "gate_status": gate,
            "blocker": blocker,
        }
    )

payload = {
    "project": "FC01",
    "revision": REVISION,
    "status": "PROFESSIONAL CONTROLLED ENGINEERING-DEVELOPMENT PACKAGE",
    "generated": "2026-08-03",
    "byte_source": "Git index (staged authoritative bytes)",
    "file_count": len(rows),
    "files": rows,
}
(ROOT / "release/manifest.json").write_text(
    json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
    newline="\n",
)
with (ROOT / "release/manifest.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
print(f"manifest_source=index manifest_files={len(rows)}")
