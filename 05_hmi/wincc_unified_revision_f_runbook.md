# WinCC Unified Revision-F execution runbook

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

These steps require a licensed, authorized TIA Portal V20/WinCC Unified engineer. The CSV files in this directory are controlled engineering binding tables; they are not represented as a native WinCC export or proof of successful import.

## Build sequence

1. Create or open the controlled MTP700 Unified Comfort device only after confirming the exact MLFB/firmware catalog entry.
2. Compile the PLC first and browse the optimized DB symbols. Reject any type/name difference from `vision_tags_revision_f.csv`.
3. Create the PLC connection and HMI tags using the listed symbolic sources. Keep every vision/result/configuration tag read-only. The only write path on the vision screen is the existing sequenced `DB_HMI.DispositionRemoved` command.
4. Create text lists from `vision_state_texts_revision_f.csv` and a script/data-driven multi-bit decoder from `vision_reason_bits_revision_f.csv`. Confirm simultaneous reason bits all render.
5. Create alarm classes and discrete alarms from `vision_alarms_revision_f.csv`. Configure event history with timestamp, user and acknowledgement fields; do not claim edge audit retention from HMI history.
6. Display the edge diagnostic UInt32 in hexadecimal. Zero means `OK`; nonzero status values are IEEE CRC-32 of the uppercase ASCII first-out token and must be correlated with the durable structured edge log. Result-specific diagnostics remain numeric payload values.
6. Build the faceplate from `vision_faceplate_revision_f.csv`. Expose a PLC-derived PASS indication only when `DiagReason=VISION_OK`, `QualityHold=FALSE`, exact IDs/sessions agree, disposition is PASS and health/identity fields agree.
7. Add NVIDIA inspection and troubleshooting screens to the controlled navigation. Keep the non-safety/PLC-authority banner visible on both.
8. Configure Operator, Supervisor and Maintenance roles. Prove that Operator cannot disposition product, Supervisor cannot write identity/threshold fields and no role can write edge/result nodes, PZD or physical outputs.
9. Compile the HMI. Retain compiler version, messages, timestamp, project/archive SHA-256 and screenshots of the final screen objects.

## Native acceptance tests

- Disconnect the edge client: readiness turns abnormal, alarm 1501/1505 occurs as designed, PASS cannot remain visible and no automatic restart occurs.
- Exercise capture-ID, result-ID and session mismatch: the screen shows all four identifiers and alarm 1503/1506; disposition remains disabled unless PLC allows it.
- Publish low-confidence, nonzero-reason HOLD and FAIL results: PASS never appears; all reason bits render; quality hold remains until physical disposition and sequenced PLC acceptance.
- Publish malformed state/disposition, timestamp regression, excessive processing time, queue saturation and identity mismatch: red diagnostic state, no release indication.
- Enter manual/setup: maintenance state is prominent, production enable is false and no bypass control exists.
- Test permissions, rejected command sequence visibility, login/audit events, alarm history, screen navigation, power cycle and restored archive.

Record actual native results. Until these checks and an error-free HMI compile exist, WinCC gates remain BLOCKED rather than PASS.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
