"""Independent native verification for the FC01 Revision-E FreeCAD package.

Run with FreeCADCmd.exe.  This script reopens the FCStd, reimports STEP, IGES
and DXF into new documents, compares geometry and schedules, and writes stable
verification evidence.  It does not use the generator's in-memory model.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True

import FreeCAD as App
import Import
import Part
import importDXF


REVISION = "E"
NOTICE = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"
SAFETY = (
    "CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, "
    "DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. "
    "NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
)
ROOT = Path(os.environ["FC01_PROJECT_ROOT"]).resolve() if os.environ.get("FC01_PROJECT_ROOT") else Path(__file__).resolve().parents[1]
OUT = ROOT / "09_panel_cad" / "revision_e"
FCSTD = OUT / "FC01_control_panel_revision_e.FCStd"
STEP = OUT / "FC01_control_panel_revision_e.step"
IGES = OUT / "FC01_control_panel_revision_e.iges"
DXF = OUT / "FC01_mounting_plate_revision_e.dxf"
PLACEMENT_CSV = OUT / "revision_e_panel_placement.csv"
HOLE_CSV = OUT / "mounting_hole_schedule.csv"
BUILD_JSON = OUT / "freecad_build_evidence.json"
REPORT_JSON = OUT / "native_verification.json"
REPORT_MD = OUT / "freecad_verification_report.md"
VERIFY_LOG = OUT / "freecad_native_verify.log"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def stable_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def shape_objects(doc):
    # STEP import also creates coordinate axes and datum planes whose Shape is
    # reported non-null but has no vertices and an infinite OpenCASCADE box.
    # They are document structure, not imported product geometry.
    return [
        obj for obj in doc.Objects
        if hasattr(obj, "Shape") and not obj.Shape.isNull() and len(obj.Shape.Vertexes) > 0
    ]


def controlled_physical_objects(doc):
    return [obj for obj in shape_objects(doc) if hasattr(obj, "ControlledPhysical") and bool(obj.ControlledPhysical)]


def bbox_summary(objects) -> dict[str, float]:
    bbox = None
    for obj in objects:
        current = obj.Shape.BoundBox
        bbox = current if bbox is None else bbox.united(current)
    if bbox is None:
        raise AssertionError("No shapes available for bounding box")
    return {
        "xmin": round(bbox.XMin, 6), "ymin": round(bbox.YMin, 6), "zmin": round(bbox.ZMin, 6),
        "xmax": round(bbox.XMax, 6), "ymax": round(bbox.YMax, 6), "zmax": round(bbox.ZMax, 6),
        "xlen": round(bbox.XLength, 6), "ylen": round(bbox.YLength, 6), "zlen": round(bbox.ZLength, 6),
    }


def close_enough(a: float, b: float, tolerance: float = 1e-3) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def compare_bbox(actual: dict, expected: dict, tolerance: float = 1e-3) -> bool:
    return all(close_enough(actual[key], expected[key], tolerance) for key in expected)


def import_exchange(path: Path, name: str) -> tuple[dict, list]:
    doc = App.newDocument(name)
    Import.insert(str(path), doc.Name)
    doc.recompute()
    objects = shape_objects(doc)
    leaf_objects = [obj for obj in objects if not obj.OutList]
    result = {
        "objects": len(doc.Objects),
        "shape_objects": len(objects),
        "leaf_shape_objects": len(leaf_objects),
        "solid_count": sum(len(obj.Shape.Solids) for obj in leaf_objects),
        "hierarchy_solid_references": sum(len(obj.Shape.Solids) for obj in objects),
        "invalid_shape_objects": [obj.Name for obj in objects if not obj.Shape.isValid()],
        "bounding_box_mm": bbox_summary(objects),
    }
    App.closeDocument(doc.Name)
    return result, objects


def import_iges(path: Path, name: str) -> dict:
    """Reimport IGES through FreeCAD's native OpenCASCADE Part reader.

    FreeCAD 1.1.3's generic ``Import.insert`` silently creates an empty
    document for this multi-body IGES export.  ``Part.read`` is the native
    IGES geometry reader and returns the expected valid face compound.  IGES
    solid retention is deliberately not claimed: the format reimports here as
    independent faces, so verification uses validity, topology and envelope.
    """
    shape = Part.read(str(path))
    doc = App.newDocument(name)
    obj = doc.addObject("Part::Feature", "IGES_Native_Reimport")
    obj.Shape = shape
    doc.recompute()
    objects = shape_objects(doc)
    result = {
        "reader": "FreeCAD Part.read (OpenCASCADE IGES)",
        "objects": len(doc.Objects),
        "shape_objects": len(objects),
        "solid_count": len(shape.Solids),
        "face_count": len(shape.Faces),
        "edge_count": len(shape.Edges),
        "vertex_count": len(shape.Vertexes),
        "invalid_shape_objects": [item.Name for item in objects if not item.Shape.isValid()],
        "bounding_box_mm": bbox_summary(objects),
    }
    App.closeDocument(doc.Name)
    return result


def parse_dxf_entities(path: Path):
    lines = path.read_text(encoding="latin-1").splitlines()
    if len(lines) % 2:
        raise AssertionError("DXF group-code/value line count is not even")
    pairs = [(lines[index].strip(), lines[index + 1].strip()) for index in range(0, len(lines), 2)]
    types = []
    circles = []
    lines_found = []
    index = 0
    while index < len(pairs):
        code, value = pairs[index]
        if code != "0":
            index += 1
            continue
        types.append(value)
        if value == "CIRCLE":
            entity = {}
            index += 1
            while index < len(pairs) and pairs[index][0] != "0":
                entity[pairs[index][0]] = pairs[index][1]
                index += 1
            circles.append({
                "x": round(float(entity["10"]), 3),
                "y": round(float(entity["20"]), 3),
                "radius": round(float(entity["40"]), 3),
            })
            continue
        if value == "LINE":
            entity = {}
            index += 1
            while index < len(pairs) and pairs[index][0] != "0":
                entity[pairs[index][0]] = pairs[index][1]
                index += 1
            lines_found.append({
                "x1": round(float(entity["10"]), 3),
                "y1": round(float(entity["20"]), 3),
                "x2": round(float(entity["11"]), 3),
                "y2": round(float(entity["21"]), 3),
            })
            continue
        index += 1
    counts = {entity_type: types.count(entity_type) for entity_type in sorted(set(types))}
    extents = []
    for circle in circles:
        extents.extend([
            (circle["x"] - circle["radius"], circle["y"] - circle["radius"]),
            (circle["x"] + circle["radius"], circle["y"] + circle["radius"]),
        ])
    for line in lines_found:
        extents.extend([(line["x1"], line["y1"]), (line["x2"], line["y2"])])
    structural_bbox = {
        "xmin": min(point[0] for point in extents),
        "ymin": min(point[1] for point in extents),
        "xmax": max(point[0] for point in extents),
        "ymax": max(point[1] for point in extents),
    }
    structural_bbox["xlen"] = round(structural_bbox["xmax"] - structural_bbox["xmin"], 3)
    structural_bbox["ylen"] = round(structural_bbox["ymax"] - structural_bbox["ymin"], 3)
    return counts, circles, lines_found, structural_bbox


checks: list[str] = []
failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        checks.append(message)
    else:
        failures.append(message)


def execute() -> None:
    required_paths = [FCSTD, STEP, IGES, DXF, PLACEMENT_CSV, HOLE_CSV, BUILD_JSON]
    for path in required_paths:
        check(path.is_file() and path.stat().st_size > 0, f"required native/exchange artifact exists: {path.name}")
    if failures:
        raise AssertionError("Missing required artifacts")

    placements = read_csv(PLACEMENT_CSV)
    holes = read_csv(HOLE_CSV)
    build_evidence = json.loads(BUILD_JSON.read_text(encoding="utf-8"))
    check(build_evidence["freecad"]["gui_up"] == 0, "final native model was rebuilt headlessly by FreeCADCmd")
    view_provenance = build_evidence["native_view_provenance"]
    gui_tool = view_provenance["gui_render_executable"]
    check(
        gui_tool == {
            "name": "FreeCAD.exe",
            "version": "1.1.3 revision 20260725 (Git shallow)",
            "sha256": "d831ed7eee385d5a370a83b078dd90b1f7621bb65bb7c427f06c736c8652d5f0",
            "scope": "Retained pre-clearance-metadata-correction GUI views only; FreeCADCmd is authoritative for the final reopen/reimport",
        },
        "retained GUI view provenance records the exact FreeCAD executable, version, SHA-256 and limited scope",
    )
    check(view_provenance["semantic_geometry_identity"] is True, "retained genuine GUI views match the invariant physical-placement geometry fingerprint")
    check(view_provenance["geometry_fingerprint_actual"] == view_provenance["geometry_fingerprint_expected"], "retained-view physical-geometry fingerprint exactly matches the controlled value")
    check(view_provenance["controlled_view_hashes_actual"] == view_provenance["controlled_view_hashes_expected"], "retained genuine GUI PNG hashes exactly match the controlled native-render set")
    check(view_provenance["placement_schedule_byte_identity_claimed"] is False, "view evidence does not claim placement-schedule byte identity after the nongeometric clearance correction")
    check(view_provenance["fcstd_byte_identity_claimed"] is False, "view evidence explicitly does not claim final FCStd byte identity")
    determinism = build_evidence["determinism"]
    check(determinism["repeated_builds_executed"] >= 2, "native build evidence records at least two repeated build passes")
    check(FCSTD.name in determinism["semantic_verification_only"] and IGES.name in determinism["semantic_verification_only"], "FCStd and IGES byte nondeterminism are explicitly bounded by semantic native verification")
    doc = App.openDocument(str(FCSTD))
    doc.recompute()
    physical = controlled_physical_objects(doc)
    physical_bbox = bbox_summary(physical)
    invalid = [obj.Name for obj in physical if not obj.Shape.isValid()]
    physical_solids = sum(len(obj.Shape.Solids) for obj in physical)

    info = doc.getObject("FC01_Revision_E_Project_Information")
    check(info is not None, "native FCStd contains controlled Revision-E project-information object")
    if info is not None:
        check(info.Revision == REVISION, "native project metadata identifies Revision E")
        check(info.SafetyBoundary == SAFETY, "native project metadata retains exact conceptual-safety boundary")
        check(info.ExpectedMountingHoleCount == len(holes), "native metadata hole count matches controlled hole schedule")

    check(len(doc.Objects) == 165, "native FCStd contains exactly 165 structured document objects")
    check(len(physical) == 148, "native FCStd contains exactly 148 controlled physical objects")
    check(physical_solids == 148, "native FCStd contains exactly 148 controlled physical solids")
    check(not invalid, "all controlled physical FCStd shapes are valid")
    expected_bbox = {"xmin": 0.0, "ymin": 0.0, "zmin": 0.0, "xmax": 800.0, "ymax": 800.0, "zmax": 327.0, "xlen": 800.0, "ylen": 800.0, "zlen": 327.0}
    check(compare_bbox(physical_bbox, expected_bbox), "native physical assembly bounding box is exactly 800 x 800 x 327 mm including external isolator handle")

    required_tags = {
        "-A100", "-A101", "-A102", "-A103", "-A104", "-H100", "-U100", "-U101",
        "-SW100", "-FW100", "-PC200", "-QF100", "-PS100", "-QF110", "-K100",
        "-SC100", "-PE100",
    }
    model_tags = {obj.ReferenceDesignation for obj in physical if hasattr(obj, "ReferenceDesignation")}
    check(required_tags <= model_tags, "native model contains every required major selected/provisional architecture tag")
    check(all(f"-K{value}" in model_tags for value in range(202, 214)), "native model contains all twelve K202-K213 relay objects")

    terminal_objects = [obj for obj in physical if hasattr(obj, "ReferenceDesignation") and re.fullmatch(r"-?(?:X\d+:.+|X0:.+|SC100:1)", obj.ReferenceDesignation)]
    check(len(terminal_objects) == 84, "native model contains one controlled physical object for each of 84 logical terminals")
    check(sum(1 for obj in physical if hasattr(obj, "ReferenceDesignation") and obj.ReferenceDesignation.startswith("-PE100:")) == 12, "native model contains 12 provisional PE terminal objects")

    plate = doc.getObject("MP100_Mounting_Plate")
    check(plate is not None and plate.Shape.isValid(), "drilled mounting-plate native solid exists and is valid")
    if plate is not None:
        check(plate.MountingHoleCount == len(holes), "mounting-plate native property matches hole schedule")
        removed = sum(math.pi * (float(row["diameter_mm"]) / 2.0) ** 2 * 3.0 for row in holes)
        expected_volume = 750.0 * 750.0 * 3.0 - removed
        check(close_enough(plate.Shape.Volume, expected_volume, 0.05), "native mounting-plate volume confirms every scheduled through-hole")

    # Device-only 2D footprint separation.  Door devices, terminals and infrastructure
    # are checked through native geometry/bounds separately.
    device_rows = [row for row in placements if row["category"] == "Device"]
    overlaps = []
    for index, left in enumerate(device_rows):
        lx0, ly0 = float(left["x_mm"]), float(left["y_mm"])
        lx1, ly1 = lx0 + float(left["width_mm"]), ly0 + float(left["height_mm"])
        for right in device_rows[index + 1 :]:
            rx0, ry0 = float(right["x_mm"]), float(right["y_mm"])
            rx1, ry1 = rx0 + float(right["width_mm"]), ry0 + float(right["height_mm"])
            if min(lx1, rx1) - max(lx0, rx0) > 1e-6 and min(ly1, ry1) - max(ly0, ry0) > 1e-6:
                overlaps.append((left["tag"], right["tag"]))
    check(not overlaps, "all backplate device footprints are non-overlapping")

    placement_by_tag = {row["tag"]: row for row in placements}
    adjacent_network_rows = [placement_by_tag[tag] for tag in ("-SW100", "-FW100", "-PC200")]
    network_clearance_overlaps = []
    for left, right in zip(adjacent_network_rows, adjacent_network_rows[1:]):
        left_limit = float(left["x_mm"]) + float(left["width_mm"]) + float(left["side_clearance_mm"])
        right_limit = float(right["x_mm"]) - float(right["side_clearance_mm"])
        if left_limit > right_limit + 1e-6:
            network_clearance_overlaps.append((left["tag"], right["tag"], left_limit - right_limit))
    check(all(float(row["side_clearance_mm"]) == 5.0 for row in adjacent_network_rows), "SW100, FW100 and PC200 use the controlled 5 mm lateral layout-clearance assumption")
    check(not network_clearance_overlaps, "adjacent SW100, FW100 and PC200 lateral clearance envelopes do not overlap")
    for row in adjacent_network_rows:
        native = next(obj for obj in physical if hasattr(obj, "ReferenceDesignation") and obj.ReferenceDesignation == row["tag"])
        check(close_enough(native.SideClearance, float(row["side_clearance_mm"])), f"native {row['tag']} SideClearance property matches the placement schedule")

    # Ensure no non-drive device enters a selected drive cooling keep-out volume.
    drive_keepout_intrusions = []
    for drive_tag in ("-U100", "-U101"):
        clearance = next(obj for obj in shape_objects(doc) if hasattr(obj, "ReferenceDesignation") and obj.ReferenceDesignation == drive_tag + "-CLR")
        for obj in physical:
            tag = getattr(obj, "ReferenceDesignation", "")
            if tag == drive_tag or tag.startswith(("-EN", "-MP", "-RA", "-WD")):
                continue
            if clearance.Shape.common(obj.Shape).Volume > 1e-4:
                drive_keepout_intrusions.append((drive_tag, tag or obj.Name))
    check(not drive_keepout_intrusions, "G120C 80 mm top / 100 mm bottom cooling keep-outs contain no other physical device")

    step_result, _ = import_exchange(STEP, "FC01_Revision_E_STEP_Reimport")
    iges_result = import_iges(IGES, "FC01_Revision_E_IGES_Reimport")
    check(not step_result["invalid_shape_objects"], "STEP reimport contains no invalid shape object")
    check(step_result["solid_count"] >= 148, "STEP reimport retains at least 148 solids")
    check(compare_bbox(step_result["bounding_box_mm"], physical_bbox, 0.01), "STEP reimport bounding box matches authoritative FCStd physical assembly")
    check(not iges_result["invalid_shape_objects"], "IGES reimport contains no invalid shape object")
    check(iges_result["shape_objects"] == 1 and iges_result["face_count"] >= 148, "IGES native reimport retains a non-empty face compound with at least one face per controlled object")
    check(compare_bbox(iges_result["bounding_box_mm"], physical_bbox, 0.01), "IGES reimport bounding box matches authoritative FCStd physical assembly")

    dxf_counts, dxf_circles, dxf_lines, dxf_structural_bbox = parse_dxf_entities(DXF)
    scheduled_circles = sorted(
        (round(float(row["x_local_mm"]), 3), round(float(row["y_local_mm"]), 3), round(float(row["diameter_mm"]) / 2.0, 3))
        for row in holes
    )
    actual_circles = sorted((row["x"], row["y"], row["radius"]) for row in dxf_circles)
    check(dxf_counts.get("CIRCLE", 0) == len(holes), "DXF CIRCLE entity count matches controlled mounting-hole schedule")
    check(dxf_counts.get("LINE", 0) >= 4, "DXF contains the four mounting-plate outline edges")
    check(actual_circles == scheduled_circles, "every DXF hole coordinate and radius matches the controlled schedule")
    check(dxf_structural_bbox == {"xmin": 0.0, "ymin": 0.0, "xmax": 750.0, "ymax": 750.0, "xlen": 750.0, "ylen": 750.0}, "DXF structural entity bounding box is exactly 750 x 750 mm")

    # Make DXF import mode explicit.  A fresh FreeCAD profile otherwise inherits
    # whichever one of the mutually exclusive GUI radio-button flags happens to
    # exist in that profile.  Individual Part shapes give the independent
    # verifier native geometry suitable for object-count and bounding-box tests.
    dxf_preferences = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft")
    dxf_preferences.SetBool("dxfUseLegacyImporter", False)
    dxf_preferences.SetBool("dxfImportAsDraft", False)
    dxf_preferences.SetBool("dxfImportAsPrimitives", False)
    dxf_preferences.SetBool("dxfImportAsFused", False)
    dxf_preferences.SetBool("dxfImportAsShapes", True)
    dxf_preferences.SetBool("dxfUseDraftVisGroups", True)
    dxf_preferences.SetBool("dxfShowDialog", False)
    dxf_doc = App.newDocument("FC01_Revision_E_DXF_Reimport")
    importDXF.insert(str(DXF), dxf_doc.Name)
    dxf_doc.recompute()
    dxf_shapes = shape_objects(dxf_doc)
    dxf_document_objects = len(dxf_doc.Objects)
    dxf_shape_objects = len(dxf_shapes)
    dxf_bbox = bbox_summary(dxf_shapes) if dxf_shapes else None
    check(dxf_document_objects > 0, "FreeCAD native DXF reimport creates a non-empty document")
    if dxf_bbox is not None:
        check(dxf_shape_objects == len(holes) + 4, "DXF native reimport retains exactly four outline and 30 scheduled-hole shape objects")
        check(close_enough(dxf_bbox["xlen"], 750.0, 0.01) and close_enough(dxf_bbox["ylen"], 750.0, 0.01), "DXF native shape bounding box is 750 x 750 mm")
    App.closeDocument(dxf_doc.Name)

    expected_outputs = [
        "front_internal.png", "isometric_internal.png", "segregation_zones.png", "door_layout.png",
        "FC01_general_arrangement_revision_e.pdf", "FC01_mounting_plate_dimensioned_revision_e.pdf",
    ]
    for name in expected_outputs:
        path = OUT / name
        check(path.is_file() and path.stat().st_size > 5000, f"rendered native evidence is non-empty: {name}")
        if path.suffix.lower() == ".png":
            check(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), f"rendered view has PNG signature: {name}")
        else:
            data = path.read_bytes()
            check(data.startswith(b"%PDF") and data.rstrip().endswith(b"%%EOF"), f"CAD drawing has valid PDF framing: {name}")
            pages = len(re.findall(rb"/Type\s*/Page\b", data))
            expected_pages = 4 if "general_arrangement" in name else 2
            check(pages == expected_pages, f"{name} contains exactly {expected_pages} pages")

    for name, artifact in build_evidence["artifacts"].items():
        path = OUT / name
        check(path.is_file() and sha256(path) == artifact["sha256"], f"build-evidence hash matches final artifact: {name}")

    uncontrolled = []
    forbidden_suffixes = {".FCBak", ".bak", ".tmp", ".lock", ".autosave", ".pyc"}
    for path in OUT.rglob("*"):
        if path.is_dir() and path.name == "__pycache__":
            uncontrolled.append(path.name)
        elif path.is_file() and path.suffix in forbidden_suffixes:
            uncontrolled.append(path.name)
    check(not uncontrolled, "Revision-E native output contains no backup, lock, autosave, temp or cache artifact")

    result = {
        "project": "FC01 Compact Filling Cell",
        "revision": REVISION,
        "result": "PASS" if not failures else "FAIL",
        "passed_checks": len(checks),
        "failed_checks": len(failures),
        "checks": checks,
        "failures": failures,
        "freecad": {
            "version": App.Version(),
            "executable_name": Path(sys.executable).name.lower(),
            "executable_sha256": sha256(Path(sys.executable).resolve()),
        },
        "fcstd": {
            "sha256": sha256(FCSTD),
            "document_objects": len(doc.Objects),
            "controlled_physical_objects": len(physical),
            "controlled_physical_solids": physical_solids,
            "invalid_shape_objects": invalid,
            "bounding_box_mm": physical_bbox,
        },
        "step_reimport": {**step_result, "sha256": sha256(STEP)},
        "iges_reimport": {**iges_result, "sha256": sha256(IGES)},
        "dxf_reimport": {
            "sha256": sha256(DXF), "entity_counts": dxf_counts,
            "circle_count": len(dxf_circles), "line_count": len(dxf_lines),
            "document_objects": dxf_document_objects,
            "shape_objects": dxf_shape_objects,
            "native_shape_bounding_box_mm": dxf_bbox,
            "structural_entity_bounding_box_mm": dxf_structural_bbox,
            "solid_retention_claimed": False,
        },
        "mounting_holes": len(holes),
        "controlled_terminal_objects": len(terminal_objects),
        "drive_keepout_intrusions": drive_keepout_intrusions,
        "device_footprint_overlaps": overlaps,
        "network_clearance_envelope_overlaps": network_clearance_overlaps,
        "native_view_provenance": view_provenance,
        "uncontrolled_native_artifacts": uncontrolled,
        "boundaries": [NOTICE, SAFETY],
        "limitations": [
            "No manufacturer/supplier approval, fabrication authorization or construction release",
            "Enclosure, protection, PSU, relays, terminals, ducts, PE system, Jetson carrier and cooling remain selection-dependent",
            "Drive drilling orientation requires confirmation against order-number CAx before manufacture",
            "No site thermal, cable-route, short-circuit, EMC, qualified safety or physical commissioning evidence",
        ],
    }
    stable_json(REPORT_JSON, result)
    md = [
        "# FC01 Revision-E native FreeCAD verification",
        "",
        f"> {NOTICE}", "", f"> {SAFETY}", "",
        f"Result: **{result['result']}** — {len(checks)} passed checks, {len(failures)} failed checks.", "",
        "## Native reopen", "",
        f"- FreeCAD: `{'.'.join(str(item) for item in App.Version()[:3])}`, revision `{App.Version()[3]}`.",
        f"- FCStd document objects: {len(doc.Objects)}.",
        f"- Controlled physical objects / solids: {len(physical)} / {physical_solids}.",
        f"- Invalid controlled shapes: {len(invalid)}.",
        f"- Physical assembly bounding box: `{json.dumps(physical_bbox, sort_keys=True)}` mm.",
        f"- Scheduled/native/DXF mounting holes: {len(holes)} / {getattr(plate, 'MountingHoleCount', 'N/A')} / {len(dxf_circles)}.",
        "", "## Exchange reimport", "",
        f"- STEP: {step_result['shape_objects']} shape objects, {step_result['solid_count']} solids, {len(step_result['invalid_shape_objects'])} invalid; matching bounding box.",
        f"- IGES: native Part.read produced {iges_result['shape_objects']} valid face compound with {iges_result['face_count']} faces and matching bounding box; solid retention is not claimed.",
        f"- DXF: {dxf_counts.get('LINE', 0)} LINE and {dxf_counts.get('CIRCLE', 0)} CIRCLE entities; structural entity envelope is 750 × 750 mm; native Part-solid retention is not claimed.",
        "", "## Native-view provenance", "",
        f"- {view_provenance['description']}",
        f"- Physical-geometry fingerprint: `{view_provenance['geometry_fingerprint_actual']}`.",
        f"- Hole schedule SHA-256: `{view_provenance['schedule_hashes_after_rebuild']['holes']}`.",
        "- No FCStd byte identity or second GUI reopen is claimed; final native geometry is proven by independent FreeCADCmd reopen/reimport.",
        "", "## Controlled limitations", "",
    ]
    md.extend(f"- {item}" for item in result["limitations"])
    md.extend(["", "## Failed checks", ""])
    md.extend([f"- {item}" for item in failures] or ["- None."])
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")

    log_lines = [
        "FC01 REVISION E NATIVE FREECAD VERIFICATION LOG",
        f"FREECAD_VERSION={' '.join(str(item) for item in App.Version())}",
        f"FREECADCMD_EXECUTABLE_SHA256={sha256(Path(sys.executable).resolve())}",
        f"RESULT={result['result']}",
        f"PASSED_CHECKS={len(checks)}",
        f"FAILED_CHECKS={len(failures)}",
        f"FCSTD_OBJECTS={len(doc.Objects)}",
        f"FCSTD_CONTROLLED_PHYSICAL_OBJECTS={len(physical)}",
        f"FCSTD_SOLIDS={physical_solids}",
        f"FCSTD_INVALID_SHAPES={len(invalid)}",
        f"STEP_SOLIDS={step_result['solid_count']}",
        f"STEP_INVALID_SHAPES={len(step_result['invalid_shape_objects'])}",
        f"IGES_SOLIDS={iges_result['solid_count']}",
        f"IGES_INVALID_SHAPES={len(iges_result['invalid_shape_objects'])}",
        f"DXF_CIRCLES={len(dxf_circles)}",
        f"DXF_NATIVE_REIMPORT_SHAPES={len(dxf_shapes)}",
        f"MOUNTING_HOLES={len(holes)}",
        f"DEVICE_FOOTPRINT_OVERLAPS={len(overlaps)}",
        f"DRIVE_KEEPOUT_INTRUSIONS={len(drive_keepout_intrusions)}",
        f"UNCONTROLLED_NATIVE_ARTIFACTS={len(uncontrolled)}",
        f"VIEW_GEOMETRY_SEMANTIC_IDENTITY={view_provenance['semantic_geometry_identity']}",
    ]
    VERIFY_LOG.write_text("\n".join(log_lines) + "\n", encoding="utf-8", newline="\n")
    for line in log_lines:
        App.Console.PrintMessage(line + "\n")
    App.closeDocument(doc.Name)
    if failures:
        raise SystemExit(1)


execute()
