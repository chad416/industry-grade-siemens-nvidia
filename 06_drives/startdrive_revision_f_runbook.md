# Startdrive Revision-F native execution runbook

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Startdrive is not installed in the audited environment. Perform these steps only with licensed compatible Siemens software, actual drive/motor data, electrical commissioning authorization and the machine secured against hazardous motion.

1. Verify both actual G120C MLFBs, firmware, option/accessory state, motor nameplates, supply and line protection. Reconcile against the BOM before creating devices.
2. Install the vendor-supported Startdrive version compatible with TIA Portal V20 and the actual drive firmware. Record version, installer/source and executable hashes.
3. Add `-U100` and `-U101`, assign controlled PROFINET names/IP addresses and Standard Telegram 1. Match every PZD address in `pzd_map_revision_f.csv`.
4. Enter motor/nameplate and application data. Resolve every OPEN row in `startdrive_parameter_baseline_revision_f.csv` through an approved change; do not copy assumed ramps/current limits into production.
5. Compile hardware. Resolve all errors and warnings; retain the complete report.
6. With motors mechanically/electrically safe, verify device identification, rotation, reference-speed scaling, current, ramps, stop behavior, communications loss and fault reset. Motor identification requires explicit physical commissioning authority.
7. Prove that loss of PLC release, quality HOLD/FAIL/FAULT, OPC UA/vision fault and PLC restart never create a run command or automatic restart. NVIDIA must have no writable route to drive PZD.
8. Verify the qualified safety design separately. Do not use standard PLC stop or software-agent testing as STO/safety validation.
9. Save a native project/archive and drive parameter backup; restore them into a clean engineering environment and record hashes.

Closure evidence: installed/licensed tool versions, actual nameplates, compiled hardware report, resolved parameter register, safe physical test record, trace files, restored archive and qualified safety records. Until then, Startdrive and physical-drive gates remain BLOCKED.
