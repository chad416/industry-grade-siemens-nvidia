"""Static regression locks for the Revision-D.1 Siemens source contracts.

These tests inspect generated SCL and generator parity. They do not compile SCL,
execute TIA Portal, or constitute PLCSIM/native-controller evidence.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCL = ROOT / "04_controls_siemens" / "scl"
sys.path.insert(0, str(ROOT / "scripts"))

from revision_d_scl import sources  # noqa: E402


class RevisionD1SiemensSourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generated = sources()
        cls.db = (SCL / "DB_Global.scl").read_text(encoding="utf-8")
        cls.hmi = (SCL / "FB_HMICommandManager.scl").read_text(encoding="utf-8")
        cls.capper = (SCL / "FB_CapperInterface.scl").read_text(encoding="utf-8")
        cls.coordinator = (SCL / "FB_MachineCoordinator.scl").read_text(encoding="utf-8")
        cls.cell = (SCL / "FB_CellMain.scl").read_text(encoding="utf-8")
        cls.startup = (SCL / "OB100_Startup.scl").read_text(encoding="utf-8")

    def test_all_generated_siemens_sources_match_authoritative_generator(self) -> None:
        self.assertEqual(set(self.generated), {path.name for path in SCL.glob("*.scl")})
        for name, generated in self.generated.items():
            with self.subTest(name=name):
                self.assertEqual((SCL / name).read_text(encoding="utf-8").rstrip(), generated.rstrip())

    def test_session_and_approved_model_identity_are_explicitly_retentive(self) -> None:
        retained = self.db.split("VAR RETAIN", 1)[1].split("END_VAR", 1)[0]
        for field in ("SessionEpoch", "ExpectedModelId", "ExpectedModelHash", "ModelConfigurationApproved"):
            self.assertIn(field, retained)
        self.assertIn('"DB_VisionComms".SessionEpoch := "DB_VisionComms".SessionEpoch + UDINT#1', self.startup)

    def test_model_configuration_is_a_blocking_release_gate(self) -> None:
        self.assertIn('ModelConfigurationApproved AND ("DB_VisionComms".ExpectedModelId <> \'\')', self.cell)
        self.assertIn('LEN("DB_VisionComms".ExpectedModelHash) = 64', self.cell)
        self.assertIn('#processPermissive AND #modelConfigured AND "DB_VisionComms".Ready', self.cell)
        self.assertIn('#Vision.Fault OR NOT #modelConfigured OR NOT "DB_VisionComms".Ready', self.cell)

    def test_vision_not_ready_is_an_active_first_out_condition(self) -> None:
        self.assertIn('#activeFaults[10] := #Vision.Fault OR #Vision.HoldRequired OR NOT #modelConfigured OR NOT "DB_VisionComms".Ready', self.cell)
        self.assertIn('NOT "DB_VisionComms".Ready AND NOT #Vision.Fault AND NOT #Vision.HoldRequired THEN #faultCodes[10] := 1501', self.cell)

    def test_capper_busy_is_correlated_only_after_request(self) -> None:
        self.assertIn('IF #Busy OR #Complete THEN #Fault := TRUE', self.capper)
        self.assertIn('IF #pending AND #Request AND #Busy THEN #seenBusy := TRUE; #Accepted := TRUE', self.capper)
        self.assertNotIn('IF #pending AND #Busy THEN #seenBusy := TRUE', self.capper)

    def test_capper_unsolicited_complete_or_pre_request_busy_faults_closed(self) -> None:
        self.assertIn('(#Complete AND NOT #seenBusy) OR (#pending AND #Busy AND NOT #Request)', self.capper)
        self.assertIn('IF #Fault THEN #Request := FALSE; #pending := FALSE; #Accepted := FALSE', self.capper)

    def test_local_stop_does_not_consume_remote_stop_sequence(self) -> None:
        self.assertIn('IF #LocalStop THEN #StopPulse := TRUE; END_IF;', self.hmi)
        self.assertIn('IF #CommunicationsHealthy AND #StopRequest AND (#StopSeq <> #StopAcceptedSeq) THEN #StopPulse := TRUE; #StopAcceptedSeq := #StopSeq; END_IF;', self.hmi)
        self.assertNotIn('OR #LocalStop', self.hmi)

    def test_local_reset_does_not_accept_or_reject_remote_reset_sequence(self) -> None:
        self.assertIn('IF #localResetEdge.Q AND #ResetAllowed THEN #ResetPulse := TRUE; END_IF;', self.hmi)
        self.assertIn('IF #CommunicationsHealthy AND #ResetRequest', self.hmi)
        self.assertNotIn('OR #localResetEdge.Q', self.hmi)

    def test_startup_explicitly_decommands_every_controlled_output_and_request(self) -> None:
        for field in (
            "FillValve1", "FillValve2", "GateOpen", "GateClose", "ClampEngage", "ClampRelease",
            "CapperRequest", "CameraLight", "StackGreen", "StackAmber", "StackRed", "Audible",
        ):
            with self.subTest(output=field):
                self.assertIn(f'"DB_IO".Commands.{field} := FALSE;', self.startup)
        for command in (
            "Start", "ControlledStop", "Reset", "AlarmAck", "AutoMode", "ManualMode",
            "DispositionRemoved", "RecipeApply", "ManualConveyorJog", "ManualPumpJog",
            "ManualValve1", "ManualValve2", "ManualSecure",
        ):
            with self.subTest(command=command):
                self.assertIn(f'"DB_HMI".{command}.Request := FALSE;', self.startup)
        self.assertIn('%QW256 := W#16#047E; %QW258 := 0; %QW260 := W#16#047E; %QW262 := 0;', self.startup)

    def test_fault_recovery_requires_product_disposition_and_empty_cell(self) -> None:
        self.assertIn('DispositionRequired : Bool', self.coordinator)
        self.assertIn('#DispositionRequired := (NOT #PairAbsent) OR (#AutoStep <> "E_AutoStep".WAIT_PAIR)', self.coordinator)
        self.assertIn('IF #DispositionRequired THEN #State := "E_MachineState".HOLDING', self.coordinator)
        self.assertIn('#DispositionRemoved AND #PairAbsent AND NOT #BlockingFault', self.coordinator)
        self.assertIn('NOT "DB_IO".Inputs.Bottle1Present AND NOT "DB_IO".Inputs.Bottle2Present', self.cell)


if __name__ == "__main__":
    unittest.main()
