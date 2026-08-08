from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "07_nvidia_vision" / "edge_service"))
from protocol import InspectionRequest, ResultDisposition
from service import VisionService
from vision_runtime import BytePreprocessor, MockModelAdapter, ModelDecision, RecordedDirectorySource, VisionPipelineBackend

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="fc01-revg-synthetic-") as directory:
        root = Path(directory)
        image = root / "synthetic.png"
        image.write_bytes(b"\\x89PNG\\r\\n\\x1a\\nFC01-SYNTHETIC-NOT-AN-IMAGE-METRIC")
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        manifest = root / "manifest.csv"
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["inspection_id","path","sha256","provenance","width_px","height_px","captured_utc_ms"], lineterminator="\n")
            writer.writeheader(); writer.writerow({"inspection_id":1,"path":image.name,"sha256":digest,"provenance":"SYNTHETIC","width_px":640,"height_px":480,"captured_utc_ms":0})
        backend = VisionPipelineBackend(RecordedDirectorySource(root, manifest), BytePreprocessor(), MockModelAdapter(ModelDecision(True, True, 2, 2, False, 0.99, 0)), dataset_id="SYNTHETIC-NO-DATASET", calibration_id="SYNTHETIC-NO-CALIBRATION", confidence_threshold=0.9)
        result = backend.infer(InspectionRequest(inspection_id=1, recipe_id=1, expected_bottles=2, target_fill_level=0.5, plc_heartbeat=1, session_epoch=1))
        service = VisionService(backend=backend)
        service.reset(disabled=True, session_epoch=1, observed_plc_heartbeat=1)
        checks = {
            "synthetic_pipeline_executed": result.disposition == int(ResultDisposition.PASS),
            "backend_never_production_authorized": backend.production_authorized is False,
            "service_refuses_synthetic_ready": service.state.ready is False,
            "diagnostic_is_explicit": service.state.diagnostic_code == "DEVELOPMENT_BACKEND_PROHIBITED",
        }
        print(json.dumps({"status":"PASS" if all(checks.values()) else "FAIL", "checks":checks, "scope":"synthetic plumbing/fail-closed authorization only; no image decoding, model, metric or latency evidence"}, indent=2, sort_keys=True))
        return 0 if all(checks.values()) else 1
if __name__ == "__main__": raise SystemExit(main())
