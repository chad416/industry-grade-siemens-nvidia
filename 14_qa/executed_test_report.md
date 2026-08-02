# Executed non-native test report

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

Execution date: 2026-08-02. Runtime: bundled Python 3.12.13. These are deterministic design/interface tests, not TIA Portal compile, PLCSIM, FAT, SAT or physical commissioning evidence.

## Process simulator

Command:

```powershell
& '<bundled-python>' -m unittest discover -s 11_simulation\tests -v
& '<bundled-python>' 11_simulation\run_scenarios.py
```

Result: 20 test methods passed. Property sweeps covered 10/20/40/50 ms time steps and 400/500/700 ml targets. Thirty-two timed scenarios generated 7,147 trace samples. Exactly one scenario releases, invariant violations are zero, and automatic restarts are zero. The model includes conveyor, two bottles, gate, clamp, common pump, two valves, pulse/analog flow, vision, capper, power and communications. Detailed summaries and per-scenario traces are under `11_simulation/outputs`.

## PLC-AI protocol oracle

Command:

```powershell
& '<bundled-python>' -m unittest discover -s 07_nvidia_vision\edge_service\tests -v
```

Result: 11 edge-service tests and 6 PLC-interface timing-harness tests passed in addition to the protocol cases within the 20-test simulator suite. The service rejects absent/malformed/swapped model identity, duplicate/non-monotonic inspection ID, regressing, timed-out or stale heartbeat, wrong bottle count and invalid target bounds; a controlled test backend proves atomic success behavior without being represented as a trained model. Protocol errors fault the service closed.

## Automated project validation

Command: `& '<bundled-python>' scripts\validate_project.py`.

Result: 238 static/data/source checks passed and zero failed. The validation result is recorded in `automated_validation_report.md`. Manifest generation and verification are separate commands so a validator run cannot silently rewrite release integrity evidence. Native/tool-dependent blockers remain open regardless of this PASS.
