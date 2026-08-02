# AI model card — untrained design record

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

- Model identity: **NOT TRAINED / NOT DELIVERED**.
- Intended use: non-safety quality inspection for two visible bottles after filling.
- Intended deployment: DeepStream 9.1-compatible Jetson Orin platform, final carrier and JetPack image TBD.
- Inputs: calibrated color frames under controlled lighting; exactly two expected ROIs.
- Outputs: presence/pass, fill status, visible damage/spill, confidence and diagnostics.
- Metrics: none; no dataset or GPU workload was available. Thresholds remain unvalidated.
- Known limits: transparent bottles, glare, foam, labels, colored/opaque product, condensation, vibration and novel bottle geometry.
- Rollback: deploy versioned signed bundle, verify SHA-256 and smoke-test on challenge set; keep previous signed bundle; rollback requires maintenance authorization and records model/version/time. Procedure is designed but untested.
