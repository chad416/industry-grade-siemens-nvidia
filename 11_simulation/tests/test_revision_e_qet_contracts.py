"""Revision-E QElectroTech controlled-source regression contracts."""

from __future__ import annotations

import csv
import hashlib
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from qet_revision_e import DEFAULT_OUTPUT, NOTICE, QET_NAME, SAFETY, generate, table_layout  # noqa: E402
from verify_qet_revision_e import verify  # noqa: E402


class RevisionEQetContracts(unittest.TestCase):
    def test_controlled_project_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = Path(first)
            b = Path(second)
            generate(a)
            generate(b)
            for name in [QET_NAME, "FC01_revision_e_element_register.csv", "FC01_revision_e_build_evidence.json"]:
                self.assertEqual(
                    hashlib.sha256((a / name).read_bytes()).hexdigest(),
                    hashlib.sha256((b / name).read_bytes()).hexdigest(),
                    name,
                )

    def test_repository_artifact_matches_generator(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            generated = Path(temp)
            generate(generated)
            for name in [QET_NAME, "FC01_revision_e_element_register.csv", "FC01_revision_e_build_evidence.json"]:
                self.assertEqual((DEFAULT_OUTPUT / name).read_bytes(), (generated / name).read_bytes(), name)

    def test_project_contract_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            generate(output)
            result = verify(output)
            self.assertEqual(result["failed"], 0, [c for c in result["checks"] if not c["pass"]])
            self.assertGreaterEqual(result["element_count"], 60)
            self.assertGreaterEqual(result["conductor_count"], 35)

    def test_native_structure_and_boundaries(self) -> None:
        project = ET.parse(DEFAULT_OUTPUT / QET_NAME).getroot()
        self.assertEqual(project.attrib["version"], "0.100.0")
        diagrams = project.findall("diagram")
        self.assertEqual(len(diagrams), 26)
        self.assertEqual([int(d.attrib["order"]) for d in diagrams], list(range(1, 27)))
        self.assertTrue(all(d.attrib["indexrev"] == "E" for d in diagrams))
        raw = (DEFAULT_OUTPUT / QET_NAME).read_text(encoding="utf-8")
        self.assertIn(NOTICE, raw)
        self.assertIn(SAFETY, raw)
        self.assertNotIn("Revision A", raw)
        self.assertNotIn('indexrev="A"', raw)

    def test_companion_register_covers_devices_terminals_and_cables(self) -> None:
        with (DEFAULT_OUTPUT / "FC01_revision_e_element_register.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 168)
        self.assertEqual({row["record_type"] for row in rows}, {"DEVICE", "TERMINAL", "CABLE"})
        self.assertEqual(len({row["reference"] for row in rows if row["record_type"] == "TERMINAL"}), 84)
        self.assertEqual(len({row["reference"] for row in rows if row["record_type"] == "CABLE"}), 22)

    def test_long_schedules_are_bounded_and_diagram_tables_do_not_overlap(self) -> None:
        for row_count in (36, 48, 62):
            columns, per_col, x_step, start_y, row_step, font_size = table_layout(row_count, False)
            self.assertEqual(columns, 3)
            self.assertEqual(x_step, 245.0)
            self.assertLessEqual(start_y + (per_col - 1) * row_step, 410.0)
            self.assertLessEqual(font_size, 2.8)

        columns, per_col, _, start_y, row_step, _ = table_layout(7, True)
        self.assertEqual(columns, 1)
        self.assertEqual(start_y, 225.0)
        self.assertGreaterEqual(start_y, 225.0)
        self.assertLessEqual(start_y + (per_col - 1) * row_step, 360.0)


if __name__ == "__main__":
    unittest.main()
