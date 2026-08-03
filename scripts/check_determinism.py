"""Compare controlled text/source outputs from two authoritative Git snapshots."""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from git_release_source import ROOT, assert_index_inputs_staged, untracked_paths

TEXT_SUFFIXES = {".md", ".csv", ".json", ".scl", ".txt", ".mmd", ".py", ".ps1", ".mjs", ".yml", ".yaml", ".service", ".example", ".log"}
EXCLUDE_PARTS = {".git", "__pycache__", "node_modules", ".cache", ".pytest_cache", ".determinism"}
EXCLUDE_FILES = {"manifest.json", "manifest.csv", "determinism_report.md"}
ARGS = argparse.ArgumentParser()
ARGS.add_argument("--source", choices=("head", "index"), default="index")
OPTIONS = ARGS.parse_args()


def export_snapshot(destination: Path) -> None:
    destination.mkdir(parents=True)
    if OPTIONS.source == "index":
        assert_index_inputs_staged(allow_unstaged={"14_qa/determinism_report.md"})
        prefix = str(destination.resolve()) + os.sep
        subprocess.run(["git", "checkout-index", "--all", f"--prefix={prefix}"], cwd=ROOT, check=True)
    else:
        archive_path = destination.parent / f"{destination.name}.tar"
        subprocess.run(
            ["git", "archive", "--format=tar", f"--output={archive_path}", "HEAD"],
            cwd=ROOT,
            check=True,
        )
        with tarfile.open(archive_path, "r") as archive:
            archive.extractall(destination, filter="data")
        archive_path.unlink()


def run_clean(destination: Path) -> dict[str, str]:
    export_snapshot(destination)
    commands = [
        [sys.executable, "scripts/build_project.py"],
        [sys.executable, "11_simulation/run_scenarios.py"],
        [sys.executable, "scripts/validate_project.py", "--check"],
    ]
    for command in commands:
        subprocess.run(command, cwd=destination, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    result = {}
    for path in sorted(destination.rglob("*"), key=lambda item: item.relative_to(destination).as_posix()):
        rel = path.relative_to(destination)
        if (
            path.is_file()
            and path.suffix.lower() in TEXT_SUFFIXES
            and path.name not in EXCLUDE_FILES
            and not any(part in EXCLUDE_PARTS for part in rel.parts)
        ):
            result[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


if untracked_paths():
    raise SystemExit(f"Unexpected files prevent deterministic release build: {untracked_paths()}")

with tempfile.TemporaryDirectory(prefix="fc01-rev-e-determinism-") as temporary:
    base = Path(temporary)
    first = run_clean(base / "run_a")
    second = run_clean(base / "run_b")

missing = sorted(set(first) - set(second))
extra = sorted(set(second) - set(first))
mismatched = sorted(path for path in set(first) & set(second) if first[path] != second[path])
passed = not (missing or extra or mismatched)
report = [
    "# Determinism report - Revision E",
    "",
    "Result: **PASS**" if passed else "Result: **FAIL**",
    "",
    "Two independent temporary exports of the selected authoritative Git snapshot ran canonical generation, all 32 scenarios and read-only deterministic validation.",
    "The comparison covers controlled text, CSV, JSON, Siemens SCL, scripts and generated reports. XLSX and PDF binary determinism is checked separately by the standard reproduction workflow.",
    "",
    f"Compared files: {len(first)}",
    f"Missing from run B: {len(missing)}",
    f"Extra in run B: {len(extra)}",
    f"Hash mismatches: {len(mismatched)}",
]
if missing:
    report += ["", "## Missing", ""] + [f"- {item}" for item in missing]
if extra:
    report += ["", "## Extra", ""] + [f"- {item}" for item in extra]
if mismatched:
    report += ["", "## Mismatched", ""] + [f"- {item}" for item in mismatched]
(ROOT / "14_qa/determinism_report.md").write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
print(
    f"determinism_source={OPTIONS.source} files={len(first)} missing={len(missing)} "
    f"extra={len(extra)} mismatched={len(mismatched)}"
)
raise SystemExit(0 if passed else 1)
