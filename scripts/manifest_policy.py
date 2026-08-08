"""Single Revision-G controlled-file inclusion and classification policy."""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

EXCLUDED_NAMES = {"manifest.json", "manifest.csv", ".DS_Store"}
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".cache", ".pytest_cache", ".determinism", "tmp"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp"}
FIELDS = ["path","bytes","sha256","category","role","revision","gate_status","blocker"]
REVISION = "G"
FORBIDDEN_PATHS = {
    "scripts/revision_c_generator.py",
    "scripts/revision_c_scl.py",
}
FORBIDDEN_PREFIXES = (
    "14_qa/pdf_renders/release/",
    "14_qa/pdf_renders/release_c/",
    "14_qa/pdf_renders/release_f/",
)


def included_rel(rel: str) -> bool:
    pure = PurePosixPath(rel)
    return (
        not pure.is_absolute()
        and ".." not in pure.parts
        and pure.name not in EXCLUDED_NAMES
        and not any(part in EXCLUDED_DIRS for part in pure.parts)
        and pure.suffix.lower() not in EXCLUDED_SUFFIXES
        and not pure.name.endswith(".inspect.ndjson")
    )


def forbidden(rel: str) -> bool:
    return rel in FORBIDDEN_PATHS or rel.startswith(FORBIDDEN_PREFIXES)


def included(root: Path, path: Path) -> bool:
    return path.is_file() and included_rel(path.relative_to(root).as_posix())


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
        "03_electrical":"Electrical design","04_controls_siemens":"Siemens sources","05_hmi":"HMI","06_drives":"Drives",
        "07_nvidia_vision":"Vision","08_digital_twin":"Digital twin","09_panel_cad":"Panel CAD","10_schedules":"Schedules",
        "11_simulation":"Simulation","12_testing":"Testing","13_documentation":"Documentation","14_qa":"QA","release":"Release","scripts":"Reproduction",
        "cloud":"Cloud execution","siemens_native":"Siemens native execution","nvidia_native":"NVIDIA native execution","commissioning":"Commissioning",".github":"CI control"
    }.get(top, "Repository control")
    if rel.startswith("03_electrical/native_baseline/") or rel.startswith("09_panel_cad/native_baseline/"):
        return category,"Quarantined historical native baseline","OPEN","Historical Revision-A evidence only; never current design authority"
    if rel.startswith("03_electrical/revision_e/"):
        return category,"Revision-E native electrical source/export/evidence","PARTIAL","Native QET gate status is controlled by the acceptance record; site electrical and qualified review remain open"
    if rel.startswith("03_electrical/revision_f_native_qet/"):
        return category,"Revision-F exact-hash QET reopen/export evidence","PARTIAL","Native reopen/export passed; folio-25 visual clipping and automatic cross-reference evidence remain open"
    if rel == "03_electrical/revision_f_nvidia_electrical_delta.md" or rel == "10_schedules/nvidia_electrical_delta.csv":
        return category,"Revision-F provisional NVIDIA electrical delta","PARTIAL","Selected devices, native QET/CAD incorporation, site calculations and qualified review remain open"
    if rel.startswith("09_panel_cad/revision_e/"):
        return category,"Revision-E native panel source/export/evidence","PASS","FreeCAD reopen/reimport evidence is controlled separately from construction/site approval"
    if top in {"04_controls_siemens","05_hmi","06_drives"}:
        return category,"Revision-F import-ready design source/specification","OPEN","Native compile/configuration not executed"
    if top == "07_nvidia_vision":
        return category,"Locally tested source, secure OPC UA adapter and deployment specification","PARTIAL","Real asyncua integration passes; production S7/Jetson endpoint, dataset/model and target runtime remain unavailable"
    if top == "08_digital_twin":
        return category,"Architecture/source","OPEN","Real dataset/target runtime unavailable"
    if top == "11_simulation":
        return category,"Independent design evidence","PASS","Not Siemens/physical evidence"
    if top == "cloud":
        return category,"Disabled-by-default reviewable cloud source","PARTIAL","Custom static controls pass; provider-native fmt/validate/plan, approval and provisioning remain open"
    if top == "siemens_native":
        return category,"Native access inventory and exact handoff","BLOCKED","TIA/WinCC licence and Openness authorization are unproven; Startdrive and PLCSIM are absent"
    if top == "nvidia_native":
        blocked_names = {"dataset_manifest.csv", "training_config.yaml", "evaluation_config.yaml", "model_card.md", "confusion_matrix_status.md", "latency_results_status.md"}
        if PurePosixPath(rel).name in blocked_names:
            return category,"Data/model/runtime execution prerequisite","BLOCKED","Representative data, trained model and target CUDA/TensorRT/DeepStream runtime are absent"
        return category,"Source-tested fail-closed execution prerequisite","PARTIAL","Synthetic/local software evidence only; production data/model/runtime/container evidence remains open"
    if top == "commissioning":
        if PurePosixPath(rel).suffix.lower() == ".csv" and ("record" in PurePosixPath(rel).name or PurePosixPath(rel).name in {"io_checkout.csv", "punch_list.csv", "as_built_redline_register.csv"}):
            return category,"Controlled blank execution record","OPEN","No physical measurement, tester, witness or signature exists"
        return category,"Commissioning and qualified-review preparation","PARTIAL","Physical execution and qualified electrical/machinery-safety review remain open"
    return category,"Controlled artifact","PASS",""
