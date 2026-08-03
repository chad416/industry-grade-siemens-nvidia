import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from filling_cell_simulator import (
    FillStatus,
    FillingPlant,
    SimulationConfig,
    VisionDevice,
    VisionRequest,
    VisionResultPayload,
    evaluate_vision_contract,
)


class VisionProtocolTests(unittest.TestCase):
    def setUp(self):
        self.request = VisionRequest(inspection_id=42)
        self.passing = VisionResultPayload(
            result_id=42,
            bottle_1_pass=True,
            bottle_2_pass=True,
            fill_1_status=FillStatus.IN_RANGE,
            fill_2_status=FillStatus.IN_RANGE,
            inference_time_ms=360,
        )

    def evaluate(self, payload=None, **overrides):
        inputs = {
            "result_valid": True,
            "ready": True,
            "busy": False,
            "heartbeat_fresh": True,
        }
        inputs.update(overrides)
        return evaluate_vision_contract(self.request, payload or self.passing, **inputs)

    def test_matched_complete_result_is_accepted(self):
        decision = self.evaluate()
        self.assertTrue(decision.protocol_valid)
        self.assertTrue(decision.quality_pass)
        self.assertEqual(decision.reason, "VISION_ACCEPTED")

    def test_stale_id_is_rejected(self):
        stale = VisionResultPayload(
            result_id=41,
            bottle_1_pass=True,
            bottle_2_pass=True,
            fill_1_status=FillStatus.IN_RANGE,
            fill_2_status=FillStatus.IN_RANGE,
        )
        decision = self.evaluate(stale)
        self.assertFalse(decision.protocol_valid)
        self.assertEqual(decision.reason, "VISION_STALE_ID")

    def test_result_valid_while_busy_is_protocol_contradiction(self):
        decision = self.evaluate(busy=True)
        self.assertFalse(decision.protocol_valid)
        self.assertEqual(decision.reason, "VISION_BUSY_VALID_CONTRADICTION")

    def test_pass_with_underfill_is_semantic_contradiction(self):
        contradictory = VisionResultPayload(
            result_id=42,
            bottle_1_pass=True,
            bottle_2_pass=True,
            fill_1_status=FillStatus.UNDER,
            fill_2_status=FillStatus.IN_RANGE,
        )
        decision = self.evaluate(contradictory)
        self.assertFalse(decision.protocol_valid)
        self.assertEqual(decision.reason, "VISION_CHANNEL_1_SEMANTIC_CONTRADICTION")

    def test_leak_cannot_coexist_with_pass(self):
        contradictory = VisionResultPayload(
            result_id=42,
            bottle_1_pass=True,
            bottle_2_pass=True,
            fill_1_status=FillStatus.IN_RANGE,
            fill_2_status=FillStatus.IN_RANGE,
            leak_or_spill_detected=True,
        )
        decision = self.evaluate(contradictory)
        self.assertFalse(decision.protocol_valid)
        self.assertEqual(decision.reason, "VISION_LEAK_PASS_CONTRADICTION")

    def test_low_confidence_nonpass_is_valid_quality_hold(self):
        uncertain = VisionResultPayload(
            result_id=42,
            bottle_1_pass=False,
            bottle_2_pass=False,
            fill_1_status=FillStatus.IN_RANGE,
            fill_2_status=FillStatus.IN_RANGE,
            low_confidence=True,
        )
        decision = self.evaluate(uncertain)
        self.assertTrue(decision.protocol_valid)
        self.assertFalse(decision.quality_pass)
        self.assertEqual(decision.reason, "VISION_LOW_CONFIDENCE")

    def test_stale_heartbeat_and_faulted_service_never_accept(self):
        self.assertEqual(self.evaluate(heartbeat_fresh=False).reason, "VISION_HEARTBEAT_STALE")
        self.assertEqual(self.evaluate(ready=False).reason, "VISION_NOT_READY")

    def test_device_rejects_duplicate_nonmonotonic_inspection_id(self):
        config = SimulationConfig()
        plant = FillingPlant(config)
        plant.physical_volume_ml[:] = [500.0, 500.0]
        device = VisionDevice(config, "protocol_test")
        request = VisionRequest(7)
        self.assertTrue(device.receive_trigger(request))
        for heartbeat in range(30):
            device.step(plant, heartbeat)
        self.assertTrue(device.result_valid)
        self.assertFalse(device.receive_trigger(request))
        self.assertTrue(device.fault)
        self.assertEqual(device.fault_reason, "NON_MONOTONIC_INSPECTION_ID")

    def test_device_detects_stale_plc_heartbeat(self):
        config = SimulationConfig(dt_ms=50)
        plant = FillingPlant(config)
        device = VisionDevice(config, "protocol_test")
        for _ in range(40):
            device.step(plant, plc_heartbeat=1)
        self.assertTrue(device.fault)
        self.assertEqual(device.fault_reason, "PLC_HEARTBEAT_STALE")


if __name__ == "__main__":
    unittest.main()
