# System design basis

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Baseline approval state

The controlled baseline is revision B. It retains the primary package's IEC 81346-style designation system and native QElectroTech/FreeCAD artifacts, replaces the secondary package's informal tags through an explicit migration table, and makes Siemens the sole executable PLC target.

### Machine boundary

Included: infeed/indexing, gate, clamp, common pump, two independent fill channels, capping handshake, bounded NVIDIA inspection, panel/control power, HMI, drives, standard-control diagnostics and deterministic simulator. Excluded: upstream/downstream mechanics, utilities generation, legal metrology, physical reject, credited safety design, sanitary process qualification and physical commissioning.

### Approved control principles

1. Fail-closed fill valves and pump stop on every blocking fill condition.
2. Each channel closes independently at target pulses; analog flow is a plausibility channel, not the dose total.
3. Any uncertain vision outcome produces HOLDING; only explicit operator disposition can release/recover.
4. Recovery/reset returns to STOPPED and never commands automatic restart.
5. External safety system removes hazardous energy; PLC and AI only observe non-safety status.
