import unittest
from plc_interface_harness import VisionContract, VisionResult
from protocol import InspectionRequest, InspectionResult
from service import VisionService


class ContractTests(unittest.TestCase):
    def test_normal(self):
        c = VisionContract(); self.assertEqual(c.trigger(10, 0, True, False), "TRIGGERED")
        self.assertEqual(c.evaluate(100, True, 1, VisionResult(True, 10, True, True)), "PASS")

    def test_timeout(self):
        c = VisionContract(); c.trigger(11, 0, True, False)
        self.assertEqual(c.evaluate(1001, True, 1, None), "HOLD_TIMEOUT")

    def test_stale_id(self):
        c = VisionContract(); c.trigger(12, 0, True, False)
        self.assertEqual(c.evaluate(100, True, 1, VisionResult(True, 9, True, True)), "HOLD_STALE_ID")

    def test_low_confidence(self):
        c = VisionContract(); c.trigger(13, 0, True, False)
        self.assertEqual(c.evaluate(100, True, 1, VisionResult(True, 13, True, True, low_confidence=True)), "HOLD_QUALITY")

    def test_fault_and_split_pass(self):
        for result in [VisionResult(True, 14, True, True, fault=True), VisionResult(True, 14, True, False), VisionResult(True, 14, True, True, warning=True)]:
            c = VisionContract(); c.trigger(14, 0, True, False)
            self.assertEqual(c.evaluate(100, True, 1, result), "HOLD_QUALITY")

    def test_heartbeat_loss(self):
        c = VisionContract(); c.trigger(15, 0, True, False); c.evaluate(1, True, 7, None)
        self.assertEqual(c.evaluate(1002, True, 7, None), "HOLD_HEALTH")

    def test_duplicate_request_requires_new_monotonic_id(self):
        c = VisionContract(); c.trigger(1, 0, True, False)
        c.evaluate(1, True, 1, VisionResult(True, 2, True, True))
        self.assertEqual(c.reset(ready=True, busy=False, result_valid=False), "RESET")
        self.assertEqual(c.trigger(1, 2, True, False), "HOLD_NONMONOTONIC_ID")

    def test_future_id_and_unsolicited_publication_hold(self):
        c = VisionContract(); c.trigger(10, 0, True, False)
        self.assertEqual(c.evaluate(1, True, 1, VisionResult(True, 11, True, True)), "HOLD_STALE_ID")
        c.reset(ready=True, busy=False, result_valid=False)
        self.assertEqual(c.evaluate(2, True, 2, VisionResult(True, 10, True, True)), "HOLD_UNSOLICITED_RESULT")

    def test_heartbeat_regression_holds_immediately(self):
        c = VisionContract(); c.trigger(1, 0, True, False); c.evaluate(1, True, 10, None)
        self.assertEqual(c.evaluate(2, True, 9, None), "HOLD_HEALTH")

    def test_result_session_mismatch_holds(self):
        c = VisionContract(); c.trigger(1, 0, True, False, session_epoch=2)
        result = VisionResult(True, 1, True, True, session_epoch=1)
        self.assertEqual(c.evaluate(1, True, 1, result), "HOLD_SESSION")

    def test_new_session_rearms_id_space(self):
        c = VisionContract(); self.assertEqual(c.trigger(10, 0, True, False), "TRIGGERED")
        self.assertEqual(c.trigger(1, 1, True, False, session_epoch=2), "TRIGGERED")

    def test_new_session_reseeds_heartbeat_baseline(self):
        c = VisionContract(); c.trigger(1, 0, True, False); c.evaluate(1, True, 10, None)
        c.trigger(1, 2, True, False, session_epoch=2)
        self.assertEqual(c.evaluate(3, True, 1, None), "WAIT")

    def test_acknowledgement_and_result_clear_gate_next_request(self):
        c = VisionContract(); c.trigger(1, 0, True, False)
        self.assertEqual(c.evaluate(1, True, 1, VisionResult(True, 1, True, True)), "PASS")
        self.assertEqual(c.acknowledgement(), 1)
        self.assertEqual(c.trigger(2, 2, True, False), "HOLD_NOT_READY")
        self.assertEqual(c.observe_publication_clear(False), "CLEARED")
        self.assertEqual(c.trigger(2, 3, True, False), "TRIGGERED")

    def test_timeout_boundaries_are_explicit(self):
        c = VisionContract(timeout_ms=100, heartbeat_timeout_ms=1000)
        c.trigger(1, 0, True, False)
        self.assertEqual(c.evaluate(100, True, 1, VisionResult(True, 1, True, True)), "PASS")
        d = VisionContract(timeout_ms=100, heartbeat_timeout_ms=1000)
        d.trigger(1, 0, True, False)
        self.assertEqual(d.evaluate(100, True, 1, None), "HOLD_TIMEOUT")
        h = VisionContract(timeout_ms=1000, heartbeat_timeout_ms=100)
        self.assertEqual(h.evaluate(0, True, 7, None), "IDLE")
        self.assertEqual(h.evaluate(100, True, 7, None), "HOLD_HEALTH")

    def test_rejected_delayed_publication_is_acked_cleared_and_rearmed(self):
        class Backend:
            controlled_identity = ("TEST-BACKEND-NOT-A-MODEL", "a" * 64)
            def infer(self, request):
                return InspectionResult(request.inspection_id, True, True, 2, 2,
                                        False, False, False, False, 1,
                                        self.controlled_identity[0], self.controlled_identity[1],
                                        request.session_epoch)

        edge = VisionService(Backend())
        edge.reset(disabled=True, session_epoch=1)
        published = edge.inspect(InspectionRequest(1, 1, 2, 0.75, 1, 1))

        plc = VisionContract(timeout_ms=100, heartbeat_timeout_ms=1000)
        self.assertEqual(plc.trigger(1, 0, True, False), "TRIGGERED")
        self.assertEqual(plc.evaluate(100, True, 1, None), "HOLD_TIMEOUT")
        delayed = VisionResult(True, published.result_id, published.bottle_1_pass,
                               published.bottle_2_pass, published.fill_1_status,
                               published.fill_2_status, session_epoch=published.session_epoch,
                               model_id=published.model_id, model_hash=published.model_hash)
        self.assertEqual(plc.evaluate(101, True, 2, delayed), "HOLD_UNSOLICITED_RESULT")
        edge.acknowledge_result(plc.acknowledgement())
        self.assertFalse(edge.state.result_valid)
        self.assertEqual(plc.observe_publication_clear(edge.state.result_valid), "CLEARED")
        self.assertEqual(plc.reset(ready=True, busy=False, result_valid=False), "RESET")
        self.assertEqual(plc.trigger(2, 102, True, False), "TRIGGERED")


if __name__ == "__main__": unittest.main()
