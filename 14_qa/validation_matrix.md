# Validation matrix - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| Domain | Evidence | Disposition |
|---|---|---|
| Canonical data / schedules | Uniqueness, cross-artifact and rationale coverage | PASS when validator reports zero failures |
| Siemens SCL | Generator parity plus process/interface/source contracts | Source-tested; native TIA compile BLOCKED |
| HMI/Startdrive/PLCSIM | Import-ready specifications/schedules only | Native execution BLOCKED |
| Process simulator | 32 deterministic scenarios and test suite | PASS; explicitly not PLCSIM/physical evidence |
| NVIDIA OPC UA | Secure asyncua server/client, PKI, reconnect, idempotency, health/metrics | Local integration PASS; production endpoint/model/runtime BLOCKED |
| QElectroTech | Corrected 26-folio QET, static/schedule contracts | Source PASS; exact-hash reopen/export/all-page review BLOCKED |
| FreeCAD/STEP/IGES/DXF | Selected-architecture native source, reopen/reimport and visual package | Native gate follows controlled verification record |
| XLSX/PDF | Deterministic generation, formula scan and rendered visual review | Final release evidence after freeze |
| Safety/electrical construction | Boundary statement and conceptual separation | Qualified/site/physical activities BLOCKED |
| Release integrity | Staged/HEAD manifest, determinism and fresh-clone reproduction | PASS for published candidate `b9633c6255fe34e48a1be34afe5024935f48651e`; final attestation commit is rechecked after push |
