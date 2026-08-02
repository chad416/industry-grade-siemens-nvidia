"""Compare controlled text/source outputs from two independent clean builds."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".csv", ".json", ".scl", ".txt", ".mmd", ".py", ".ps1", ".mjs"}
EXCLUDE_PARTS = {".git", "__pycache__", "node_modules", ".cache", ".pytest_cache", ".determinism"}
EXCLUDE_FILES = {"manifest.json", "manifest.csv", "determinism_report.md"}


def ignore(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in EXCLUDE_PARTS}


def run_clean(destination: Path) -> dict[str, str]:
    shutil.copytree(ROOT, destination, ignore=ignore)
    commands = [
        [sys.executable, "scripts/build_project.py"],
        [sys.executable, "11_simulation/run_scenarios.py"],
        [sys.executable, "scripts/validate_project.py"],
    ]
    for command in commands:
        subprocess.run(command, cwd=destination, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    result = {}
    for path in sorted(destination.rglob("*"), key=lambda p: p.relative_to(destination).as_posix()):
        rel = path.relative_to(destination)
        if (path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and path.name not in EXCLUDE_FILES
                and not any(part in EXCLUDE_PARTS for part in rel.parts)):
            result[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


with tempfile.TemporaryDirectory(prefix="fc01-rev-d-determinism-") as temporary:
    base = Path(temporary)
    first = run_clean(base / "run_a")
    second = run_clean(base / "run_b")

missing = sorted(set(first) - set(second))
unlisted = sorted(set(second) - set(first))
mismatched = sorted(path for path in set(first) & set(second) if first[path] != second[path])
passed = not (missing or unlisted or mismatched)
report = [
    "# Determinism report - Revision D", "",
    "Result: **PASS**" if passed else "Result: **FAIL**", "",
    "Two independent temporary copies ran canonical generation, all 32 scenarios and the deterministic project validator.",
    "The comparison covers controlled text, CSV, JSON, Siemens SCL, scripts and generated reports. XLSX ZIP metadata and PDF metadata are normalized separately in their builders.", "",
    f"Compared files: {len(first)}", f"Missing from run B: {len(missing)}", f"Extra in run B: {len(unlisted)}", f"Hash mismatches: {len(mismatched)}",
]
if missing: report += ["", "## Missing", ""] + [f"- {item}" for item in missing]
if unlisted: report += ["", "## Extra", ""] + [f"- {item}" for item in unlisted]
if mismatched: report += ["", "## Mismatched", ""] + [f"- {item}" for item in mismatched]
(ROOT / "14_qa/determinism_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
print(f"determinism_files={len(first)} missing={len(missing)} extra={len(unlisted)} mismatched={len(mismatched)}")
raise SystemExit(0 if passed else 1)
