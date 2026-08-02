# PLC-NVIDIA interface control document - Revision D

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Atomic transaction

The PLC publishes a nonzero, strictly monotonic `INSPECTION_ID`, `SESSION_EPOCH`, recipe/expected-bottle/target data and a one-scan trigger. NVIDIA publishes an immutable payload (result ID, bottle/fill semantics, warning/fault, model ID/SHA-256, inference duration and heartbeat) before asserting `RESULT_VALID`. The PLC accepts product only for the current ID with coherent READY/BUSY state and fail-closed semantics. Independently, it writes the exact observed `RESULT_ID` to `RESULT_ACK_ID` for every complete publication, including rejected or orphaned data; this transport acknowledgement never grants product acceptance. NVIDIA clears `RESULT_VALID` only after matching acknowledgement and rejects new work while a result is unacknowledged.

`READY=1,BUSY=0` is available; `READY=1,BUSY=1` is processing; `READY=0,BUSY=0` is unavailable; `READY=0,BUSY=1` and `BUSY=1,RESULT_VALID=1` are contradictions. Missing, stale, duplicate, future, late, malformed, uncertain or model-mismatched results never permit transfer. A result sampled on the discrete timeout scan has declared success precedence; later results are acknowledged for transport cleanup but rejected for quality. Coherent quality rejections enter HOLDING; protocol/health faults enter FAULTED while retaining the product and output interlock.

At edge startup or restart, `READY` remains low and the PLC therefore holds `VISION_ENABLE` low. The adapter atomically seeds `SESSION_EPOCH`, current `INSPECTION_ID`, `RESULT_ACK_ID` and `PLC_HEARTBEAT` into the edge reset operation before asserting `READY`; this prevents same-session replay after loss of edge process memory. Session changes require the same disabled synchronization. A PLC fault reset requires no pending transaction, not BUSY, publication low and no request edge; when enabled it additionally requires READY and healthy heartbeat. Reset creates no trigger/acceptance edge. Heartbeat supervision is suppressed while disabled and reseeded on enable; disabling during a transaction faults and locks out the transaction.

The Python models/tests are independent contract evidence only. Native OPC UA namespace, certificates, reconnect persistence and PLC/edge integration remain blocked.
