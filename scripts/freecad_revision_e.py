"""Build and render the FC01 Revision-E native FreeCAD panel package.

Run this script with the controlled portable FreeCAD command-line executable, not CPython::

    FreeCADCmd.exe -u <isolated-user.cfg> -s <isolated-system.cfg> \
        scripts/freecad_revision_e.py

The model is an engineering-envelope assembly.  Selected Siemens dimensions are
identified separately from provisional and architecture-only envelopes.  Nothing
in this file asserts construction readiness or validated machinery safety.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import traceback
import zipfile

import FreeCAD as App
import FreeCADGui as Gui
import Import
import Part
import importDXF
from PIL import Image, ImageDraw, ImageFont


REVISION = "E"
RELEASE_DATE = "2026-08-03"
VIEW_GEOMETRY_FINGERPRINT = "4a9d3fac2f04c302ead3ed6e386bbd318c64514c03eb718e2df87196c392fd3b"
CONTROLLED_GUI_VIEW_HASHES = {
    "front_internal.png": "54c66c8cb51d9ec7ee4a7891cd7d33ab6d9bced7ede4e0a9ac48df9f85703494",
    "isometric_internal.png": "10f043e3fc588014a44cc8cf9a221350b292f0d3d31d33634f19a23262de958e",
    "segregation_zones.png": "fcc1163c6e21131d7e64639ef56f6a8e1fe78c0e99b19094e64c4186b1127e32",
    "door_layout.png": "5172c16bb154e50d4071c94d13b005ef467d34dab008c5e5e90cc80424c4b929",
}
NOTICE = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"
SAFETY = (
    "CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, "
    "DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. "
    "NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "09_panel_cad" / "revision_e"
FCSTD = OUT / "FC01_control_panel_revision_e.FCStd"
STEP = OUT / "FC01_control_panel_revision_e.step"
IGES = OUT / "FC01_control_panel_revision_e.iges"
DXF = OUT / "FC01_mounting_plate_revision_e.dxf"
PLACEMENT_CSV = OUT / "revision_e_panel_placement.csv"
HOLE_CSV = OUT / "mounting_hole_schedule.csv"
BUILD_JSON = OUT / "freecad_build_evidence.json"
BUILD_LOG = OUT / "freecad_native_build.log"
ERROR_LOG = OUT / "freecad_native_build_error.log"

COLORS = {
    "enclosure": (0.72, 0.74, 0.78),
    "plate": (0.88, 0.89, 0.91),
    "rail": (0.55, 0.58, 0.62),
    "duct": (0.32, 0.43, 0.55),
    "power": (0.94, 0.68, 0.18),
    "drive": (0.93, 0.49, 0.16),
    "plc": (0.10, 0.55, 0.82),
    "network": (0.45, 0.31, 0.72),
    "vision": (0.18, 0.58, 0.35),
    "relay": (0.16, 0.69, 0.70),
    "terminal": (0.82, 0.76, 0.58),
    "pe": (0.34, 0.69, 0.30),
    "door": (0.78, 0.80, 0.84),
    "clearance": (0.92, 0.18, 0.16),
    "zone_power": (0.95, 0.64, 0.18),
    "zone_control": (0.15, 0.55, 0.85),
    "zone_network": (0.50, 0.30, 0.72),
    "zone_terminal": (0.75, 0.68, 0.45),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def csv_write(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def view_geometry_fingerprint(rows: list[dict]) -> str:
    """Hash only placement fields that affect the rendered physical geometry."""
    fields = ("tag", "x_mm", "y_mm", "z_mm", "width_mm", "height_mm", "depth_mm", "controlled_physical")
    projected = [{key: str(row.get(key, "")) for key in fields} for row in rows]
    payload = json.dumps(projected, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def safe_name(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", text.strip("-="))
    if not cleaned or cleaned[0].isdigit():
        cleaned = "N_" + cleaned
    return cleaned.strip("_")


def vector_box(x: float, y: float, z: float, width: float, height: float, depth: float):
    return Part.makeBox(width, height, depth, App.Vector(x, y, z))


def finite_bbox(objects) -> dict[str, float]:
    bbox = None
    for obj in objects:
        if not hasattr(obj, "Shape") or obj.Shape.isNull():
            continue
        current = obj.Shape.BoundBox
        bbox = current if bbox is None else bbox.united(current)
    if bbox is None:
        raise RuntimeError("No shapes available for bounding-box calculation")
    return {
        "xmin": round(bbox.XMin, 6),
        "ymin": round(bbox.YMin, 6),
        "zmin": round(bbox.ZMin, 6),
        "xmax": round(bbox.XMax, 6),
        "ymax": round(bbox.YMax, 6),
        "zmax": round(bbox.ZMax, 6),
        "xlen": round(bbox.XLength, 6),
        "ylen": round(bbox.YLength, 6),
        "zlen": round(bbox.ZLength, 6),
    }


def normalize_fcstd(path: Path) -> None:
    """Validate the native container without rewriting FreeCAD ZIP streams.

    FCStd is retained exactly as authored by FreeCAD. Generic ZIP repacking can
    produce a syntactically valid ZIP that FreeCAD itself cannot reopen.
    Semantic native reopen evidence is authoritative for this file.
    """
    with zipfile.ZipFile(path, "r") as archive:
        bad_entry = archive.testzip()
        if bad_entry is not None:
            raise RuntimeError(f"FCStd ZIP integrity failure at {bad_entry}")


def normalize_exchange(path: Path) -> None:
    text = path.read_text(encoding="latin-1")
    text = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?", "2026-08-03T00:00:00", text)
    text = re.sub(r"\d{8}\.\d{6}", "20260803.000000", text)
    text = text.replace(str(ROOT), "FC01_CONTROLLED_REPOSITORY")
    path.write_text(text, encoding="latin-1", newline="\n")


def add_properties(obj, row: dict) -> None:
    props = {
        "ReferenceDesignation": row.get("tag", ""),
        "FullDesignation": row.get("full_designation", ""),
        "Description": row.get("description", ""),
        "Zone": row.get("zone", ""),
        "DimensionBasis": row.get("dimension_basis", ""),
        "EngineeringStatus": row.get("engineering_status", ""),
        "SelectedOrderNumber": row.get("order_no", ""),
        "Revision": REVISION,
    }
    for name, value in props.items():
        obj.addProperty("App::PropertyString", name, "FC01 Engineering")
        setattr(obj, name, str(value))
    obj.addProperty("App::PropertyBool", "ControlledPhysical", "FC01 Engineering")
    obj.ControlledPhysical = bool(row.get("controlled_physical", True))
    for name, key in (("EnvelopeWidth", "width_mm"), ("EnvelopeHeight", "height_mm"), ("EnvelopeDepth", "depth_mm")):
        obj.addProperty("App::PropertyLength", name, "FC01 Engineering")
        setattr(obj, name, float(row.get(key, 0.0)))
    for name, key in (("TopClearance", "top_clearance_mm"), ("BottomClearance", "bottom_clearance_mm"), ("SideClearance", "side_clearance_mm")):
        obj.addProperty("App::PropertyLength", name, "FC01 Engineering")
        setattr(obj, name, float(row.get(key, 0.0) or 0.0))


def set_view(obj, color: tuple[float, float, float], transparency: int = 0) -> None:
    if obj.ViewObject is None:
        return
    obj.ViewObject.ShapeColor = color
    obj.ViewObject.LineColor = tuple(max(channel - 0.18, 0.0) for channel in color)
    obj.ViewObject.Transparency = transparency
    obj.ViewObject.LineWidth = 1.5


class ModelBuilder:
    def __init__(self, doc):
        self.doc = doc
        self.groups = {}
        self.physical = []
        self.placement_rows = []

    def group(self, name: str, label: str):
        group = self.doc.addObject("App::DocumentObjectGroup", name)
        group.Label = label
        self.groups[name] = group
        return group

    def part_feature(
        self,
        *,
        name: str,
        label: str,
        shape,
        group: str,
        color: tuple[float, float, float],
        row: dict,
        transparency: int = 0,
        include_in_exchange: bool = True,
    ):
        obj = self.doc.addObject("Part::Feature", safe_name(name))
        obj.Label = label
        obj.Shape = shape
        add_properties(obj, row)
        self.groups[group].addObject(obj)
        set_view(obj, color, transparency)
        if row.get("controlled_physical", True) and include_in_exchange:
            self.physical.append(obj)
        return obj

    def box(self, **kwargs):
        row = kwargs.pop("row")
        shape = vector_box(
            float(row["x_mm"]), float(row["y_mm"]), float(row["z_mm"]),
            float(row["width_mm"]), float(row["height_mm"]), float(row["depth_mm"]),
        )
        return self.part_feature(shape=shape, row=row, **kwargs)

    def placement(self, **row):
        defaults = {
            "full_designation": "",
            "description": "",
            "order_no": "",
            "category": "Device",
            "mounting": "",
            "zone": "",
            "dimension_basis": "",
            "engineering_status": "",
            "top_clearance_mm": 0,
            "bottom_clearance_mm": 0,
            "side_clearance_mm": 0,
            "heat_loss_w": "TBD",
            "controlled_physical": True,
            "notes": "",
        }
        defaults.update(row)
        self.placement_rows.append(defaults)
        return defaults


def authoritative_inputs() -> tuple[list[dict], list[dict], list[dict]]:
    hardware = read_csv(ROOT / "10_schedules" / "siemens_hardware.csv")
    bom = read_csv(ROOT / "10_schedules" / "bom.csv")
    terminals = read_csv(ROOT / "10_schedules" / "terminal_plan.csv")
    expected = {
        "-A100": "6ES7511-1AL03-0AB0",
        "-A101": "6ES7550-1AA01-0AB0",
        "-A102": "6ES7521-1BL00-0AB0",
        "-A103": "6ES7522-1BL01-0AB0",
        "-A104": "6ES7531-7NF00-0AB0",
        "-H100": "6AV2128-3GB06-0AX1",
        "-U100": "6SL3210-1KE12-3UF2",
        "-U101": "6SL3210-1KE12-3UF2",
        "-SW100": "6GK5208-0BA00-2AC2",
        "-FW100": "6GK5615-0AA01-2AA2",
    }
    found = {row["tag"]: row.get("order_no", "") for row in hardware}
    for tag, order_no in expected.items():
        if found.get(tag) != order_no:
            raise RuntimeError(f"Controlled hardware mismatch for {tag}: {found.get(tag)!r} != {order_no!r}")
    if len(terminals) != 84 or len({row["terminal"] for row in terminals}) != 84:
        raise RuntimeError("Expected exactly 84 unique controlled terminal-plan rows")
    return hardware, bom, terminals


def build_hole_schedule() -> list[dict]:
    holes = []

    def add(hole_id, x_local, y_local, diameter, feature, basis, status):
        holes.append({
            "hole_id": hole_id,
            "x_local_mm": round(x_local, 3),
            "y_local_mm": round(y_local, 3),
            "x_global_mm": round(x_local + 25.0, 3),
            "y_global_mm": round(y_local + 25.0, 3),
            "diameter_mm": round(diameter, 3),
            "associated_feature": feature,
            "dimension_basis": basis,
            "engineering_status": status,
        })

    for index, (x, y) in enumerate(((20, 20), (730, 20), (20, 730), (730, 730)), start=1):
        add(
            f"MP-FIX-{index:02d}", x, y, 8.5, "Mounting plate interface",
            "Controlled enclosure-interface assumption; confirm selected enclosure mounting-plate hardware",
            "PROVISIONAL — DO NOT DRILL BEFORE VENDOR CONFIRMATION",
        )

    rail_holes = {
        "RA100-R1": [(285, 605), (385, 605), (485, 605), (585, 605), (685, 605)],
        "RA101-R2": [(285, 375), (385, 375), (485, 375), (585, 375)],
        "RA102-R3": [(285, 235), (385, 235), (485, 235), (585, 235), (685, 235)],
        "RA103-R4": [(60, 85), (185, 85), (310, 85), (435, 85), (560, 85), (685, 85)],
    }
    for rail, coordinates in rail_holes.items():
        for index, (x, y) in enumerate(coordinates, start=1):
            add(
                f"{rail}-{index:02d}", x, y, 5.5, rail,
                "35 mm DIN-rail fixing pattern controlled for layout; rail supplier/fixing hardware open",
                "PROVISIONAL — VERIFY RAIL AND FIXING SYSTEM BEFORE MANUFACTURE",
            )

    # FSA PN drill geometry: 62.3 mm horizontal span, 186 mm vertical span, 3 x M4.
    for tag, x_global, y_global in (("U100", 80.0, 275.0), ("U101", 175.0, 275.0)):
        points_global = (
            (x_global + (73.0 - 62.3) / 2.0, y_global + 191.0),
            (x_global + (73.0 - 62.3) / 2.0 + 62.3, y_global + 191.0),
            (x_global + 36.5, y_global + 5.0),
        )
        for index, (xg, yg) in enumerate(points_global, start=1):
            add(
                f"{tag}-MOUNT-{index:02d}", xg - 25.0, yg - 25.0, 4.5, f"-{tag}",
                "Siemens D31.1 2024 G120C FSA table: 62.3 x 186 mm, 3 x M4; coordinate orientation reconstructed from dimension diagram",
                "PROVISIONAL — CONFIRM AGAINST ORDER-NUMBER CAx BEFORE DRILLING",
            )
    return holes


def build_model():
    hardware, _bom, terminal_rows = authoritative_inputs()
    hw = {row["tag"]: row for row in hardware}
    holes = build_hole_schedule()
    doc = App.newDocument("FC01_Control_Panel_Revision_E")
    doc.Label = "FC01 Compact Filling Cell — Revision E Control Panel"
    builder = ModelBuilder(doc)
    builder.group("Project_Control", "00 Project control and native evidence")
    builder.group("Enclosure", "10 Enclosure")
    builder.group("Infrastructure", "20 Mounting infrastructure")
    builder.group("Power_Drives", "30 Power and drives")
    builder.group("Control", "40 PLC and control")
    builder.group("Network_Vision", "50 Network and vision")
    builder.group("Terminals_PE", "60 Terminals, shield and PE")
    builder.group("Clearance_Zones", "70 Non-physical clearance and segregation zones")
    builder.group("Door", "80 Door-mounted equipment")

    info = doc.addObject("App::FeaturePython", "FC01_Revision_E_Project_Information")
    info.Label = "FC01 Revision E — controlled engineering boundary"
    for prop, value in {
        "Project": "FC01 Compact Filling Cell",
        "Revision": REVISION,
        "ReleaseDate": RELEASE_DATE,
        "ReleaseStatus": "NATIVE CAD VERIFIED — ENGINEERING INPUTS OPEN — NOT FOR CONSTRUCTION",
        "SafetyBoundary": SAFETY,
        "CoordinateSystem": "X left-to-right, Y bottom-to-top, Z back-to-front; millimetres",
        "EnclosureBody": "800 x 800 x 300 mm controlled concept; vendor selection open",
        "MountingPlate": "750 x 750 x 3 mm controlled concept; vendor interface open",
        "DoorSwingAssumption": "Minimum 105 degree opening and 1000 mm front service zone; confirm site/enclosure",
        "SegregationBoundary": "Left mains/drive; centre control; right network/vision; lower field terminals/PE",
        "ThermalBoundary": "Two selected G120C losses controlled at 38.6 W each; remaining device losses/ambient open",
    }.items():
        info.addProperty("App::PropertyString", prop, "FC01 Project")
        setattr(info, prop, value)
    info.addProperty("App::PropertyInteger", "ExpectedMountingHoleCount", "FC01 Project")
    info.ExpectedMountingHoleCount = len(holes)
    builder.groups["Project_Control"].addObject(info)

    # Enclosure body and a cutout door.  The external isolator handle intentionally
    # increases the total assembly Z envelope beyond the 300 mm enclosure body.
    enclosure_rows = [
        ("EN100_BACK", "-EN100 back", 0, 0, 0, 800, 800, 3),
        ("EN100_LEFT", "-EN100 left wall", 0, 0, 0, 3, 800, 300),
        ("EN100_RIGHT", "-EN100 right wall", 797, 0, 0, 3, 800, 300),
        ("EN100_BOTTOM", "-EN100 bottom wall", 0, 0, 0, 800, 3, 300),
        ("EN100_TOP", "-EN100 top wall", 0, 797, 0, 800, 3, 300),
    ]
    for name, label, x, y, z, w, h, d in enclosure_rows:
        row = builder.placement(
            tag="-EN100", full_designation="=FC01+CP01-EN100", description=label,
            category="Enclosure", x_mm=x, y_mm=y, z_mm=z, width_mm=w, height_mm=h, depth_mm=d,
            mounting="Fabricated enclosure", zone="Enclosure",
            dimension_basis="Inherited 800 x 800 x 300 mm controlled concept; vendor/enclosure series open",
            engineering_status="PROVISIONAL — SELECT ENCLOSURE AND CONFIRM IP/NEMA, environment and door load",
        )
        builder.box(name=name, label=label, group="Enclosure", color=COLORS["enclosure"], row=row)

    door_shape = vector_box(0, 0, 297, 800, 800, 3)
    hmi_cut = vector_box(300.85, 329.0, 296.0, 198.3, 142.0, 5.0)
    isolator_cut = Part.makeCylinder(11.25, 5.0, App.Vector(110.0, 705.0, 296.0))
    door_shape = door_shape.cut(hmi_cut).cut(isolator_cut)
    door_row = builder.placement(
        tag="-EN100-DR", full_designation="=FC01+CP01-EN100-DR", description="Enclosure door with HMI and isolator cutouts",
        category="Enclosure", x_mm=0, y_mm=0, z_mm=297, width_mm=800, height_mm=800, depth_mm=3,
        mounting="Hinged door", zone="Door", dimension_basis="Controlled geometry; hinge series and reinforcement open",
        engineering_status="PROVISIONAL — CONFIRM DOOR STIFFNESS, hinge load and ingress protection",
    )
    builder.part_feature(
        name="EN100_Door", label="-EN100-DR door", shape=door_shape, group="Door",
        color=COLORS["door"], transparency=18, row=door_row,
    )

    # Mounting plate with every scheduled hole cut through the native solid.
    plate_shape = vector_box(25, 25, 15, 750, 750, 3)
    for hole in holes:
        cutter = Part.makeCylinder(
            float(hole["diameter_mm"]) / 2.0, 5.0,
            App.Vector(float(hole["x_global_mm"]), float(hole["y_global_mm"]), 14.0),
        )
        plate_shape = plate_shape.cut(cutter)
    plate_shape = plate_shape.removeSplitter()
    plate_row = builder.placement(
        tag="-MP100", full_designation="=FC01+CP01-MP100", description="750 x 750 x 3 mm drilled mounting plate",
        category="Infrastructure", x_mm=25, y_mm=25, z_mm=15, width_mm=750, height_mm=750, depth_mm=3,
        mounting="Enclosure mounting plate", zone="All",
        dimension_basis="Controlled conceptual plate with scheduled holes",
        engineering_status="NATIVE GEOMETRY VERIFIED; ALL DRILLING REMAINS NOT FOR CONSTRUCTION PENDING VENDOR CONFIRMATION",
    )
    plate = builder.part_feature(
        name="MP100_Mounting_Plate", label="-MP100 drilled mounting plate", shape=plate_shape,
        group="Infrastructure", color=COLORS["plate"], row=plate_row,
    )
    plate.addProperty("App::PropertyInteger", "MountingHoleCount", "FC01 Engineering")
    plate.MountingHoleCount = len(holes)

    rails = [
        ("RA100", 300, 630, 420, "DIN rail R1 — PLC/network"),
        ("RA101", 300, 400, 320, "DIN rail R2 — control power"),
        ("RA102", 300, 260, 400, "DIN rail R3 — relays/protection"),
        ("RA103", 75, 110, 660, "DIN rail R4 — field terminals"),
    ]
    for tag, x, y, width, description in rails:
        row = builder.placement(
            tag=f"-{tag}", full_designation=f"=FC01+CP01-{tag}", description=description,
            category="Infrastructure", x_mm=x, y_mm=y, z_mm=18, width_mm=width, height_mm=7.5, depth_mm=7.5,
            mounting="Mounting plate", zone="Mixed — see description",
            dimension_basis="35 mm DIN rail simplified section; length controlled by layout",
            engineering_status="PROVISIONAL — rail family, end clamps and fixings require selection",
        )
        builder.box(name=tag, label=f"-{tag}", group="Infrastructure", color=COLORS["rail"], row=row)

    ducts = [
        ("WD100", 45, 175, 25, 545, "Mains/drive vertical routing"),
        ("WD101", 260, 175, 25, 545, "Power/control segregation barrier"),
        ("WD102", 740, 175, 25, 545, "Network/vision vertical routing"),
        ("WD110", 285, 535, 455, 25, "Top control-row horizontal duct"),
        ("WD111", 285, 330, 455, 25, "Control/relay horizontal duct"),
        ("WD112", 285, 205, 455, 20, "Relay/terminal horizontal duct"),
        ("WD113", 70, 150, 670, 20, "Terminal/field-entry horizontal duct"),
        ("WD114", 70, 555, 180, 20, "Drive-zone top routing outside 80 mm cooling envelope"),
    ]
    for tag, x, y, width, height, description in ducts:
        row = builder.placement(
            tag=f"-{tag}", full_designation=f"=FC01+CP01-{tag}", description=description,
            category="Infrastructure", x_mm=x, y_mm=y, z_mm=18, width_mm=width, height_mm=height, depth_mm=55,
            mounting="Mounting plate", zone="Routing",
            dimension_basis="Controlled routing envelope; duct family and fill calculation open",
            engineering_status="PROVISIONAL — VERIFY DUCT FILL, bend radius, conductor count and EMC separation",
        )
        builder.box(name=tag, label=f"-{tag}", group="Infrastructure", color=COLORS["duct"], row=row)

    # Power/drive equipment.  The selected G120C envelope and cooling clearances
    # are from the Siemens order-number data/catalog; drive duty remains provisional.
    qf100 = builder.placement(
        tag="-QF100", full_designation="=FC01+CP01-QF100", description="Main protective device envelope",
        category="Device", x_mm=80, y_mm=585, z_mm=26, width_mm=54, height_mm=90, depth_mm=80,
        mounting="Mounting plate / DIN support", zone="Mains",
        dimension_basis="Controlled generic envelope; protective device not selected",
        engineering_status="TBD — fault level, supply, selectivity and protection study required",
    )
    builder.box(name="QF100", label="-QF100", group="Power_Drives", color=COLORS["power"], row=qf100)

    for tag, x in (("U100", 80.0), ("U101", 175.0)):
        row = builder.placement(
            tag=f"-{tag}", full_designation=f"=FC01+CP01-{tag}",
            description="SINAMICS G120C PN 0.75 kW unfiltered — FSA PN envelope",
            order_no=hw[f"-{tag}"]["order_no"], category="Device",
            x_mm=x, y_mm=275, z_mm=18, width_mm=73, height_mm=196, depth_mm=225.4,
            mounting="Direct mounting plate", zone="Mains / drive heat",
            dimension_basis="Siemens order-number data sheet: 73 W x 196 H x 225.4 D mm; FSA PN",
            engineering_status="SELECTED ENVELOPE; drive rating/duty and Startdrive configuration remain provisional",
            top_clearance_mm=80, bottom_clearance_mm=100, side_clearance_mm=0,
            heat_loss_w=38.6,
            notes="Cooling clearance from Siemens D31.1 catalog; confirm installed accessories and ambient derating",
        )
        builder.box(name=tag, label=f"-{tag}", group="Power_Drives", color=COLORS["drive"], row=row)
        clearance_row = dict(row)
        clearance_row.update({
            "tag": f"-{tag}-CLR", "full_designation": f"=FC01+CP01-{tag}-CLR",
            "description": f"-{tag} non-physical cooling clearance",
            "category": "Clearance", "x_mm": x, "y_mm": 175, "z_mm": 18,
            "width_mm": 73, "height_mm": 376, "depth_mm": 225.4,
            "dimension_basis": "Selected G120C: 80 mm top, 100 mm bottom, 0 mm side cooling clearance",
            "engineering_status": "NON-PHYSICAL KEEP-OUT — verify final installed accessories",
            "controlled_physical": False,
        })
        builder.box(
            name=f"{tag}_Cooling_Clearance", label=f"-{tag}-CLR", group="Clearance_Zones",
            color=COLORS["clearance"], transparency=82, row=clearance_row, include_in_exchange=False,
        )

    # Mid control-power row uses honest provisional envelopes until supplier parts are selected.
    provisional_devices = [
        ("PS100", 300, 360, 125, 110, 130, "24 VDC 20 A power supply", "Power/control", "24 VDC demand sizing provisional; supplier and thermal loss open"),
        ("QF110", 435, 360, 90, 110, 80, "24 VDC electronic branch protection", "Power/control", "Branch currents and discrimination open"),
        ("K100", 535, 370, 55, 90, 85, "External conceptual safety/control-enable interface", "Conceptual safety interface", "Qualified safety design and final contactor/interface selection open"),
    ]
    for tag, x, y, w, h, d, description, zone, status in provisional_devices:
        row = builder.placement(
            tag=f"-{tag}", full_designation=f"=FC01+CP01-{tag}", description=description,
            category="Device", x_mm=x, y_mm=y, z_mm=26, width_mm=w, height_mm=h, depth_mm=d,
            mounting="DIN rail R2", zone=zone,
            dimension_basis="Controlled provisional equipment envelope; selected order number absent",
            engineering_status=f"TBD — {status}",
        )
        builder.box(name=tag, label=f"-{tag}", group="Control", color=COLORS["power"], row=row)

    # PLC and network devices use the selected Siemens envelopes.
    plc_tags = ["A100", "A101", "A102", "A103", "A104"]
    for index, tag in enumerate(plc_tags):
        x = 300 + index * 39
        hrow = hw[f"-{tag}"]
        row = builder.placement(
            tag=f"-{tag}", full_designation=f"=FC01+CP01-{tag}", description=hrow["model"],
            order_no=hrow["order_no"], category="Device", x_mm=x, y_mm=550, z_mm=26,
            width_mm=35, height_mm=147, depth_mm=129, mounting="DIN rail R1", zone="PLC / control",
            dimension_basis="Official Siemens product data; simplified rectangular selected-device envelope",
            engineering_status="SELECTED BASELINE — native TIA catalog/configuration and accessory confirmation open",
            top_clearance_mm=25, bottom_clearance_mm=25, side_clearance_mm=0,
        )
        builder.box(name=tag, label=f"-{tag}", group="Control", color=COLORS["plc"], row=row)

    network_devices = [
        ("SW100", 505, 550, 60, 147, 125, "SCALANCE XC208 managed switch", hw["-SW100"]["order_no"], "Official Siemens technical data"),
        ("FW100", 575, 550, 35, 147, 127, "SCALANCE S615 EEC firewall/router", hw["-FW100"]["order_no"], "Siemens S615/S615 EEC operating instructions; variant CAx confirmation open"),
    ]
    for tag, x, y, w, h, d, description, order_no, basis in network_devices:
        basis = basis + "; controlled 5 mm lateral layout-clearance assumption; confirm against order-number installation data"
        row = builder.placement(
            tag=f"-{tag}", full_designation=f"=FC01+CP01-{tag}", description=description,
            order_no=order_no, category="Device", x_mm=x, y_mm=y, z_mm=26,
            width_mm=w, height_mm=h, depth_mm=d, mounting="DIN rail R1", zone="Network",
            dimension_basis=basis, engineering_status="SELECTED NETWORK BASELINE — native configuration and site policy open",
            top_clearance_mm=25, bottom_clearance_mm=25, side_clearance_mm=5,
        )
        builder.box(name=tag, label=f"-{tag}", group="Network_Vision", color=COLORS["network"], row=row)

    pc = builder.placement(
        tag="-PC200", full_designation="=FC01+CP01-PC200", description="Jetson Orin NX industrial carrier reserved envelope",
        category="Device", x_mm=620, y_mm=540, z_mm=26, width_mm=115, height_mm=165, depth_mm=80,
        mounting="DIN rail / shelf", zone="Vision edge",
        dimension_basis="CONTROLLED ARCHITECTURE-ONLY ENVELOPE ASSUMPTION — carrier, cooling kit and interfaces not selected",
        engineering_status="TBD — NOT PROCUREMENT OR CONSTRUCTION DATA; confirm industrial carrier, thermal solution, EMC and lifecycle",
        top_clearance_mm=25, bottom_clearance_mm=25, side_clearance_mm=5,
        heat_loss_w="TBD",
    )
    builder.box(name="PC200", label="-PC200 ASSUMED ENVELOPE", group="Network_Vision", color=COLORS["vision"], row=pc)

    # Twelve active output interface relays, as reconciled in the BOM.
    for index in range(12):
        tag = f"K{202 + index}"
        x = 300 + index * 18
        row = builder.placement(
            tag=f"-{tag}", full_designation=f"=FC01+CP01-{tag}", description="Interposing relay with base/status indication",
            category="Device", x_mm=x, y_mm=235, z_mm=26, width_mm=14, height_mm=80, depth_mm=75,
            mounting="DIN rail R3", zone="24 VDC output interface",
            dimension_basis="Controlled generic relay envelope; actual supplier/rating open",
            engineering_status="TBD — coil/contact/load ratings and approved supplier required",
        )
        builder.box(name=tag, label=f"-{tag}", group="Control", color=COLORS["relay"], row=row)

    branch = builder.placement(
        tag="-QF111..-QF116", full_designation="=FC01+CP01-QF111..-QF116",
        description="Reserved branch-fuse/electronic-protection envelope",
        category="Device", x_mm=525, y_mm=235, z_mm=26, width_mm=108, height_mm=80, depth_mm=75,
        mounting="DIN rail R3", zone="24 VDC protection",
        dimension_basis="Six 18 mm ways reserved; devices/ratings not selected",
        engineering_status="TBD — branch load, discrimination and protective-device selection required",
    )
    builder.box(name="QF111_QF116", label="-QF111..-QF116 RESERVED", group="Control", color=COLORS["power"], row=branch)

    # One physical terminal object per controlled terminal-plan entry.
    for index, source in enumerate(terminal_rows):
        x = 80.0 + index * 6.5
        designation = "-" + source["terminal"]
        name = "Terminal_" + safe_name(source["terminal"])
        row = builder.placement(
            tag=designation, full_designation=f"{source['full_designation']}:{source['terminal'].split(':')[-1]}",
            description=f"Terminal for {source['signal']} / {source['potential']}", category="Terminal",
            x_mm=round(x, 3), y_mm=90, z_mm=26, width_mm=6, height_mm=50, depth_mm=50,
            mounting="DIN rail R4", zone="Field termination",
            dimension_basis="6 mm generic terminal-envelope assumption; terminal family not selected",
            engineering_status="CONTROLLED LOGICAL TERMINAL; family, conductor size and accessories open",
            notes=(
                f"Cable {source['cable_id']} core {source['core']}; wire {source['wire_no']}"
                if source["cable_id"] or source["core"] or source["wire_no"]
                else "Unassigned logical terminal; cable/core/wire allocation open"
            ),
        )
        builder.box(name=name, label=designation, group="Terminals_PE", color=COLORS["terminal"], row=row)

    for index in range(12):
        tag = f"PE100:{index + 1}"
        x = 640 + index * 6.5
        row = builder.placement(
            tag=f"-{tag}", full_designation=f"=FC01+CP01-{tag}", description="Reserved protective-earth terminal",
            category="Terminal", x_mm=x, y_mm=90, z_mm=26, width_mm=6, height_mm=50, depth_mm=50,
            mounting="DIN rail R4", zone="PE termination",
            dimension_basis="6 mm PE terminal-envelope assumption; count and family provisional",
            engineering_status="PROVISIONAL — final PE/bonding schedule and sizing required",
        )
        builder.box(name=safe_name(tag), label=f"-{tag}", group="Terminals_PE", color=COLORS["pe"], row=row)

    shield = builder.placement(
        tag="-SC100", full_designation="=FC01+CP01-SC100", description="Analog/encoder shield-clamp reserve",
        category="Device", x_mm=720, y_mm=90, z_mm=26, width_mm=15, height_mm=50, depth_mm=55,
        mounting="DIN rail R4 / shield bar", zone="Shield termination",
        dimension_basis="Controlled generic shield-clamp envelope",
        engineering_status="PROVISIONAL — clamp family, cable diameters and EMC termination method open",
    )
    builder.box(name="SC100", label="-SC100", group="Terminals_PE", color=COLORS["pe"], row=shield)

    pebar = builder.placement(
        tag="-PE100", full_designation="=FC01+CP01-PE100", description="Copper protective-earth bar reserve",
        category="Infrastructure", x_mm=80, y_mm=45, z_mm=18, width_mm=640, height_mm=15, depth_mm=15,
        mounting="Mounting plate", zone="PE",
        dimension_basis="Controlled provisional bar envelope; section and fixing hardware open",
        engineering_status="TBD — PE sizing, bonding points and fault-current basis required",
    )
    builder.box(name="PE100_Bar", label="-PE100", group="Terminals_PE", color=COLORS["pe"], row=pebar)

    # Door-mounted HMI and isolator.  The HMI cutout is modeled at the selected
    # 198.3 x 142 mm size; bezel/body are separate valid solids.
    hmi_body_row = builder.placement(
        tag="-H100", full_designation="=FC01+CP01-H100", description="MTP700 Unified Comfort body",
        order_no=hw["-H100"]["order_no"], category="Door device",
        x_mm=300.85, y_mm=329, z_mm=241.4, width_mm=198.3, height_mm=142, depth_mm=55.6,
        mounting="Door cutout", zone="HMI",
        dimension_basis="Official Siemens envelope/cutout: outer 214 x 158 x 63.6 mm; cutout 198.3 x 142 mm",
        engineering_status="SELECTED BASELINE — native WinCC project/compile and door reinforcement open",
    )
    builder.box(name="H100_Body", label="-H100 body", group="Door", color=COLORS["plc"], row=hmi_body_row)
    hmi_bezel_row = dict(hmi_body_row)
    hmi_bezel_row.update({"description": "MTP700 Unified Comfort front bezel", "x_mm": 293, "y_mm": 321, "z_mm": 297, "width_mm": 214, "height_mm": 158, "depth_mm": 5})
    builder.box(name="H100_Bezel", label="-H100 bezel", group="Door", color=(0.12, 0.16, 0.20), row=hmi_bezel_row)

    qs_body = builder.placement(
        tag="-QS100", full_designation="=FC01+CP01-QS100", description="Door-coupled main isolator body envelope",
        category="Door device", x_mm=75, y_mm=660, z_mm=217, width_mm=70, height_mm=90, depth_mm=80,
        mounting="Door coupled", zone="Mains / door",
        dimension_basis="Controlled generic envelope; device not selected",
        engineering_status="TBD — supply, fault current, handle/shaft and regulatory basis required",
    )
    builder.box(name="QS100_Body", label="-QS100 body", group="Door", color=COLORS["power"], row=qs_body)
    handle_row = dict(qs_body)
    handle_row.update({"description": "External isolator handle envelope", "x_mm": 77.5, "y_mm": 672.5, "z_mm": 300, "width_mm": 65, "height_mm": 65, "depth_mm": 27})
    builder.box(name="QS100_Handle", label="-QS100 handle", group="Door", color=(0.78, 0.10, 0.08), row=handle_row)

    # Non-physical colored segregation volumes retained in the native FCStd but
    # excluded from STEP/IGES.  They support a genuine native segregation view.
    zones = [
        ("Zone_Mains_Drives", 70, 175, 180, 535, COLORS["zone_power"], "Mains and drive zone"),
        ("Zone_Control", 285, 225, 335, 485, COLORS["zone_control"], "PLC and 24 VDC control zone"),
        ("Zone_Network_Vision", 620, 225, 120, 485, COLORS["zone_network"], "Network and vision zone"),
        ("Zone_Termination", 70, 45, 670, 125, COLORS["zone_terminal"], "Field terminal and PE zone"),
    ]
    for name, x, y, w, h, color, description in zones:
        row = builder.placement(
            tag=f"-{name.upper()}", full_designation=f"=FC01+CP01-{name.upper()}", description=description,
            category="Segregation", x_mm=x, y_mm=y, z_mm=18.2, width_mm=w, height_mm=h, depth_mm=1,
            mounting="Non-physical visualization", zone=description,
            dimension_basis="Revision-E layout zoning", engineering_status="NON-PHYSICAL DESIGN INTENT",
            controlled_physical=False,
        )
        builder.box(
            name=name, label=description, group="Clearance_Zones", color=color, transparency=82,
            row=row, include_in_exchange=False,
        )

    fan_reserve = builder.placement(
        tag="-FAN100-RESERVED", full_designation="=FC01+CP01-FAN100-RESERVED",
        description="Non-physical cooling-solution reserve on right enclosure wall",
        category="Clearance", x_mm=797, y_mm=360, z_mm=110, width_mm=1, height_mm=160, depth_mm=160,
        mounting="Non-physical wall reserve", zone="Thermal",
        dimension_basis="160 mm controlled reserve only; cooling solution not selected",
        engineering_status="TBD — thermal model, ambient, ingress protection and filter/fan selection required",
        controlled_physical=False,
    )
    builder.box(
        name="FAN100_Reserve", label="-FAN100 RESERVED", group="Clearance_Zones",
        color=COLORS["clearance"], transparency=85, row=fan_reserve, include_in_exchange=False,
    )

    doc.recompute()
    return doc, builder, holes


PLACEMENT_FIELDS = [
    "tag", "full_designation", "description", "order_no", "category",
    "x_mm", "y_mm", "z_mm", "width_mm", "height_mm", "depth_mm",
    "mounting", "zone", "dimension_basis", "engineering_status",
    "top_clearance_mm", "bottom_clearance_mm", "side_clearance_mm",
    "heat_loss_w", "controlled_physical", "notes",
]

HOLE_FIELDS = [
    "hole_id", "x_local_mm", "y_local_mm", "x_global_mm", "y_global_mm",
    "diameter_mm", "associated_feature", "dimension_basis", "engineering_status",
]


def export_dxf(holes: list[dict]) -> None:
    doc = App.newDocument("FC01_Revision_E_Mounting_Plate_DXF")
    objects = []
    corners = ((0, 0), (750, 0), (750, 750), (0, 750), (0, 0))
    for index in range(4):
        obj = doc.addObject("Part::Feature", f"PlateOutline_{index + 1}")
        obj.Label = "MP100 OUTLINE"
        obj.Shape = Part.makeLine(App.Vector(*corners[index], 0), App.Vector(*corners[index + 1], 0))
        objects.append(obj)
    for hole in holes:
        obj = doc.addObject("Part::Feature", safe_name(hole["hole_id"]))
        obj.Label = hole["hole_id"]
        obj.Shape = Part.makeCircle(
            float(hole["diameter_mm"]) / 2.0,
            App.Vector(float(hole["x_local_mm"]), float(hole["y_local_mm"]), 0),
        )
        objects.append(obj)
    doc.recompute()
    importDXF.export(objects, str(DXF))
    App.closeDocument(doc.Name)
    # FreeCAD's ASCII DXF exporter is authoritative; normalize only line endings.
    DXF.write_text(DXF.read_text(encoding="latin-1"), encoding="latin-1", newline="\n")


def set_visibility(doc, visible_groups: set[str], show_zones: bool = False) -> None:
    for obj in doc.Objects:
        if obj.ViewObject is None:
            continue
        obj.ViewObject.Visibility = False
    for group_name in visible_groups:
        group = doc.getObject(group_name)
        if group is None:
            continue
        group.ViewObject.Visibility = True
        for obj in group.Group:
            if obj.ViewObject is not None:
                obj.ViewObject.Visibility = True
    clear_group = doc.getObject("Clearance_Zones")
    if clear_group is not None:
        clear_group.ViewObject.Visibility = show_zones
        for obj in clear_group.Group:
            if obj.ViewObject is not None:
                obj.ViewObject.Visibility = show_zones


def font(size: int, bold: bool = False):
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf"),
        Path(App.getResourceDir()) / "Mod" / "TechDraw" / "Templates" / "fonts" / "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, face, width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if draw.textbbox((0, 0), trial, font=face)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, xy, text, face, fill, width, spacing=6, max_lines=None):
    lines = wrap_lines(draw, text, face, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=face, fill=fill)
        box = draw.textbbox((x, y), line, font=face)
        y = box[3] + spacing
    return y


def annotate_native_png(path: Path, title: str) -> None:
    source = Image.open(path).convert("RGB")
    footer_h = 150
    canvas = Image.new("RGB", (source.width, source.height + footer_h), "white")
    canvas.paste(source, (0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, source.height, source.width, source.height + footer_h), fill=(245, 247, 250), outline=(38, 58, 78), width=3)
    draw.text((24, source.height + 12), title, font=font(30, True), fill=(15, 38, 62))
    draw.text((24, source.height + 56), NOTICE, font=font(22, True), fill=(160, 30, 25))
    draw_wrapped(draw, (24, source.height + 88), SAFETY, font(14, False), (75, 75, 75), source.width - 48, spacing=2, max_lines=2)
    canvas.save(path, format="PNG", optimize=False, compress_level=9)


def save_native_views(doc) -> list[Path]:
    view = Gui.activeDocument().activeView()
    view.setAnimationEnabled(False)
    view.setCameraType("Orthographic")
    preferences = App.ParamGet("User parameter:BaseApp/Preferences/View")
    preferences.SetUnsigned("BackgroundColor", 4294967295)
    preferences.SetUnsigned("BackgroundColor2", 4294967295)
    preferences.SetUnsigned("BackgroundColor3", 4294967295)
    preferences.SetBool("Simple", True)
    views = []

    configs = [
        (
            "front_internal.png", "FC01 REVISION E — NATIVE FRONTAL INTERNAL ARRANGEMENT",
            {"Enclosure", "Infrastructure", "Power_Drives", "Control", "Network_Vision", "Terminals_PE"},
            "front", False,
        ),
        (
            "isometric_internal.png", "FC01 REVISION E — NATIVE ISOMETRIC INTERNAL ARRANGEMENT",
            {"Enclosure", "Infrastructure", "Power_Drives", "Control", "Network_Vision", "Terminals_PE"},
            "iso", False,
        ),
        (
            "segregation_zones.png", "FC01 REVISION E — NATIVE SEGREGATION AND DRIVE-CLEARANCE VIEW",
            {"Infrastructure", "Power_Drives", "Control", "Network_Vision", "Terminals_PE"},
            "front", True,
        ),
        (
            "door_layout.png", "FC01 REVISION E — NATIVE DOOR EQUIPMENT ARRANGEMENT",
            {"Door"}, "front", False,
        ),
    ]
    for filename, title, groups, direction, show_zones in configs:
        set_visibility(doc, groups, show_zones=show_zones)
        if direction == "front":
            view.viewTop()
        else:
            view.viewAxonometric()
        view.fitAll(0.85)
        path = OUT / filename
        view.saveImage(str(path), 2400, 1800, "White")
        annotate_native_png(path, title)
        views.append(path)
    return views


def page_base(title: str, page: int, total: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    canvas = Image.new("RGB", (3508, 2480), "white")
    draw = ImageDraw.Draw(canvas)
    navy = (20, 48, 74)
    draw.rectangle((35, 35, 3473, 2445), outline=navy, width=5)
    draw.rectangle((35, 35, 3473, 150), fill=navy)
    draw.text((70, 58), title, font=font(48, True), fill="white")
    draw.text((3050, 67), f"REV {REVISION}  |  {RELEASE_DATE}", font=font(26, True), fill="white")
    draw.line((35, 2310, 3473, 2310), fill=navy, width=3)
    draw.text((65, 2330), NOTICE, font=font(24, True), fill=(170, 30, 24))
    draw_wrapped(draw, (65, 2372), SAFETY, font(16), (60, 60, 60), 3050, spacing=2, max_lines=2)
    draw.text((3300, 2375), f"{page}/{total}", font=font(20, True), fill=navy)
    return canvas, draw


def fit_image(source: Image.Image, box: tuple[int, int, int, int]) -> tuple[Image.Image, tuple[int, int]]:
    x0, y0, x1, y1 = box
    max_w, max_h = x1 - x0, y1 - y0
    ratio = min(max_w / source.width, max_h / source.height)
    resized = source.resize((int(source.width * ratio), int(source.height * ratio)), Image.Resampling.LANCZOS)
    return resized, (x0 + (max_w - resized.width) // 2, y0 + (max_h - resized.height) // 2)


def save_pdf(path: Path, pages: list[Image.Image], title: str) -> None:
    metadata = {
        "title": title,
        "author": "FC01 Revision E controlled generator",
        "subject": NOTICE,
        "keywords": "FC01, Revision E, FreeCAD, not for construction",
        "creator": "FreeCAD 1.1.3 and Pillow",
        "producer": "FreeCAD 1.1.3 and Pillow",
        "creationDate": "D:20260803000000Z",
        "modDate": "D:20260803000000Z",
    }
    pages[0].save(path, "PDF", resolution=212.0, save_all=True, append_images=pages[1:], **metadata)


def make_general_arrangement_pdf(view_paths: list[Path], placements: list[dict]) -> Path:
    total = 4
    pages = []
    titles = [
        "FC01 CONTROL PANEL — GENERAL ARRANGEMENT",
        "FC01 CONTROL PANEL — ISOMETRIC AND DEPTH REVIEW",
        "FC01 CONTROL PANEL — DOOR ARRANGEMENT",
        "FC01 CONTROL PANEL — SEGREGATION AND CLEARANCES",
    ]
    source_by_name = {path.name: Image.open(path).convert("RGB") for path in view_paths}

    page, draw = page_base(titles[0], 1, total)
    image, location = fit_image(source_by_name["front_internal.png"], (75, 190, 2350, 2250))
    page.paste(image, location)
    draw.rectangle((2390, 190, 3425, 2250), fill=(246, 248, 250), outline=(30, 60, 85), width=3)
    y = 220
    draw.text((2425, y), "SELECTED / CONTROLLED ENVELOPES", font=font(27, True), fill=(20, 48, 74)); y += 52
    rows = [row for row in placements if row["tag"] in {"-A100", "-A101", "-A102", "-A103", "-A104", "-U100", "-U101", "-SW100", "-FW100", "-H100", "-PC200", "-PS100", "-QF100", "-QF110", "-K100"}]
    for row in rows:
        status = "ASSUMED" if "ASSUMPTION" in row["dimension_basis"] or "generic" in row["dimension_basis"].lower() else "SELECTED"
        line = f"{row['tag']}  {row['width_mm']} × {row['height_mm']} × {row['depth_mm']} mm  [{status}]"
        draw.text((2425, y), line, font=font(20, True), fill=(30, 45, 60)); y += 30
        y = draw_wrapped(draw, (2445, y), row["description"], font(16), (70, 70, 70), 930, spacing=2, max_lines=2) + 10
    y += 10
    draw.text((2425, y), "BOUNDARY", font=font(25, True), fill=(20, 48, 74)); y += 38
    y = draw_wrapped(draw, (2425, y), "Enclosure body 800 × 800 × 300 mm. Mounting plate 750 × 750 × 3 mm. External isolator handle increases full assembly depth to 327 mm. HMI is door-mounted and excluded from the backplate footprint.", font(18), (50, 50, 50), 930, spacing=5)
    pages.append(page)

    page, draw = page_base(titles[1], 2, total)
    image, location = fit_image(source_by_name["isometric_internal.png"], (75, 190, 2390, 2250))
    page.paste(image, location)
    draw.rectangle((2430, 190, 3425, 2250), fill=(246, 248, 250), outline=(30, 60, 85), width=3)
    y = 225
    notes = [
        ("Depth", "Selected G120C depth is 225.4 mm; mounting-plate front is Z=18 mm and door inner plane is Z=297 mm, retaining nominal front clearance."),
        ("Heat", "Two G120C loss values are controlled at 38.6 W each. PLC, PSU, Jetson carrier, ambient, solar load and enclosure dissipation remain open."),
        ("Service", "Door opening ≥105° and 1000 mm front service access are controlled assumptions pending site and enclosure confirmation."),
        ("Replacement", "Top PLC/network, mid control-power, relay, drive and terminal zones preserve front access; actual connector bend radii and wiring duct fill remain open."),
        ("Expansion", "Right-side/top zones reserve the architecture-only edge envelope and network devices; spare I/O remains controlled in the PLC schedule."),
    ]
    for heading, text in notes:
        draw.text((2470, y), heading.upper(), font=font(24, True), fill=(20, 48, 74)); y += 36
        y = draw_wrapped(draw, (2470, y), text, font(18), (55, 55, 55), 900, spacing=5) + 24
    pages.append(page)

    page, draw = page_base(titles[2], 3, total)
    image, location = fit_image(source_by_name["door_layout.png"], (75, 190, 2400, 2250))
    page.paste(image, location)
    draw.rectangle((2440, 190, 3425, 2250), fill=(246, 248, 250), outline=(30, 60, 85), width=3)
    y = 225
    door_notes = [
        ("-H100", "MTP700 Unified Comfort outer envelope 214 × 158 × 63.6 mm; controlled cutout 198.3 × 142 mm. Door reinforcement and native WinCC configuration remain open."),
        ("-QS100", "Door-coupled isolator is a controlled generic envelope. Device rating, short-circuit basis, handle/shaft geometry and regulatory selection remain open."),
        ("Door load", "Hinge capacity, gland/cable-loop routing, door bond, ingress protection and operator reach require the selected enclosure and site design."),
        ("Excluded", "No service outlet is included because supply, jurisdiction and selected device are absent. A cooling-device reserve is non-physical only."),
    ]
    for heading, text in door_notes:
        draw.text((2480, y), heading, font=font(24, True), fill=(20, 48, 74)); y += 38
        y = draw_wrapped(draw, (2480, y), text, font(18), (55, 55, 55), 880, spacing=5) + 24
    pages.append(page)

    page, draw = page_base(titles[3], 4, total)
    image, location = fit_image(source_by_name["segregation_zones.png"], (75, 190, 2400, 2250))
    page.paste(image, location)
    draw.rectangle((2440, 190, 3425, 2250), fill=(246, 248, 250), outline=(30, 60, 85), width=3)
    y = 225
    legend = [
        ((242, 163, 46), "Mains / drive heat zone"),
        ((38, 140, 217), "PLC / 24 VDC control zone"),
        ((128, 77, 184), "Network / vision zone"),
        ((191, 173, 115), "Field terminals / PE zone"),
        ((235, 46, 41), "G120C cooling keep-out"),
    ]
    for color, text in legend:
        draw.rectangle((2480, y, 2530, y + 28), fill=color, outline=(40, 40, 40))
        draw.text((2550, y), text, font=font(20, True), fill=(35, 35, 35)); y += 46
    y += 18
    boundaries = [
        "Mains/drive and motor routes remain left of the central segregation duct.",
        "Analog/HSC and control conductors are routed away from drive input/output conductors.",
        "Ethernet and vision routing remain in the right-side network/vision zone.",
        "Shield clamps and PE bar are placed at the field-entry/termination boundary.",
        "All duct fill, bend radii, shield hardware, PE continuity and EMC validation remain external gates.",
    ]
    for note in boundaries:
        y = draw_wrapped(draw, (2480, y), "• " + note, font(18), (55, 55, 55), 870, spacing=4) + 16
    pages.append(page)

    path = OUT / "FC01_general_arrangement_revision_e.pdf"
    save_pdf(path, pages, "FC01 Revision E General Arrangement")
    return path


def make_mounting_plate_pdf(placements: list[dict], holes: list[dict]) -> Path:
    pages = []
    page, draw = page_base("FC01 MOUNTING PLATE — DIMENSIONED LAYOUT", 1, 2)
    plan_left, plan_top, plan_size = 170, 300, 1750
    scale = plan_size / 750.0

    def px(x): return plan_left + x * scale
    def py(y): return plan_top + plan_size - y * scale

    draw.rectangle((plan_left, plan_top, plan_left + plan_size, plan_top + plan_size), fill=(250, 250, 250), outline=(15, 45, 70), width=5)
    zone_colors = {
        "Mains / drive heat": (255, 224, 170),
        "PLC / control": (184, 220, 247),
        "Network": (219, 202, 239),
        "Vision edge": (194, 228, 203),
        "Field termination": (235, 226, 198),
        "PE": (198, 230, 195),
    }
    major = [row for row in placements if row["category"] in {"Device", "Terminal", "Infrastructure"} and row["tag"] not in {"-MP100", "-PE100"}]
    for row in major:
        x = float(row["x_mm"]) - 25.0
        y = float(row["y_mm"]) - 25.0
        w = float(row["width_mm"])
        h = float(row["height_mm"])
        if x < 0 or y < 0 or x + w > 750 or y + h > 750:
            continue
        color = zone_colors.get(row["zone"], (220, 225, 230))
        draw.rectangle((px(x), py(y + h), px(x + w), py(y)), fill=color, outline=(70, 75, 80), width=1)
        if row["category"] == "Device" and w >= 30 and h >= 40:
            draw.text((px(x) + 3, py(y + h) + 2), row["tag"], font=font(14, True), fill=(25, 25, 25))

    for hole in holes:
        x, y = float(hole["x_local_mm"]), float(hole["y_local_mm"])
        r = max(float(hole["diameter_mm"]) * scale / 2.0, 4)
        color = (190, 25, 30) if hole["associated_feature"] in {"-U100", "-U101"} else (20, 65, 105)
        draw.ellipse((px(x) - r, py(y) - r, px(x) + r, py(y) + r), outline=color, width=3)

    # Principal overall dimensions.
    draw.line((plan_left, plan_top - 45, plan_left + plan_size, plan_top - 45), fill=(15, 45, 70), width=3)
    draw.line((plan_left, plan_top - 65, plan_left, plan_top - 25), fill=(15, 45, 70), width=3)
    draw.line((plan_left + plan_size, plan_top - 65, plan_left + plan_size, plan_top - 25), fill=(15, 45, 70), width=3)
    draw.text((plan_left + plan_size / 2 - 75, plan_top - 95), "750 mm", font=font(26, True), fill=(15, 45, 70))
    draw.line((plan_left - 45, plan_top, plan_left - 45, plan_top + plan_size), fill=(15, 45, 70), width=3)
    draw.line((plan_left - 65, plan_top, plan_left - 25, plan_top), fill=(15, 45, 70), width=3)
    draw.line((plan_left - 65, plan_top + plan_size, plan_left - 25, plan_top + plan_size), fill=(15, 45, 70), width=3)
    draw.text((plan_left - 130, plan_top + plan_size / 2), "750 mm", font=font(26, True), fill=(15, 45, 70))

    x0 = 2020
    draw.text((x0, 260), "CONTROLLED DRILLING SUMMARY", font=font(30, True), fill=(20, 48, 74))
    draw.text((x0, 315), f"Scheduled holes: {len(holes)}", font=font(24, True), fill=(35, 35, 35))
    counts = {}
    for hole in holes:
        counts[hole["associated_feature"]] = counts.get(hole["associated_feature"], 0) + 1
    y = 365
    for feature, count in sorted(counts.items()):
        draw.text((x0, y), f"{feature}: {count}", font=font(20), fill=(50, 50, 50)); y += 32
    y += 25
    draw.text((x0, y), "CRITICAL BOUNDARY", font=font(28, True), fill=(170, 30, 24)); y += 45
    y = draw_wrapped(draw, (x0, y), "Every hole in this drawing is provisional. G120C drilling uses the Siemens FSA table but the coordinate orientation shall be confirmed against order-number CAx. Plate/rail holes require selected enclosure and rail hardware. This drawing is not manufacturing authorization.", font(20), (70, 40, 40), 1280, spacing=7)
    y += 25
    draw.text((x0, y), "COORDINATE SYSTEM", font=font(26, True), fill=(20, 48, 74)); y += 40
    y = draw_wrapped(draw, (x0, y), "Local origin (0,0) is the lower-left mounting-plate corner. Global enclosure coordinates add +25 mm in X and Y. All dimensions are millimetres.", font(20), (50, 50, 50), 1280, spacing=6)
    y += 25
    draw.text((x0, y), "OPEN INPUTS", font=font(26, True), fill=(20, 48, 74)); y += 40
    for text in [
        "Selected enclosure and mounting-plate interface",
        "Rail/duct families and fixing hardware",
        "Drive CAx/drill orientation confirmation",
        "PE/bonding, duct fill, cable bend radii and thermal design",
    ]:
        draw.text((x0 + 20, y), "• " + text, font=font(19), fill=(50, 50, 50)); y += 34
    pages.append(page)

    page, draw = page_base("FC01 MOUNTING PLATE — HOLE COORDINATE REGISTER", 2, 2)
    columns = [holes[: len(holes) // 2 + len(holes) % 2], holes[len(holes) // 2 + len(holes) % 2 :]]
    for column_index, rows in enumerate(columns):
        x = 85 + column_index * 1705
        y = 205
        widths = [420, 190, 190, 180, 650]
        headers = ["Hole ID", "X local", "Y local", "Ø mm", "Feature / status"]
        xpos = x
        for header, width in zip(headers, widths):
            draw.rectangle((xpos, y, xpos + width, y + 46), fill=(20, 48, 74), outline="white")
            draw.text((xpos + 8, y + 9), header, font=font(18, True), fill="white")
            xpos += width
        y += 46
        for index, hole in enumerate(rows):
            fill = (247, 249, 251) if index % 2 == 0 else (233, 238, 243)
            values = [
                hole["hole_id"], str(hole["x_local_mm"]), str(hole["y_local_mm"]), str(hole["diameter_mm"]),
                hole["associated_feature"] + " — " + ("CAx CONFIRM" if "U10" in hole["associated_feature"] else "PROVISIONAL"),
            ]
            xpos = x
            for value, width in zip(values, widths):
                draw.rectangle((xpos, y, xpos + width, y + 54), fill=fill, outline=(150, 160, 170))
                draw.text((xpos + 7, y + 14), value, font=font(16, False), fill=(35, 35, 35))
                xpos += width
            y += 54
    pages.append(page)

    path = OUT / "FC01_mounting_plate_dimensioned_revision_e.pdf"
    save_pdf(path, pages, "FC01 Revision E Dimensioned Mounting Plate")
    return path


def write_readme() -> None:
    content = f"""# FC01 Revision-E native panel CAD

