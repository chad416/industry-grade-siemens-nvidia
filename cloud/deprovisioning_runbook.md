# Cloud deprovisioning runbook

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

1. Export and hash approved evidence; confirm no secrets are included.
2. Stop both VMs and verify status.
3. Review persistent disks, snapshots, buckets, NAT, logging sinks and reserved addresses with owners.
4. Run a saved Terraform destroy plan; require a second reviewer before apply.
5. Preserve only approved retention artifacts; `force_destroy` is disabled.
6. Remove IAM grants/service accounts, then network resources.
7. Confirm Billing export shows no continuing compute/storage/network resource and record final cost.

Revision G does not execute these destructive actions.
