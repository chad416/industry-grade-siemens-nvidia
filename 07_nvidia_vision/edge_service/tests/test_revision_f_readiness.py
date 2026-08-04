from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import replace

VISION_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(VISION_ROOT))
sys.path.insert(0, str(VISION_ROOT / "edge_service"))

from dataset_tool import (  # noqa: E402
    MANIFEST_COLUMNS, DatasetError, assign_grouped_splits, evaluate_binary,
    load_manifest, validate_manifest, write_manifest,
)
from opcua_adapter import (  # noqa: E402
    ALL_SIGNALS, EXPECTED_VARIANT_TYPES, PLC_OWNED, RESULT_PAYLOAD, PlcSnapshot,
    _validate_active_request_context, _validate_contract_document, edge_diagnostic_code,
)
from protocol import (  # noqa: E402
    InspectionRequest, ProcessingState, ProtocolError, ReasonBits,
    ResultDisposition, validate_result,
)
from service import VisionService  # noqa: E402
from vision_runtime import (  # noqa: E402
    BytePreprocessor, MockModelAdapter, ModelDecision, RecordedDirectorySource,
    OnnxAdapterStructure, VisionPipelineBackend,
)
from benchmark_harness import benchmark  # noqa: E402
from dependency_inventory import parse_lock  # noqa: E402


