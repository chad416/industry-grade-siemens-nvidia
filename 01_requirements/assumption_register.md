# Assumption and limitation register

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| ID | Assumption | Impact if false | Required verification |
|---|---|---|---|
| AS-01 | 400/230 VAC TN-S and 24 VDC PELV are available | Protection and PSU architecture changes | Site survey and supply data |
| AS-02 | Two 24 V pulse outputs plus isolated 4–20 mA outputs are available | Counter and AI modules/interface change | Flowmeter data sheet |
| AS-03 | 0.75 kW drives cover conveyor and pump | Drive, cable, protection and heat change | Nameplates and pump curve |
| AS-04 | Bottles are optically transparent enough for visible fill estimation | Vision method/camera/lighting change | Optical feasibility trial |
| AS-05 | External safety system provides a standard diagnostic mirror | Monitoring I/O changes | Qualified safety design |
| AS-06 | Capping interface is dry-contact/24 V PNP compatible | Interface relays/protocol change | Capper ICD |
| AS-07 | OPC UA is permitted across a routed OT quality zone | Protocol/gateway change | Cybersecurity review |
| AS-08 | No automatic physical reject is required | Mechanics, I/O and logic expand | Operational approval |
