import json
from pathlib import Path
import sys
import unittest


SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM))

from revision_f_vision_sil import VisionReadinessSil, VisionScenario, load_scenarios, run_all  # noqa: E402


REQUIRED = {
    "normal_pass", "valid_fail", "hold_result", "ai_timeout", "heartbeat_loss",
    "camera_disconnected", "model_unavailable", "low_confidence", "malformed_result",
    "stale_result_id", "duplicate_result", "future_unknown_id", "delayed_after_timeout",
    "reordered_messages", "opcua_disconnect", "opcua_reconnection", "edge_service_restart",
    "plc_restart", "recipe_change_during_inspection", "clock_discontinuity",
    "log_storage_failure", "corrupt_configuration", "invalid_model_hash",
    "excessive_latency", "queue_saturation", "operator_bypass_request",
    "recovery_after_fault", "contradictory_result",
}


class RevisionFVisionSilTests(unittest.TestCase):
    def setUp(self):
        self.scenarios = load_scenarios()
        self.results = run_all()

    def test_requested_fault_matrix_is_complete_and_unique(self):
        names = [row.scenario for row in self.scenarios]
        self.assertEqual(set(names), REQUIRED)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 28)

    def test_only_exact_normal_pass_releases_product(self):
        released = [row.scenario for row in self.results if row.product_released]
        self.assertEqual(released, ["normal_pass"])

    def test_every_nonvalid_result_fails_closed(self):
        for row in self.results:
            with self.subTest(row.scenario):
                if row.result_class != "PASS":
                    self.assertFalse(row.product_released)
                    self.assertIn(row.final_state, {"HOLDING", "FAULTED", "STOPPED"})

    def test_vision_never_commands_process_outputs(self):
        for row in self.results:
            with self.subTest(row.scenario):
                self.assertFalse(row.pump_cmd or row.valve_1_cmd or row.valve_2_cmd)

    def test_restart_and_recovery_never_automatically_restart(self):
        for row in self.results:
            with self.subTest(row.scenario):
                self.assertFalse(row.automatic_restart)
        stopped = {row.scenario for row in self.results if row.final_state == "STOPPED"}
        self.assertEqual(stopped, {"plc_restart", "recovery_after_fault"})

    def test_identity_faults_are_rejected(self):
        rejected = {row.scenario for row in self.results if not row.identity_accepted}
        self.assertEqual(
            rejected,
            {"stale_result_id", "duplicate_result", "future_unknown_id", "delayed_after_timeout", "plc_restart"},
        )
        self.assertFalse(any(row.product_released for row in self.results if not row.identity_accepted))

    def test_every_blocked_case_has_specific_diagnostic_and_recovery(self):
        for row in self.results:
            with self.subTest(row.scenario):
                if not row.product_released:
                    self.assertNotEqual(row.diagnostic, "NONE")
                    self.assertNotEqual(row.explicit_recovery, "NONE")

    def test_output_is_deterministic(self):
        first = [row.as_row() for row in run_all()]
        second = [row.as_row() for row in run_all()]
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_zero_identity_is_refused(self):
        with self.assertRaises(ValueError):
            VisionReadinessSil(session_epoch=0, inspection_id=42)
        with self.assertRaises(ValueError):
            VisionReadinessSil(session_epoch=100, inspection_id=0)

    def test_policy_does_not_copy_expected_fields_from_scenario(self):
        wrong = VisionScenario(
            scenario="normal_pass",
            stimulus="healthy exact PASS",
            injection={},
            expected_state="FAULTED",
            diagnostic="WRONG",
            result_class="INVALID",
            identity_policy="STALE",
            recovery="RESET",
        )
        with self.assertRaisesRegex(AssertionError, "acceptance criteria"):
            VisionReadinessSil().run(wrong)

    def test_structured_injection_drives_behavior_independent_of_scenario_name(self):
        injected = VisionScenario(
            scenario="arbitrary_new_case",
            stimulus="edge heartbeat forced stale",
            injection={"heartbeat_ok": False},
            expected_state="FAULTED",
            diagnostic="EDGE_HEARTBEAT_LOSS",
            result_class="INVALID",
            identity_policy="EXACT",
            recovery="RESTORE_HEARTBEAT_RESET_NEW_REQUEST",
        )
        result = VisionReadinessSil().run(injected)
        self.assertEqual(result.diagnostic, "EDGE_HEARTBEAT_LOSS")
        self.assertFalse(result.product_released)


if __name__ == "__main__":
    unittest.main()
