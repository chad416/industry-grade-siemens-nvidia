# Design basis - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

The canonical owner is `00_project_control/canonical_model.json`. `scripts/build_project.py` applies the frozen Revision-D generator and the deterministic Revision-E overlay; `scripts/revision_d_scl.py` owns the complete 15-file Siemens source export. Schedules, controlled documents, workbook, release PDF and manifest follow the recorded dependency order. Native CAD/QET binaries are authored only by their dedicated sources and are never synthesized by the release generator.

The S7-1500 PLC remains authoritative for sequence, permissives, interlocks, timeouts, actuator/drive requests, quality-result acceptance, product disposition and transfer permission. HMI access is supervisory and audited. NVIDIA is a non-safety quality subsystem and has no hazardous-motion command path. Missing, stale, contradictory, low-confidence, malformed or unacknowledged AI data fails closed to HOLD/FAULT. A request is level-held with immutable session/inspection identity until coherent edge observation or terminal result.

Revision-E FreeCAD geometry represents the selected architecture and has controlled native verification when its record is PASS. The corrected Revision-E QET is a deterministic, schedule-reconciled source; its exact final hash was not natively reopened or exported, so its native/visual gates remain partial/blocked. Site supply, fault current, motor/pump data, cable routes, ambient/environment, final vendor selections, qualified safety work, real dataset/model/target runtime, FAT/SAT and physical commissioning remain controlled inputs or blockers.