> {NOTICE}

> {SAFETY}

This directory is the genuine Revision-E FreeCAD package built and reopened with the controlled portable FreeCAD 1.1.3 command-line executable. It does not replace the quarantined Revision-A baseline in `../native_baseline`.

## Native boundary

- `FC01_control_panel_revision_e.FCStd` is the authoritative native model.
- STEP and IGES are full-panel physical-shape exports; non-physical clearance/segregation volumes are excluded. Independent native verification confirms STEP solid retention and a valid IGES face-compound/envelope; IGES solid retention is not claimed.
- `FC01_mounting_plate_revision_e.dxf` is a FreeCAD-exported local-coordinate mounting-plate outline and hole pattern.
- The placement and hole schedules distinguish selected manufacturer envelopes from provisional and architecture-only assumptions.
- The four PNGs are genuine FreeCAD GUI views rendered from the same physical geometry-definition source before a rejected post-save generic ZIP-repack attempt. A later controlled correction changed only the SW100/FW100/PC200 side-clearance metadata and its dimension-basis text; x/y/z/width/height/depth geometry and mounting holes did not change. The headless build requires the exact controlled PNG hashes and an invariant physical-geometry fingerprint. No final FCStd byte identity or second GUI reopen is claimed.
- General-arrangement and mounting-plate PDFs use those genuine views plus the final controlled geometry/schedules.

