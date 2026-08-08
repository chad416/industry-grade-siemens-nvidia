# Cloud cost assumptions

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

No cloud resource was created and actual cost is **EUR/USD 0.00 from this Revision-G execution**.

The estimate is intentionally formula-driven because project region, quota, current price, Windows licence treatment, discounts and run hours are not approved:

`monthly estimate = Windows VM hourly rate * approved hours + GPU VM hourly rate * active training hours + persistent-disk GB-month + snapshot GB-month + object-storage GB-month + network/NAT/logging charges`.

Before plan approval, the owner must record a dated Google Cloud Pricing Calculator export for the selected region and a maximum monthly budget. Budget alerts are notifications and do not automatically cap ordinary Compute Engine spend. Stopping a VM stops vCPU/GPU runtime charges but does not remove persistent disk, snapshot, IP/NAT, Data Access logging, monitoring or storage charges. The Terraform defaults keep both VMs disabled and configure weekday shutdown schedules if enabled. Audit-log volume and retention must be priced before apply.

Official sources: https://cloud.google.com/products/calculator, https://cloud.google.com/billing/docs/how-to/budgets, https://cloud.google.com/compute/docs/instances/schedule-instance-start-stop.
