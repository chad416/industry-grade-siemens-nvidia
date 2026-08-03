# Post-push fresh-clone reproduction - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Published candidate

- Branch: `codex/revision-e-native-engineering-execution`
- GitHub commit: `b9633c6255fe34e48a1be34afe5024935f48651e`
- Clone basis: brand-new GitHub clone outside OneDrive
- Workflow: `powershell -ExecutionPolicy Bypass -File scripts/reproduce_validation.ps1`
- Result: **PASS** with exit code 0

| Check | Result |
|---|---|
| Manifest | 310 listed / 310 actual; 0 missing, unlisted, unexpected or discrepant |
| Release integrity | 534/534 PASS |
| Engineering validator | 551/551 PASS |
| Siemens/simulator/native contracts | 88/88 PASS |
| NVIDIA edge-service tests | 59/59 PASS |
| PLC-AI interface harness | 15/15 PASS |
| Timed scenarios | 32/32 PASS |
| QET structural verifier | 24/24 PASS |
| FreeCAD native verifier | 80/80 PASS |
| Workbook/PDF | Two deterministic builds each; 21 sheets and 5 pages rendered |
| Final repository state | Clean |

This closes the locally achievable release-integrity gate for the published candidate. It is configuration-management evidence, not qualified-human engineering approval. The final attestation commit is re-cloned and rerun after publication; no native Siemens, exact-final-hash QET reopen/export, construction, model, physical or safety gate is implied.
