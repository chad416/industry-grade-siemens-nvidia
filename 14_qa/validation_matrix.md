# Validation matrix - Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| Domain | Local evidence | Boundary |
|---|---|---|
| Canonical/interface | 47-node ownership/type/schedule/source parity | Native TIA/production endpoint external |
| Edge service | Acquisition/configuration/adapters/audit plus encrypted OPC UA tests | Synthetic/mock inputs are non-production |
| Dataset/evaluation tools | Hash/split/QA/metrics/threshold harnesses with synthetic fixtures | Real dataset/model metrics blocked |
| Process and vision behavioral simulation | Existing 32 process scenarios plus 28 structured vision fault injections | Software-only model; not PLCSIM, HIL, FAT or physical evidence |
| Electrical/CAD/QET | Revision-E native CAD retained; controlled Revision-F electrical delta | Final devices/site calculations/native delta/qualified review open |
| Workbook/PDF/release | Deterministic build, formula scan, page/sheet renders, manifest and clean clone | Final evidence recorded after freeze/push |
