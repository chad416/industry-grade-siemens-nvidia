"""Revision-E static contracts for a poll-safe PLC-to-edge request handshake.

These checks lock source intent and generator parity only. They do not compile
SCL, execute TIA Portal, or constitute PLCSIM/controller evidence.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCL = ROOT / "04_controls_siemens" / "scl"
sys.path.insert(0, str(ROOT / "scripts"))

from revision_f_scl import sources  # noqa: E402


class RevisionEVisionRequestContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generated = sources()
        cls.vision = (SCL / "FB_VisionInterface.scl").read_text(encoding="utf-8")
        cls.cell = (SCL / "FB_CellMain.scl").read_text(encoding="utf-8")

    def test_generated_sources_match_authoritative_generator(self) -> None:
        self.assertEqual(self.vision.rstrip(), self.generated["FB_VisionInterface.scl"].rstrip())
        self.assertEqual(self.cell.rstrip(), self.generated["FB_CellMain.scl"].rstrip())

    def test_trigger_is_level_held_for_polling_transport(self) -> None:
        self.assertIn("Trigger is a level-held OPC UA request", self.vision)
        self.assertIn(
            "#Trigger := #pending AND #triggered AND NOT #requestObserved AND NOT #Result.ResultValid AND NOT #Fault;",
            self.vision,
        )
        self.assertNotIn("Trigger and Accepted are one-scan pulses", self.vision)

    def test_busy_observation_latches_request_seen_once(self) -> None:
        self.assertIn(
            "IF #pending AND #triggered AND #Ready AND #Busy THEN #requestObserved := TRUE; END_IF;",
            self.vision,
        )
        self.assertNotIn("#requestObserved := FALSE;\n   #Trigger := #pending", self.vision)

    def test_terminal_result_may_complete_before_busy_is_sampled(self) -> None:
        self.assertIn("IF #pending AND #triggered AND #Result.ResultValid AND NOT #Fault THEN", self.vision)
        self.assertNotIn(
            "#pending AND #triggered AND #requestObserved AND #Result.ResultValid",
            self.vision,
        )

    def test_transaction_id_is_immutable_while_pending(self) -> None:
        self.assertIn("IF #pending AND (#InspectionId <> #latchedId) THEN", self.vision)
        self.assertIn('DiagReason := "E_VisionDiag".NON_MONOTONIC_REQUEST', self.vision)

    def test_duplicate_request_cannot_advance_active_id(self) -> None:
        self.assertIn(
            "#Coordinator.VisionRequestPulse AND NOT #Vision.RequestInProgress",
            self.cell,
        )
        self.assertIn("RequestInProgress : Bool", self.vision)

    def test_id_and_session_are_latched_before_request_publication(self) -> None:
        arm = self.vision.index("#pending := TRUE; #triggered := FALSE; #requestObserved := FALSE")
        publish = self.vision.index("#Trigger := #pending AND #triggered")
        self.assertLess(arm, publish)
        self.assertIn("#latchedId := #InspectionId", self.vision[arm:publish])
        self.assertIn("#latchedSessionEpoch := #SessionEpoch", self.vision[arm:publish])

    def test_fault_and_disable_paths_clear_request_latches(self) -> None:
        self.assertIn(
            "IF #Fault THEN #Trigger := FALSE; #triggered := FALSE; #requestObserved := FALSE; END_IF;",
            self.vision,
        )
        self.assertIn(
            "#Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #requestObserved := FALSE;",
            self.vision,
        )

    def test_request_state_tracks_pending_after_all_transitions(self) -> None:
        self.assertIn("#RequestInProgress := #pending;\nEND_FUNCTION_BLOCK", self.vision)


if __name__ == "__main__":
    unittest.main()
