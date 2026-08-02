"""Normalize XLSX ZIP metadata after artifact-tool export for stable hashes."""
from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "10_schedules/FC01_engineering_schedules.xlsx"
FIXED = (2026, 8, 2, 0, 0, 0)


def relationship_owner(name: str) -> str | None:
    parts = name.split("/")
    if parts == ["_rels", ".rels"] or "_rels" not in parts:
        return None
    rel_index = parts.index("_rels")
    rel_name = parts[-1]
    if not rel_name.endswith(".rels"):
        return None
    return "/".join(parts[:rel_index] + [rel_name[:-5]])


with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", dir=TARGET.parent) as handle:
    temp = Path(handle.name)
try:
    with zipfile.ZipFile(TARGET, "r") as source, zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        entries = {name: source.read(name) for name in source.namelist()}
        if "docProps/core.xml" in entries:
            core = entries["docProps/core.xml"].decode("utf-8")
            core = re.sub(r"<dcterms:(created|modified)[^>]*>.*?</dcterms:\1>", lambda m: re.sub(r">.*?<", ">2026-08-02T00:00:00Z<", m.group(0)), core)
            entries["docProps/core.xml"] = core.encode("utf-8")

        # artifact-tool creates random relationship identifiers.  Canonicalize
        # every .rels part and the corresponding r:id references in its owner.
        for rel_name in sorted(name for name in entries if name.endswith(".rels")):
            rel_text = entries[rel_name].decode("utf-8-sig")
            relationship_ids = re.findall(r'\bId="([^"]+)"', rel_text)
            replacements = {old: f"rId{index}" for index, old in enumerate(relationship_ids, 1)}
            for old, new in replacements.items():
                rel_text = rel_text.replace(f'Id="{old}"', f'Id="{new}"')
            entries[rel_name] = ("\ufeff" + rel_text).encode("utf-8")
            owner = relationship_owner(rel_name)
            if owner in entries:
                owner_data = entries[owner]
                for old, new in replacements.items():
                    owner_data = owner_data.replace(old.encode("utf-8"), new.encode("utf-8"))
                entries[owner] = owner_data

        for name in sorted(entries):
            data = entries[name]
            original = source.getinfo(name)
            info = zipfile.ZipInfo(name, FIXED)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = original.external_attr
            info.create_system = original.create_system
            output.writestr(info, data)
    temp.replace(TARGET)
finally:
    if temp.exists(): temp.unlink()
print(f"normalized_xlsx={TARGET.relative_to(ROOT).as_posix()}")
