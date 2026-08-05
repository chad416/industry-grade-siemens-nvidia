"""Report locked Python dependency/version/license metadata without network I/O."""
from __future__ import annotations

import argparse
from importlib import metadata
import json
from pathlib import Path
import re


LOCK_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s#]+)$")


def parse_lock(path: Path) -> list[tuple[str, str]]:
    packages: list[tuple[str, str]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = LOCK_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"unlocked or malformed requirement at line {number}")
        packages.append((match.group(1), match.group(2)))
    if len({name.casefold() for name, _ in packages}) != len(packages):
        raise ValueError("dependency lock contains duplicate package names")
    return packages


def inventory(path: Path) -> dict:
    entries = []
    for name, locked in parse_lock(path):
        try:
            distribution = metadata.distribution(name)
            installed = distribution.version
            license_text = distribution.metadata.get("License-Expression") or distribution.metadata.get("License") or "UNKNOWN"
            status = "MATCH" if installed == locked else "VERSION_MISMATCH"
        except metadata.PackageNotFoundError:
            installed = None
            license_text = "NOT_INSTALLED"
            status = "MISSING"
        entries.append({
            "name": name,
            "locked_version": locked,
            "installed_version": installed,
            "license_metadata": license_text,
            "status": status,
        })
    return {
        "format": "FC01 dependency inventory v1",
        "scope": "Python lock metadata; not a vulnerability scan or target-image SBOM",
        "packages": entries,
        "status": "PASS" if all(item["status"] == "MATCH" for item in entries) else "INCOMPLETE",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lock", type=Path)
    args = parser.parse_args()
    print(json.dumps(inventory(args.lock), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
