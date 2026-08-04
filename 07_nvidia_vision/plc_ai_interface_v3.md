# FC01 PLC–NVIDIA interface control — Revision F / namespace v3

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

> THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.

## Authority and compatibility

The S7-1500 owns modes, sequence, motion, interlocks, timeouts, restart, transfer and product disposition. NVIDIA publishes one non-safety quality observation. Namespace `FC01.Vision.v3` preserves all 27 Revision-E nodes and adds 20 nodes; it does not repurpose a prior node. OPC UA scalar types follow IEC/UA types and use normal UA encoding—no application byte packing exists.

The authoritative machine tag source remains the project canonical model. This document and `plc_ai_node_map.csv` define the vision-side implementation proposal; native TIA import, compile and S7 OPC UA namespace confirmation remain required before deployment.

## Added PLC-owned inputs

| Signal | UA type | Rule |
|---|---|---|
| `MAINTENANCE_MODE` | Boolean | PLC-controlled; never grants motion or bypass authority to edge |
| `EXPECTED_DATASET_ID` | String, max controlled value 32 characters | Immutable with a pending request; exact match required |
| `EXPECTED_CALIBRATION_ID` | String, max controlled value 32 characters | Immutable with a pending request; exact match required |

## Added NVIDIA-owned status and result fields

| Signal | UA type | Semantics |
|---|---|---|
| `CAPTURE_ACK_ID` | UInt32 | Exact inspection ID whose capture was accepted; zero before any accepted capture |
| `PROCESSING_STATE` | Byte | `0 NOT_READY`, `1 READY`, `2 CAPTURE_ACKNOWLEDGED`, `3 PROCESSING`, `4 RESULT_COMPLETE`, `5 FAULT` |
| `SERVICE_HEALTHY` | Boolean | Transport/service self-health only; never a safety indication |
| `CAMERA_HEALTHY` | Boolean | Camera/source health; real camera meaning requires vendor-driver implementation |
| `MODEL_LOADED` | Boolean | Controlled model identity is loaded; not a validity or accuracy claim |
| `MAINTENANCE_ACTIVE` | Boolean | Echo of accepted PLC maintenance state, not authority |
| `RESULT_DISPOSITION` | Byte | `0 NONE`, `1 PASS`, `2 HOLD`, `3 FAIL`, `4 FAULT` |
| `REASON_BITS` | UInt32 | Blocking quality/diagnostic mask below |
| `CONFIDENCE` | Float | Normalized `[0,1]`; threshold must be recipe/model validated |
| `DATASET_ID`, `CALIBRATION_ID` | String | Exact controlled identities used for this result |
| `CAPTURE_TIMESTAMP_UTC_MS` | UInt64 | Capture epoch milliseconds; source clock quality must be commissioned |
| `INFERENCE_TIMESTAMP_UTC_MS` | UInt64 | Inference-completion epoch milliseconds |
| `PUBLICATION_TIMESTAMP_UTC_MS` | UInt64 | Result-publication epoch milliseconds |
| `PROCESSING_TIME_MS` | UInt32 | Edge processing duration; `INFERENCE_TIME` is retained as a compatibility alias |
| `DIAGNOSTIC_CODE` | UInt32 | Implementation-specific bounded diagnostic code |
| `QUEUE_DEPTH` | UInt16 | Must remain zero in the released no-buffering policy |

Reason bits: b0 bottle missing; b1 misaligned; b2 underfill; b3 overfill; b4 severe foam; b5 spill/leak; b6 low confidence; b7 camera unhealthy; b8 model unavailable; b9 timeout/late; b10 malformed/contradictory; b11 model/dataset/calibration identity mismatch; b12 session/ID mismatch, stale, duplicate or future data; b13 communications/heartbeat; b14 queue saturation; b15 recipe changed. Bits 16–31 are reserved and must be zero.

## Transaction sequence

1. With production disabled, the edge reads a coherent session/counter/configuration snapshot and keeps `VISION_READY=0` until identities, PKI, node types, access rights, model and camera are valid.
2. PLC freezes request payload, raises `INSPECTION_TRIGGER` and allocates one strictly monotonic nonzero `INSPECTION_ID` within the current nonzero session.
3. Edge accepts exactly that request, publishes `CAPTURE_ACK_ID=<INSPECTION_ID>`, `VISION_BUSY=1`, and `PROCESSING_STATE=3`. An absent or mismatched capture acknowledgement can never support PASS.
4. Edge validates the complete result and writes every payload field first. It sets `RESULT_VALID=1` in a separate final write. Payload remains immutable.
5. PLC accepts PASS only when ID/session/capture ACK match, state is complete, disposition is PASS, reason mask is zero, confidence meets the controlled threshold, model/dataset/calibration match, health flags are true, queue is within policy and result age/latency are within limits. Every other case enters PLC HOLD/reject/fault disposition.
6. PLC writes the exact `RESULT_ID` to `VISION_RESULT_ACK_ID`, including for discarded results. Edge then clears `RESULT_VALID`. No timeout implies acknowledgement.

Recipe, expected identity or maintenance changes during a pending transaction invalidate the transaction. A clock jump never changes ID-based correlation; it invalidates time-based acceptance until synchronization is restored. Disconnect, heartbeat loss, incoherent reads, malformed types, stale/future/duplicate IDs, queue growth or service restart makes READY false and requires the documented disabled synchronization. No request, image or unpublished result is queued for later bottle disposition.

## Closure evidence

Source tests verify the contract and fail-closed rules. Remaining evidence: native TIA V20 compilation; HMI compilation; actual S7 OPC UA NodeIds/types/access; subscription-cycle timing; site PKI; NTP/PTP behavior; real camera/model bundle; target runtime soak; and physical fault injection.
