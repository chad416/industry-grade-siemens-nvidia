# PLC–NVIDIA interface control — Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Authority and transport

The approved transport remains secure OPC UA. PLC-owned nodes are read-only to NVIDIA; edge-owned nodes are read-only to PLC application logic. Namespace index is discovered at connection time while controlled string NodeIds remain fixed. OPC UA scalar encoding is used; no application-level byte swapping is permitted. The exact endpoint, certificate trust and user permissions require site commissioning.

All 27 Revision-E signals remain. Revision F adds the following diagnostics without changing PLC motion or sequence ownership.

| Signal | Type | Owner | PLC binding | Acceptance use |
|---|---|---|---|---|
| `MAINTENANCE_MODE` | BOOL | PLC | `DB_VisionComms.MaintenanceMode` | Production enable inhibited |
| `EXPECTED_DATASET_ID` | STRING[32] | PLC | `DB_VisionComms.ExpectedDatasetId` | Exact result identity |
| `EXPECTED_CALIBRATION_ID` | STRING[32] | PLC | `DB_VisionComms.ExpectedCalibrationId` | Exact result identity |
| `CAPTURE_ACK_ID` | UDINT | NVIDIA | `DB_VisionComms.CaptureAckId` | Must equal active ID |
| `PROCESSING_STATE` | USINT | NVIDIA | `DB_VisionComms.ProcessingState` | Must reach RESULT_COMPLETE |
| `RESULT_DISPOSITION` | USINT | NVIDIA | `DB_VisionComms.Result.Disposition` | PASS/HOLD/FAIL/FAULT arbitration |
| `REASON_BITS` | DWORD | NVIDIA | `DB_VisionComms.Result.ReasonBits` | Zero for PASS; nonzero for non-pass |
| `CONFIDENCE` | REAL | NVIDIA | `DB_VisionComms.Result.Confidence` | Bounded 0..1 and compared with policy |
| `DATASET_ID` | STRING[32] | NVIDIA | `DB_VisionComms.Result.DatasetId` | Exact approved baseline |
| `CALIBRATION_ID` | STRING[32] | NVIDIA | `DB_VisionComms.Result.CalibrationId` | Exact approved optics setup |
| `CAPTURE_TIMESTAMP_UTC_MS` | ULINT | NVIDIA | `DB_VisionComms.Result.CaptureTimestampUtcMs` | Ordering diagnostic |
| `INFERENCE_TIMESTAMP_UTC_MS` | ULINT | NVIDIA | `DB_VisionComms.Result.InferenceTimestampUtcMs` | Ordering diagnostic |
| `PUBLICATION_TIMESTAMP_UTC_MS` | ULINT | NVIDIA | `DB_VisionComms.Result.PublicationTimestampUtcMs` | Ordering diagnostic |
| `PROCESSING_TIME_MS` | UDINT | NVIDIA | `DB_VisionComms.Result.ProcessingTimeMs` | Normative processing duration |
| `SERVICE_HEALTHY` | BOOL | NVIDIA | `DB_VisionComms.ServiceHealthy` | Required for production acceptance |
| `CAMERA_HEALTHY` | BOOL | NVIDIA | `DB_VisionComms.CameraHealthy` | Required for production acceptance |
| `MODEL_LOADED` | BOOL | NVIDIA | `DB_VisionComms.ModelLoaded` | Required for production acceptance |
| `MAINTENANCE_ACTIVE` | BOOL | NVIDIA | `DB_VisionComms.MaintenanceActive` | Production acceptance prohibited |
| `DIAGNOSTIC_CODE` | UDINT | NVIDIA | `DB_VisionComms.DiagnosticCode` | Troubleshooting only |
| `QUEUE_DEPTH` | UINT | NVIDIA | `DB_VisionComms.QueueDepth` | Must not exceed approved maximum |

Legacy `INFERENCE_TIME` remains as a compatibility alias and must equal `PROCESSING_TIME_MS`. It is not a GPU-performance claim.

When no immutable result is active, `DIAGNOSTIC_CODE` is zero for `OK` and otherwise the IEEE CRC-32 value of the controlled uppercase ASCII first-out token. During an immutable result it is the result-specific numeric diagnostic. Maintenance uses the structured edge log to resolve a nonzero code; this diagnostic never authorizes release.

The transport contains 47 nodes. `DB_VisionComms.ResultAgeMs` is calculated by the PLC from its monotonic transaction timer, displayed on the HMI and compared with the PLC policy. It is deliberately not an OPC UA node and does not trust edge wall-clock time.

## State and disposition enumerations

Processing state: 0 NOT_READY, 1 READY, 2 CAPTURE_ACKNOWLEDGED, 3 PROCESSING, 4 RESULT_COMPLETE, 5 FAULT.

Result disposition: 0 NONE, 1 PASS, 2 HOLD, 3 FAIL, 4 FAULT.

Reason bits 0–15 are, respectively: bottle missing, misaligned, underfill, overfill, severe foam, spill/leak, low confidence, camera unhealthy, model unavailable, timeout/late, malformed/contradictory, identity mismatch, correlation error, communications/heartbeat, queue saturation and recipe changed. Unknown high bits make the result non-pass and require diagnostic review.

## Handshake

1. After PLC startup, a serially advanced nonzero session is synchronized with enable low. After a same-session edge transport reconnect, enable remains low while the edge snapshots session, request ID, ACK ID, PLC heartbeat and any retained publication. An unacknowledged same-session publication is restored immutably; only an exact ACK clears it. A genuinely older-session publication may be invalidated only under the controlled new-session rule.
2. Edge reports healthy/ready with maintenance state consistent. PLC enables only when its retained model/dataset/calibration policy is approved.
3. PLC allocates exactly one higher inspection ID, publishes recipe/target fields and holds trigger high.
4. Edge latches the request, publishes exact capture-ack ID and state 2/3, then sets BUSY. PLC may then lower trigger.
5. Edge writes the entire immutable result, state 4 and BUSY false, then writes RESULT_VALID last.
6. PLC acknowledges the exact result ID for transport clearing, independently validates every field and either releases PASS or enters HOLD/FAULT. Edge clears RESULT_VALID only on exact ACK.
7. A new request cannot arm until RESULT_VALID is low. No queued/offline publication may be replayed for another session or bottle.

## Fault and recovery rules

- Network loss, heartbeat loss, late result, queue saturation, edge restart, PLC restart, recipe change, clock discontinuity, malformed data and contradictory state all fail closed.
- UTC timestamps are diagnostic. PLC request timeout and monotonic session/ID correlation remain authoritative; no wall-clock adjustment may convert a late result to PASS.
- Recipe change while a request is active causes HOLD; a new recipe requires a new inspection ID after the prior publication clears.
- Manual/setup requests maintenance. There is no inspection bypass. Product disposition is a separate PLC-sequenced HMI action after physical segregation.
- Cause-cleared reset requires BUSY false, RESULT_VALID false, no trigger edge and healthy/consistent interface state. Reset never causes automatic restart.

Native OPC UA server exposure, access rights, update rates, compiled DB offsets and end-to-end PLC/edge execution remain acceptance gates; this source contract does not claim them.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
