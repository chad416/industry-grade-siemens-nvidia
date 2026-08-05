"""Revision-F Siemens SCL overlay sourced from controlled text templates.

Revision D remains the historical generator.  Revision F deliberately keeps the
expanded PLC/AI source in separate templates so a clean build can reproduce the
exact import-ready bytes without rewriting Revision-D history.
"""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = Path(__file__).resolve().parent / "revision_f_scl_templates"
OUTPUT_ROOT = ROOT / "04_controls_siemens" / "scl"
OWNED_NAMES = (
    "00_types.scl",
    "DB_Global.scl",
    "FB_CellMain.scl",
    "FB_VisionInterface.scl",
    "OB100_Startup.scl",
)


def sources() -> dict[str, str]:
    """Return the complete authoritative SCL source set for Revision F."""
    from revision_d_scl import sources as revision_d_sources

    result = revision_d_sources()
    for name in OWNED_NAMES:
        result[name] = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    return result


def apply_revision_f_scl(root: Path = ROOT) -> None:
    output_root = root / "04_controls_siemens" / "scl"
    output_root.mkdir(parents=True, exist_ok=True)
    for name, content in sources().items():
        (output_root / name).write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    apply_revision_f_scl()
    print(f"Applied Revision-F Siemens SCL under {OUTPUT_ROOT}")
