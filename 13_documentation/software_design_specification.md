# Software design specification - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Ownership and scan order

`OB1` calls the single `DB_CellMain` instance. `FB_CellMain` owns command sequencing, two VFD instances, gate, clamp, two fill channels, recipe, vision, capper, alarm and coordinator instances. The cyclic order is normalized inputs, command arbitration, equipment control/status, sequence, first-out/alarm mapping and final physical-output mapping. Startup decommands outputs and requires explicit recovery/reset and a new Start edge.

## PLC-edge transaction

`FB_VisionInterface` latches a nonzero session epoch and strictly monotonic inspection ID. `RequestInProgress` prevents duplicate coordinator pulses from advancing the ID. The request trigger is level-held until coherent BUSY or a terminal result for the exact identity is observed. Wrong/stale/future/regressed identity, heartbeat loss/regression, invalid model ID/hash, partial/contradictory result, warning/fault or low confidence prevents acceptance. Results remain immutable until exact acknowledgement; transport cleanup never authorizes transfer.

## Edge adapter

The production-shaped Python adapter requires Basic256Sha256 SignAndEncrypt, X.509 application and user identity, pinned server certificate, trust/CRL stores, a controlled 27-node map and bounded connect/operation/inference/reconnect timing. It writes one typed result payload and publishes `RESULT_VALID` last. Structured JSON logs, local health/readiness and metrics expose first-out state without accepting remote motion commands.

## Evidence boundary

Source parity, simulator contracts and encrypted asyncua test-server/client evidence are controlled. No native TIA/WinCC compile, PLCSIM equivalence, production S7 endpoint validation, target Jetson qualification, trained model, performance result or physical commissioning is claimed.
