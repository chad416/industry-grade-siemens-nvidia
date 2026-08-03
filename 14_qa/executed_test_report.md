# Executed test report - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Execution date: 2026-08-03. Source/design tests use the controlled Python 3.12.13 toolchain; encrypted OPC UA tests use the separately locked Python 3.12.13 / asyncua 2.0.1 environment. Native CAD evidence uses FreeCADCmd 1.1.3. These results are not TIA compile, PLCSIM, FAT, SAT, safety validation, electrical construction test or model-performance evidence.

| Workstream | Exact result | Evidence boundary |
|---|---:|---|
| Simulator/source/native contracts | 88/88 PASS | Includes inherited 58, nine poll-safe Siemens contracts, six QET contracts and 15 CAD contracts |
| NVIDIA edge service | 59/59 PASS | 47 protocol/service, two observability, eight encrypted asyncua server/client and two operational-documentation tests |
| PLC-AI interface harness | 15/15 PASS | Deterministic composed interface model |
| Timed scenarios | 32/32 generated with zero invariant violations | Exactly one normal release; no automatic restart |
| Engineering validator | 551/551 PASS | Static/data/source/native-evidence contracts; no Siemens-native claim |
| QET verifier | 24/24 PASS; dedicated tests 6/6 | Corrected source only; exact-hash native reopen/export remains BLOCKED |
| FreeCAD native verifier | 80/80 PASS | 165 objects, 148 valid controlled solids, exact GUI-tool provenance, STEP solids, IGES bounded faces, DXF and 30 holes |
| FreeCAD verifier repeatability | 3/3 generated evidence files byte-identical across two runs | Native geometry/evidence determinism; FCStd/IGES byte identity is not claimed |
| Workbook | 21 sheets; zero formula-error matches | Two normalized builds SHA-256 `32D6D4CC67054C911149D65444F332D04EA1D6907B4F887E93A5FF5118B85D49` |
| Release PDF | 5 pages | Two builds SHA-256 `5E9DEEEF050524140B730BEDFAB41998811F7C7EB472183CC264FCA092400E08` |

Published candidate `b9633c6255fe34e48a1be34afe5024935f48651e` was cloned afresh from GitHub outside OneDrive. The complete workflow passed: manifest 310/310 with zero discrepancies, integrity 534/534, validator 551/551, 88/88 simulator/source/native contracts, 59/59 edge tests, 15/15 interface tests, 32 scenarios, FreeCAD 80/80, QET 24/24, deterministic workbook/PDF builds and a clean final worktree. The final attestation commit is subjected to the same post-push check before handoff.