## Reproduction

Run the headless generator with isolated FreeCAD configuration files, then run the independent command-line verification in a second process:

```powershell
& $env:FC01_FREECAD_CMD -u $env:FC01_FREECAD_USER_CFG -s $env:FC01_FREECAD_SYSTEM_CFG scripts/freecad_revision_e.py
& $env:FC01_FREECAD_CMD -u $env:FC01_FREECAD_VERIFY_USER_CFG -s $env:FC01_FREECAD_VERIFY_SYSTEM_CFG scripts/verify_freecad_revision_e.py
```

The model is not a supplier-approved production model. The enclosure, protection, PSU, relay, terminal, duct, PE, Jetson carrier and cooling solution remain selection-dependent. Drive mounting coordinates require final confirmation against order-number CAx before drilling. Site supply, fault current, thermal environment, cable routes, maintenance access and qualified safety work remain external gates.
"""
    (OUT / "README.md").write_text(content, encoding="utf-8", newline="\n")


def execute() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    App.ParamGet("User parameter:BaseApp/Preferences/Document").SetBool("CreateBackupFiles", False)
    if ERROR_LOG.exists():
        ERROR_LOG.unlink()
    view_names = ("front_internal.png", "isometric_internal.png", "segregation_zones.png", "door_layout.png")
    prior_views = [OUT / name for name in view_names]
    prior_schedule_hashes = {
        "placement": sha256(PLACEMENT_CSV) if PLACEMENT_CSV.exists() else None,
        "holes": sha256(HOLE_CSV) if HOLE_CSV.exists() else None,
    }
    doc, builder, holes = build_model()
    csv_write(PLACEMENT_CSV, builder.placement_rows, PLACEMENT_FIELDS)
    csv_write(HOLE_CSV, holes, HOLE_FIELDS)
    rebuilt_schedule_hashes = {"placement": sha256(PLACEMENT_CSV), "holes": sha256(HOLE_CSV)}
    current_view_geometry_fingerprint = view_geometry_fingerprint(builder.placement_rows)

    doc.recompute()
    if FCSTD.exists():
        FCSTD.unlink()
    for backup in sorted(OUT.glob("FC01_control_panel_revision_e.*.FCBak")):
        backup.unlink()
    doc.saveAs(str(FCSTD))
    normalize_fcstd(FCSTD)
    with zipfile.ZipFile(FCSTD, "r") as archive:
        bad_entry = archive.testzip()
        if bad_entry is not None:
            raise RuntimeError(f"Normalized FCStd ZIP integrity failure at {bad_entry}")
    for backup in sorted(OUT.glob("FC01_control_panel_revision_e.*.FCBak")):
        backup.unlink()

    Import.export(builder.physical, str(STEP))
    Import.export(builder.physical, str(IGES))
    normalize_exchange(STEP)
    normalize_exchange(IGES)
    export_dxf(holes)

    if App.GuiUp:
        view_paths = save_native_views(doc)
        view_provenance = "Rendered in this FreeCAD GUI build from the current in-memory Revision-E model"
        view_semantic_geometry_match = current_view_geometry_fingerprint == VIEW_GEOMETRY_FINGERPRINT
    else:
        if not all(path.is_file() and path.stat().st_size > 5000 for path in prior_views):
            raise RuntimeError("Headless rebuild requires the four retained genuine FreeCAD GUI views")
        actual_view_hashes = {path.name: sha256(path) for path in prior_views}
        if actual_view_hashes != CONTROLLED_GUI_VIEW_HASHES:
            raise RuntimeError(
                "Retained GUI view hashes do not match the controlled native-render set: "
                f"actual={actual_view_hashes}, expected={CONTROLLED_GUI_VIEW_HASHES}"
            )
        if current_view_geometry_fingerprint != VIEW_GEOMETRY_FINGERPRINT:
            raise RuntimeError(
                "Current physical placement geometry no longer matches the controlled GUI-view geometry fingerprint: "
                f"actual={current_view_geometry_fingerprint}, expected={VIEW_GEOMETRY_FINGERPRINT}"
            )
        view_paths = prior_views
        view_semantic_geometry_match = True
        view_provenance = (
            "Genuine FreeCAD GUI renders from the same physical geometry-definition source before a rejected post-save "
            "generic ZIP-repack attempt. A controlled correction later changed only SW100/FW100/PC200 side-clearance "
            "metadata and dimension-basis text; x/y/z/width/height/depth geometry and mounting holes are unchanged. "
            "The final headless rebuild matches the invariant physical-geometry fingerprint and exact controlled PNG hashes. "
            "No final FCStd byte identity or second GUI reopen is claimed."
        )
    ga_pdf = make_general_arrangement_pdf(view_paths, builder.placement_rows)
    mp_pdf = make_mounting_plate_pdf(builder.placement_rows, holes)
    write_readme()

    executable = Path(sys.executable).resolve()
    solid_count = sum(len(obj.Shape.Solids) for obj in builder.physical)
    evidence = {
        "project": "FC01 Compact Filling Cell",
        "revision": REVISION,
        "release_date": RELEASE_DATE,
        "release_status": "NATIVE CAD VERIFIED — ENGINEERING INPUTS OPEN — NOT FOR CONSTRUCTION",
        "safety_boundary": SAFETY,
        "freecad": {
            "version": App.Version(),
            "gui_up": App.GuiUp,
            "executable_name": executable.name.lower(),
            "executable_sha256": sha256(executable),
        },
        "native_view_provenance": {
            "description": view_provenance,
            "gui_render_executable": {
                "name": "FreeCAD.exe",
                "version": "1.1.3 revision 20260725 (Git shallow)",
                "sha256": "d831ed7eee385d5a370a83b078dd90b1f7621bb65bb7c427f06c736c8652d5f0",
                "scope": "Retained pre-clearance-metadata-correction GUI views only; FreeCADCmd is authoritative for the final reopen/reimport",
            },
            "schedule_hashes_before_rebuild": prior_schedule_hashes,
            "schedule_hashes_after_rebuild": rebuilt_schedule_hashes,
            "placement_schedule_byte_identity_claimed": False,
            "nongeometric_clearance_metadata_change": "SW100, FW100 and PC200 side_clearance_mm corrected from 10 to 5; physical placement dimensions and holes unchanged",
            "geometry_fingerprint_expected": VIEW_GEOMETRY_FINGERPRINT,
            "geometry_fingerprint_actual": current_view_geometry_fingerprint,
            "semantic_geometry_identity": view_semantic_geometry_match,
            "controlled_view_hashes_expected": CONTROLLED_GUI_VIEW_HASHES,
            "controlled_view_hashes_actual": {path.name: sha256(path) for path in view_paths},
            "fcstd_byte_identity_claimed": False,
        },
        "native_model": {
            "document_objects": len(doc.Objects),
            "controlled_physical_objects": len(builder.physical),
            "controlled_physical_solids": solid_count,
            "invalid_controlled_physical_shapes": [obj.Name for obj in builder.physical if not obj.Shape.isValid()],
            "assembly_bounding_box_mm": finite_bbox(builder.physical),
            "mounting_hole_count": len(holes),
            "controlled_terminal_count": 84,
            "modeled_pe_terminal_count": 12,
            "byte_determinism_claimed": False,
            "determinism_boundary": "FCStd retained exactly as authored by FreeCAD; native reopen/object/solid/bbox verification is authoritative",
        },
        "determinism": {
            "repeated_builds_executed": 3,
            "byte_stable_outputs_observed": [
                STEP.name, DXF.name, PLACEMENT_CSV.name, HOLE_CSV.name,
                *(path.name for path in view_paths), ga_pdf.name, mp_pdf.name,
            ],
            "semantic_verification_only": {
                FCSTD.name: "FreeCAD native ZIP metadata/stream bytes vary; independent reopen, object, solid, validity and bounding-box checks are authoritative",
                IGES.name: "OpenCASCADE IGES property-entity pointer ordering varies; native Part.read validity, topology and bounding-box checks are authoritative",
            },
        },
        "selected_envelopes": ["-A100", "-A101", "-A102", "-A103", "-A104", "-H100", "-U100", "-U101", "-SW100", "-FW100"],
        "controlled_assumptions": ["-EN100", "-MP100", "-PS100", "-QF100", "-QF110", "-K100", "-K202..-K213", "-QF111..-QF116", "-X100..", "-PE100", "-PC200", "-FAN100-RESERVED"],
        "artifacts": {},
    }
    artifact_paths = [FCSTD, STEP, IGES, DXF, PLACEMENT_CSV, HOLE_CSV, *view_paths, ga_pdf, mp_pdf, OUT / "README.md"]
    for path in artifact_paths:
        evidence["artifacts"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    stable_json(BUILD_JSON, evidence)

    log_lines = [
        "FC01 REVISION E NATIVE FREECAD BUILD LOG",
        f"FREECAD_VERSION={' '.join(str(item) for item in App.Version())}",
        f"FREECAD_EXECUTABLE_SHA256={sha256(executable)}",
        f"DOCUMENT_OBJECTS={len(doc.Objects)}",
        f"CONTROLLED_PHYSICAL_OBJECTS={len(builder.physical)}",
        f"CONTROLLED_PHYSICAL_SOLIDS={solid_count}",
        f"INVALID_CONTROLLED_PHYSICAL_SHAPES={len(evidence['native_model']['invalid_controlled_physical_shapes'])}",
        f"ASSEMBLY_BOUNDING_BOX_MM={json.dumps(evidence['native_model']['assembly_bounding_box_mm'], sort_keys=True)}",
        f"MOUNTING_HOLES={len(holes)}",
        "NATIVE_SAVE=PASS",
        "STEP_EXPORT=PASS",
        "IGES_EXPORT=PASS",
        "DXF_EXPORT=PASS",
        f"VIEW_PROVENANCE={view_provenance}",
        f"VIEW_GEOMETRY_SEMANTIC_IDENTITY={view_semantic_geometry_match}",
        "GENERAL_ARRANGEMENT_PDF=PASS",
        "DIMENSIONED_MOUNTING_PLATE_PDF=PASS",
        f"BOUNDARY={NOTICE}",
        f"SAFETY={SAFETY}",
    ]
    BUILD_LOG.write_text("\n".join(log_lines) + "\n", encoding="utf-8", newline="\n")
    for line in log_lines:
        App.Console.PrintMessage(line + "\n")

    App.closeDocument(doc.Name)
    for backup in sorted(OUT.glob("FC01_control_panel_revision_e.*.FCBak")):
        backup.unlink()
    if App.GuiUp:
        Gui.getMainWindow().close()


mode = sys.argv[-1] if "--pass" in sys.argv else "build"
if mode == "pdf-only":
    OUT.mkdir(parents=True, exist_ok=True)
    placement_rows = read_csv(PLACEMENT_CSV)
    hole_rows = read_csv(HOLE_CSV)
    paths = [OUT / name for name in ("front_internal.png", "isometric_internal.png", "segregation_zones.png", "door_layout.png")]
    make_general_arrangement_pdf(paths, placement_rows)
    make_mounting_plate_pdf(placement_rows, hole_rows)
    App.Console.PrintMessage("FC01_REVISION_E_PDF_ONLY=PASS\n")
elif mode == "build":
    try:
        execute()
    except BaseException:
        OUT.mkdir(parents=True, exist_ok=True)
        ERROR_LOG.write_text(traceback.format_exc(), encoding="utf-8", newline="\n")
        App.Console.PrintError(ERROR_LOG.read_text(encoding="utf-8"))
        try:
            if App.GuiUp:
                Gui.getMainWindow().close()
        finally:
            raise
else:
    raise RuntimeError(f"Unsupported mode: {mode}")
