"""Restore the controlled Revision-F NVIDIA files rewritten by legacy generators."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = Path(__file__).resolve().parent / "revision_f_nvidia_templates"
OWNED = {
    "dataset_annotation_guide.md": "07_nvidia_vision/dataset_annotation_guide.md",
    "model_card.md": "07_nvidia_vision/model_card.md",
    "plc_ai_node_map.csv": "07_nvidia_vision/plc_ai_node_map.csv",
    "edge_service/service_config.json": "07_nvidia_vision/edge_service/service_config.json",
}


def apply_revision_f_nvidia(root: Path = ROOT) -> None:
    for source, destination in OWNED.items():
        content = (TEMPLATES / source).read_text(encoding="utf-8")
        target = root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    apply_revision_f_nvidia()
    print("Applied controlled Revision-F NVIDIA generator overlay")
