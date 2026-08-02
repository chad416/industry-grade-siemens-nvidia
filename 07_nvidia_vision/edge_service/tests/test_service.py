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
        return InspectionResult(request.inspection_id, True, True, 2, 2, False, False, False, False, 25, self.controlled_identity[0], self.controlled_identity[1], request.session_epoch)


class EdgeServiceTests(unittest.TestCase):
    def request(self, inspection_id: int = 1, heartbeat: int = 1, session_epoch: int = 1) -> InspectionRequest:
        return InspectionRequest(inspection_id, 1, 2, 0.75, heartbeat, session_epoch)

    def service(self, backend=None, *, session_epoch: int = 1, observed_inspection_id: int = 0,
                observed_ack_id: int = 0, observed_plc_heartbeat: int = 0, **kwargs) -> VisionService:
        service = VisionService(backend or ControlledTestBackend(), **kwargs)
        service.reset(disabled=True, session_epoch=session_epoch,
                      observed_inspection_id=observed_inspection_id,
                      observed_ack_id=observed_ack_id,
                      observed_plc_heartbeat=observed_plc_heartbeat)
        return service

    def test_no_model_is_fail_closed(self) -> None:
        service = VisionService()
        self.assertFalse(service.state.ready)
        with self.assertRaises(ProtocolError): service.inspect(self.request())

    def test_controlled_backend_stays_not_ready_until_disabled_sync(self) -> None:
        service = VisionService(ControlledTestBackend())
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.diagnostic_code, "SESSION_SYNC_REQUIRED")
        with self.assertRaisesRegex(ProtocolError, "disabled session synchronization"):
            service.inspect(self.request())
        service.reset(disabled=True, session_epoch=1)
        self.assertTrue(service.state.ready)

    def test_controlled_backend_accepts_one_atomic_result(self) -> None:
        service = self.service()
        result = service.inspect(self.request())
        self.assertTrue(service.state.result_valid)
        self.assertTrue(quality_pass(result))

    def test_duplicate_id_is_rejected_and_service_faults_closed(self) -> None:
        service = self.service()
        service.inspect(self.request())
        service.acknowledge_result(1)
        with self.assertRaisesRegex(ProtocolError, "strictly monotonic"): service.inspect(self.request(1, 2))
        self.assertFalse(service.state.ready)

    def test_stale_heartbeat_is_rejected(self) -> None:
        service = self.service()
        service.inspect(self.request(1, 5))
        service.acknowledge_result(1)
        with self.assertRaisesRegex(ProtocolError, "PLC heartbeat is stale"): service.inspect(self.request(2, 5))

    def test_exactly_two_bottles_are_required(self) -> None:
        service = self.service()
        bad = InspectionRequest(1, 1, 1, 0.75, 1)
        with self.assertRaises(ProtocolError): service.inspect(bad)

    def test_simulator_normal_request_contract_is_accepted(self) -> None:
        service = self.service()
        result = service.inspect(InspectionRequest(1, 1, 2, 1.0, 1))
        self.assertTrue(quality_pass(result))

    def test_heartbeat_timeout_faults_closed(self) -> None:
        service = self.service(heartbeat_timeout_ms=1000)
        service.tick(1, 0)
        service.tick(1, 999)
        self.assertTrue(service.state.ready)
        service.tick(1, 1000)
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.fault, "PLC heartbeat timeout")

    def test_inspection_never_regresses_observed_heartbeat_or_timeout_age(self) -> None:
        service = self.service(heartbeat_timeout_ms=1000)
        service.tick(10, 0)
        service.inspect(self.request(1, 10))
        service.tick(10, 999)
        self.assertTrue(service.state.ready)
        service.tick(10, 1000)
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.heartbeat_last_change_ms, 0)

    def test_request_heartbeat_older_than_observed_counter_is_rejected(self) -> None:
        service = self.service()
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
                return InspectionResult(request.inspection_id, True, True, 2, 2, False, False, False, False, 25, "MODEL-B", "b" * 64, request.session_epoch)
        service = self.service(SwappingBackend())
        with self.assertRaises(ProtocolError):
            service.inspect(self.request())
        self.assertFalse(service.state.ready)

    def test_matching_ack_clears_publication_and_allows_next_id(self) -> None:
        service = self.service()
        service.inspect(self.request(1, 1))
        service.acknowledge_result(1)
        self.assertFalse(service.state.result_valid)
        result = service.inspect(self.request(2, 2))
        self.assertEqual(result.result_id, 2)

    def test_mismatched_ack_faults_closed(self) -> None:
        service = self.service()
        service.inspect(self.request(1, 1))
        with self.assertRaisesRegex(ProtocolError, "acknowledgement"):
            service.acknowledge_result(2)
        self.assertFalse(service.state.ready)

    def test_malformed_ack_never_clears_valid_publication(self) -> None:
        for malformed in (True, 1.0, -1, 0x1_0000_0000):
            service = self.service()
            service.inspect(self.request())
            with self.assertRaisesRegex(ProtocolError, "UDINT bounds"):
                service.acknowledge_result(malformed)
            self.assertTrue(service.state.result_valid)
            self.assertEqual(service.state.published_result_id, 1)

    def test_regressing_heartbeat_faults_immediately(self) -> None:
        service = self.service()
        service.tick(10, 0)
        service.tick(9, 1)
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.diagnostic_code, "PLC_HEARTBEAT_REGRESSION")

    def test_heartbeat_rollover_is_accepted(self) -> None:
        service = self.service()
        service.tick(0xFFFFFFFE, 0)
        service.tick(1, 1)
        self.assertTrue(service.state.ready)

    def test_delayed_backend_result_is_discarded(self) -> None:
        ticks = iter([0, 10])
        service = self.service(inference_timeout_ms=10, clock_ms=lambda: next(ticks))
        with self.assertRaisesRegex(ProtocolError, "deadline"):
            service.inspect(self.request())
        self.assertFalse(service.state.result_valid)

    def test_warning_bearing_pass_claim_is_rejected(self) -> None:
        class WarningBackend(ControlledTestBackend):
            def infer(self, request: InspectionRequest) -> InspectionResult:
                return InspectionResult(request.inspection_id, True, True, 2, 2, False, False, True, False, 25, self.controlled_identity[0], self.controlled_identity[1], request.session_epoch)
        with self.assertRaisesRegex(ProtocolError, "blocking quality"):
            self.service(WarningBackend()).inspect(self.request())

    def test_per_channel_pass_fill_contradiction_is_rejected(self) -> None:
        class ContradictoryBackend(ControlledTestBackend):
            def infer(self, request: InspectionRequest) -> InspectionResult:
                return InspectionResult(request.inspection_id, True, False, 1, 1, False, False, False, False, 25, self.controlled_identity[0], self.controlled_identity[1], request.session_epoch)
        with self.assertRaisesRegex(ProtocolError, "bottle 1"):
            self.service(ContradictoryBackend()).inspect(self.request())

    def test_heartbeat_rollover_allows_next_inspection(self) -> None:
        service = self.service()
        service.tick(0xFFFFFFFE, 0)
        service.inspect(self.request(1, 0xFFFFFFFE))
        service.acknowledge_result(1)
        service.tick(1, 1)
        result = service.inspect(self.request(2, 1))
        self.assertEqual(result.result_id, 2)

    def test_new_session_requires_disabled_sync_and_restarts_id_space(self) -> None:
        service = self.service()
        service.inspect(self.request(10, 10, 1))
        with self.assertRaisesRegex(ProtocolError, "disabled synchronization"):
            service.inspect(self.request(1, 1, 2))
        service.reset(disabled=True, session_epoch=2, observed_inspection_id=0,
                      observed_ack_id=0, observed_plc_heartbeat=1)
        result = service.inspect(self.request(1, 2, 2))
        self.assertEqual((result.result_id, result.session_epoch), (1, 2))
        self.assertEqual(service.state.session_epoch, 2)

    def test_session_regression_faults_closed(self) -> None:
        service = self.service(session_epoch=2)
        service.inspect(self.request(1, 1, 2)); service.acknowledge_result(1)
        with self.assertRaisesRegex(ProtocolError, "session change"):
            service.inspect(self.request(2, 2, 1))

    def test_disabled_reset_rearms_fault_without_reopening_id_replay(self) -> None:
        service = self.service()
        with self.assertRaises(ProtocolError):
            service.inspect(InspectionRequest(1, 70000, 2, 0.75, 1, 1))
        with self.assertRaisesRegex(ProtocolError, "VISION_ENABLE low"):
            service.reset(disabled=False)
        service.reset(disabled=True, session_epoch=1)
        self.assertTrue(service.state.ready)
        self.assertEqual(service.inspect(self.request(1, 1, 1)).result_id, 1)

    def test_cold_restart_same_session_seeds_plc_counter_baselines(self) -> None:
        service = self.service(observed_inspection_id=17, observed_ack_id=16,
                               observed_plc_heartbeat=90)
        with self.assertRaisesRegex(ProtocolError, "strictly monotonic"):
            service.inspect(self.request(17, 91, 1))
        service.reset(disabled=True, session_epoch=1, observed_inspection_id=17,
                      observed_ack_id=16, observed_plc_heartbeat=90)
        self.assertEqual(service.inspect(self.request(18, 91, 1)).result_id, 18)

    def test_seeded_prior_ack_poll_does_not_clear_new_publication(self) -> None:
        service = self.service(observed_inspection_id=1, observed_ack_id=1,
                               observed_plc_heartbeat=10)
        service.inspect(self.request(2, 11, 1))
        service.acknowledge_result(1)
        self.assertTrue(service.state.result_valid)
        self.assertEqual(service.state.published_result_id, 2)

    def test_reset_rejects_incoherent_plc_counter_snapshot(self) -> None:
        service = VisionService(ControlledTestBackend())
        with self.assertRaisesRegex(ProtocolError, "cannot exceed"):
            service.reset(disabled=True, session_epoch=1,
                          observed_inspection_id=4, observed_ack_id=5)

    def test_service_ingress_rejects_boolean_counters(self) -> None:
        service = self.service()
        service.tick(True, 0, 1)
        self.assertFalse(service.state.ready)
        service.reset(disabled=True, session_epoch=1)
        with self.assertRaises(ProtocolError):
            service.inspect(InspectionRequest(True, 1, 2, 0.75, 1, 1))

    def test_runtime_model_identity_change_faults_closed(self) -> None:
        backend = ControlledTestBackend()
        service = self.service(backend)
        backend.controlled_identity = ("MODEL-SWAPPED", "b" * 64)
        with self.assertRaisesRegex(ProtocolError, "changed"):
            service.inspect(self.request())
        self.assertFalse(service.state.ready)

    def test_level_polled_matching_ack_is_idempotent(self) -> None:
        service = self.service()
        service.inspect(self.request()); service.acknowledge_result(1)
        service.acknowledge_result(1)
        self.assertTrue(service.state.ready)

    def test_prior_ack_level_is_ignored_while_new_result_waits(self) -> None:
        service = self.service()
        service.inspect(self.request(1, 1)); service.acknowledge_result(1)
        service.inspect(self.request(2, 2))
        service.acknowledge_result(1)
        self.assertTrue(service.state.result_valid)
        self.assertEqual(service.state.published_result_id, 2)

    def test_vision_heartbeat_wraps_as_udint(self) -> None:
        service = self.service()
        service.state.vision_heartbeat = 0xFFFFFFFF
        service.tick(1, 0)
        self.assertEqual(service.state.vision_heartbeat, 0)

    def test_plc_type_bounds_are_enforced(self) -> None:
        service = self.service()
        with self.assertRaises(ProtocolError):
            service.inspect(InspectionRequest(0x1_0000_0000, 1, 2, 0.75, 1, 1))
        class LongIdentityBackend(ControlledTestBackend):
            controlled_identity = ("X" * 33, "a" * 64)
        self.assertFalse(VisionService(LongIdentityBackend()).state.ready)

    def test_malformed_identity_shapes_and_property_failure_stay_not_ready(self) -> None:
        malformed = [(), ("MODEL",), ("MODEL", "a" * 64, "EXTRA"),
                     ["MODEL", "a" * 64], {"model":"MODEL", "hash":"a" * 64}]
        for identity in malformed:
            class Backend(ControlledTestBackend):
                controlled_identity = identity
            service = VisionService(Backend())
            self.assertFalse(service.state.ready)
            self.assertEqual(service.state.diagnostic_code, "NO_CONTROLLED_MODEL")

        class RaisingBackend(ControlledTestBackend):
            @property
            def controlled_identity(self):
                raise RuntimeError("identity store unavailable")
        service = VisionService(RaisingBackend())
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.diagnostic_code, "NO_CONTROLLED_MODEL")

    def test_rearm_uses_single_validated_identity_read_and_catches_transition_failure(self) -> None:
        class ThirdReadRaises(ControlledTestBackend):
            reads = 0
            @property
            def controlled_identity(self):
                self.reads += 1
                if self.reads >= 3:
                    raise RuntimeError("identity store changed during rearm")
                return ("TEST-BACKEND-NOT-A-MODEL", "a" * 64)
        service = VisionService(ThirdReadRaises())
        service.reset(disabled=True, session_epoch=1)
        self.assertTrue(service.state.ready)
        self.assertEqual(service.backend.reads, 2)

        class SecondReadRaises(ThirdReadRaises):
            @property
            def controlled_identity(self):
                self.reads += 1
                if self.reads >= 2:
                    raise RuntimeError("identity store unavailable during rearm")
                return ("TEST-BACKEND-NOT-A-MODEL", "a" * 64)
        service = VisionService(SecondReadRaises())
        service.reset(disabled=True, session_epoch=1)
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.diagnostic_code, "NO_CONTROLLED_MODEL")


if __name__ == "__main__": unittest.main()
