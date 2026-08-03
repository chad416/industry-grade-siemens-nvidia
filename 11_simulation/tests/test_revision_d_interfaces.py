import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interface_models import FillChannelDiagnosticModel, FillCompletionModel, FillDiag, QualityArbitrationModel, UINT32_MAX, VisionDiag, VisionInterfaceModel


class VisionContractTests(unittest.TestCase):
    def arm(self, model: VisionInterfaceModel, inspection_id: int = 1) -> None:
        model.scan(trigger_edge=True, inspection_id=inspection_id, heartbeat=1)
        self.assertTrue(model.trigger)

    def test_stale_id_terminates_transaction_and_holds(self):
        m = VisionInterfaceModel(); self.arm(m, 10)
        m.scan(result_valid=True, result_id=9, heartbeat=2)
        self.assertEqual((m.diag, m.pending, m.trigger, m.hold), (VisionDiag.RESULT_ID_MISMATCH, False, False, True))

    def test_future_id_is_rejected(self):
        m = VisionInterfaceModel(); self.arm(m, 10)
        m.scan(result_valid=True, result_id=11, heartbeat=2)
        self.assertEqual(m.diag, VisionDiag.RESULT_ID_MISMATCH)

    def test_duplicate_request_id_is_never_retriggered(self):
        m = VisionInterfaceModel(); self.arm(m, 10)
        m.scan(result_valid=True, result_id=9, heartbeat=2)
        m.scan(reset_edge=True, heartbeat=3)
        m.scan(trigger_edge=True, inspection_id=10, heartbeat=4)
        self.assertEqual(m.diag, VisionDiag.NON_MONOTONIC_REQUEST)
        self.assertFalse(m.trigger)

    def test_result_valid_stuck_high(self):
        m = VisionInterfaceModel(timeout_ms=20); self.arm(m, 1)
        m.scan(result_valid=True, result_id=1, heartbeat=2, dt_ms=10)
        m.scan(result_valid=True, result_id=1, heartbeat=3, dt_ms=10)
        self.assertFalse(m.fault)
        m.scan(result_valid=True, result_id=1, heartbeat=4, dt_ms=10)
        self.assertTrue(m.fault and m.result_stuck_high)

    def test_acknowledgement_clear_window_is_not_unsolicited(self):
        m = VisionInterfaceModel(timeout_ms=30); self.arm(m, 1)
        m.scan(result_valid=True, result_id=1, heartbeat=2, dt_ms=10)
        m.scan(result_valid=True, result_id=1, heartbeat=3, dt_ms=10)
        self.assertFalse(m.fault)
        m.scan(result_valid=False, heartbeat=4, dt_ms=10)
        self.assertFalse(m.result_must_clear)
        m.scan(trigger_edge=True, inspection_id=2, heartbeat=5)
        self.assertTrue(m.trigger)

    def test_busy_ready_contradiction(self):
        m = VisionInterfaceModel(); m.scan(ready=False, busy=True, heartbeat=1)
        self.assertEqual(m.diag, VisionDiag.INTERFACE_CONTRADICTION)

    def test_busy_result_contradiction_is_never_accepted(self):
        m = VisionInterfaceModel(); self.arm(m, 1)
        m.scan(ready=True, busy=True, result_valid=True, result_id=1, heartbeat=2)
        self.assertEqual(m.diag, VisionDiag.INTERFACE_CONTRADICTION)
        self.assertTrue(m.fault and m.hold)
        self.assertFalse(m.accepted or m.quality_pass)

    def test_warning_bearing_result_holds_quality(self):
        m = VisionInterfaceModel(); self.arm(m, 1)
        m.scan(result_valid=True, result_id=1, result_warning=True, heartbeat=2)
        self.assertTrue(m.accepted and m.hold)
        self.assertFalse(m.quality_pass)
        self.assertEqual(m.diag, VisionDiag.QUALITY_BLOCK)

    def test_result_session_must_match_latched_request(self):
        m = VisionInterfaceModel(); m.scan(trigger_edge=True, inspection_id=1, session_epoch=7, heartbeat=1)
        m.scan(result_valid=True, result_id=1, session_epoch=7, result_session_epoch=6, heartbeat=2)
        self.assertEqual(m.diag, VisionDiag.SESSION_MISMATCH)
        self.assertFalse(m.accepted)

    def test_heartbeat_regression_latches_until_disable_reseed(self):
        m = VisionInterfaceModel(); self.arm(m, 1)
        m.scan(heartbeat=10)
        m.scan(heartbeat=9)
        self.assertTrue(m.fault)
        m.scan(reset_edge=True, heartbeat=9)
        self.assertTrue(m.fault)
        m.scan(enable=False, heartbeat=9)
        m.scan(enable=True, heartbeat=9)
        m.scan(reset_edge=True, heartbeat=9)
        self.assertFalse(m.fault)

    def test_timeout_then_delayed_result_never_accepts(self):
        m = VisionInterfaceModel(timeout_ms=20); self.arm(m, 1)
        m.scan(heartbeat=2, dt_ms=20)
        self.assertEqual(m.diag, VisionDiag.RESULT_TIMEOUT)
        self.assertTrue(m.result_must_clear)
        m.scan(enable=False, result_valid=True, result_id=1, heartbeat=3)
        self.assertFalse(m.accepted)
        self.assertTrue(m.publication_ack)
        self.assertTrue(m.hold)

    def test_reset_after_stale_requires_result_low_and_new_id(self):
        m = VisionInterfaceModel(); self.arm(m, 1)
        m.scan(result_valid=True, result_id=2, heartbeat=2)
        m.scan(reset_edge=True, result_valid=True, result_id=2, heartbeat=3)
        self.assertTrue(m.fault)
        m.scan(reset_edge=True, result_valid=False, heartbeat=4)
        self.assertFalse(m.fault)
        m.scan(trigger_edge=True, inspection_id=2, heartbeat=5)
        self.assertTrue(m.trigger)

    def test_reset_does_not_restart(self):
        m = VisionInterfaceModel(); self.arm(m, 1)
        m.scan(result_valid=True, result_id=2, heartbeat=2)
        m.scan(reset_edge=True, heartbeat=3)
        self.assertFalse(m.trigger or m.pending or m.accepted)

    def test_disabled_heartbeat_supervision_is_suppressed(self):
        m = VisionInterfaceModel(heartbeat_timeout_ms=10)
        for _ in range(5): m.scan(enable=False, heartbeat=0, dt_ms=10)
        self.assertTrue(m.heartbeat_healthy)
        self.assertFalse(m.fault)

    def test_deadline_scan_result_has_declared_success_precedence(self):
        m = VisionInterfaceModel(timeout_ms=20); self.arm(m, 1)
        m.scan(result_valid=True, result_id=1, heartbeat=2, dt_ms=20)
        self.assertTrue(m.accepted)
        self.assertFalse(m.fault)


