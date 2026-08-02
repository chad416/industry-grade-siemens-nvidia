import unittest
from plc_interface_harness import VisionContract, VisionResult


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
        for result in [VisionResult(True, 14, True, True, fault=True), VisionResult(True, 14, True, False)]:
            c = VisionContract(); c.trigger(14, 0, True, False)
            self.assertEqual(c.evaluate(100, True, 1, result), "HOLD_QUALITY")

    def test_heartbeat_loss(self):
        c = VisionContract(); c.trigger(15, 0, True, False); c.evaluate(1, True, 7, None)
        self.assertEqual(c.evaluate(1002, True, 7, None), "HOLD_HEALTH")


if __name__ == "__main__": unittest.main()
