from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from protocol import InspectionRequest, InspectionResult, ProtocolError, quality_pass
from service import VisionService


class ControlledTestBackend:
    controlled_identity = ("TEST-BACKEND-NOT-A-MODEL", "a" * 64)

    def infer(self, request: InspectionRequest) -> InspectionResult:
        return InspectionResult(request.inspection_id, True, True, 2, 2, False, False, False, False, 25, self.controlled_identity[0], self.controlled_identity[1])


class EdgeServiceTests(unittest.TestCase):
    def request(self, inspection_id: int = 1, heartbeat: int = 1) -> InspectionRequest:
        return InspectionRequest(inspection_id, 1, 2, 0.75, heartbeat)

    def test_no_model_is_fail_closed(self) -> None:
        service = VisionService()
        self.assertFalse(service.state.ready)
        with self.assertRaises(ProtocolError): service.inspect(self.request())

    def test_controlled_backend_accepts_one_atomic_result(self) -> None:
        service = VisionService(ControlledTestBackend())
        result = service.inspect(self.request())
        self.assertTrue(service.state.result_valid)
        self.assertTrue(quality_pass(result))

    def test_duplicate_id_is_rejected_and_service_faults_closed(self) -> None:
        service = VisionService(ControlledTestBackend())
        service.inspect(self.request())
        with self.assertRaises(ProtocolError): service.inspect(self.request())
        self.assertFalse(service.state.ready)

    def test_stale_heartbeat_is_rejected(self) -> None:
        service = VisionService(ControlledTestBackend())
        service.inspect(self.request(1, 5))
        with self.assertRaisesRegex(ProtocolError, "PLC heartbeat is stale"): service.inspect(self.request(2, 5))

    def test_exactly_two_bottles_are_required(self) -> None:
        service = VisionService(ControlledTestBackend())
        bad = InspectionRequest(1, 1, 1, 0.75, 1)
        with self.assertRaises(ProtocolError): service.inspect(bad)

    def test_simulator_normal_request_contract_is_accepted(self) -> None:
        service = VisionService(ControlledTestBackend())
        result = service.inspect(InspectionRequest(1, 1, 2, 1.0, 1))
        self.assertTrue(quality_pass(result))

    def test_heartbeat_timeout_faults_closed(self) -> None:
        service = VisionService(ControlledTestBackend(), heartbeat_timeout_ms=1000)
        service.tick(1, 0)
        service.tick(1, 999)
        self.assertTrue(service.state.ready)
        service.tick(1, 1000)
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.fault, "PLC heartbeat timeout")

    def test_inspection_never_regresses_observed_heartbeat_or_timeout_age(self) -> None:
        service = VisionService(ControlledTestBackend(), heartbeat_timeout_ms=1000)
        service.tick(10, 0)
        service.inspect(self.request(1, 10))
        service.tick(10, 999)
        self.assertTrue(service.state.ready)
        service.tick(10, 1000)
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.heartbeat_last_change_ms, 0)

    def test_request_heartbeat_older_than_observed_counter_is_rejected(self) -> None:
        service = VisionService(ControlledTestBackend())
        service.tick(10, 0)
        with self.assertRaisesRegex(ProtocolError, "older than the observed counter"):
            service.inspect(self.request(1, 9))

    def test_non_hexadecimal_controlled_hash_is_rejected(self) -> None:
        class BadIdentityBackend(ControlledTestBackend):
            controlled_identity = ("MODEL-A", "z" * 64)
        self.assertFalse(VisionService(BadIdentityBackend()).state.ready)

    def test_result_identity_must_match_backend(self) -> None:
        class SwappingBackend(ControlledTestBackend):
            controlled_identity = ("MODEL-A", "a" * 64)
            def infer(self, request: InspectionRequest) -> InspectionResult:
                return InspectionResult(request.inspection_id, True, True, 2, 2, False, False, False, False, 25, "MODEL-B", "b" * 64)
        service = VisionService(SwappingBackend())
        with self.assertRaises(ProtocolError):
            service.inspect(self.request())
        self.assertFalse(service.state.ready)


if __name__ == "__main__": unittest.main()
