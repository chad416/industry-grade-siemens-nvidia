# Executed non-native test report - Revision D.1

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Execution date: 2026-08-03. Runtime: bundled Python 3.12. These are deterministic source/design/interface tests, not TIA Portal compile, PLCSIM, FAT, SAT or physical commissioning evidence.

## Process and interface models

`python -m unittest discover -s 11_simulation/tests -v` passed 58 tests: the 48 process simulator/property/protocol/interface tests plus ten Revision-D.1 Siemens restart, capper, HMI-ledger, first-out, decommand and disposition source contracts. `python 11_simulation/run_scenarios.py` regenerated all 32 timed scenarios and their per-scenario traces; exactly one normal scenario releases, invariant violations are zero and reset/power restoration never causes automatic restart.

## PLC-NVIDIA edge contract

`python -m unittest discover -s 07_nvidia_vision/edge_service/tests -v` passed 42 edge-service tests. `python -m unittest -v test_plc_interface_harness.py` passed 15 interface-harness tests. Coverage includes disabled restart synchronization and PLC counter seeding, immutable publication through same-session faults until exact acknowledgement, coherent reset snapshots, serially advanced session invalidation, malformed ACK and model-identity ingress/rearm transitions, canonical model IDs, monotonic nonzero IDs, stale/future/duplicate IDs, delayed-result cleanup, heartbeat timeout/regression/rollover, PLC model identity, per-channel semantic contradictions, warning-bearing pass rejection and fail-closed behavior without a trained model claim.

## Automated project validation

`python scripts/validate_project.py` passes the current static/data/source check set with zero failures. `scripts/check_determinism.py` independently rebuilds the controlled source/report set twice with zero missing, extra or mismatched files; the release entry point additionally compares two normalized workbook builds and two PDF builds by SHA-256. The workbook renders 20 sheets with zero formula-error matches; the PDF renders five pages. Final manifest verification must report equal listed/actual controlled-file counts and zero missing, unlisted, classification or hash mismatches. Native/tool-dependent blockers remain open regardless of these passes.
