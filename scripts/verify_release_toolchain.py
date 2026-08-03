from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "release" / "reproduction_toolchain_lock.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(actual: str, expected: str, label: str) -> None:
    if actual != expected:
        raise SystemExit(f"toolchain mismatch: {label}: expected {expected!r}, observed {actual!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the exact Revision-E artifact-reproduction toolchain")
    parser.add_argument("--node", required=True, type=Path)
    parser.add_argument("--node-modules", required=True, type=Path)
    parser.add_argument("--pdftoppm", required=True, type=Path)
    args = parser.parse_args()

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    python_lock = lock["python"]
    node_lock = lock["node"]
    poppler_lock = lock["pdftoppm"]

    python_path = Path(sys.executable).resolve()
    node_path = args.node.resolve()
    pdftoppm_path = args.pdftoppm.resolve()
    require(".".join(str(part) for part in sys.version_info[:3]), python_lock["version"], "Python version")
    require(sha256(python_path), python_lock["executable_sha256"], "Python executable SHA-256")
    for package, version in python_lock["packages"].items():
        require(importlib.metadata.version(package), version, f"Python package {package}")

    node_version = subprocess.run(
        [str(node_path), "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    require(node_version, node_lock["version"], "Node.js version")
    require(sha256(node_path), node_lock["executable_sha256"], "Node.js executable SHA-256")
    artifact_package = (args.node_modules / "@oai" / "artifact-tool" / "package.json").resolve()
    artifact_version = json.loads(artifact_package.read_text(encoding="utf-8"))["version"]
    require(artifact_version, node_lock["packages"]["@oai/artifact-tool"], "@oai/artifact-tool version")

    require(sha256(pdftoppm_path), poppler_lock["executable_sha256"], "pdftoppm executable SHA-256")
    version_result = subprocess.run(
        [str(pdftoppm_path), "-v"], check=False, capture_output=True, text=True
    )
    version_text = (version_result.stdout + version_result.stderr).splitlines()[0]
    require(version_text, f"pdftoppm version {poppler_lock['version']}", "pdftoppm version")

    print(
        "toolchain_result=PASS "
        f"python={python_lock['version']} node={node_lock['version']} "
        f"artifact_tool={artifact_version} pdftoppm={poppler_lock['version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
