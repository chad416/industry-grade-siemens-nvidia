# Revision G consolidated external handoff

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Use this single handoff only when the project owner elects to continue external execution. Do not provide secrets in chat.

## 1. Cloud approval

Approve only a non-destructive Terraform plan first. Provide the Google project ID, billing account ID, approved IAM principals and Application Default Credentials through the local Google CLI/OS credential store. Set an approved monthly budget after checking the current Google Cloud Pricing Calculator. No apply is authorized by this handoff. Pricing is uncertain until region, quotas, Windows licensing, sustained-use/Spot policy and storage are selected. The plan is reversible; no resource exists until a separate apply approval. Stop/removal controls are instance schedules plus the deprovisioning runbook; disks, snapshots and buckets can continue to cost money while VMs are stopped.

## 2. Siemens native access

On a supported Windows engineering host, add the named engineer to the local **Siemens TIA Openness** group, sign out/in, assign valid STEP 7 Professional V20 and WinCC Unified licences through Automation License Manager, and install/authorise Startdrive and PLCSIM/PLCSIM Advanced. Do not send licence keys. Then execute `siemens_native/preflight.ps1` and the native runbook. This changes local security membership and licensed software state and may require administrator approval/restart.

## 3. NVIDIA runtime and data

Approve either the reviewed Linux GPU cloud plan or a local Ubuntu 24.04/container installation and any NVIDIA registry terms. Provide representative bottle/process images through controlled storage, not chat. The owner must approve the label taxonomy before training. Keep the GPU stopped outside active work.

## 4. Physical and qualified execution

Provide the confirmed supply/earthing/fault-current/site/environment data, motor and pump nameplates, selected camera/lens/light/carrier data, built equipment and calibrated instruments. Appoint qualified electrical and machinery-safety engineers and a commissioning manager. They own measurements, signatures, construction release, safety lifecycle and final acceptance.
