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
| Workbook | 21 sheets; zero formula-error matches | Two normalized builds SHA-256 `C6899C10D680F030901E966FAD00694D6F22C77CD9B7C6BF8F0E33B39145E855` |
| Release PDF | 5 pages | Two builds SHA-256 `76D12BAEB56E60E5025D2995546EF08B5085462C8DD6F3C8A2AA3CAC77906D03` |

Final manifest/release-integrity counts and the pushed-commit clean-clone result are frozen only after all controlled content and review records are complete.