class FillDiagnosticTests(unittest.TestCase):
    def model(self, timeout: float = 1.0) -> FillChannelDiagnosticModel:
        return FillChannelDiagnosticModel(timeout_s=timeout)

    def settle(self, m: FillChannelDiagnosticModel) -> None:
        m.observe_window(pulse_flow=0.0, analog_flow=0.0, dt_s=0.5)
        self.assertFalse(m.fault)

    def test_both_measurements_no_flow(self):
        m=self.model(); self.settle(m); m.observe_window(pulse_flow=0, analog_flow=0, dt_s=1.0)
        self.assertEqual(m.diag, FillDiag.NO_FLOW)

    def test_pulse_zero_analog_positive(self):
        m=self.model(); self.settle(m); m.observe_window(pulse_flow=0, analog_flow=5, dt_s=1.0)
        self.assertEqual(m.diag, FillDiag.PULSE_MISSING)

    def test_analog_zero_pulses_positive(self):
        m=self.model(); self.settle(m); m.observe_window(pulse_flow=5, analog_flow=0, dt_s=1.0)
        self.assertEqual(m.diag, FillDiag.ANALOG_NO_FLOW)

    def test_broken_wire_is_distinct(self):
        m=self.model(); m.observe_window(pulse_flow=5, analog_flow=0, dt_s=0, analog_fault=True)
        self.assertEqual(m.diag, FillDiag.ANALOG_BROKEN_WIRE)

    def test_excessive_disagreement(self):
        m=self.model(); self.settle(m); m.observe_window(pulse_flow=8, analog_flow=4, dt_s=1.0)
        self.assertEqual(m.diag, FillDiag.PULSE_ANALOG_DISAGREE)

    def test_timer_boundary_and_preboundary(self):
        m=self.model(); self.settle(m); m.observe_window(pulse_flow=0, analog_flow=5, dt_s=0.999)
        self.assertFalse(m.fault)
        m.observe_window(pulse_flow=0, analog_flow=5, dt_s=0.001)
        self.assertEqual(m.diag, FillDiag.PULSE_MISSING)

    def test_counter_rollover_is_valid_and_reported(self):
        m=self.model(); delta=m.counter_delta(UINT32_MAX-2, 3)
        self.assertEqual(delta, 6); self.assertTrue(m.rollover_observed); self.assertFalse(m.fault)

    def test_counter_regression_is_not_misclassified_as_rollover(self):
        m=self.model(); self.assertEqual(m.counter_delta(1000, 10), 0)
        self.assertEqual(m.diag, FillDiag.PULSE_COUNTER_DISCONTINUITY)

    def test_valve_close_and_continued_flow_are_distinct(self):
        a=self.model(); a.close_diagnostics(valve_closed=False, flow_present=False, elapsed_s=1)
        b=self.model(); b.close_diagnostics(valve_closed=True, flow_present=True, elapsed_s=1)
        self.assertEqual(a.diag, FillDiag.VALVE_CLOSE_MISMATCH)
        self.assertEqual(b.diag, FillDiag.CONTINUED_FLOW)

    def test_underfill_and_overfill_are_distinct(self):
        a=self.model(); a.complete(90,100,5,5)
        b=self.model(); b.complete(110,100,5,5)
        self.assertEqual(a.diag, FillDiag.UNDERFILL); self.assertEqual(b.diag, FillDiag.OVERFILL)

    def test_independent_channel_shutdown(self):
        bad=self.model(); good=self.model(); self.settle(bad); self.settle(good)
        bad.observe_window(pulse_flow=0, analog_flow=5, dt_s=1)
        good.observe_window(pulse_flow=5, analog_flow=5, dt_s=1)
        self.assertFalse(bad.pump_request); self.assertTrue(good.pump_request)

    def test_target_reached_on_deadline_scan_precedes_fill_timeout(self):
        m = FillCompletionModel()
        m.deadline_scan(target_reached=True, timeout_elapsed=True)
        self.assertEqual((m.fault, m.active, m.closing), (False, False, True))


class QualityArbitrationTests(unittest.TestCase):
    def test_quality_block_enters_holding_but_interlocks_outputs(self):
        m = QualityArbitrationModel()
        m.apply_vision(accepted=True, quality_pass=False, vision_fault=False, hold_required=True)
        self.assertEqual(m.state, "HOLDING")
        self.assertTrue(m.alarm_active)
        self.assertFalse(m.release_permissive)


if __name__ == "__main__":
    unittest.main()
