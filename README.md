# Industry-grade Siemens/NVIDIA compact filling cell

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

This repository is the integrated revision-B engineering package. Siemens sources are reviewable exports, not a native TIA project. The inherited QElectroTech and FreeCAD baselines are genuine and were previously reopened in their native applications; they predate the final Siemens/NVIDIA selection and are quarantined under `native_baseline` so they cannot be mistaken for the completed upgrade.

## Current status

**PARTIALLY COMPLETE.** Canonical engineering data, modular Siemens-oriented SCL, HMI specification, drive philosophy, deterministic simulator, PLC–AI contract, DeepStream deployment configuration, schedules, traceability and release controls are implemented. Mandatory native TIA/WinCC/Startdrive/PLCSIM, trained-model, upgraded-QET and revised-CAD gates remain incomplete.

## Reproduce

```powershell
python scripts/build_project.py
python -m unittest discover -s 11_simulation/tests -v
python 11_simulation/run_scenarios.py
python scripts/validate_project.py
```

See `release/RELEASE_NOTES.md` and `14_qa/acceptance_gate_status.md` before use.
