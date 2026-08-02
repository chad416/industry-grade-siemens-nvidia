"""Single Revision-D controlled-file inclusion and classification policy."""
from __future__ import annotations

import os
from pathlib import Path

EXCLUDED_NAMES = {"manifest.json", "manifest.csv", ".DS_Store"}
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".cache", ".pytest_cache", ".determinism", "tmp"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp"}
FIELDS = ["path","bytes","sha256","category","role","revision","gate_status","blocker"]


def included(root: Path, path: Path) -> bool:
    rel = path.relative_to(root)
    return (path.is_file() and path.name not in EXCLUDED_NAMES and
            not any(part in EXCLUDED_DIRS for part in rel.parts) and
            path.suffix.lower() not in EXCLUDED_SUFFIXES and
            not path.name.endswith(".inspect.ndjson"))


def reparse_points(root: Path) -> list[str]:
    result = []
    for path in root.rglob("*"):
        try:
            attrs = path.stat(follow_symlinks=False).st_file_attributes
        except (AttributeError, OSError):
            attrs = 0
        if path.is_symlink() or attrs & getattr(os.stat_result, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            result.append(path.relative_to(root).as_posix())
    return sorted(result)


def classify(rel: str) -> tuple[str, str, str, str]:
    top = rel.split("/", 1)[0]
    category = {
        "00_project_control":"Project control","01_requirements":"Requirements","02_system_architecture":"Architecture",
        "03_electrical":"Electrical baseline","04_controls_siemens":"Siemens sources","05_hmi":"HMI","06_drives":"Drives",
        "07_nvidia_vision":"Vision","08_digital_twin":"Digital twin","09_panel_cad":"Panel baseline","10_schedules":"Schedules",
        "11_simulation":"Simulation","12_testing":"Testing","13_documentation":"Documentation","14_qa":"QA","release":"Release","scripts":"Reproduction"
    }.get(top, "Repository control")
    if top in {"03_electrical","09_panel_cad"}:
        return category,"Historical/native-boundary and controlled design data","OPEN","Revision-D native replacement/reopen blocked"
    if top in {"04_controls_siemens","05_hmi","06_drives"}:
        return category,"Design source/specification","OPEN","Native compile/configuration not executed"
    if top == "07_nvidia_vision":
        return category,"Locally tested source plus deployment specification","PARTIAL","Python tests pass; real dataset/OPC UA/target runtime unavailable"
    if top == "08_digital_twin":
        return category,"Architecture/source","OPEN","Real dataset/target runtime unavailable"
    if top == "11_simulation":
        return category,"Independent design evidence","PASS","Not Siemens/physical evidence"
    return category,"Controlled artifact","PASS",""
