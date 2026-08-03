#!/usr/bin/env python3
"""Build the native Revision-E QElectroTech project from controlled schedules.

The output is deterministic QElectroTech XML.  It is intentionally generated from
the controlled BOM, I/O, terminal, cable, network and Siemens hardware schedules;
the historical Revision-A project is not read or copied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "03_electrical" / "revision_e"
NOTICE = "FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION"
SAFETY = (
    "CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, "
    "DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. "
    "NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
)
QET_NAME = "FC01_revision_e.qet"
PROJECT_TITLE = "FC01 Compact Filling-Cell Electrical Design Package - Revision E"
NAMESPACE = uuid.UUID("f7e21ad0-14a4-52f0-8d94-1fe2918752c8")


@dataclass(frozen=True)
class Block:
    kind: str
    tag: str
    description: str
    detail: str = ""


@dataclass
class Page:
    title: str
    blocks: list[Block] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    table_rows: list[str] = field(default_factory=list)


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / "10_schedules" / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def designation(tag: str, bom_by_tag: dict[str, dict[str, str]]) -> str:
    row = bom_by_tag.get(tag)
    if row and row.get("full_designation"):
        return row["full_designation"]
    clean = tag.lstrip("-")
    return f"=FC01+CP01-{clean}"


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u2013", "-").replace("\u2014", "-")).strip()


def rich_text(text: str, size: float, color: str, bold: bool) -> str:
    weight = 600 if bold else 400
    safe = html.escape(clean_text(text), quote=False)
    return (
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" '
        '"http://www.w3.org/TR/REC-html40/strict.dtd">'
        '<html><head><meta name="qrichtext" content="1" />'
        '<style type="text/css">p, li { white-space: pre-wrap; }</style></head>'
        '<body style="font-family:\'Liberation Sans\'; font-size:9pt; font-weight:400; font-style:normal;">'
        '<p style="margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; '
        f'-qt-block-indent:0; text-indent:0px;"><span style="font-family:\'Liberation Sans\'; '
        f'font-size:{size:g}pt; font-weight:{weight}; color:{color};">{safe}</span></p></body></html>'
    )


def add_input(parent: ET.Element, x: float, y: float, text: str, *, size: float = 6.0,
              color: str = "#111827", bold: bool = False) -> None:
    ET.SubElement(
        parent,
        "input",
        {
            "rotation": "0",
            "text": rich_text(text, size, color, bold),
            "y": f"{y:g}",
            "x": f"{x:g}",
            "font": "Liberation Sans,9,-1,0,50,0,0,0,0,0,Regular",
        },
    )


def default_conductor_attrs(number: str = "", display: bool = False) -> dict[str, str]:
    return {
        "function": "",
        "bicolor": "false",
        "cable": "",
        "color2": "#000000",
        "num": number,
        "text_color": "#000000",
        "onetextperfolio": "0",
        "bus": "",
        "conductor_color": "",
        "vertirotatetext": "0",
        "condsize": "1",
        "formula": "",
        "dash-size": "1",
        "numsize": "7",
        "vertical-alignment": "AlignRight",
        "displaytext": "1" if display else "0",
        "tension_protocol": "",
        "horizontal-alignment": "AlignBottom",
        "type": "multi",
        "conductor_section": "",
        "horizrotatetext": "0",
    }


def add_project_defaults(project: ET.Element) -> None:
    properties = ET.SubElement(project, "properties")
    for name, value in [
        ("saveddate", "2026-08-03"),
        ("saveddate-eu", "03-08-2026"),
        ("saveddate-us", "2026-08-03"),
        ("savedfilename", QET_NAME),
        ("savedfilepath", "03_electrical/revision_e/FC01_revision_e.qet"),
        ("savedtime", "00:00"),
    ]:
        item = ET.SubElement(properties, "property", {"name": name, "show": "1"})
        item.text = value
    ET.SubElement(project, "usage", {"enabled": "true", "time_spent": "0"})
    new = ET.SubElement(project, "newdiagrams")
    ET.SubElement(new, "border", {"cols": "15", "displayrows": "true", "displaycols": "true", "rows": "6", "rowsize": "80", "colsize": "50"})
    ET.SubElement(new, "inset", {"filename": QET_NAME, "title": "", "indexrev": "E", "date": "2026-08-03", "plant": "FC01 Compact Filling Cell", "version": "E", "displayAt": "bottom", "author": "FC01 engineering team", "auto_page_num": "", "locmach": "FC01", "folio": "%id/%total"})
    ET.SubElement(new, "conductors", default_conductor_attrs("_", True))
    ET.SubElement(new, "report", {"label": "/%f.%l%c"})
    xrefs = ET.SubElement(new, "xrefs")
    for kind in ["plc", "protection", "commutator", "coil"]:
        ET.SubElement(xrefs, "xref", {"displayhas": "cross", "switchprefix": "", "type": kind, "delayprefix": "", "showpowerctc": "true" if kind == "plc" else "false", "offset": "0", "powerprefix": "", "xrefpos": "AlignBottom", "snapto": "label", "master_label": "%f-%l%c", "slave_label": "(%f-%l%c)", "showterminalname": "true"})
    ET.SubElement(new, "conductors_autonums", {"freeze_new_conductors": "false", "current_autonum": ""})
    ET.SubElement(new, "folio_autonums")
    ET.SubElement(new, "element_autonums", {"freeze_new_elements": "false", "current_autonum": ""})
    ET.SubElement(new, "guides")


def add_embedded_collection(project: ET.Element) -> None:
    collection = ET.SubElement(project, "collection")
    category = ET.SubElement(collection, "category", {"name": "fc01_reve"})
    names = ET.SubElement(category, "names")
    ET.SubElement(names, "name", {"lang": "en"}).text = "FC01 Revision-E controlled symbols"
    symbols = {
        "device": ("Device", "rect"),
        "protection": ("Protective device", "protection"),
        "power": ("Power supply", "power"),
        "plc": ("PLC / module", "plc"),
        "drive": ("Variable-frequency drive", "drive"),
        "motor": ("Motor", "motor"),
        "sensor": ("Sensor / instrument", "sensor"),
        "actuator": ("Actuator / relay", "actuator"),
        "network": ("Network node", "network"),
        "terminal": ("Terminal / shield", "terminal"),
        "safety": ("Conceptual safety interface", "safety"),
    }
    style = "line-style:normal;line-weight:normal;filling:none;color:black"
    for key, (name, shape) in symbols.items():
        wrapper = ET.SubElement(category, "element", {"name": f"{key}.elmt"})
        definition = ET.SubElement(wrapper, "definition", {"hotspot_y": "25", "hotspot_x": "60", "height": "50", "type": "element", "link_type": "simple", "orientation": "dnny", "version": "0.100", "width": "120"})
        ET.SubElement(definition, "uuid", {"uuid": "{" + str(uuid.uuid5(NAMESPACE, f"symbol-{key}")) + "}"})
        def_names = ET.SubElement(definition, "names")
        ET.SubElement(def_names, "name", {"lang": "en"}).text = name
        ET.SubElement(definition, "informations").text = "FC01 controlled embedded symbol - fictional engineering project"
        desc = ET.SubElement(definition, "description")
        if shape in {"sensor", "motor", "terminal"}:
            ET.SubElement(desc, "ellipse", {"height": "38", "style": style, "y": "-19", "x": "-35" if shape != "terminal" else "-18", "width": "70" if shape != "terminal" else "36"})
        else:
            ET.SubElement(desc, "rect", {"height": "40", "antialias": "false", "style": style, "y": "-20", "x": "-48", "width": "96"})
        if shape in {"protection", "power", "drive", "actuator", "network", "safety"}:
            ET.SubElement(desc, "line", {"end2": "none", "antialias": "false", "end1": "none", "y1": "-13", "style": style, "length2": "1.5", "length1": "1.5", "x1": "-35", "x2": "35", "y2": "13"})
        ET.SubElement(desc, "text", {"text": name.upper(), "x": "-42", "y": "4", "rotation": "0", "font": "Liberation Sans,4,-1,5,50,0,0,0,0,0,Regular", "color": "#17365d"})
        for orient, x, y in [("w", "-50", "0"), ("e", "50", "0"), ("n", "0", "-22"), ("s", "0", "22")]:
            ET.SubElement(desc, "terminal", {"orientation": orient, "y": y, "x": x, "type": "Generic"})


def add_element(diagram: ET.Element, inputs: ET.Element, page_no: int, index: int, block: Block, x: float, y: float) -> tuple[int, int, int, int]:
    elements = diagram.find("elements")
    assert elements is not None
    base = index * 4
    node = ET.SubElement(elements, "element", {
        "uuid": "{" + str(uuid.uuid5(NAMESPACE, f"p{page_no:02d}-{index}-{block.tag}")) + "}",
        "type": f"embed://fc01_reve/{block.kind}.elmt",
        "z": "10",
        "orientation": "0",
        "prefix": "",
        "y": f"{y:g}",
        "freezeLabel": "true",
        "x": f"{x:g}",
    })
    terminals = ET.SubElement(node, "terminals")
    for offset, orient, tx, ty in [(0, "0", "0", "-22"), (1, "3", "-50", "0"), (2, "1", "50", "0"), (3, "2", "0", "22")]:
        ET.SubElement(terminals, "terminal", {"orientation": orient, "y": ty, "x": tx, "id": str(base + offset)})
    ET.SubElement(node, "inputs")
    ET.SubElement(node, "dynamic_texts")
    ET.SubElement(node, "texts_groups")
    info = ET.SubElement(node, "elementInformations")
    ET.SubElement(info, "elementInformation", {"name": "label"}).text = block.tag
    ET.SubElement(info, "elementInformation", {"name": "function"}).text = block.description
    add_input(inputs, x - 48, y + 31, block.tag, size=6.0, color="#17365d", bold=True)
    add_input(inputs, x - 48, y + 45, block.description, size=4.4)
    if block.detail:
        add_input(inputs, x - 48, y + 57, block.detail, size=3.8, color="#374151")
    return base, base + 1, base + 2, base + 3


def add_conductor(diagram: ET.Element, terminal1: int, terminal2: int) -> None:
    conductors = diagram.find("conductors")
    assert conductors is not None
    attrs = default_conductor_attrs("", False)
    attrs.update({"terminal1": str(terminal1), "terminal2": str(terminal2), "x": "0", "y": "0", "freezeLabel": "false"})
    conductor = ET.SubElement(conductors, "conductor", attrs)
    ET.SubElement(conductor, "sequentialNumbers")


def table_layout(row_count: int, has_blocks: bool) -> tuple[int, int, float, float, float, float]:
    """Return a bounded folio layout for schedule text.

    Long schedules use compact three-column pagination.  Diagram-plus-table
    folios reserve the upper band for symbols and conductors so schedule text
    cannot overlap the native diagram objects.
    """
    if row_count <= 0:
        return (0, 0, 0.0, 0.0, 0.0, 0.0)
    columns = 3 if row_count > 32 else (2 if row_count > 16 else 1)
    per_col = (row_count + columns - 1) // columns
    start_y = 225.0 if has_blocks else 69.0
    if columns == 3:
        return (columns, per_col, 245.0, start_y, 15.8, 2.8)
    if columns == 2:
        return (columns, per_col, 365.0, start_y, 19.0, 3.3)
    return (columns, per_col, 0.0, start_y, 21.5, 4.1)


def make_diagram(project: ET.Element, page_no: int, page: Page, total_pages: int) -> None:
    diagram = ET.SubElement(project, "diagram", {
        "displaycols": "true", "author": "FC01 engineering team", "freezeNewElement": "false",
        "locmach": "FC01", "version": "0.100.0", "filename": QET_NAME, "displayAt": "bottom",
        "displayrows": "true", "title": page.title, "order": str(page_no), "auto_page_num": "",
        "rows": "6", "date": "2026-08-03", "height": "500", "indexrev": "E",
        "plant": "FC01 Compact Filling Cell", "folio": "%id/%total", "cols": "15",
        "rowsize": "80", "colsize": "50", "freezeNewConductor": "false",
    })
    ET.SubElement(diagram, "defaultconductor", default_conductor_attrs("_", True))
    inputs = ET.SubElement(diagram, "inputs")
    ET.SubElement(diagram, "elements")
    ET.SubElement(diagram, "conductors")
    add_input(inputs, 38, 27, f"E-{page_no:02d}  {page.title.upper()}", size=10.5, color="#17365d", bold=True)
    add_input(inputs, 605, 28, f"REV E | {page_no}/{total_pages}", size=5.5, color="#374151", bold=True)

    if page.blocks:
        positions: list[tuple[float, float]] = []
        first = page.blocks[:5]
        second = page.blocks[5:10]
        for count, row, y in [(len(first), first, 115.0), (len(second), second, 255.0)]:
            if not count:
                continue
            xs = [75 + i * (600 / max(1, count - 1)) for i in range(count)] if count > 1 else [375]
            positions.extend((x, y) for x in xs)
        terminal_sets: list[tuple[int, int, int, int]] = []
        for index, (block, (x, y)) in enumerate(zip(page.blocks[:10], positions)):
            terminal_sets.append(add_element(diagram, inputs, page_no, index, block, x, y))
        row_break = min(5, len(terminal_sets))
        for i in range(row_break - 1):
            add_conductor(diagram, terminal_sets[i][2], terminal_sets[i + 1][1])
        for i in range(row_break, len(terminal_sets) - 1):
            add_conductor(diagram, terminal_sets[i][2], terminal_sets[i + 1][1])

    table_end = 0.0
    if page.table_rows:
        if page.blocks and len(page.blocks) > 5:
            raise ValueError(f"E-{page_no:02d} cannot combine a two-row block diagram with a schedule")
        columns, per_col, x_step, table_start, row_step, font_size = table_layout(len(page.table_rows), bool(page.blocks))
        for idx, row in enumerate(page.table_rows):
            col = idx // per_col
            pos = idx % per_col
            add_input(inputs, 40 + col * x_step, table_start + pos * row_step, row, size=font_size, color="#111827")
        table_end = table_start + (per_col - 1) * row_step

    if page.blocks and page.table_rows:
        note_start = max(335.0, table_end + 25.0)
    elif page.blocks:
        note_start = 335.0
    elif page.table_rows:
        note_start = min(420.0, table_end + 25.0)
    else:
        note_start = 85.0
    for idx, note in enumerate(page.notes[:5]):
        add_input(inputs, 45, note_start + idx * 17, note, size=4.6, color="#7c2d12" if "OPEN" in note or "PROVISIONAL" in note else "#374151", bold="OPEN" in note)
    add_input(inputs, 38, 451, NOTICE, size=5.0, color="#b91c1c", bold=True)
    add_input(inputs, 38, 466, SAFETY, size=3.4, color="#b91c1c", bold=True)


def io_rows(rows: Iterable[dict[str, str]], terminals_by_signal: dict[str, list[dict[str, str]]]) -> list[str]:
    result = []
    for row in rows:
        terminals = terminals_by_signal.get(row["symbol"], [])
        term = terminals[0]["terminal"] if terminals else "SPARE/NO FIELD TERM"
        cable = terminals[0]["cable_id"] if terminals else "-"
        core = terminals[0]["core"] if terminals else "-"
        result.append(
            f"{row['address']:<10} {row['module']}/CH{row['channel']:<4} {row['symbol']:<29} {row['device']:<7} {term:<9} {cable}/{core}"
        )
    return result


def terminal_rows(rows: Iterable[dict[str, str]]) -> list[str]:
    return [
        f"{r['terminal']:<8} {r['signal']:<27} {r['cable_id'] or '-':<5}/{r['core'] or '-':<3} {r['plc_address'] or '-':<9} {r['potential']:<18} {r['wire_no']}"
        for r in rows
    ]


def build_pages(data: dict[str, list[dict[str, str]]]) -> list[Page]:
    bom = data["bom"]
    bom_by_tag = {r["tag"]: r for r in bom}
    plc = data["plc_io"]
    terminals = data["terminal_plan"]
    terminals_by_signal: dict[str, list[dict[str, str]]] = {}
    for row in terminals:
        terminals_by_signal.setdefault(row["signal"], []).append(row)
    directions = {d: [r for r in plc if r["direction"] == d] for d in ["DI", "DO", "AI", "HSC"]}
    hardware = {r["tag"]: r for r in data["siemens_hardware"]}
    network = data["network_nodes"]

    def b(kind: str, tag: str, description: str | None = None, detail: str = "") -> Block:
        row = bom_by_tag.get(tag, {})
        desc = description or row.get("description") or tag
        return Block(kind, designation(tag, bom_by_tag), clean_text(desc), clean_text(detail))

    pages: list[Page] = [
        Page("Cover and controlled revision status", notes=[
            PROJECT_TITLE,
            "Selected architecture: CPU 1511-1 PN, local S7-1500 I/O, MTP700 Unified, two G120C PN drives and non-safety NVIDIA inspection.",
            "Native source generated from the controlled Revision-D.1 schedules and first validated with QElectroTech 0.100.0.",
            "OPEN: site supply, fault current, motor data, cable routes, ambient, enclosure duty and qualified safety engineering.",
        ]),
        Page("Drawing index", table_rows=[]),
        Page("Design basis, legend and reference designations", blocks=[
            b("protection", "-QS100", "Main isolation"), b("plc", "-A100", "PLC/controller"),
            b("sensor", "-FT100", "Field instrument"), b("actuator", "-YV100", "Solenoid actuator"),
            b("terminal", "-X100..-X199", "Terminal family"),
        ], notes=[
            "Designation form: =FC01+<location>-<tag>; CP01 control panel, FD01 field, OP01 operator and IF01 external capper interface.",
            "Ordinary PNP 24 VDC field sensing; 4-20 mA analog; TM Count pulse channels; PROFINET Standard Telegram 1 for drives.",
            "PROVISIONAL: 400/230 VAC 3P+N+PE 50 Hz TN-S and 24 VDC PELV are design assumptions pending site confirmation.",
        ]),
        Page("Single-line incoming power distribution", blocks=[
            b("power", "-GL100", "Site cable entry", "3P+N+PE assumption"),
            b("protection", "-QS100", "Door-coupled main isolator"),
            b("protection", "-QF100", "Main protective device"),
            b("device", "-PE100", "PE bar and enclosure bonding"),
            b("terminal", "-X0", "Incoming distribution terminals"),
        ], notes=[
            "Functional single-line path only; conductor sizing and protection ratings remain open and are not construction values.",
            "PE is not switched. Bond enclosure, mounting plate, door and equipment PE to PE100 using verified conductors.",
            "OPEN: supply earthing system, prospective fault current, SCCR, selectivity, voltage drop and installation method.",
        ]),
        Page("Main distribution and branch protection", blocks=[
            b("protection", "-QF100", "Main protective device"), b("drive", "-U100", "Conveyor G120C PN"),
            b("drive", "-U101", "Pump G120C PN"), b("power", "-PS100", "24 VDC 20 A supply"),
            b("protection", "-QF110", "24 VDC branch protection"),
        ], notes=[
            "Separate mains/drive routes from 24 VDC control, instrumentation and Ethernet wiring.",
            "Drive input protection, EMC accessories, braking duty and motor cable selections are provisional pending nameplates and vendor coordination.",
        ]),
        Page("24 VDC PELV distribution", blocks=[
            b("power", "-PS100", "24 VDC 20 A supply"), b("protection", "-QF110", "Electronic branch protection"),
            b("plc", "-A100", "PLC and local modules"), b("network", "-SW100", "Managed switch"),
            b("network", "-PC200", "NVIDIA edge compute"),
        ], notes=[
            "Protected branches: PLC/I-O, HMI, relays/solenoids, network/security and vision/lighting; exact channel ratings remain a native design input.",
            "0 V reference and functional-earth/shield paths are controlled separately; do not substitute shield drain for protective earth.",
        ]),
        Page("S7-1500 rack and module allocation", blocks=[
            b("plc", "-A100", hardware["-A100"]["model"], hardware["-A100"]["order_no"]),
            b("plc", "-A101", hardware["-A101"]["model"], hardware["-A101"]["order_no"]),
            b("plc", "-A102", hardware["-A102"]["model"], hardware["-A102"]["order_no"]),
            b("plc", "-A103", hardware["-A103"]["model"], hardware["-A103"]["order_no"]),
            b("plc", "-A104", hardware["-A104"]["model"], hardware["-A104"]["order_no"]),
        ], notes=[
            "Rack order: CPU, TM Count, DI, DQ, AI. Memory card, rail, front connectors and load-group wiring require native TIA confirmation.",
            "CPU baseline FS03/FW4.0 is a controlled assumption; delivered hardware state and exact V20 catalog compatibility remain open.",
        ]),
        Page("PLC digital inputs I0.0-I1.7", table_rows=io_rows(directions["DI"][:16], terminals_by_signal)),
        Page("PLC digital inputs I2.0-I3.7 and spares", table_rows=io_rows(directions["DI"][16:], terminals_by_signal)),
        Page("PLC digital outputs Q0.0-Q1.7", table_rows=io_rows(directions["DO"][:16], terminals_by_signal)),
        Page("PLC digital outputs Q2.0-Q3.7 and spares", table_rows=io_rows(directions["DO"][16:], terminals_by_signal)),
        Page("Analog inputs and shield termination", table_rows=io_rows(directions["AI"], terminals_by_signal), notes=[
            "FT100/FT101 are 4-20 mA channels; overall shields/drains terminate at SC100 on the panel end only unless the final EMC study requires otherwise.",
            "AI spare channels are uncommitted. Final MANA grouping, transmitter isolation and fault-range behavior require native configuration.",
        ]),
        Page("TM Count high-speed pulse inputs", table_rows=io_rows(directions["HSC"], terminals_by_signal), blocks=[
            b("sensor", "-FT100", "Flowmeter pulse channel 1", "C021 core 4 to TM1.CH0.A"),
            b("plc", "-A101", "TM Count 2x24V", "CH0 A / CH1 A"),
            b("sensor", "-FT101", "Flowmeter pulse channel 2", "C022 core 4 to TM1.CH1.A"),
        ], notes=[
            "Pulse and 4-20 mA signals are independent diagnostics from each flowmeter; neither substitutes for the other.",
        ]),
        Page("Conveyor G120C power and PROFINET control", blocks=[
            b("protection", "-QF100", "Provisional drive branch protection"), b("drive", "-U100", "G120C PN conveyor drive", "Standard Telegram 1; IW/QW256-259"),
            b("motor", "-M100", "Conveyor motor", "Nameplate and duty open"), b("terminal", "-PE100", "Motor PE/bonding"),
        ], notes=[
            "PLC controls STW1 and speed reference; drive returns ZSW1 and actual speed. No hardwired ordinary run/ready path is claimed.",
            "External STO is conceptual safety scope and is not controlled or credited by the standard PLC.",
        ]),
        Page("Pump G120C power and PROFINET control", blocks=[
            b("protection", "-QF100", "Provisional drive branch protection"), b("drive", "-U101", "G120C PN dosing-pump drive", "Standard Telegram 1; IW/QW260-263"),
            b("motor", "-M101", "Pump motor", "Nameplate and hydraulic duty open"), b("terminal", "-PE100", "Motor PE/bonding"),
        ], notes=[
            "Pump speed, ramps, current limits and overload duty remain provisional until motor and pump nameplates and process duty are supplied.",
            "External STO is conceptual safety scope and is not controlled or credited by the standard PLC.",
        ]),
        Page("Motor cables, PE and shield termination", blocks=[
            b("drive", "-U100", "Conveyor drive"), b("terminal", "-SC100", "360-degree shield-clamp rail"),
            b("motor", "-M100", "Conveyor motor"), b("drive", "-U101", "Pump drive"),
            b("motor", "-M101", "Pump motor"),
        ], notes=[
            "W901 denotes the controlled requirement for shielded VFD motor cables and EMC termination kits; exact cable identifiers and routes remain open.",
            "Maintain short, low-impedance shield terminations and continuous PE. Final routing, ampacity and EMC checks require installed geometry.",
        ]),
        Page("PROFINET and OT network architecture", blocks=[
            b("network", "-FW100", "SCALANCE S615 boundary"), b("network", "-SW100", "SCALANCE XC208 managed switch"),
            b("plc", "-A100", "PLC / OPC UA server"), b("network", "-H100", "MTP700 Unified HMI"),
            b("network", "-PC200", "NVIDIA OPC UA client"),
        ], table_rows=[f"{r['node']:<14} {r['ip']:<18} VLAN {r['vlan']:<8} {r['switch_port']:<14} {r['zone']:<12} {r['role']}" for r in network], notes=[
            "U100 and U101 are PROFINET nodes on the CONTROL VLAN; PC200 remains in QUALITY and never owns hazardous motion commands.",
            "Firewall rules, certificates, NTP, logging and engineering access require site cybersecurity approval.",
        ]),
        Page("HMI and NVIDIA inspection interface", blocks=[
            b("network", "-H100", "MTP700 Unified Comfort"), b("plc", "-A100", "Sequence and interlock authority"),
            b("network", "-PC200", "Non-safety quality inspection"), b("sensor", "-CAM200", "Industrial camera"),
            b("actuator", "-LT200", "Controlled vision lighting"),
        ], notes=[
            "OPC UA transaction uses nonzero session/inspection identity, held request handshake, immutable result publication and exact acknowledgement.",
            "Missing, stale, duplicate, contradictory, uncertain, model-mismatched or timed-out AI data produces deterministic HOLD or reject disposition.",
            "NVIDIA cannot command physical outputs, drives, sequence transitions or bypass PLC interlocks.",
        ]),
        Page("Solenoid valves and interposing relays", blocks=[
            b("plc", "-A103", "DQ 32x24V DC"), b("actuator", "-K202..-K213", "Interposing relay family"),
            b("actuator", "-YV100", "Gate solenoid", "C017"), b("actuator", "-YV101", "Clamp solenoid", "C018"),
            b("actuator", "-YV102", "Fill valve 1 fail closed", "C015"),
            b("actuator", "-YV103", "Fill valve 2 fail closed", "C016"),
        ], notes=[
            "K202-K213 relay coils require D202-D213 suppression. Gate/clamp opposing commands are interlocked in PLC logic.",
            "Fill valves are fail closed; de-energized state is closed. Final coil current and protection coordination remain open.",
        ]),
        Page("Field sensors, flow and level instrumentation", blocks=[
            b("sensor", "-B100", "Air pressure switch"), b("sensor", "-B101", "Product supply permissive"),
            b("sensor", "-B110", "Bottle nest 1"), b("sensor", "-B111", "Bottle nest 2"),
            b("sensor", "-FT100", "Flow channel 1 pulse + 4-20 mA"),
            b("sensor", "-FT101", "Flow channel 2 pulse + 4-20 mA"), b("sensor", "-B120", "Gate open proof"),
            b("sensor", "-B121", "Gate closed proof"), b("sensor", "-B122", "Clamp released proof"),
            b("sensor", "-B123", "Clamp engaged proof"),
        ], notes=[
            "B130/B131 provide fill-valve closed proof; LT200 is vision lighting, not a process-level transmitter.",
            "All ordinary sensing is non-safety unless separately designed and validated by a qualified machinery-safety engineer.",
        ]),
        Page("Stack light, local stations and capper interface", blocks=[
            b("device", "-S100", "Local reset pushbutton", "C013"), b("device", "-S101", "Local controlled-stop pushbutton", "C014"),
            b("actuator", "-H101", "Three-color stack light and sounder", "C019"),
            b("terminal", "-IF140", "Capper ready/busy/complete/fault/request", "C012"),
            b("plc", "-A102", "DI capper/local feedback"), b("plc", "-A103", "DO request/indication"),
        ], notes=[
            "Capper BUSY/COMPLETE is accepted only after a correlated request. Unsolicited status is a deterministic interface fault.",
            "Local stop is a controlled process stop, not an emergency-stop or protective device.",
        ]),
        Page("Terminal strips X100 and X101", table_rows=terminal_rows([r for r in terminals if r["terminal"].startswith(("X100:", "X101:"))])),
        Page("Terminal strips X102/X103, power, common and shields", table_rows=terminal_rows([r for r in terminals if not r["terminal"].startswith(("X100:", "X101:"))])),
        Page("Cable schedule and external field connections", table_rows=[
            f"{r['cable_id']:<5} {r['from_location']:<8} -> {r['to_designation']:<20} {r['cable_type']:<24} cores {r['allocated_cores']}/{r['installed_cores']} {r['shield']:<30} {r['route_zone']}"
            for r in data["cable_schedule"]
        ], notes=[
            "Cable/core identifiers on this folio are copied from the controlled schedule; conductor sizes remain blank pending site and installation data.",
            "C021/C022 instrumentation shields terminate at SC100. Power and VFD motor cables remain open schedule inputs.",
        ]),
        Page("Conceptual safety interface and boundaries", blocks=[
            b("safety", "-S102", "Guard-status monitoring mirror"), b("safety", "-K100", "External safety-interface monitoring contact"),
            b("plc", "-A102", "Ordinary PLC status monitoring only"), b("drive", "-U100", "External STO conceptual interface"),
            b("drive", "-U101", "External STO conceptual interface"),
        ], notes=[
            SAFETY,
            "Standard PLC, HMI and NVIDIA functions receive status only and receive no safety credit.",
            "OPEN: hazard analysis, protective-device selection, reset/restart design, PL/SIL/category determination and validation.",
        ]),
        Page("Spare capacity, BOM coverage and open inputs", table_rows=[
            f"{r['full_designation'] or designation(r['tag'], bom_by_tag):<28} {r['description']:<56} {r['selection_status']}"
            for r in bom
        ], notes=[
            "Controlled spare capacity: 8 DI, 18 DO and 6 AI allocated spares; spare terminals/cores require final allocation and labeling.",
            "OPEN: supply/fault current, motor and pump data, cable routes, conductor sizing, thermal/EMC study, exact PC200 envelope and construction review.",
        ]),
    ]
    pages[1].table_rows = [f"E-{idx:02d}  {page.title}" for idx, page in enumerate(pages, start=1)]
    return pages


def write_element_register(output: Path, data: dict[str, list[dict[str, str]]]) -> None:
    rows: list[dict[str, str]] = []
    for item in data["bom"]:
        rows.append({
            "record_type": "DEVICE",
            "reference": item["full_designation"] or item["tag"],
            "description": item["description"],
            "interface_or_location": item["scope"],
            "controlled_basis": item["basis_or_blocker"],
            "status": item["selection_status"],
        })
    for item in data["terminal_plan"]:
        terminal_reference = f"=FC01+CP01-{item['terminal']}"
        rows.append({
            "record_type": "TERMINAL",
            "reference": terminal_reference,
            "description": f"{item['signal']} - {item['function']}",
            "interface_or_location": f"{item['cable_id']}/{item['core']} -> {item['module']} {item['plc_address']}",
            "controlled_basis": item["potential"],
            "status": item["status"],
        })
    for item in data["cable_schedule"]:
        rows.append({
            "record_type": "CABLE",
            "reference": item["cable_id"],
            "description": f"{item['from_location']} to {item['to_designation']} - {item['cable_type']}",
            "interface_or_location": f"cores {item['core_range']}; {item['route_zone']}",
            "controlled_basis": item["shield"],
            "status": item["status"],
        })
    path = output / "FC01_revision_e_element_register.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["record_type", "reference", "description", "interface_or_location", "controlled_basis", "status"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    data = {
        "bom": read_csv("bom.csv"),
        "plc_io": read_csv("plc_io.csv"),
        "terminal_plan": read_csv("terminal_plan.csv"),
        "cable_schedule": read_csv("cable_schedule.csv"),
        "network_nodes": read_csv("network_nodes.csv"),
        "siemens_hardware": read_csv("siemens_hardware.csv"),
    }
    pages = build_pages(data)
    project = ET.Element("project", {"title": PROJECT_TITLE, "version": "0.100.0"})
    add_project_defaults(project)
    for number, page in enumerate(pages, start=1):
        make_diagram(project, number, page, len(pages))
    add_embedded_collection(project)
    ET.indent(project, space="    ")
    qet = output / QET_NAME
    qet.write_bytes(ET.tostring(project, encoding="utf-8", xml_declaration=False) + b"\n")
    write_element_register(output, data)
    evidence = {
        "release": "Revision E",
        "project": qet.name,
        "generator": "scripts/qet_revision_e.py",
        "byte_authority": "deterministic controlled schedules; historical Revision-A QET not read",
        "page_count": len(pages),
        "element_count": len(project.findall(".//diagram/elements/element")),
        "conductor_count": len(project.findall(".//diagram/conductors/conductor")),
        "qet_sha256": hashlib.sha256(qet.read_bytes()).hexdigest(),
        "native_reopen": "PENDING",
        "native_export": "PENDING",
    }
    (output / "FC01_revision_e_build_evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    evidence = generate(args.output_dir.resolve())
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
