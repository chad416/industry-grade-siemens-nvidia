"""Secure, fail-closed OPC UA transport for the FC01 vision contract.

This module contains no model and makes no inference-performance claim.  The
PLC remains the transaction and motion authority.  The adapter only transports
the controlled request/result contract to a :class:`VisionService` backend.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import random
import threading
import time
from typing import Any
from urllib.parse import urlparse

from observability import HealthSnapshot, Metrics
from protocol import InspectionRequest, InspectionResult, ProtocolError, UINT32_MAX, heartbeat_advance
from service import VisionService

try:  # The source-only D.1 tests still run without the optional OPC UA stack.
    from asyncua import Client, ua
    from asyncua.crypto import security_policies
    from asyncua.crypto.truststore import TrustStore
    from asyncua.crypto.validator import CertificateValidator, CertificateValidatorOptions
except ImportError:  # pragma: no cover - exercised by the locked integration environment
    Client = None
    ua = None
    security_policies = None
    TrustStore = None
    CertificateValidator = None
    CertificateValidatorOptions = None


PLC_OWNED = (
    "VISION_ENABLE", "INSPECTION_TRIGGER", "INSPECTION_ID", "RECIPE_ID",
    "EXPECTED_BOTTLES", "TARGET_FILL_LEVEL", "PLC_HEARTBEAT",
    "VISION_RESULT_ACK_ID", "VISION_SESSION_EPOCH", "VISION_DIAG_REASON",
)
EDGE_STATUS = ("VISION_READY", "VISION_BUSY", "VISION_HEARTBEAT")
RESULT_PAYLOAD = (
    "RESULT_ID", "BOTTLE_1_PASS", "BOTTLE_2_PASS", "FILL_1_STATUS",
    "FILL_2_STATUS", "LEAK_OR_SPILL_DETECTED", "LOW_CONFIDENCE",
    "VISION_WARNING", "VISION_FAULT", "INFERENCE_TIME",
    "VISION_RESULT_SESSION_EPOCH", "VISION_MODEL_ID", "VISION_MODEL_SHA256",
)
RESULT_VALID = "RESULT_VALID"
ALL_SIGNALS = PLC_OWNED + EDGE_STATUS + (RESULT_VALID,) + RESULT_PAYLOAD

# UA VariantType names are used here so the module remains importable when the
# optional asyncua dependency is absent.
EXPECTED_VARIANT_TYPES = {
    "VISION_ENABLE": "Boolean", "INSPECTION_TRIGGER": "Boolean",
    "INSPECTION_ID": "UInt32", "RECIPE_ID": "UInt16",
    "EXPECTED_BOTTLES": "Byte", "TARGET_FILL_LEVEL": "Float",
    "PLC_HEARTBEAT": "UInt32", "VISION_READY": "Boolean",
    "VISION_BUSY": "Boolean", "RESULT_VALID": "Boolean",
    "RESULT_ID": "UInt32", "BOTTLE_1_PASS": "Boolean",
    "BOTTLE_2_PASS": "Boolean", "FILL_1_STATUS": "Byte",
    "FILL_2_STATUS": "Byte", "LEAK_OR_SPILL_DETECTED": "Boolean",
    "LOW_CONFIDENCE": "Boolean", "VISION_WARNING": "Boolean",
    "VISION_FAULT": "Boolean", "INFERENCE_TIME": "UInt32",
    "VISION_HEARTBEAT": "UInt32", "VISION_RESULT_ACK_ID": "UInt32",
    "VISION_SESSION_EPOCH": "UInt32", "VISION_RESULT_SESSION_EPOCH": "UInt32",
    "VISION_DIAG_REASON": "UInt16", "VISION_MODEL_ID": "String",
    "VISION_MODEL_SHA256": "String",
}


@dataclass(frozen=True)
class RuntimeOptions:
    poll_interval_ms: int = 50
    connect_timeout_ms: int = 5_000
    operation_timeout_ms: int = 1_000
    inference_timeout_ms: int = 1_000
    reconnect_initial_ms: int = 250
    reconnect_max_ms: int = 5_000
    reconnect_jitter_ms: int = 100
    coherent_snapshot_attempts: int = 3

    def validate(self) -> None:
        for name in (
            "poll_interval_ms", "connect_timeout_ms", "operation_timeout_ms",
            "inference_timeout_ms", "reconnect_initial_ms", "reconnect_max_ms",
            "coherent_snapshot_attempts",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.reconnect_jitter_ms) is not int or self.reconnect_jitter_ms < 0:
            raise ValueError("reconnect_jitter_ms must be a nonnegative integer")
        if self.reconnect_initial_ms > self.reconnect_max_ms:
            raise ValueError("reconnect backoff bounds are inverted")


@dataclass(frozen=True)
class SecurityOptions:
    application_uri: str
    certificate: Path
    private_key: Path
    server_certificate: Path
    trusted_certificates: Path
    certificate_revocation_lists: Path
    user_certificate: Path
    user_private_key: Path
    policy: str = "Basic256Sha256"
    mode: str = "SignAndEncrypt"

    def validate(self) -> None:
        if self.policy != "Basic256Sha256" or self.mode != "SignAndEncrypt":
            raise ValueError("only Basic256Sha256/SignAndEncrypt is released")
        if not self.application_uri.startswith("urn:"):
            raise ValueError("OPC UA application URI must be a controlled URN")
        for name in (
            "certificate", "private_key", "server_certificate",
            "trusted_certificates", "certificate_revocation_lists",
            "user_certificate", "user_private_key",
        ):
            path = getattr(self, name)
            if not path.exists():
                raise ValueError(f"configured security path does not exist: {name}")
        if not self.trusted_certificates.is_dir() or not self.certificate_revocation_lists.is_dir():
            raise ValueError("trust and CRL locations must be directories")


@dataclass(frozen=True)
class AdapterConfig:
    endpoint: str
    nodes: dict[str, str]
    security: SecurityOptions
    runtime: RuntimeOptions

    @classmethod
    def from_files(cls, runtime_config_path: Path) -> "AdapterConfig":
        data = json.loads(runtime_config_path.read_text(encoding="utf-8"))
        contract_path = runtime_config_path.parent / data["contract_config"]
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        env_names = data["security"]["environment"]

        def env_path(key: str) -> Path:
            value = os.environ.get(env_names[key], "")
            if not value:
                raise ValueError(f"required security environment variable is absent: {env_names[key]}")
            return Path(value).expanduser().resolve()

        security = SecurityOptions(
            application_uri=data["security"]["application_uri"],
            certificate=env_path("application_certificate"),
            private_key=env_path("application_private_key"),
            server_certificate=env_path("server_certificate"),
            trusted_certificates=env_path("trusted_certificates"),
            certificate_revocation_lists=env_path("certificate_revocation_lists"),
            user_certificate=env_path("user_certificate"),
            user_private_key=env_path("user_private_key"),
            policy=data["security"]["policy"],
            mode=data["security"]["mode"],
        )
        runtime = RuntimeOptions(**data["runtime"])
        config = cls(contract["opcua_endpoint"], dict(contract["nodes"]), security, runtime)
        config.validate()
        return config

    def validate(self) -> None:
        endpoint = urlparse(self.endpoint)
        if endpoint.scheme != "opc.tcp" or not endpoint.hostname or endpoint.port is None:
            raise ValueError("OPC UA endpoint must be an explicit opc.tcp host and port")
        if endpoint.username or endpoint.password:
            raise ValueError("credentials are prohibited in the endpoint URL")
        if set(self.nodes) != set(ALL_SIGNALS):
            missing = sorted(set(ALL_SIGNALS) - set(self.nodes))
            extra = sorted(set(self.nodes) - set(ALL_SIGNALS))
            raise ValueError(f"node map differs from the 27-signal contract: missing={missing}, extra={extra}")
        if len(set(self.nodes.values())) != len(self.nodes):
            raise ValueError("node map contains duplicate NodeIds")
        self.runtime.validate()
        self.security.validate()


@dataclass(frozen=True)
class PlcSnapshot:
    values: dict[str, Any]

    @property
    def enabled(self) -> bool:
        return self.values["VISION_ENABLE"]

    @property
    def trigger(self) -> bool:
        return self.values["INSPECTION_TRIGGER"]

    @property
    def inspection_id(self) -> int:
        return self.values["INSPECTION_ID"]

    @property
    def acknowledgement_id(self) -> int:
        return self.values["VISION_RESULT_ACK_ID"]

    @property
    def plc_heartbeat(self) -> int:
        return self.values["PLC_HEARTBEAT"]

    @property
    def session_epoch(self) -> int:
        return self.values["VISION_SESSION_EPOCH"]

    @property
    def result_valid(self) -> bool:
        return self.values["RESULT_VALID"]

    def retained_result(self) -> InspectionResult:
        return InspectionResult(
            result_id=self.values["RESULT_ID"],
            bottle_1_pass=self.values["BOTTLE_1_PASS"],
            bottle_2_pass=self.values["BOTTLE_2_PASS"],
            fill_1_status=self.values["FILL_1_STATUS"],
            fill_2_status=self.values["FILL_2_STATUS"],
            leak_or_spill=self.values["LEAK_OR_SPILL_DETECTED"],
            low_confidence=self.values["LOW_CONFIDENCE"],
            vision_warning=self.values["VISION_WARNING"],
            vision_fault=self.values["VISION_FAULT"],
            inference_time_ms=self.values["INFERENCE_TIME"],
            model_id=self.values["VISION_MODEL_ID"],
            model_hash=self.values["VISION_MODEL_SHA256"],
            session_epoch=self.values["VISION_RESULT_SESSION_EPOCH"],
        )


class OpcUaVisionAdapter:
    """One secure OPC UA connection supervising one :class:`VisionService`."""

    def __init__(self, config: AdapterConfig, service: VisionService, *,
                 metrics: Metrics | None = None, logger: logging.Logger | None = None,
                 clock_ms=None) -> None:
        config.validate()
        if Client is None:
            raise RuntimeError("asyncua is not installed; use requirements-opcua.txt")
        self.config = config
        self.service = service
        self.metrics = metrics or Metrics()
        self.logger = logger or logging.getLogger("fc01.vision.edge")
        self.clock_ms = clock_ms or (lambda: time.monotonic_ns() // 1_000_000)
        self.client: Client | None = None
        self.nodes: dict[str, Any] = {}
        self.connected = False
        self._trigger_consumed_id = 0
        self._timed_out_inference: asyncio.Task | None = None
        self._last_result_write_order: list[str] = []
        self._set_metrics()

    @property
    def last_result_write_order(self) -> tuple[str, ...]:
        return tuple(self._last_result_write_order)

    def health_snapshot(self) -> HealthSnapshot:
        return HealthSnapshot(
            alive=True,
            connected=self.connected,
            ready=self.service.state.ready,
            busy=self.service.state.busy,
            result_valid=self.service.state.result_valid,
            session_epoch=self.service.state.session_epoch,
            diagnostic_code=self.service.state.diagnostic_code,
        )

    async def _bounded(self, awaitable, timeout_ms: int | None = None):
        return await asyncio.wait_for(
            awaitable,
            (timeout_ms or self.config.runtime.operation_timeout_ms) / 1000,
        )

    async def connect(self) -> None:
        if self.connected:
            return
        security = self.config.security
        trust_store = TrustStore(
            [security.trusted_certificates], [security.certificate_revocation_lists],
        )
        await trust_store.load()
        client = Client(
            self.config.endpoint,
            timeout=self.config.runtime.operation_timeout_ms / 1000,
            watchdog_intervall=max(self.config.runtime.poll_interval_ms / 1000, 0.05),
            auto_reconnect=False,
        )
        client.name = "FC01 Vision Edge OPC UA Client"
        client.application_uri = security.application_uri
        options = (
            CertificateValidatorOptions.TRUSTED_VALIDATION
            | CertificateValidatorOptions.PEER_SERVER
        )
        client.certificate_validator = CertificateValidator(options, trust_store)
        await client.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            security.certificate,
            security.private_key,
            server_certificate=security.server_certificate,
            mode=ua.MessageSecurityMode.SignAndEncrypt,
        )
        await client.load_client_certificate(security.user_certificate)
        await client.load_private_key(security.user_private_key)
        await self._bounded(client.connect(), self.config.runtime.connect_timeout_ms)
        self.client = client
        try:
            self.nodes = {name: client.get_node(node_id) for name, node_id in self.config.nodes.items()}
            await self._validate_nodes()
            snapshot = await self.read_coherent_snapshot()
            self.connected = True
            self.metrics.increment("connections_total")
            self.logger.info("secure OPC UA session established", extra={"event": "opcua_connected"})
            # Never erase an inherited result before it is read and reconciled.
            await self._write_typed({"VISION_READY": False, "VISION_BUSY": False})
            await self._synchronize_if_disabled(snapshot)
            await self._publish_status()
        except Exception:
            await client.disconnect()
            self.client = None
            self.nodes = {}
            self.connected = False
            raise

    async def disconnect(self) -> None:
        client = self.client
        if client is None:
            self.connected = False
            return
        if self.connected:
            try:
                await self._write_typed({"VISION_READY": False, "VISION_BUSY": False})
            except Exception:
                pass
        self.connected = False
        self.nodes = {}
        self.client = None
        try:
            await client.disconnect()
        finally:
            self._set_metrics()

    async def _validate_nodes(self) -> None:
        for signal in ALL_SIGNALS:
            node = self.nodes[signal]
            variant_type = await self._bounded(node.read_data_type_as_variant_type())
            if variant_type.name != EXPECTED_VARIANT_TYPES[signal]:
                raise ProtocolError(
                    f"{signal} has UA type {variant_type.name}, expected {EXPECTED_VARIANT_TYPES[signal]}"
                )
            access = await self._bounded(node.get_user_access_level())
            if ua.AccessLevel.CurrentRead not in access:
                raise ProtocolError(f"named OPC UA identity cannot read {signal}")
            if signal in PLC_OWNED and ua.AccessLevel.CurrentWrite in access:
                raise ProtocolError(f"named OPC UA identity has excessive write access to PLC-owned {signal}")
            if signal not in PLC_OWNED and ua.AccessLevel.CurrentWrite not in access:
                raise ProtocolError(f"named OPC UA identity cannot write NVIDIA-owned {signal}")
        self.metrics.gauge("node_contract_valid", 1)

    def _validate_value_types(self, values: dict[str, Any]) -> None:
        python_types = {
            "Boolean": bool, "UInt32": int, "UInt16": int, "Byte": int,
            "Float": float, "String": str,
        }
        bounds = {"UInt32": UINT32_MAX, "UInt16": 0xFFFF, "Byte": 0xFF}
        for signal, value in values.items():
            variant_name = EXPECTED_VARIANT_TYPES[signal]
            expected = python_types[variant_name]
            if type(value) is not expected:
                raise ProtocolError(f"{signal} value has Python type {type(value).__name__}, expected {expected.__name__}")
            if variant_name in bounds and not 0 <= value <= bounds[variant_name]:
                raise ProtocolError(f"{signal} value is outside {variant_name} bounds")

    async def _read_snapshot(self) -> PlcSnapshot:
        signals = PLC_OWNED + (RESULT_VALID,) + RESULT_PAYLOAD
        raw = await self._bounded(self.client.read_values([self.nodes[name] for name in signals]))
        values = dict(zip(signals, raw, strict=True))
        self._validate_value_types(values)
        return PlcSnapshot(values)

    async def read_coherent_snapshot(self) -> PlcSnapshot:
        stable = (
            "VISION_ENABLE", "INSPECTION_ID", "VISION_RESULT_ACK_ID",
            "VISION_SESSION_EPOCH", "RESULT_VALID",
        )
        for _ in range(self.config.runtime.coherent_snapshot_attempts):
            first = await self._read_snapshot()
            second = await self._read_snapshot()
            if all(first.values[name] == second.values[name] for name in stable):
                if second.result_valid:
                    for name in RESULT_PAYLOAD:
                        if name == "VISION_HEARTBEAT":
                            continue
                        if first.values[name] != second.values[name]:
                            break
                    else:
                        return second
                else:
                    return second
        raise ProtocolError("OPC UA snapshot did not stabilize within the bounded retry count")

    async def _write_typed(self, values: dict[str, Any]) -> None:
        if any(signal in PLC_OWNED for signal in values):
            raise ProtocolError("adapter attempted to write a PLC-owned node")
        self._validate_value_types(values)
        variants = [ua.Variant(value, getattr(ua.VariantType, EXPECTED_VARIANT_TYPES[signal]))
                    for signal, value in values.items()]
        await self._bounded(self.client.write_values(
            [self.nodes[signal] for signal in values], variants,
        ))

    async def _synchronize_if_disabled(self, snapshot: PlcSnapshot) -> bool:
        if snapshot.enabled:
            self.service.state.ready = False
            self.service.state.warning = "AWAITING VISION_ENABLE LOW FOR SESSION SYNCHRONIZATION"
            self.service.state.diagnostic_code = "SESSION_SYNC_ENABLE_HIGH"
            return False
        if snapshot.session_epoch == 0:
            self.service.state.ready = False
            self.service.state.diagnostic_code = "SESSION_INVALID"
            return False

        if (self.service.state.session_synchronized
                and snapshot.session_epoch == self.service.state.session_epoch
                and self.service.state.result_valid):
            was_valid = self.service.state.result_valid
            self.service.resume_transport(
                disabled=True,
                session_epoch=snapshot.session_epoch,
                observed_inspection_id=snapshot.inspection_id,
                observed_ack_id=snapshot.acknowledgement_id,
                observed_plc_heartbeat=snapshot.plc_heartbeat,
                observed_result_valid=snapshot.result_valid,
                observed_result=snapshot.retained_result() if snapshot.result_valid else None,
            )
            if was_valid and not self.service.state.result_valid:
                await self._write_typed({RESULT_VALID: False})
                self.metrics.increment("reconnect_ack_reconciliations_total")
            else:
                self.metrics.increment("transport_resumes_total")
            return True

        self.service.reset(
            disabled=True,
            session_epoch=snapshot.session_epoch,
            observed_inspection_id=snapshot.inspection_id,
            observed_ack_id=snapshot.acknowledgement_id,
            observed_plc_heartbeat=snapshot.plc_heartbeat,
        )
        self._trigger_consumed_id = snapshot.inspection_id
        if snapshot.result_valid:
            retained = snapshot.retained_result()
            if retained.session_epoch != snapshot.session_epoch:
                # A serially advanced disabled session is the only condition in
                # which an old-session publication may be invalidated.
                if not heartbeat_advance(retained.session_epoch, snapshot.session_epoch):
                    raise ProtocolError("retained result session did not precede the disabled PLC session")
                await self._write_typed({RESULT_VALID: False})
                self.metrics.increment("old_session_publications_invalidated_total")
            elif retained.result_id == snapshot.acknowledgement_id:
                await self._write_typed({RESULT_VALID: False})
                self.metrics.increment("restart_ack_reconciliations_total")
            else:
                self.service.restore_publication(retained)
                self.metrics.increment("publications_restored_total")
        return True

    async def _publish_status(self) -> None:
        status = {
            "VISION_READY": bool(self.service.state.ready and self.connected),
            "VISION_BUSY": bool(self.service.state.busy),
            "VISION_HEARTBEAT": self.service.state.vision_heartbeat,
        }
        # WARNING and FAULT are inspection payload fields while RESULT_VALID is
        # high; transport faults are instead conveyed by READY low and heartbeat.
        if not self.service.state.result_valid:
            status["VISION_WARNING"] = bool(self.service.state.warning)
            status["VISION_FAULT"] = bool(self.service.state.fault)
        await self._write_typed(status)
        self._set_metrics()

    async def _publish_result(self, result: InspectionResult) -> None:
        payload = {
            "RESULT_ID": result.result_id,
            "BOTTLE_1_PASS": result.bottle_1_pass,
            "BOTTLE_2_PASS": result.bottle_2_pass,
            "FILL_1_STATUS": result.fill_1_status,
            "FILL_2_STATUS": result.fill_2_status,
            "LEAK_OR_SPILL_DETECTED": result.leak_or_spill,
            "LOW_CONFIDENCE": result.low_confidence,
            "VISION_WARNING": result.vision_warning,
            "VISION_FAULT": result.vision_fault,
            "INFERENCE_TIME": result.inference_time_ms,
            "VISION_RESULT_SESSION_EPOCH": result.session_epoch,
            "VISION_MODEL_ID": result.model_id,
            "VISION_MODEL_SHA256": result.model_hash,
        }
        self._last_result_write_order = list(payload)
        await self._write_typed(payload)
        # RESULT_VALID is a separate Write service call and is always last.
        await self._write_typed({RESULT_VALID: True})
        self._last_result_write_order.append(RESULT_VALID)
        self.metrics.increment("results_published_total")

    async def _run_inference(self, request: InspectionRequest) -> InspectionResult:
        cancelled = threading.Event()
        task = asyncio.create_task(asyncio.to_thread(
            self.service.inspect, request, cancellation_requested=cancelled.is_set,
        ))
        try:
            return await asyncio.wait_for(
                asyncio.shield(task), self.config.runtime.inference_timeout_ms / 1000,
            )
        except TimeoutError as exc:
            cancelled.set()
            self._timed_out_inference = task
            task.add_done_callback(self._consume_timed_out_inference)
            self.service.state.ready = False
            self.service.state.fault = "inference deadline exceeded; late publication prohibited"
            self.service.state.diagnostic_code = "INFERENCE_TIMEOUT"
            self.metrics.increment("inference_timeouts_total")
            raise ProtocolError(self.service.state.fault) from exc

    def _consume_timed_out_inference(self, task: asyncio.Task) -> None:
        """Retrieve the expected late cancellation exception and retain evidence."""
        try:
            task.result()
        except Exception:
            self.logger.warning(
                "timed-out backend completed after its publication deadline",
                extra={"event": "late_backend_completion_discarded",
                       "diagnostic_code": "INFERENCE_TIMEOUT"},
            )
            self.metrics.increment("late_backend_completions_discarded_total")

    async def _reconcile_publication(self, snapshot: PlcSnapshot) -> None:
        if not self.service.state.result_valid:
            return
        if snapshot.acknowledgement_id == self.service.state.published_result_id:
            self.service.acknowledge_result(snapshot.acknowledgement_id)
            await self._write_typed({RESULT_VALID: False})
            self.metrics.increment("results_acknowledged_total")
            return
        if not snapshot.result_valid:
            # Exact ACK may not be hidden behind an externally cleared VALID.
            self.service.state.ready = False
            self.service.state.fault = "RESULT_VALID cleared before exact acknowledgement"
            self.service.state.diagnostic_code = "PUBLICATION_CLEARED_WITHOUT_ACK"
            await self._write_typed({RESULT_VALID: True})
            raise ProtocolError(self.service.state.fault)
        observed = snapshot.retained_result()
        if observed != self.service.published_result:
            self.service.state.ready = False
            self.service.state.fault = "immutable result payload changed before acknowledgement"
            self.service.state.diagnostic_code = "PUBLICATION_MUTATED"
            raise ProtocolError(self.service.state.fault)

    async def run_cycle(self) -> None:
        if not self.connected or self.client is None:
            raise RuntimeError("OPC UA adapter is not connected")
        snapshot = await self.read_coherent_snapshot()
        now_ms = self.clock_ms()
        self.service.tick(snapshot.plc_heartbeat, now_ms, snapshot.session_epoch)

        if (self.service.state.session_synchronized
                and snapshot.session_epoch == self.service.state.session_epoch
                and snapshot.result_valid and not self.service.state.result_valid):
            self.service.state.ready = False
            self.service.state.fault = "unsolicited server-side result publication"
            self.service.state.diagnostic_code = "UNSOLICITED_PUBLICATION"
            raise ProtocolError(self.service.state.fault)

        if (not self.service.state.session_synchronized
                or snapshot.session_epoch != self.service.state.session_epoch):
            await self._synchronize_if_disabled(snapshot)

        await self._reconcile_publication(snapshot)

        if (snapshot.enabled and self.service.state.ready and not self.service.state.result_valid
                and snapshot.inspection_id > self.service.state.last_inspection_id):
            if not snapshot.trigger:
                self.service.state.ready = False
                self.service.state.fault = "inspection ID advanced without a sampled request level"
                self.service.state.diagnostic_code = "REQUEST_LEVEL_MISSED"
                self.metrics.increment("request_handshake_faults_total")
                raise ProtocolError(self.service.state.fault)
            if snapshot.inspection_id <= self._trigger_consumed_id:
                raise ProtocolError("inspection request level was duplicated")
            request = InspectionRequest(
                inspection_id=snapshot.inspection_id,
                recipe_id=snapshot.values["RECIPE_ID"],
                expected_bottles=snapshot.values["EXPECTED_BOTTLES"],
                target_fill_level=snapshot.values["TARGET_FILL_LEVEL"],
                plc_heartbeat=snapshot.plc_heartbeat,
                session_epoch=snapshot.session_epoch,
            )
            self._trigger_consumed_id = snapshot.inspection_id
            self.service.state.busy = True
            await self._publish_status()
            try:
                result = await self._run_inference(request)
                await self._publish_result(result)
                self.metrics.increment("inspections_total")
            finally:
                self.service.state.busy = False

        await self._publish_status()

    async def run_forever(self, stop: asyncio.Event) -> None:
        delay_ms = self.config.runtime.reconnect_initial_ms
        while not stop.is_set():
            try:
                await self.connect()
                delay_ms = self.config.runtime.reconnect_initial_ms
                while not stop.is_set():
                    await self.run_cycle()
                    try:
                        await asyncio.wait_for(stop.wait(), self.config.runtime.poll_interval_ms / 1000)
                    except TimeoutError:
                        pass
            except asyncio.CancelledError:
                raise
            except Exception:
                self.metrics.increment("transport_or_protocol_faults_total")
                self.logger.error(
                    "OPC UA supervision cycle failed closed",
                    exc_info=True,
                    extra={"event": "opcua_cycle_failed", "diagnostic_code": self.service.state.diagnostic_code},
                )
                await self.disconnect()
                jitter = random.SystemRandom().randint(0, self.config.runtime.reconnect_jitter_ms)
                try:
                    await asyncio.wait_for(stop.wait(), (delay_ms + jitter) / 1000)
                except TimeoutError:
                    pass
                delay_ms = min(delay_ms * 2, self.config.runtime.reconnect_max_ms)
        await self.disconnect()

    def _set_metrics(self) -> None:
        self.metrics.gauge("connected", self.connected)
        self.metrics.gauge("ready", self.service.state.ready)
        self.metrics.gauge("busy", self.service.state.busy)
        self.metrics.gauge("result_valid", self.service.state.result_valid)
        self.metrics.gauge("session_epoch", self.service.state.session_epoch)
        self.metrics.gauge("last_inspection_id", self.service.state.last_inspection_id)
        self.metrics.gauge("vision_heartbeat", self.service.state.vision_heartbeat)
