# PLC-NVIDIA interface control document - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Atomic request and result lifecycle

The PLC owns sequence and publishes the complete request payload with a nonzero retained `SESSION_EPOCH` and strictly monotonic `INSPECTION_ID` before raising `INSPECTION_TRIGGER`. Trigger is a level-held transport request, not a one-scan event: it remains true until coherent `VISION_READY=1, VISION_BUSY=1` is observed or a terminal result arrives. A repeated coordinator pulse cannot mutate the active ID. Session, ID, recipe, expected bottle count and target remain immutable while pending.

The edge adapter deduplicates by `(session epoch, inspection ID)`, publishes BUSY when it owns the request, and never processes the same pair twice across polling or reconnect. A matching terminal result may complete before BUSY is sampled. Any wrong, stale, future or regressed session/ID, heartbeat regression/loss, malformed value, model-ID/hash mismatch, contradictory state, low confidence, partial result, warning or fault fails closed to PLC HOLD/FAULT. No edge node can command motion or bypass PLC permissives.

The immutable result payload is written before `RESULT_VALID`. It remains stable until the PLC writes the exact `RESULT_ACK_ID`; the acknowledgement is transport cleanup only and never grants product transfer. Restart/reconnect re-seeds the coherent PLC snapshot, preserves same-session unacknowledged publication, and permits invalidation only under the controlled serially advanced disabled-session rule.

Revision-E automated evidence includes a real encrypted asyncua test server/client and controlled PKI flow, but not a production S7-1500 endpoint, production certificate authority, Jetson deployment or trained model. Native TIA compilation/PLCSIM and site cybersecurity acceptance remain explicit gates.
