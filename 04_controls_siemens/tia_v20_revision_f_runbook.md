# TIA Portal V20 Revision-F native execution runbook

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Use an authorized, licensed TIA Portal V20 engineering station. This runbook is closure procedure, not evidence that native execution occurred.

1. Confirm product version `2000.0.9501.1`, target CPU catalog/firmware, MTP700 catalog entry, Openness group membership and active licences. Record screenshots and executable SHA-256.
2. Create a new controlled project, hardware configuration and PROFINET topology. Select the exact CPU/I/O/device versions; do not substitute a catalog item silently.
3. Import SCL in `import_order.txt` order. Resolve all syntax/type errors without weakening the fail-closed logic.
4. Compile hardware and software with zero errors. Retain the full compiler report and PLC resource/retentivity report.
5. Review `DB_VisionComms` retentivity: only session, controlled identities, acceptance thresholds and approval flag are retained. Edge-owned states/results and all physical outputs are non-retentive.
6. Expose the controlled PLC/edge symbols through the CPU OPC UA server with least privilege: NVIDIA reads PLC-owned nodes and writes edge-owned nodes only. Verify each NodeId, Variant type, owner, update behavior and namespace discovery against the controlled node map.
7. Set expected model ID/hash, dataset ID, calibration ID, confidence, age, processing and queue limits only through a signed engineering change. Keep `ModelConfigurationApproved=FALSE` until genuine model/dataset/calibration evidence is approved.
8. Build and compile WinCC Unified using `05_hmi/wincc_unified_revision_f_runbook.md`.
9. Configure both G120C PN drives from `06_drives/startdrive_revision_f_runbook.md` only after Startdrive and motor/site inputs are available.
10. Execute PLCSIM/PLCSIM Advanced fault scenarios: PASS, HOLD, FAIL, FAULT, timeout, stale/duplicate/future ID, session mismatch, capture mismatch, state/disposition contradiction, low confidence, health loss, identity mismatch, excessive age/latency, queue saturation, recipe change, clock regression, OPC UA loss/reconnect, edge restart and PLC restart.
11. Prove every invalid result suppresses release and every restart requires the documented deterministic recovery. Retain actual traces and archive hash.

Acceptance requires zero compile errors, reviewed warnings, restored archive, exact tag/node types, negative permissions tests and trace evidence. Without these, native Siemens gates remain BLOCKED.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
