# Executed test report - Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Execution date: 2026-08-03. Source/design tests use Python 3.12.13; encrypted OPC UA tests use Python 3.12.13 / asyncua 2.0.1. Native CAD evidence uses FreeCADCmd 1.1.3 and schematic evidence uses QElectroTech 0.100.0+git8590. These are not TIA compile, PLCSIM, FAT, SAT, safety validation, construction test, model performance or production NVIDIA runtime results.

| Workstream | Exact result | Evidence boundary |
|---|---:|---|
| Simulator/Siemens/source/native contracts | 99/99 PASS | Includes inherited contracts plus eleven Revision-F behavioral fault-injection tests |
| NVIDIA edge service | 86/86 PASS | Includes 10/10 certificate-backed local asyncua cases; synthetic endpoint |
| PLC-AI interface harness | 17/17 PASS | Deterministic composed 47-node acceptance model |
| Process scenarios | 32/32 PASS | Exactly one normal release; no invariant violation/automatic restart |
| Vision behavioral fault injections | 28/28 PASS | Exactly one normal pass releases; outputs decommanded; no automatic restart; software-only evidence |
| Engineering validator | 551/551 PASS | Static/data/source/native-evidence contracts |
| Revision-F verifier | 96/96 PASS | Contract, HMI, electrical, traceability, hygiene, data/model honesty, gates and version policy |
| QET source / dedicated contracts | 24/24 and 6/6 PASS | Corrected source contracts |
| QET exact-hash native verifier | 19/19 PASS | Reopen/export/hash/page metadata; overall gate PARTIAL |
| FreeCAD native verifier | 80/80 PASS | 165 objects, 148 controlled solids, STEP/IGES/DXF and 30 holes |
| Workbook | 26 sheets; 12 stored formula cells; zero formula-error matches | Two builds SHA-256 `F7B326032B630B551B87A2882BB65FFD3867A250C2BF7AACD047B54F2B31534A` |
| Release PDF | 6 pages | Two builds SHA-256 `DF06D0C5E5C19E567FF277EB84B9284295C4BF2944FAD38172186A9827BED702` |

Final manifest, release-integrity, authoritative-snapshot determinism and post-push fresh-clone results are recorded separately after candidate freeze/commit. No software-agent record constitutes qualified-human approval.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
