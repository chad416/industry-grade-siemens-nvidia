"""Adversarial checks for Git byte policy and superseded-release containment."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

from git_release_source import ROOT, read_bytes, tracked_paths, untracked_paths
from manifest_policy import forbidden, included_rel

ARGS = argparse.ArgumentParser()
ARGS.add_argument("--source", choices=("head", "index"), default="head")
OPTIONS = ARGS.parse_args()

BINARY_SUFFIXES = {
    ".qet", ".dxf", ".fcstd", ".step", ".stp", ".iges", ".igs", ".xlsx", ".xls",
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".7z", ".ap20", ".zap20",
    ".onnx", ".engine", ".plan", ".usd", ".usda", ".usdc",
}
TEXT_SUFFIXES = {".md", ".csv", ".json", ".scl", ".txt", ".mmd", ".py", ".ps1", ".mjs", ".yml", ".yaml", ".tf", ".dockerignore", ".service", ".example", ".log"}
EXPECTED_NATIVE = {
    "03_electrical/native_baseline/filling_cell.qet": (875734, "d817036497afbf0f48379da4dbce81cd1d7b7cca28bfc8341d5b437d2421660b"),
    "09_panel_cad/native_baseline/mounting_plate.dxf": (15277, "9ddd38069e43c74c92393bf7f2d3dda729dfce041cedcd16fcdfca0dd433828d"),
}

checks: list[str] = []
errors: list[str] = []


def ok(condition: bool, label: str) -> None:
    (checks if condition else errors).append(label)


def attribute(rel: str, name: str) -> str:
    result = subprocess.run(
        ["git", "check-attr", name, "--", rel],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip().rsplit(": ", 1)[-1]


paths = [rel for rel in tracked_paths(OPTIONS.source) if included_rel(rel)]
ok(not [rel for rel in paths if forbidden(rel)], "no superseded Revision-C path is controlled")
ok(not [rel for rel in untracked_paths() if forbidden(rel)], "no superseded Revision-C path is resurrected")

unknown_suffixes = set()
for rel in paths:
    suffix = Path(rel).suffix.lower()
    if suffix in TEXT_SUFFIXES or Path(rel).name in {".gitignore", ".gitattributes"}:
        ok(attribute(rel, "text") == "set", f"text policy is explicit: {rel}")
        content = read_bytes(OPTIONS.source, rel)
        ok(b"\r\n" not in content, f"authoritative text is LF-only: {rel}")
    elif suffix in BINARY_SUFFIXES:
        ok(attribute(rel, "text") == "unset", f"byte-exact policy is explicit: {rel}")
    elif suffix:
        unknown_suffixes.add(suffix)
ok(not unknown_suffixes, f"all controlled suffixes have explicit policy: {sorted(unknown_suffixes)}")

for rel, (expected_size, expected_hash) in EXPECTED_NATIVE.items():
    content = read_bytes(OPTIONS.source, rel)
    ok(len(content) == expected_size, f"authoritative native size: {rel}")
    ok(hashlib.sha256(content).hexdigest() == expected_hash, f"authoritative native SHA-256: {rel}")

print(f"release_integrity_source={OPTIONS.source} checks={len(checks)} failures={len(errors)}")
for error in errors:
    print(f"ERROR: {error}")
raise SystemExit(1 if errors else 0)
