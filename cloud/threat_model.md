# Cloud threat model

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| Threat | Control | Residual risk / verification |
|---|---|---|
| Public RDP/SSH exposure | No external IP; IAP-only ingress rule | Verify plan and effective firewall after apply |
| Overprivileged workload identity | Separate keyless service accounts; bucket-level object role only | Review effective IAM; organization policies may add grants |
| Credential disclosure | No key files or secrets in Git; ADC/Secret Manager only | Terraform state and screenshots still require access control |
| Unbounded cost | VM creation false by default, schedules, budget alerts, GPU stopped when idle | Budget alerts do not cap spend; disks/snapshots/storage persist |
| Malicious dependency/image | Require approved image digest, SBOM and vulnerability scan before container build | No container was built in Revision G |
| OT pivot | Lab-only VPC, no plant route/VPN/interconnect | Future OT connection requires separate zone/conduit design |
| Dataset exfiltration | Restricted bucket, versioning, no public access, retention decision | Privacy/provenance approval remains absent |
| Untrusted OPC UA peer | Site PKI, named identities, SignAndEncrypt, least-privilege nodes | Production S7/Jetson PKI integration remains untested |
| Accidental apply/destroy | All create flags false; scripts separate validate/plan from apply; deletion protection | An authorized operator can still override controls |