class RevisionFContractTests(unittest.TestCase):
    def test_contract_is_additive_and_complete(self) -> None:
        self.assertEqual(len(ALL_SIGNALS), 47)
        self.assertEqual(len(set(ALL_SIGNALS)), 47)
        self.assertEqual(set(ALL_SIGNALS), set(EXPECTED_VARIANT_TYPES))
        self.assertTrue({"MAINTENANCE_MODE", "EXPECTED_DATASET_ID",
                         "EXPECTED_CALIBRATION_ID"}.issubset(PLC_OWNED))
        self.assertTrue({"RESULT_DISPOSITION", "REASON_BITS", "CONFIDENCE",
                         "DATASET_ID", "CALIBRATION_ID"}.issubset(RESULT_PAYLOAD))

    def test_csv_json_and_implementation_node_maps_match(self) -> None:
        config = json.loads((VISION_ROOT / "edge_service" / "service_config.json").read_text(encoding="utf-8"))
        with (VISION_ROOT / "plc_ai_node_map.csv").open("r", encoding="utf-8", newline="") as handle:
            csv_nodes = {row["signal"]: row["node_id"] for row in csv.DictReader(handle)}
        self.assertEqual(config["namespace_version"], "FC01.Vision.v3")
        self.assertEqual(config["signal_count"], 47)
        self.assertEqual(config["nodes"], csv_nodes)
        self.assertEqual(set(config["nodes"]), set(ALL_SIGNALS))

    def test_service_configuration_schema_is_executed_and_rejects_unknown_keys(self) -> None:
        config = json.loads((VISION_ROOT / "edge_service" / "service_config.json").read_text(encoding="utf-8"))
        schema = json.loads((VISION_ROOT / "edge_service" / "service_config.schema.json").read_text(encoding="utf-8"))
        _validate_contract_document(config, schema)
        config["uncontrolled_key"] = True
        with self.assertRaisesRegex(ValueError, "unknown"):
            _validate_contract_document(config, schema)

    def test_recipe_or_clock_change_invalidates_active_request(self) -> None:
        request = InspectionRequest(5, 11, 2, 0.75, 9, 3,
                                    expected_dataset_id="DS-1",
                                    expected_calibration_id="CAL-1")
        values = {
            "VISION_ENABLE": True, "INSPECTION_TRIGGER": True,
            "INSPECTION_ID": 5, "RECIPE_ID": 12, "EXPECTED_BOTTLES": 2,
            "TARGET_FILL_LEVEL": 0.75, "PLC_HEARTBEAT": 9,
            "VISION_RESULT_ACK_ID": 0, "VISION_SESSION_EPOCH": 3,
            "RESULT_VALID": False, "MAINTENANCE_MODE": False,
            "EXPECTED_DATASET_ID": "DS-1", "EXPECTED_CALIBRATION_ID": "CAL-1",
        }
        snapshot = PlcSnapshot(values)
        with self.assertRaisesRegex(ProtocolError, "recipe_id"):
            _validate_active_request_context(request, snapshot, 10, 10, 250)
        values["RECIPE_ID"] = 11
        with self.assertRaisesRegex(ProtocolError, "clock"):
            _validate_active_request_context(request, PlcSnapshot(values), 10, 400, 250)

    def test_edge_first_out_token_has_stable_uint32_transport(self) -> None:
        self.assertEqual(edge_diagnostic_code("OK"), 0)
        code = edge_diagnostic_code("AUDIT_STORAGE_FAILURE")
        self.assertGreater(code, 0)
        self.assertLessEqual(code, 0xFFFFFFFF)
        self.assertEqual(code, edge_diagnostic_code("AUDIT_STORAGE_FAILURE"))

    def test_reason_bits_are_unique_powers_of_two(self) -> None:
        values = [int(reason) for reason in ReasonBits if reason != ReasonBits.NONE]
        self.assertEqual(len(values), len(set(values)))
        self.assertTrue(all(value & (value - 1) == 0 for value in values))

    def test_pass_disposition_requires_health_and_exact_capture_ack(self) -> None:
        request = InspectionRequest(5, 1, 2, 0.75, 7, expected_dataset_id="DS-1",
                                    expected_calibration_id="CAL-1")
        backend = _pipeline_backend(self._recorded_source(5), confidence=0.99)
        result = backend.infer(request)
        validate_result(request, result, backend.controlled_identity)
        self.assertEqual(result.disposition, ResultDisposition.PASS)
        self.assertEqual(result.capture_ack_id, request.inspection_id)
        self.assertEqual(result.reason_bits, 0)

    def test_every_terminal_disposition_rejects_partial_or_malformed_publication(self) -> None:
        request = InspectionRequest(55, 1, 2, 0.75, 7, expected_dataset_id="DS-1",
                                    expected_calibration_id="CAL-1")
        backend = _pipeline_backend(self._recorded_source(55), confidence=0.99)
        valid = backend.infer(request)
        malformed = {
            "missing capture acknowledgement": replace(valid, capture_ack_id=0),
            "nonterminal processing state": replace(valid, processing_state=int(ProcessingState.READY)),
            "zero timestamp": replace(valid, capture_timestamp_utc_ms=0),
            "unordered timestamps": replace(valid, capture_timestamp_utc_ms=valid.inference_timestamp_utc_ms + 1),
            "duration mismatch": replace(valid, processing_time_ms=valid.inference_time_ms + 1),
            "undefined reason bit": replace(valid, reason_bits=1 << 31),
            "unhealthy service": replace(valid, service_healthy=False),
            "unhealthy camera": replace(valid, camera_healthy=False),
            "unloaded model": replace(valid, model_loaded=False),
            "maintenance publication": replace(valid, maintenance_active=True),
            "missing disposition": replace(valid, disposition=int(ResultDisposition.NONE)),
            "nonpass without reason": replace(valid, disposition=int(ResultDisposition.HOLD)),
        }
        for label, result in malformed.items():
            with self.subTest(label), self.assertRaises(ProtocolError):
                validate_result(request, result, backend.controlled_identity)

    def test_low_confidence_can_never_be_pass(self) -> None:
        request = InspectionRequest(6, 1, 2, 0.75, 8, expected_dataset_id="DS-1",
                                    expected_calibration_id="CAL-1")
        backend = _pipeline_backend(self._recorded_source(6), confidence=0.49)
        result = backend.infer(request)
        self.assertEqual(result.disposition, ResultDisposition.HOLD)
        self.assertTrue(result.reason_bits & ReasonBits.LOW_CONFIDENCE)

    def test_dataset_identity_mismatch_fails_closed(self) -> None:
        request = InspectionRequest(7, 1, 2, 0.75, 9, expected_dataset_id="WRONG",
                                    expected_calibration_id="CAL-1")
        with self.assertRaisesRegex(ProtocolError, "dataset"):
            _pipeline_backend(self._recorded_source(7), confidence=0.99).infer(request)

    def test_synthetic_mock_backend_cannot_assert_service_ready(self) -> None:
        service = VisionService(_pipeline_backend(self._recorded_source(8), confidence=0.99))
        service.reset(disabled=True, session_epoch=1)
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.diagnostic_code, "DEVELOPMENT_BACKEND_PROHIBITED")

    def test_backend_without_explicit_external_authorization_is_prohibited(self) -> None:
        class IncompleteBackend:
            controlled_identity = ("UNREVIEWED", "a" * 64)
        service = VisionService(IncompleteBackend())
        self.assertFalse(service.state.ready)
        self.assertEqual(service.state.diagnostic_code, "DEVELOPMENT_BACKEND_PROHIBITED")

    def test_benchmark_is_explicitly_development_only(self) -> None:
        result = benchmark(lambda: 1 + 1, warmup=1, iterations=3)
        self.assertEqual(result.iterations, 3)
        self.assertIn("NOT TARGET PERFORMANCE", result.evidence_class)

    def test_dependency_lock_requires_exact_versions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fc01-lock-") as directory:
            path = Path(directory) / "requirements.txt"
            path.write_text("package>=1.0\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unlocked"):
                parse_lock(path)

    def test_model_bundle_cannot_self_authorize_production(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fc01-model-") as directory:
            root = Path(directory)
            model = root / "model.onnx"
            model.write_bytes(b"NOT A REAL MODEL")
            bundle = root / "bundle.json"
            bundle.write_text(json.dumps({
                "model_id": "TEST-ONLY",
                "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
                "dataset_id": "DS-TEST",
                "calibration_id": "CAL-TEST",
                "approval_status": "APPROVED",
            }), encoding="utf-8")
            adapter = OnnxAdapterStructure(model, bundle)
            self.assertFalse(adapter.production_authorized)

            approved_hash = hashlib.sha256(bundle.read_bytes()).hexdigest()
            allowlisted = OnnxAdapterStructure(
                model, bundle, externally_approved_bundle_hashes=frozenset({approved_hash}),
            )
            self.assertTrue(allowlisted.bundle_hash_verified)
            self.assertFalse(allowlisted.production_authorized)
            with self.assertRaisesRegex(ProtocolError, "not implemented"):
                allowlisted.infer(None, None)

    def test_recorded_input_is_exactly_once(self) -> None:
        source = self._recorded_source(9)
        source.capture(9)
        with self.assertRaisesRegex(ProtocolError, "replay"):
            source.capture(9)

    def test_recorded_input_detects_hash_change(self) -> None:
        source = self._recorded_source(10)
        next(iter(source._records.values())).path.write_bytes(b"changed")
        with self.assertRaisesRegex(ProtocolError, "hash"):
            source.capture(10)

    def _recorded_source(self, inspection_id: int) -> RecordedDirectorySource:
        temp = tempfile.TemporaryDirectory(prefix="fc01-frame-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        image = root / "frame.png"
        image.write_bytes(b"SYNTHETIC UNIT-TEST IMAGE BYTES")
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        manifest = root / "capture.csv"
        manifest.write_text(
            "inspection_id,path,sha256,provenance,width_px,height_px,captured_utc_ms\n"
            f"{inspection_id},frame.png,{digest},SYNTHETIC_TEST_ONLY,1280,720,1700000000000\n",
            encoding="utf-8",
        )
        return RecordedDirectorySource(root, manifest)


def _pipeline_backend(source: RecordedDirectorySource, *, confidence: float) -> VisionPipelineBackend:
    decision = ModelDecision(True, True, 2, 2, False, confidence, 0)
    return VisionPipelineBackend(
        source, BytePreprocessor(), MockModelAdapter(decision),
        dataset_id="DS-1", calibration_id="CAL-1", confidence_threshold=0.75,
    )


class DatasetToolTests(unittest.TestCase):
    def _row(self, root: Path, image_id: str, group: str, session: str) -> dict[str, str]:
        image = root / f"{image_id}.png"
        annotation = root / f"{image_id}.json"
        image.write_bytes(f"SYNTHETIC TEST {image_id}".encode())
        annotation.write_text(json.dumps({"test_only": True}), encoding="utf-8")
        return dict(zip(MANIFEST_COLUMNS, (
            image_id, image.name, hashlib.sha256(image.read_bytes()).hexdigest(),
            "UNIT_TEST_SYNTHETIC", "", group, session, "1", "TEST-BOTTLE",
            annotation.name, hashlib.sha256(annotation.read_bytes()).hexdigest(),
            "DOUBLE_REVIEWED", "synthetic", "CAM-TEST", "LENS-TEST", "LIGHT-TEST",
            "1280", "720",
        )))

    def test_empty_controlled_manifest_is_valid_but_not_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fc01-dataset-") as directory:
            root = Path(directory)
            manifest = root / "manifest.csv"
            write_manifest(manifest, [])
            report = validate_manifest(manifest, root)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["rows"], 0)
            self.assertIn("not model-performance evidence", report["scope"])

    def test_grouped_split_never_leaks_lot_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fc01-dataset-") as directory:
            root = Path(directory)
            rows = [self._row(root, "A", "LOT-1", "S-1"),
                    self._row(root, "B", "LOT-1", "S-1"),
                    self._row(root, "C", "LOT-2", "S-2")]
            split = assign_grouped_splits(rows)
            grouped = {(row["production_lot"], row["acquisition_session"]): row["split"]
                       for row in split}
            self.assertEqual(split[0]["split"], split[1]["split"])
            self.assertEqual(len(grouped), 2)

    def test_manifest_validation_detects_exact_duplicate_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fc01-dataset-") as directory:
            root = Path(directory)
            first = self._row(root, "A", "LOT-1", "S-1")
            second = self._row(root, "B", "LOT-2", "S-2")
            (root / second["uri"]).write_bytes((root / first["uri"]).read_bytes())
            second["sha256"] = first["sha256"]
            manifest = root / "manifest.csv"
            write_manifest(manifest, [first, second])
            report = validate_manifest(manifest, root)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("exact duplicate" in error for error in report["errors"]))

    def test_manifest_rejects_group_leakage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fc01-dataset-") as directory:
            root = Path(directory)
            first = self._row(root, "A", "LOT-1", "S-1")
            second = self._row(root, "B", "LOT-1", "S-1")
            first["split"], second["split"] = "train", "test"
            manifest = root / "manifest.csv"
            write_manifest(manifest, [first, second])
            self.assertTrue(any("leakage" in error for error in validate_manifest(manifest, root)["errors"]))

    def test_binary_metrics_report_false_accept_and_reject(self) -> None:
        rows = [
            {"truth_pass": "true", "pass_score": "0.9"},
            {"truth_pass": "true", "pass_score": "0.2"},
            {"truth_pass": "false", "pass_score": "0.8"},
            {"truth_pass": "false", "pass_score": "0.1"},
        ]
        metrics = evaluate_binary(rows, 0.5).as_dict()
        self.assertEqual((metrics["tp"], metrics["tn"], metrics["fp"], metrics["fn"]),
                         (1, 1, 1, 1))
        self.assertEqual(metrics["false_accept_rate"], 0.5)
        self.assertEqual(metrics["false_reject_rate"], 0.5)

    def test_binary_metrics_reject_invalid_scores(self) -> None:
        with self.assertRaises(DatasetError):
            evaluate_binary([{"truth_pass": "true", "pass_score": "1.1"}], 0.5)

    def test_manifest_loader_rejects_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fc01-dataset-") as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("image_id,uri\nA,a.png\n", encoding="utf-8")
            with self.assertRaises(DatasetError):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()
