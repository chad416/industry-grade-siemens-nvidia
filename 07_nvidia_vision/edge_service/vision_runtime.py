"""Controlled camera/model boundary for FC01 vision integration readiness.

The module deliberately contains no production model and makes no accuracy or
latency claim.  It provides deterministic recorded-image input and explicit
test-only adapters so that transaction, hashing and fail-closed behavior can be
verified before real data and target hardware exist.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
from pathlib import Path
import time
from typing import Protocol

from protocol import (
    InspectionRequest, InspectionResult, ProcessingState, ProtocolError,
    ReasonBits, ResultDisposition,
)


ALLOWED_IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png"}
REAL_PROVENANCE = {"REAL_CAPTURE", "COMMISSIONING_CAPTURE"}


@dataclass(frozen=True)
class CapturedFrame:
    inspection_id: int
    path: Path
    sha256: str
    provenance: str
    width_px: int
    height_px: int
    captured_utc_ms: int


@dataclass(frozen=True)
class PreparedFrame:
    capture: CapturedFrame
    content: bytes


@dataclass(frozen=True)
class ModelDecision:
    bottle_1_pass: bool
    bottle_2_pass: bool
    fill_1_status: int
    fill_2_status: int
    leak_or_spill: bool
    confidence: float
    reason_bits: int
    warning: bool = False
    fault: bool = False
    diagnostic_code: int = 0


class FrameSource(Protocol):
    @property
    def healthy(self) -> bool: ...
    def capture(self, inspection_id: int) -> CapturedFrame: ...


class ModelAdapter(Protocol):
    @property
    def controlled_identity(self) -> tuple[str, str]: ...
    @property
    def production_authorized(self) -> bool: ...
    def infer(self, frame: PreparedFrame, request: InspectionRequest) -> ModelDecision: ...


class RecordedDirectorySource:
    """Manifest-driven, exactly-once recorded input for tests and commissioning.

    Manifest columns are ``inspection_id,path,sha256,provenance,width_px,
    height_px,captured_utc_ms``.  Paths must remain beneath ``root``; the source
    verifies each hash at capture time and prohibits replay in one process.
    """

    def __init__(self, root: Path, manifest: Path) -> None:
        self.root = root.resolve()
        self._records: dict[int, CapturedFrame] = {}
        self._consumed: set[int] = set()
        with manifest.open("r", encoding="utf-8", newline="") as handle:
            rows = csv.DictReader(handle)
            required = {
                "inspection_id", "path", "sha256", "provenance", "width_px",
                "height_px", "captured_utc_ms",
            }
            if rows.fieldnames is None or set(rows.fieldnames) != required:
                raise ValueError("recorded-image manifest columns do not match the controlled schema")
            for row in rows:
                inspection_id = int(row["inspection_id"])
                path = (self.root / row["path"]).resolve()
                if self.root not in path.parents:
                    raise ValueError("recorded-image path escapes its controlled root")
                if path.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
                    raise ValueError("recorded-image suffix is not allowed")
                if inspection_id in self._records:
                    raise ValueError("recorded-image manifest contains duplicate inspection IDs")
                digest = row["sha256"].lower()
                if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                    raise ValueError("recorded-image manifest contains a malformed SHA-256")
                self._records[inspection_id] = CapturedFrame(
                    inspection_id=inspection_id,
                    path=path,
                    sha256=digest,
                    provenance=row["provenance"],
                    width_px=int(row["width_px"]),
                    height_px=int(row["height_px"]),
                    captured_utc_ms=int(row["captured_utc_ms"]),
                )

    @property
    def healthy(self) -> bool:
        return bool(self._records) and all(record.path.is_file() for record in self._records.values())

    @property
    def production_authorized(self) -> bool:
        # A recorded directory is deterministic test/commissioning input, not a
        # live production camera.  Provenance labels alone can never authorize
        # production READY.
        return False

    def capture(self, inspection_id: int) -> CapturedFrame:
        if inspection_id in self._consumed:
            raise ProtocolError("recorded image replay is prohibited")
        try:
            record = self._records[inspection_id]
        except KeyError as exc:
            raise ProtocolError("no recorded image is correlated to this inspection ID") from exc
        if not record.path.is_file():
            raise ProtocolError("recorded image is missing")
        digest = hashlib.sha256(record.path.read_bytes()).hexdigest()
        if digest != record.sha256:
            raise ProtocolError("recorded image hash does not match its manifest")
        self._consumed.add(inspection_id)
        return record


class BytePreprocessor:
    """Bounded ingress validation before an adapter-specific decoder."""

    def __init__(self, *, max_image_bytes: int = 25_000_000,
                 min_width_px: int = 640, min_height_px: int = 480) -> None:
        if max_image_bytes <= 0 or min_width_px <= 0 or min_height_px <= 0:
            raise ValueError("preprocessing limits must be positive")
        self.max_image_bytes = max_image_bytes
        self.min_width_px = min_width_px
        self.min_height_px = min_height_px

    def prepare(self, capture: CapturedFrame) -> PreparedFrame:
        content = capture.path.read_bytes()
        if not content or len(content) > self.max_image_bytes:
            raise ProtocolError("image payload is empty or exceeds its bounded size")
        if capture.width_px < self.min_width_px or capture.height_px < self.min_height_px:
            raise ProtocolError("image dimensions are below the controlled minimum")
        if hashlib.sha256(content).hexdigest() != capture.sha256:
            raise ProtocolError("image changed between capture and preprocessing")
        return PreparedFrame(capture, content)


class MockModelAdapter:
    """Deterministic test adapter; permanently prohibited from production READY."""

    controlled_identity = ("SYNTHETIC-PIPELINE-TEST", "0" * 64)
    production_authorized = False

    def __init__(self, decision: ModelDecision) -> None:
        self.decision = decision

    def infer(self, frame: PreparedFrame, request: InspectionRequest) -> ModelDecision:
        del frame, request
        return self.decision


class OnnxAdapterStructure:
    """Fail-closed ONNX adapter boundary pending a controlled model bundle.

    Construction verifies model bytes and metadata.  Inference intentionally
    remains unavailable until the model's tensor contract and preprocessing are
    approved against representative data; a generic output guess would be less
    safe than an explicit blocker.
    """

    def __init__(self, model_path: Path, bundle_path: Path,
                 *, externally_approved_bundle_hashes: frozenset[str] = frozenset()) -> None:
        bundle_bytes = bundle_path.read_bytes()
        metadata = json.loads(bundle_bytes.decode("utf-8"))
        digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
        if digest != metadata.get("model_sha256"):
            raise ValueError("ONNX model hash does not match its bundle")
        self._identity = (metadata["model_id"], digest)
        self.dataset_id = metadata["dataset_id"]
        self.calibration_id = metadata["calibration_id"]
        bundle_hash = hashlib.sha256(bundle_bytes).hexdigest()
        self.bundle_hash_verified = bundle_hash in externally_approved_bundle_hashes
        # The tensor/preprocessing contract and infer() are intentionally not
        # implemented in Revision F.  Metadata and an allowlisted bundle hash
        # cannot authorize a nonfunctional execution path.
        self.production_authorized = False

    @property
    def controlled_identity(self) -> tuple[str, str]:
        return self._identity

    def infer(self, frame: PreparedFrame, request: InspectionRequest) -> ModelDecision:
        del frame, request
        raise ProtocolError("ONNX tensor contract is not implemented or approved")


class VisionPipelineBackend:
    """Synchronous backend compatible with :class:`VisionService`."""

    def __init__(self, source: FrameSource, preprocessor: BytePreprocessor,
                 adapter: ModelAdapter, *, dataset_id: str, calibration_id: str,
                 confidence_threshold: float) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence threshold is outside [0, 1]")
        self.source = source
        self.preprocessor = preprocessor
        self.adapter = adapter
        self.dataset_id = dataset_id
        self.calibration_id = calibration_id
        self.confidence_threshold = confidence_threshold

    @property
    def controlled_identity(self) -> tuple[str, str]:
        return self.adapter.controlled_identity

    @property
    def production_authorized(self) -> bool:
        return bool(
            self.adapter.production_authorized
            and getattr(self.source, "production_authorized", False)
        )

    @property
    def camera_healthy(self) -> bool:
        return self.source.healthy

    def infer(self, request: InspectionRequest) -> InspectionResult:
        if request.expected_dataset_id and request.expected_dataset_id != self.dataset_id:
            raise ProtocolError("PLC expected dataset identity does not match the loaded bundle")
        if request.expected_calibration_id and request.expected_calibration_id != self.calibration_id:
            raise ProtocolError("PLC expected calibration identity does not match the loaded bundle")
        capture = self.source.capture(request.inspection_id)
        prepared = self.preprocessor.prepare(capture)
        start_ns = time.monotonic_ns()
        decision = self.adapter.infer(prepared, request)
        processing_ms = max(0, (time.monotonic_ns() - start_ns) // 1_000_000)
        completed_utc_ms = int(time.time_ns() // 1_000_000)
        low_confidence = decision.confidence < self.confidence_threshold
        reason_bits = ReasonBits(decision.reason_bits)
        if low_confidence:
            reason_bits |= ReasonBits.LOW_CONFIDENCE
        if not self.camera_healthy:
            reason_bits |= ReasonBits.CAMERA_UNHEALTHY
        pass_claim = (
            decision.bottle_1_pass and decision.bottle_2_pass
            and decision.fill_1_status == 2 and decision.fill_2_status == 2
            and not decision.leak_or_spill and not decision.warning
            and not decision.fault and not low_confidence and reason_bits == ReasonBits.NONE
        )
        if decision.fault:
            disposition = ResultDisposition.FAULT
        elif pass_claim:
            disposition = ResultDisposition.PASS
        elif low_confidence or decision.warning:
            disposition = ResultDisposition.HOLD
        else:
            disposition = ResultDisposition.FAIL
        return InspectionResult(
            result_id=request.inspection_id,
            bottle_1_pass=decision.bottle_1_pass,
            bottle_2_pass=decision.bottle_2_pass,
            fill_1_status=decision.fill_1_status,
            fill_2_status=decision.fill_2_status,
            leak_or_spill=decision.leak_or_spill,
            low_confidence=low_confidence,
            vision_warning=decision.warning,
            vision_fault=decision.fault,
            inference_time_ms=processing_ms,
            model_id=self.controlled_identity[0],
            model_hash=self.controlled_identity[1],
            session_epoch=request.session_epoch,
            capture_ack_id=request.inspection_id,
            processing_state=int(ProcessingState.RESULT_COMPLETE),
            disposition=int(disposition),
            reason_bits=int(reason_bits),
            confidence=float(decision.confidence),
            dataset_id=self.dataset_id,
            calibration_id=self.calibration_id,
            capture_timestamp_utc_ms=capture.captured_utc_ms,
            inference_timestamp_utc_ms=completed_utc_ms,
            publication_timestamp_utc_ms=completed_utc_ms,
            processing_time_ms=processing_ms,
            service_healthy=True,
            camera_healthy=self.camera_healthy,
            model_loaded=True,
            maintenance_active=request.maintenance_mode,
            diagnostic_code=decision.diagnostic_code,
            queue_depth=0,
        )
