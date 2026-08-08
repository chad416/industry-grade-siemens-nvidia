# Windows TIA build runbook

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

1. Confirm the selected host/virtualization route is supported by Siemens or obtain written support confirmation.
2. Provision only after approved Terraform plan and cost/security review.
3. Connect through IAP; do not add an external IP or public RDP rule.
4. Patch Windows; install Git/evidence tooling from approved sources.
5. Install TIA V20, STEP 7 Professional, WinCC Unified, Startdrive, PLCSIM and TIA Openness under the organisation licence process.
6. Assign licences without placing keys in Git/logs. Add the engineer to Siemens TIA Openness and re-authenticate.
7. Clone the exact Revision-G commit, run `siemens_native/preflight.ps1`, then follow the existing TIA/WinCC/Startdrive runbooks.
8. Store raw native logs/screenshots/archives only in the controlled evidence path; hash every artifact.
9. Stop the VM after exporting evidence; retain only approved disks/snapshots.
