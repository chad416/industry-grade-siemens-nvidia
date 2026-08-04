from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
    from asyncua import Server, ua
    from asyncua.crypto.permission_rules import UserRole
    from asyncua.crypto.truststore import TrustStore
    from asyncua.crypto.validator import CertificateValidator, CertificateValidatorOptions
    from asyncua.server.user_managers import CertificateUserManager
    ASYNCUA_AVAILABLE = True
except ImportError:
    ASYNCUA_AVAILABLE = False

from observability import HealthServer, HealthSnapshot, Metrics
from opcua_adapter import (
    ALL_SIGNALS, EDGE_STATUS, EXPECTED_VARIANT_TYPES, PLC_OWNED, RESULT_PAYLOAD,
    AdapterConfig, OpcUaVisionAdapter, RuntimeOptions, SecurityOptions,
)
from protocol import (
    InspectionRequest, InspectionResult, ProcessingState, ProtocolError,
    ResultDisposition,
)
from service import VisionService

logging.getLogger("asyncua").setLevel(logging.CRITICAL)
logging.getLogger("asyncuagds.validate").setLevel(logging.CRITICAL)


class ControlledTestBackend:
    controlled_identity = ("TEST-BACKEND-NOT-A-MODEL", "a" * 64)
    production_authorized = True  # test fixture only; not a deployable backend
    camera_healthy = True

    def __init__(self, delay_s: float = 0.0) -> None:
        self.calls = 0
        self.delay_s = delay_s

    def infer(self, request: InspectionRequest) -> InspectionResult:
        self.calls += 1
        if self.delay_s:
            time.sleep(self.delay_s)
        return InspectionResult(
            request.inspection_id, True, True, 2, 2, False, False, False, False,
            25, self.controlled_identity[0], self.controlled_identity[1], request.session_epoch,
            capture_ack_id=request.inspection_id,
            processing_state=int(ProcessingState.RESULT_COMPLETE),
            disposition=int(ResultDisposition.PASS),
            confidence=0.99,
            dataset_id=request.expected_dataset_id,
            calibration_id=request.expected_calibration_id,
            capture_timestamp_utc_ms=1,
            inference_timestamp_utc_ms=2,
            publication_timestamp_utc_ms=2,
            processing_time_ms=25,
            service_healthy=True,
            camera_healthy=True,
            model_loaded=True,
        )


class TestAuditSink:
    healthy = True

    def probe(self) -> bool:
        return True

    def write(self, event: dict) -> None:
        self.last_event = dict(event)


class ObservabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_readiness_and_metrics_are_local_and_truthful(self) -> None:
        metrics = Metrics()
        metrics.increment("connections_total")
        metrics.gauge("ready", 0)
        snapshot = lambda: HealthSnapshot(True, True, False, False, False, 1, "NO_MODEL")
        server = HealthServer("127.0.0.1", 0, snapshot, metrics)
        await server.start()
        try:
            async def get(path: str) -> bytes:
                reader, writer = await asyncio.open_connection("127.0.0.1", server.bound_port)
                writer.write(f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode("ascii"))
                await writer.drain()
                response = await reader.read()
                writer.close()
                await writer.wait_closed()
                return response

            self.assertIn(b"200 OK", await get("/healthz"))
            self.assertIn(b"503 Service Unavailable", await get("/readyz"))
            metrics_response = await get("/metrics")
            self.assertIn(b"fc01_vision_edge_connections_total 1", metrics_response)
            self.assertIn(b"fc01_vision_edge_ready 0", metrics_response)
            self.assertIn(b"404 Not Found", await get("/unknown"))
        finally:
            await server.stop()

    async def test_health_endpoint_rejects_non_loopback_binding(self) -> None:
        with self.assertRaisesRegex(ValueError, "loopback"):
            HealthServer("0.0.0.0", 8088,
                         lambda: HealthSnapshot(True, False, False, False, False, 0, "STARTING"),
                         Metrics())


