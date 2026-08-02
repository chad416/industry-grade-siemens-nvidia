# Validation matrix

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| Domain | Evidence available | Result |
|---|---|---|
| Canonical data / schedules | Automated uniqueness, required signals, CSV parse, hash manifest | Pass when validator reports zero errors |
| Modular Siemens SCL | Text/source review only | Implemented; native compile blocked |
| HMI/Startdrive | Functional specifications and tag schedules | Native configuration/compile blocked |
| Deterministic simulator | 32 regression scenarios | Executed locally; not PLCSIM evidence |
| NVIDIA interface | Contract and simulator cases | Logic design tested; runtime/model blocked |
| QElectroTech | Genuine inherited native baseline | Baseline reopen evidence only; upgrade blocked |
| FreeCAD/STEP/IGES/DXF | Genuine inherited native baseline | Baseline reopen/reimport evidence only; upgrade blocked |
| PDFs/XLSX | Final release artifacts require render inspection | See visual QA report |
| Safety | Boundary statement and non-safety separation | Concept only; qualified project work required |
