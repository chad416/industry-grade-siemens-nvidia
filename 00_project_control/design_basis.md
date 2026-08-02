# Design basis - Revision D

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

The only current canonical owner is `00_project_control/canonical_model.json`, finalized by `scripts/revision_d_generator.py`; `scripts/revision_d_scl.py` owns all 15 Siemens source exports. Schedules, rationale, documents, workbook, PDF, validator evidence and manifests derive downstream in the recorded dependency order.

The PLC remains authoritative for sequence, interlocks, timeouts, safe decommanding, recovery and transfer permission. NVIDIA is a non-safety quality subsystem. Historical QET/FreeCAD files are quarantined Revision-A evidence and never represent selected Revision-D hardware. Site supply, fault current, motor/pump data, cable routes, environmental limits, qualified safety work, native engineering, real dataset/model/runtime and physical testing remain controlled inputs/gates.