@unittest.skipUnless(ASYNCUA_AVAILABLE, "asyncua integration environment is not installed")
class SecureOpcUaIntegrationTests(unittest.IsolatedAsyncioTestCase):
    SERVER_URI = "urn:fc01:test:plc-server"
    CLIENT_URI = "urn:fc01:vision-edge:client"
    NAMESPACE_URI = "urn:fc01:test:vision-contract"

    @classmethod
    def _issue_certificate(cls, ca_key, ca_cert, common_name: str, uri: str, eku,
                           path: Path) -> tuple[Path, Path]:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)]))
            .issuer_name(ca_cert.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=30))
            .add_extension(x509.SubjectAlternativeName([
                x509.UniformResourceIdentifier(uri),
                x509.DNSName(socket.gethostname()),
                x509.DNSName("localhost"),
            ]), critical=False)
            .add_extension(x509.KeyUsage(
                digital_signature=True, content_commitment=True, key_encipherment=True,
                data_encipherment=True, key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=None, decipher_only=None,
            ), critical=True)
            .add_extension(x509.ExtendedKeyUsage([eku]), critical=False)
            .sign(ca_key, hashes.SHA256())
        )
        cert_path = path.with_suffix(".der")
        key_path = path.with_suffix(".pem")
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.DER))
        key_path.write_bytes(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
        return cert_path, key_path

    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        self.temp = tempfile.TemporaryDirectory(prefix="fc01-opcua-e2e-")
        root = Path(self.temp.name)
        self.server_trust = root / "server-trust"
        self.client_trust = root / "client-trust"
        self.crl = root / "crl"
        for directory in (self.server_trust, self.client_trust, self.crl):
            directory.mkdir()

        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = datetime.now(timezone.utc)
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "FC01 TEST CA")]))
            .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "FC01 TEST CA")]))
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=30))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=True, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=True,
                crl_sign=True, encipher_only=None, decipher_only=None,
            ), critical=True)
            .sign(ca_key, hashes.SHA256())
        )
        for directory in (self.server_trust, self.client_trust):
            (directory / "test-ca.der").write_bytes(ca_cert.public_bytes(serialization.Encoding.DER))

        self.server_cert, self.server_key = self._issue_certificate(
            ca_key, ca_cert, "FC01 TEST PLC", self.SERVER_URI,
            ExtendedKeyUsageOID.SERVER_AUTH, root / "server",
        )
        self.client_cert, self.client_key = self._issue_certificate(
            ca_key, ca_cert, "FC01 TEST VISION EDGE", self.CLIENT_URI,
            ExtendedKeyUsageOID.CLIENT_AUTH, root / "client",
        )

        user_manager = CertificateUserManager()
        await user_manager.add_role(self.client_cert, UserRole.User, "fc01-vision-test")
        self.server = Server(user_manager=user_manager)
        await self.server.init()
        await self.server.set_application_uri(self.SERVER_URI)
        self.server.set_server_name("FC01 secure OPC UA integration test server")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.endpoint = f"opc.tcp://127.0.0.1:{port}/fc01-test/"
        self.server.set_endpoint(self.endpoint)
        await self.server.load_certificate(self.server_cert)
        await self.server.load_private_key(self.server_key)
        self.server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
        self.server.set_identity_tokens([ua.X509IdentityToken])
        trust_store = TrustStore([self.server_trust], [self.crl])
        await trust_store.load()
        self.server.set_certificate_validator(CertificateValidator(
            CertificateValidatorOptions.TRUSTED_VALIDATION
            | CertificateValidatorOptions.PEER_CLIENT,
            trust_store,
        ))

        index = await self.server.register_namespace(self.NAMESPACE_URI)
        obj = await self.server.nodes.objects.add_object(index, "FC01Vision")
        self.server_nodes: dict[str, object] = {}
        default_for_type = {
            "Boolean": False, "UInt64": 0, "UInt32": 0, "UInt16": 0,
            "Byte": 0, "Float": 0.75, "String": "",
        }
        for signal in ALL_SIGNALS:
            variant_type = getattr(ua.VariantType, EXPECTED_VARIANT_TYPES[signal])
            node_id = ua.NodeId(f"FC01.Vision.{signal}", index)
            node = await obj.add_variable(node_id, signal,
                                          ua.Variant(default_for_type[variant_type.name], variant_type))
            if signal not in PLC_OWNED:
                await node.set_writable()
            self.server_nodes[signal] = node
        await self._plc_write("EXPECTED_BOTTLES", 2)
        await self._plc_write("VISION_SESSION_EPOCH", 1)
        await self._plc_write("EXPECTED_DATASET_ID", "DATASET-TEST")
        await self._plc_write("EXPECTED_CALIBRATION_ID", "CAL-TEST")
        await self.server.start()

        nodes = {signal: self.server_nodes[signal].nodeid.to_string() for signal in ALL_SIGNALS}
        security = SecurityOptions(
            application_uri=self.CLIENT_URI,
            certificate=self.client_cert,
            private_key=self.client_key,
            server_certificate=self.server_cert,
            trusted_certificates=self.client_trust,
            certificate_revocation_lists=self.crl,
            user_certificate=self.client_cert,
            user_private_key=self.client_key,
        )
        self.runtime = RuntimeOptions(
            poll_interval_ms=10, connect_timeout_ms=3000, operation_timeout_ms=1000,
            inference_timeout_ms=500, reconnect_initial_ms=10, reconnect_max_ms=50,
            reconnect_jitter_ms=0, coherent_snapshot_attempts=3,
        )
        self.config = AdapterConfig(self.endpoint, nodes, security, self.runtime)
        self.adapters: list[OpcUaVisionAdapter] = []

    async def asyncTearDown(self) -> None:
        for adapter in reversed(self.adapters):
            await adapter.disconnect()
        await self.server.stop()
        self.temp.cleanup()

    async def _plc_write(self, signal: str, value) -> None:
        variant_type = getattr(ua.VariantType, EXPECTED_VARIANT_TYPES[signal])
        await self.server_nodes[signal].write_value(ua.Variant(value, variant_type))

    async def _read(self, signal: str):
        return await self.server_nodes[signal].read_value()

    async def _adapter(self, backend=None, runtime=None) -> OpcUaVisionAdapter:
        service = VisionService(backend or ControlledTestBackend(), audit_sink=TestAuditSink())
        config = AdapterConfig(self.endpoint, self.config.nodes, self.config.security,
                               runtime or self.runtime)
        adapter = OpcUaVisionAdapter(config, service)
        await adapter.connect()
        self.adapters.append(adapter)
        return adapter

    async def test_secure_named_client_endpoint_and_atomic_acknowledged_result(self) -> None:
        backend = ControlledTestBackend()
        adapter = await self._adapter(backend)
        writes: list[dict] = []
        original_write = adapter._write_typed

        async def observed_write(values):
            writes.append(dict(values))
            await original_write(values)

        adapter._write_typed = observed_write
        endpoints = await self.server.get_endpoints()
        self.assertTrue(endpoints)
        self.assertTrue(all(ep.SecurityMode == ua.MessageSecurityMode.SignAndEncrypt for ep in endpoints))
        self.assertTrue(all(ep.SecurityPolicyUri.endswith("#Basic256Sha256") for ep in endpoints))
        self.assertTrue(all(all(token.TokenType != ua.UserTokenType.Anonymous
                                for token in ep.UserIdentityTokens) for ep in endpoints))
        self.assertTrue(await self._read("VISION_READY"))

        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", True),
            ("INSPECTION_ID", 1), ("RECIPE_ID", 1),
            ("EXPECTED_BOTTLES", 2), ("TARGET_FILL_LEVEL", 0.75),
            ("PLC_HEARTBEAT", 1),
        ):
            await self._plc_write(signal, value)
        await adapter.run_cycle()

        self.assertEqual(backend.calls, 1)
        self.assertTrue(await self._read("RESULT_VALID"))
        self.assertEqual(await self._read("RESULT_ID"), 1)
        self.assertEqual(adapter.last_result_write_order[-1], "RESULT_VALID")
        self.assertEqual(tuple(adapter.last_result_write_order[:-1]), RESULT_PAYLOAD)
        valid_write = next(index for index, values in enumerate(writes)
                           if values == {"RESULT_VALID": True})
        terminal_write = max(index for index, values in enumerate(writes[:valid_write])
                             if values.get("VISION_BUSY") is False
                             and values.get("PROCESSING_STATE") == int(ProcessingState.RESULT_COMPLETE))
        self.assertLess(terminal_write, valid_write)

        await self._plc_write("INSPECTION_TRIGGER", False)
        await self._plc_write("VISION_RESULT_ACK_ID", 1)
        await adapter.run_cycle()
        self.assertFalse(await self._read("RESULT_VALID"))
        self.assertFalse(adapter.service.state.result_valid)

    async def test_untrusted_server_certificate_is_rejected(self) -> None:
        empty_trust = Path(self.temp.name) / "empty-trust"
        empty_trust.mkdir()
        security = SecurityOptions(
            application_uri=self.CLIENT_URI,
            certificate=self.client_cert,
            private_key=self.client_key,
            server_certificate=self.server_cert,
            trusted_certificates=empty_trust,
            certificate_revocation_lists=self.crl,
            user_certificate=self.client_cert,
            user_private_key=self.client_key,
        )
        adapter = OpcUaVisionAdapter(
            AdapterConfig(self.endpoint, self.config.nodes, security, self.runtime),
            VisionService(ControlledTestBackend(), audit_sink=TestAuditSink()),
        )
        with self.assertRaisesRegex(Exception, "Untrusted|untrusted"):
            await adapter.connect()
        self.assertFalse(adapter.connected)

    async def test_cold_process_restart_adopts_unacknowledged_server_publication(self) -> None:
        first_backend = ControlledTestBackend()
        first = await self._adapter(first_backend)
        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", True),
            ("INSPECTION_ID", 1), ("RECIPE_ID", 1),
            ("EXPECTED_BOTTLES", 2), ("TARGET_FILL_LEVEL", 0.75),
            ("PLC_HEARTBEAT", 1),
        ):
            await self._plc_write(signal, value)
        await first.run_cycle()
        retained = {name: await self._read(name) for name in RESULT_PAYLOAD}
        await self._plc_write("VISION_ENABLE", False)
        await self._plc_write("INSPECTION_TRIGGER", False)
        await first.disconnect()
        self.adapters.remove(first)

        restarted_backend = ControlledTestBackend()
        restarted = await self._adapter(restarted_backend)
        self.assertTrue(restarted.service.state.result_valid)
        self.assertEqual(restarted.service.events[-1]["event"], "publication_restored_after_restart")
        self.assertEqual(restarted_backend.calls, 0)
        self.assertEqual(retained, {name: await self._read(name) for name in RESULT_PAYLOAD})
        self.assertTrue(await self._read("RESULT_VALID"))

        await self._plc_write("VISION_RESULT_ACK_ID", 1)
        await restarted.run_cycle()
        self.assertFalse(await self._read("RESULT_VALID"))

    async def test_same_process_transport_reconnect_preserves_unacknowledged_result(self) -> None:
        backend = ControlledTestBackend()
        adapter = await self._adapter(backend)
        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", True),
            ("INSPECTION_ID", 1), ("RECIPE_ID", 1),
            ("EXPECTED_BOTTLES", 2), ("TARGET_FILL_LEVEL", 0.75),
            ("PLC_HEARTBEAT", 1),
        ):
            await self._plc_write(signal, value)
        await adapter.run_cycle()
        retained = {name: await self._read(name) for name in RESULT_PAYLOAD}
        await self._plc_write("VISION_ENABLE", False)
        await self._plc_write("INSPECTION_TRIGGER", False)

        await adapter.disconnect()
        await adapter.connect()
        self.assertTrue(adapter.service.state.result_valid)
        self.assertEqual(adapter.service.events[-1]["event"], "transport_resumed")
        self.assertEqual(backend.calls, 1)
        self.assertEqual(retained, {name: await self._read(name) for name in RESULT_PAYLOAD})

        await self._plc_write("VISION_RESULT_ACK_ID", 1)
        await adapter.run_cycle()
        self.assertFalse(await self._read("RESULT_VALID"))

    async def test_payload_mutation_before_ack_faults_without_overwriting_plc_input(self) -> None:
        adapter = await self._adapter()
        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", True),
            ("INSPECTION_ID", 1), ("RECIPE_ID", 1),
            ("EXPECTED_BOTTLES", 2), ("TARGET_FILL_LEVEL", 0.75),
            ("PLC_HEARTBEAT", 1), ("VISION_DIAG_REASON", 77),
        ):
            await self._plc_write(signal, value)
        await adapter.run_cycle()
        await self.server_nodes["RESULT_ID"].write_value(ua.Variant(2, ua.VariantType.UInt32))
        with self.assertRaisesRegex(ProtocolError, "immutable"):
            await adapter.run_cycle()
        self.assertEqual(await self._read("VISION_DIAG_REASON"), 77)
        self.assertEqual(adapter.service.state.diagnostic_code, "PUBLICATION_MUTATED")

    async def test_unsolicited_server_side_publication_fails_closed(self) -> None:
        adapter = await self._adapter()
        await self.server_nodes["RESULT_VALID"].write_value(
            ua.Variant(True, ua.VariantType.Boolean)
        )
        with self.assertRaisesRegex(ProtocolError, "unsolicited"):
            await adapter.run_cycle()
        self.assertEqual(adapter.service.state.diagnostic_code, "UNSOLICITED_PUBLICATION")
        self.assertFalse(adapter.service.state.ready)

    async def test_missed_one_scan_request_level_fails_closed(self) -> None:
        adapter = await self._adapter()
        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", False),
            ("INSPECTION_ID", 1), ("RECIPE_ID", 1),
            ("EXPECTED_BOTTLES", 2), ("TARGET_FILL_LEVEL", 0.75),
            ("PLC_HEARTBEAT", 1),
        ):
            await self._plc_write(signal, value)
        with self.assertRaisesRegex(ProtocolError, "request level"):
            await adapter.run_cycle()
        self.assertEqual(adapter.service.state.diagnostic_code, "REQUEST_LEVEL_MISSED")
        self.assertFalse(adapter.service.state.ready)

    async def test_bounded_deadline_prevents_late_result_publication(self) -> None:
        backend = ControlledTestBackend(delay_s=0.15)
        runtime = RuntimeOptions(
            poll_interval_ms=10, connect_timeout_ms=3000, operation_timeout_ms=1000,
            inference_timeout_ms=20, reconnect_initial_ms=10, reconnect_max_ms=50,
            reconnect_jitter_ms=0, coherent_snapshot_attempts=3,
        )
        adapter = await self._adapter(backend, runtime)
        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", True),
            ("INSPECTION_ID", 1), ("RECIPE_ID", 1),
            ("EXPECTED_BOTTLES", 2), ("TARGET_FILL_LEVEL", 0.75),
            ("PLC_HEARTBEAT", 1),
        ):
            await self._plc_write(signal, value)
        with self.assertRaisesRegex(ProtocolError, "deadline"):
            await adapter.run_cycle()
        await asyncio.sleep(0.2)
        self.assertFalse(adapter.service.state.result_valid)
        self.assertIsNone(adapter.service.published_result)
        self.assertFalse(await self._read("RESULT_VALID"))

    async def test_timeout_blocks_new_session_rearm_until_worker_has_exited(self) -> None:
        release_worker = threading.Event()

        class BlockingBackend(ControlledTestBackend):
            def infer(self, request: InspectionRequest) -> InspectionResult:
                self.calls += 1
                if self.calls == 1:
                    release_worker.wait(timeout=2.0)
                return InspectionResult(
                    request.inspection_id, True, True, 2, 2, False, False, False, False,
                    25, self.controlled_identity[0], self.controlled_identity[1], request.session_epoch,
                    capture_ack_id=request.inspection_id,
                    processing_state=int(ProcessingState.RESULT_COMPLETE),
                    disposition=int(ResultDisposition.PASS), confidence=0.99,
                    dataset_id=request.expected_dataset_id,
                    calibration_id=request.expected_calibration_id,
                    capture_timestamp_utc_ms=1, inference_timestamp_utc_ms=2,
                    publication_timestamp_utc_ms=2, processing_time_ms=25,
                    service_healthy=True, camera_healthy=True, model_loaded=True,
                )

        backend = BlockingBackend()
        runtime = RuntimeOptions(
            poll_interval_ms=10, connect_timeout_ms=3000, operation_timeout_ms=1000,
            inference_timeout_ms=20, reconnect_initial_ms=10, reconnect_max_ms=50,
            reconnect_jitter_ms=0, coherent_snapshot_attempts=3,
        )
        adapter = await self._adapter(backend, runtime)
        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", True),
            ("INSPECTION_ID", 1), ("RECIPE_ID", 1),
            ("EXPECTED_BOTTLES", 2), ("TARGET_FILL_LEVEL", 0.75),
            ("PLC_HEARTBEAT", 1),
        ):
            await self._plc_write(signal, value)
        with self.assertRaisesRegex(ProtocolError, "deadline"):
            await adapter.run_cycle()
        self.assertIsNotNone(adapter._timed_out_inference)
        self.assertTrue(adapter.service.state.busy)

        # A serially advanced disabled session must not reset shared state while
        # the old synchronous backend is still live.
        for signal, value in (
            ("VISION_ENABLE", False), ("INSPECTION_TRIGGER", False),
            ("INSPECTION_ID", 0), ("VISION_SESSION_EPOCH", 2),
            ("PLC_HEARTBEAT", 2),
        ):
            await self._plc_write(signal, value)
        await adapter.run_cycle()
        self.assertFalse(adapter.service.state.ready)
        self.assertTrue(adapter.service.state.busy)
        self.assertEqual(adapter.service.state.session_epoch, 1)

        # Enabling/triggering the new session while blocked cannot launch a
        # second backend call or publish a result.
        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", True),
            ("INSPECTION_ID", 1), ("PLC_HEARTBEAT", 3),
        ):
            await self._plc_write(signal, value)
        await adapter.run_cycle()
        self.assertEqual(backend.calls, 1)
        self.assertFalse(await self._read("RESULT_VALID"))

        release_worker.set()
        for _ in range(100):
            if adapter._timed_out_inference is None:
                break
            await asyncio.sleep(0.01)
        self.assertIsNone(adapter._timed_out_inference)
        self.assertFalse(adapter.service.state.ready)

        # Only now may disabled synchronization rearm the new session.
        for signal, value in (
            ("VISION_ENABLE", False), ("INSPECTION_TRIGGER", False),
            ("INSPECTION_ID", 0), ("PLC_HEARTBEAT", 4),
        ):
            await self._plc_write(signal, value)
        await adapter.run_cycle()
        self.assertTrue(adapter.service.state.ready)
        self.assertEqual(adapter.service.state.session_epoch, 2)

        for signal, value in (
            ("VISION_ENABLE", True), ("INSPECTION_TRIGGER", True),
            ("INSPECTION_ID", 1), ("PLC_HEARTBEAT", 5),
        ):
            await self._plc_write(signal, value)
        await adapter.run_cycle()
        self.assertEqual(backend.calls, 2)
        self.assertTrue(await self._read("RESULT_VALID"))


if __name__ == "__main__":
    unittest.main()
