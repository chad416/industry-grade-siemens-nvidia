# Executed non-native test report

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

Execution date: 2026-08-02. Runtime: bundled Python 3.12.13. These are deterministic design/interface tests, not TIA Portal compile, PLCSIM, FAT, SAT or physical commissioning evidence.

## Process simulator

Command:

```powershell
& '<bundled-python>' -m unittest discover -s 11_simulation\tests -v
& '<bundled-python>' 11_simulation\run_scenarios.py
```

Result: 3 unit-test methods passed. The parameterized safety invariant covered all 32 required scenarios. All scenarios end with pump and both valve commands false; only the normal two-bottle cycle releases; power recovery and reset do not restart. Detailed rows are in `11_simulation/outputs/scenario_results.csv`.

## PLC-AI protocol oracle

Command:

```powershell
Set-Location 07_nvidia_vision
& '<bundled-python>' -m unittest -v test_plc_interface_harness.py
```

Result: 6 tests passed: normal correlated result, timeout, stale ID, low confidence, internal fault/split bottle result, and heartbeat loss. Every negative case returned a quality-hold disposition.

## Automated project validation

Command: `& '<bundled-python>' scripts\validate_project.py`.

The final result is recorded in `automated_validation_report.md`; the validator also regenerates SHA-256 manifests. Native/tool-dependent blockers remain open regardless of this PASS.
