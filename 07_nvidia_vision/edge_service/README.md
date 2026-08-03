# NVIDIA edge-service source boundary

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

`protocol.py` is the edge-service protocol oracle. It defines the controlled target-fill bounds (0.1 through 1.0), request/result rules, exact model identity checks and a hexadecimal SHA-256 requirement. `service.py` adds fail-closed 1000 ms PLC-heartbeat supervision, compares every result to the backend's controlled identity, and can adopt a validated unacknowledged server-side publication after a cold edge-process restart without re-running inference.

Revision E adds `opcua_adapter.py`, a genuine `asyncua` 2.0.1 client implementation. It requires Basic256Sha256/SignAndEncrypt, a named X.509 user, a trusted server certificate/CA and CRL store, validates all 27 NodeIds, data types and least-privilege access rights, reads coherent counter/session snapshots, writes the result payload before `RESULT_VALID`, preserves that payload until exact acknowledgement, reconnects with bounded exponential backoff and fails closed on stale, malformed or contradictory data. `observability.py` provides JSON-line logs, fixed-cardinality metrics and loopback-only health/readiness endpoints. Configuration and PKI material are described by `opcua_runtime_config.json`; secrets and certificates remain external to the repository.

At process startup or reconnect the adapter must keep `READY` low. After observing `VISION_ENABLE=0`, it must take one coherent PLC snapshot of `VISION_SESSION_EPOCH`, `INSPECTION_ID`, `RESULT_ACK_ID` and `PLC_HEARTBEAT`, pass those four values to `VisionService.reset`, and only then assert `READY`. Those PLC-owned counter baselines prevent a cold edge process from replaying an already issued identifier in an unchanged session. Session changes use the same disabled synchronization; changing a session while enabled is rejected.

The secure integration suite creates an ephemeral CA, server and named client certificates and runs a real asyncua server/client session. It verifies the secure endpoint, non-anonymous identity, 27-node contract, payload-before-valid order, exact acknowledgement, restart restoration, trust rejection, immutable-publication tamper detection, missed-request fail-closed behavior and bounded late-result suppression. This is local software evidence, not a connection to the Siemens CPU and not site PKI validation.

## Offline buffering policy

There is no offline request, image or result queue and no later replay for product disposition. The only retained transaction is one immutable result already published in the OPC UA server and awaiting its exact same-session acknowledgement. A disconnect, ambiguous read/write completion or loss of a coherent PLC snapshot forces READY low and the PLC remains in HOLD. Recovery requires disabled-state synchronization and coherent reconciliation of the session, inspection, acknowledgement and heartbeat counters before READY may return. An image, request or result that was not coherently completed online is never silently reused for another bottle.

## Software rollback boundary

The adapter package, locked requirements, runtime configuration and systemd unit are versioned and rolled back together through the controlled procedure in `opcua_adapter_runbook.md`. Rollback begins with the service stopped and production disabled; the previously reviewed package is restored, hashes and PKI permissions are checked, the complete 27-node map is revalidated, and the service cold-starts disabled before negative tests are repeated. Model rollback is separate and remains blocked until a genuine approved model lifecycle exists.

No camera driver, production inference backend, dataset, model, ONNX file, TensorRT engine or DeepStream execution is delivered. `main.py` therefore starts with no backend and intentionally holds `VISION_READY` low. Revision-E Siemens source now holds `INSPECTION_TRIGGER` until coherent `VISION_BUSY` observation or a terminal result and freezes the externally visible ID while the request is pending. That SCL remains source-tested only: native TIA compilation and a real S7 subscription/publish-cycle test are still required. The adapter also fails closed if an advanced ID is ever observed without the held request level.

See `opcua_adapter_runbook.md` for installation, PKI, test and deployment steps. The hardened systemd unit is a deployment baseline only and requires target Linux/Jetson, site account, firewall and cybersecurity approval.
