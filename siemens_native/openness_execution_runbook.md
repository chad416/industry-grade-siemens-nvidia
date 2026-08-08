# TIA Openness execution runbook

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

After licence/group authorization, run `siemens_native/preflight.ps1` under the named engineering identity. Create a new V20 project only through TIA Portal/Openness; import the controlled SCL and tag/alarm/HMI tables, configure the exact catalog hardware and PROFINET topology, then compile hardware/software/HMI/drives. Export raw compiler messages without filtering. Classify every warning as corrected, accepted with rationale, blocking or tool limitation. Run PLCSIM scenarios and archive through supported Siemens mechanisms. Hash AP20/ZAP20, logs and screenshots. Never use file renaming or fabricated XML as a native artifact.
