#!/usr/bin/env python3
"""Verify the controlled and native-evidence contracts for Revision-E QET."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from qet_revision_e import DEFAULT_OUTPUT, NOTICE, QET_NAME, ROOT, SAFETY, read_csv


EXPECTED_QET_EXE_SHA256 = "FCC3465825CC6F1BF3997D9C8054858E647A2038C8C01B7A3335A914106DE926"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def visible_text(root: ET.Element) -> str:
    values: list[str] = []
    for node in root.findall(".//diagram/inputs/input"):
        value = html.unescape(node.attrib.get("text", ""))
        value = re.sub(r"<[^>]+>", " ", value)
        values.append(re.sub(r"\s+", " ", value).strip())
    return "\n".join(values)


def verify(output: Path, qet_exe: Path | None = None) -> dict[str, object]:
    checks: list[dict[str, object]] = []

    def require(name: str, condition: bool, evidence: object) -> None:
        checks.append({"check": name, "pass": bool(condition), "evidence": evidence})

    qet = output / QET_NAME
    try:
        qet_relative = qet.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        # Contract tests intentionally verify a generated copy in a disposable
        # directory.  Evidence must remain path-independent there as well.
        qet_relative = qet.name
    require("native QET source exists", qet.is_file(), qet_relative)
    if not qet.is_file():
        return {"passed": 0, "failed": 1, "checks": checks}
    root = ET.parse(qet).getroot()
    diagrams = root.findall("diagram")
    elements = root.findall(".//diagram/elements/element")
    conductors = root.findall(".//diagram/conductors/conductor")
    text = visible_text(root)
    raw = qet.read_text(encoding="utf-8")

    require("project version is QET 0.100.0", root.attrib.get("version") == "0.100.0", root.attrib)
    require("26 controlled folios", len(diagrams) == 26, len(diagrams))
    require("folio order contiguous", [int(d.attrib["order"]) for d in diagrams] == list(range(1, 27)), [d.attrib.get("order") for d in diagrams])
    require("all folios Revision E", all(d.attrib.get("indexrev") == "E" for d in diagrams), sorted({d.attrib.get("indexrev") for d in diagrams}))
    require("no historical Revision-A claim", "Revision A" not in raw and 'indexrev="A"' not in raw, "Revision A absent")
    require("embedded native symbols", len(elements) >= 60, len(elements))
    require("native conductor topology", len(conductors) >= 35, len(conductors))
    require("fictional boundary present", NOTICE in text, NOTICE)
    require("mandatory safety boundary present", SAFETY in text, SAFETY)
    element_positions = [
        (float(node.attrib.get("x", "-1")), float(node.attrib.get("y", "-1")))
        for node in elements
    ]
    input_positions = [
        (float(node.attrib.get("x", "-1")), float(node.attrib.get("y", "-1")))
        for node in root.findall(".//diagram/inputs/input")
    ]
    require(
        "all embedded element anchors remain inside the controlled folio canvas",
        all(0 <= x <= 1000 and 0 <= y <= 700 for x, y in element_positions),
        {"positions": len(element_positions), "canvas": "1000 x 700"},
    )
    require(
        "all controlled text/table anchors remain inside the controlled folio canvas",
        all(0 <= x <= 1000 and 0 <= y <= 700 for x, y in input_positions),
        {"positions": len(input_positions), "canvas": "1000 x 700"},
    )
    long_schedule_columns = {}
    for order in (22, 23, 26):
        diagram = next(item for item in diagrams if int(item.attrib["order"]) == order)
        xs = {float(node.attrib["x"]) for node in diagram.findall("./inputs/input")}
        long_schedule_columns[str(order)] = sorted(x for x in xs if x in {40.0, 285.0, 530.0})
    require(
        "long terminal/BOM schedules retain controlled three-column pagination",
        all(columns == [40.0, 285.0, 530.0] for columns in long_schedule_columns.values()),
        long_schedule_columns,
    )

    bom = read_csv("bom.csv")
    plc = read_csv("plc_io.csv")
    terminals = read_csv("terminal_plan.csv")
    cables = read_csv("cable_schedule.csv")
    network = read_csv("network_nodes.csv")
    missing_bom = [r["full_designation"] or r["tag"] for r in bom if (r["full_designation"] or r["tag"]) not in text]
    missing_symbols = [r["symbol"] for r in plc if r["symbol"] not in text]
    missing_addresses = [r["address"] for r in plc if r["address"] not in text]
    missing_terminals = [r["terminal"] for r in terminals if r["terminal"] not in text]
    missing_cables = [r["cable_id"] for r in cables if r["cable_id"] not in text]
    missing_nodes = [r["node"] for r in network if r["node"] not in text]
    require("all BOM designations represented", not missing_bom, missing_bom)
    require("all PLC symbols represented", not missing_symbols, missing_symbols)
    require("all PLC addresses represented", not missing_addresses, missing_addresses)
    require("all terminal references represented", not missing_terminals, missing_terminals)
    require("all cable identifiers represented", not missing_cables, missing_cables)
    require("all network nodes represented", not missing_nodes, missing_nodes)
    require("PLC addresses unique", len({r["address"] for r in plc}) == len(plc), len(plc))
    require("terminal references unique", len({r["terminal"] for r in terminals}) == len(terminals), len(terminals))
    require("cable identifiers unique", len({r["cable_id"] for r in cables}) == len(cables), len(cables))

    register = output / "FC01_revision_e_element_register.csv"
    register_rows: list[dict[str, str]] = []
    if register.is_file():
        with register.open(encoding="utf-8", newline="") as stream:
            register_rows = list(csv.DictReader(stream))
    expected_register = len(bom) + len(terminals) + len(cables)
    require("controlled element register row count", len(register_rows) == expected_register, {"actual": len(register_rows), "expected": expected_register})
    require("element register classifications", {r["record_type"] for r in register_rows} == {"DEVICE", "TERMINAL", "CABLE"}, sorted({r["record_type"] for r in register_rows}))

    tool: dict[str, object] = {"status": "NOT_REQUESTED"}
    if qet_exe:
        exists = qet_exe.is_file()
        require("QElectroTech executable exists", exists, str(qet_exe))
        if exists:
            proc = subprocess.run([str(qet_exe), "--version"], capture_output=True, text=True, timeout=30, check=False)
            version = (proc.stdout + proc.stderr).strip()
            exe_hash = digest(qet_exe)
            tool = {"path": str(qet_exe), "version_output": version, "sha256": exe_hash, "return_code": proc.returncode}
            require("QElectroTech version 0.100.0", proc.returncode == 0 and "0.100.0" in version, tool)
            require("approved QElectroTech executable hash", exe_hash == EXPECTED_QET_EXE_SHA256, exe_hash)

    pdf = output / "FC01_revision_e_schematics.pdf"
    if pdf.is_file():
        try:
            from pypdf import PdfReader

            reader = PdfReader(pdf)
            require("native multipage PDF has 26 folios", len(reader.pages) == 26, len(reader.pages))
        except Exception as exc:  # pragma: no cover - evidence error path
            require("native multipage PDF reopens", False, str(exc))

    failed = sum(not item["pass"] for item in checks)
    evidence = {
        "release": "Revision E",
        "project": qet_relative,
        "qet_sha256": digest(qet),
        "page_count": len(diagrams),
        "element_count": len(elements),
        "conductor_count": len(conductors),
        "tool": tool,
        "passed": len(checks) - failed,
        "failed": failed,
        "checks": checks,
        "claim_boundary": "Static structure and tool provenance are verified here; native reopen/export evidence is recorded separately after actual GUI execution.",
    }
    (output / "FC01_revision_e_verification.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--qet-exe", type=Path)
    args = parser.parse_args()
    evidence = verify(args.output_dir.resolve(), args.qet_exe.resolve() if args.qet_exe else None)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 1 if evidence["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
