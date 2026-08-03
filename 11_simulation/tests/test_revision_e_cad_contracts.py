from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "09_panel_cad" / "revision_e"
VERIFY = CAD / "native_verification.json"
PLACEMENT = CAD / "revision_e_panel_placement.csv"
HOLES = CAD / "mounting_hole_schedule.csv"
FCSTD = CAD / "FC01_control_panel_revision_e.FCStd"
DXF = CAD / "FC01_mounting_plate_revision_e.dxf"
SAFETY = (
    "CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, "
    "DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. "
    "NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED."
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pdf_pages(path: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", path.read_bytes()))


def dxf_circles(path: Path) -> list[tuple[float, float, float]]:
    lines = path.read_text(encoding="latin-1").splitlines()
    pairs = [(lines[index].strip(), lines[index + 1].strip()) for index in range(0, len(lines), 2)]
    output = []
    index = 0
    while index < len(pairs):
        if pairs[index] != ("0", "CIRCLE"):
            index += 1
            continue
        entity = {}
        index += 1
        while index < len(pairs) and pairs[index][0] != "0":
            entity[pairs[index][0]] = pairs[index][1]
            index += 1
        output.append((round(float(entity["10"]), 3), round(float(entity["20"]), 3), round(float(entity["40"]), 3)))
    return sorted(output)


class RevisionECADContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not VERIFY.is_file():
            raise AssertionError("native_verification.json is absent; native FreeCAD gate cannot pass")
        cls.evidence = json.loads(VERIFY.read_text(encoding="utf-8"))
        cls.placements = rows(PLACEMENT)
        cls.holes = rows(HOLES)

    def test_native_verification_is_genuine_pass(self):
        self.assertEqual(self.evidence["result"], "PASS")
        self.assertEqual(self.evidence["failed_checks"], 0)
        self.assertGreaterEqual(self.evidence["passed_checks"], 40)

    def test_controlled_freecad_executable_is_recorded(self):
        freecad = self.evidence["freecad"]
        self.assertEqual(freecad["version"][:4], ["1", "1", "3", "20260725 (Git shallow)"])
        self.assertEqual(freecad["executable_name"], "freecadcmd.exe")
        self.assertNotIn("executable", freecad)
        self.assertRegex(freecad["executable_sha256"], r"^[0-9a-f]{64}$")

    def test_fcstd_native_structure_and_bbox(self):
        native = self.evidence["fcstd"]
        self.assertEqual(native["document_objects"], 165)
        self.assertEqual(native["controlled_physical_objects"], 148)
        self.assertEqual(native["controlled_physical_solids"], 148)
        self.assertEqual(native["invalid_shape_objects"], [])
        self.assertEqual([native["bounding_box_mm"][key] for key in ("xlen", "ylen", "zlen")], [800.0, 800.0, 327.0])
        self.assertEqual(hashlib.sha256(FCSTD.read_bytes()).hexdigest(), native["sha256"])

    def test_fcstd_is_a_real_reopenable_container(self):
        self.assertTrue(zipfile.is_zipfile(FCSTD))
        with zipfile.ZipFile(FCSTD) as archive:
            self.assertIsNone(archive.testzip())
            names = set(archive.namelist())
            self.assertIn("Document.xml", names)
            document_xml = archive.read("Document.xml").decode("utf-8")
        self.assertIn("FC01_Revision_E_Project_Information", document_xml)
        self.assertIn("ExpectedMountingHoleCount", document_xml)

    def test_step_reimport_matches_native_model(self):
        step = self.evidence["step_reimport"]
        self.assertEqual(step["invalid_shape_objects"], [])
        self.assertGreaterEqual(step["solid_count"], 148)
        self.assertEqual(step["bounding_box_mm"], self.evidence["fcstd"]["bounding_box_mm"])

    def test_iges_reimport_matches_native_model(self):
        iges = self.evidence["iges_reimport"]
        self.assertEqual(iges["invalid_shape_objects"], [])
        self.assertEqual(iges["reader"], "FreeCAD Part.read (OpenCASCADE IGES)")
        self.assertEqual(iges["shape_objects"], 1)
        self.assertEqual(iges["solid_count"], 0)
        self.assertGreaterEqual(iges["face_count"], 148)
        self.assertEqual(iges["bounding_box_mm"], self.evidence["fcstd"]["bounding_box_mm"])

    def test_dxf_holes_match_schedule_exactly(self):
        scheduled = sorted(
            (round(float(row["x_local_mm"]), 3), round(float(row["y_local_mm"]), 3), round(float(row["diameter_mm"]) / 2.0, 3))
            for row in self.holes
        )
        self.assertEqual(dxf_circles(DXF), scheduled)
        self.assertEqual(self.evidence["dxf_reimport"]["circle_count"], len(self.holes))
        self.assertEqual(self.evidence["mounting_holes"], len(self.holes))

    def test_hole_schedule_marks_manufacturing_boundaries(self):
        self.assertGreaterEqual(len(self.holes), 30)
        self.assertTrue(all("PROVISIONAL" in row["engineering_status"] for row in self.holes))
        drive_holes = [row for row in self.holes if row["associated_feature"] in {"-U100", "-U101"}]
        self.assertEqual(len(drive_holes), 6)
        self.assertTrue(all("CAx" in row["engineering_status"] for row in drive_holes))

    def test_placement_register_covers_selected_architecture(self):
        tags = {row["tag"] for row in self.placements}
        required = {
            "-A100", "-A101", "-A102", "-A103", "-A104", "-H100", "-U100", "-U101",
            "-SW100", "-FW100", "-PC200", "-PS100", "-QF100", "-QF110", "-K100", "-SC100", "-PE100",
        }
        self.assertLessEqual(required, tags)
        self.assertTrue(all(f"-K{value}" in tags for value in range(202, 214)))

    def test_selected_and_assumed_envelopes_are_not_conflated(self):
        by_tag = {row["tag"]: row for row in self.placements}
        for tag in ("-A100", "-A101", "-A102", "-A103", "-A104", "-U100", "-U101", "-SW100"):
            self.assertNotIn("ASSUMPTION", by_tag[tag]["dimension_basis"])
        self.assertIn("ARCHITECTURE-ONLY ENVELOPE ASSUMPTION", by_tag["-PC200"]["dimension_basis"])
        self.assertIn("NOT PROCUREMENT OR CONSTRUCTION DATA", by_tag["-PC200"]["engineering_status"])

    def test_terminal_and_pe_counts_are_explicit(self):
        terminal_rows = [row for row in self.placements if row["category"] == "Terminal"]
        logical = [row for row in terminal_rows if not row["tag"].startswith("-PE100:")]
        pe = [row for row in terminal_rows if row["tag"].startswith("-PE100:")]
        self.assertEqual(len(logical), 84)
        self.assertEqual(len(pe), 12)
        self.assertEqual(self.evidence["controlled_terminal_objects"], 84)

    def test_device_and_drive_clearance_checks_are_clean(self):
        self.assertEqual(self.evidence["device_footprint_overlaps"], [])
        self.assertEqual(self.evidence["drive_keepout_intrusions"], [])
        by_tag = {row["tag"]: row for row in self.placements}
        adjacent = [by_tag[tag] for tag in ("-SW100", "-FW100", "-PC200")]
        self.assertTrue(all(float(row["side_clearance_mm"]) == 5.0 for row in adjacent))
        for left, right in zip(adjacent, adjacent[1:]):
            left_limit = float(left["x_mm"]) + float(left["width_mm"]) + float(left["side_clearance_mm"])
            right_limit = float(right["x_mm"]) - float(right["side_clearance_mm"])
            self.assertLessEqual(left_limit, right_limit)

    def test_native_views_are_present(self):
        for name in ("front_internal.png", "isometric_internal.png", "segregation_zones.png", "door_layout.png"):
            path = CAD / name
            self.assertGreater(path.stat().st_size, 5000)
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_cad_pdfs_have_controlled_page_counts_and_safety_text(self):
        expected = {
            "FC01_general_arrangement_revision_e.pdf": 4,
            "FC01_mounting_plate_dimensioned_revision_e.pdf": 2,
        }
        for name, count in expected.items():
            path = CAD / name
            self.assertEqual(pdf_pages(path), count)
            self.assertTrue(path.read_bytes().startswith(b"%PDF"))
        readme = (CAD / "README.md").read_text(encoding="utf-8")
        self.assertIn(SAFETY, readme)
        self.assertIn("NOT FOR CONSTRUCTION", readme)

    def test_no_native_backup_lock_or_cache_artifact_is_controlled(self):
        forbidden_suffixes = {".FCBak", ".bak", ".tmp", ".lock", ".autosave", ".pyc"}
        unexpected = [path.name for path in CAD.rglob("*") if path.is_file() and path.suffix in forbidden_suffixes]
        unexpected.extend(path.name for path in CAD.rglob("__pycache__") if path.is_dir())
        self.assertEqual(unexpected, [])


if __name__ == "__main__":
    unittest.main()
