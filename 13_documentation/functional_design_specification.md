# Functional design specification - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Scope and state model

The machine indexes exactly two bottles, proves conveyor stopped, closes the gate, engages the clamp, fills two independently metered channels from one pump, settles drips, obtains a matched non-safety vision result, then handshakes the accepted pair to the capper. States are UNINITIALIZED, INITIALIZING, STOPPED, READY, AUTOMATIC, MANUAL_SETUP, HOLDING, CONTROLLED_STOPPING, FAULTED and RECOVERY_RESET.

## Automatic sequence

| Step | Entry condition | Commands | Completion | Failure response |
|---|---|---|---|---|
| Index | New Start edge in READY | Conveyor speed request | Two nest sensors true | Stop/hold on missing or contradictory sensing |
| Secure | Conveyor stopped | Gate close, clamp engage | Both feedbacks true | Equipment timeout fault |
| Fill | Secured pair and valid recipe | Pump, two independent valves | Both close-confirmed in tolerance | Close valves, stop pump, hold |
| Drip | Both channels complete | Pump/valves off | Recipe timer expires | Controlled stop on blocking fault |
| Inspect | Fresh monotonic ID | Camera light and trigger | Matched, valid, high-confidence result | HOLDING for a coherent quality rejection; FAULTED with product/output hold for timeout, stale/session/model mismatch, heartbeat loss or interface contradiction |
| Transfer | Process and quality accepted | Capper request | Busy then complete | HOLDING/FAULTED on order/timeout/fault |
| Release | Capper complete | Gate open, clamp release | Pair absent and actuators released | No new cycle until confirmed |

## Recovery rules

Reset clears eligible latches only. Power or communication recovery sets a recovery-required condition and returns to STOPPED; a new reset release and new Start edge are mandatory. Held product requires supervised physical removal and a disposition sequence. Reset cannot accept uncertain quality.

## Revision-E PLC-edge request transport

The Inspect step creates one immutable `(session epoch, inspection ID)` transaction and holds its request level until the edge is coherently BUSY or an exact terminal result is received. Polling, reconnect or a repeated coordinator request cannot allocate a second ID. Result acceptance remains a PLC decision; a quality reject enters controlled product disposition, while communications/identity/model/integrity faults decommand the process and prevent transfer. Recovery never restarts a cycle automatically.
