# Integrated interface-control document

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Physical and logical chain

Field sensor → identified cable/core → numbered terminal → Siemens module/channel → symbolic PLC tag → equipment FB input → coordinator permissive/interlock → HMI diagnostic. The revision-C schedules are machine-generated from the canonical model.

## PLC–vision contract

Transport selection: OPC UA using fixed node identifiers in a routed quality VLAN. The PLC publishes request data atomically then toggles `INSPECTION_TRIGGER`; NVIDIA latches the payload, sets busy, and publishes the complete result before `RESULT_VALID`. The PLC accepts a result only when `RESULT_VALID`, `RESULT_ID = INSPECTION_ID`, heartbeat is fresh, ready is true, fault is false and all semantic fields are non-contradictory.

Timeout: 1000 ms default, recipe-bounded 250–5000 ms. No retry with the same ID. After timeout the PLC enters HOLDING; a new inspection requires a new monotonic ID and explicit operator action. Byte order for non-OPC-UA fallback is big-endian network order. Heartbeats are UDINT counters updated at 500 ms; unchanged for 1500 ms is failed.

Startup defaults are disabled/not ready/result invalid. Shutdown invalidates results. Model identity and SHA-256 are read-only metadata; a model-loading state keeps `VISION_READY = FALSE`. Communications loss, stale ID, low confidence or contradiction can never grant transfer.
