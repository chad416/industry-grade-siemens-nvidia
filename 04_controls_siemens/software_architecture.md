# Siemens PLC software architecture

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

OB1 executes input normalization, equipment modules, coordinator, alarm/recipe/counters/HMI communications, and final output mapping in that order. Each timer and edge detector belongs to one instance. Equipment modules expose command, feedback, permissive, interlock, state, fault, warning, configuration and diagnostics separately. The coordinator owns legal machine transitions; equipment FBs own actuator dynamics and timeouts.

Simulation hooks are held in a dedicated non-retentive DB with a compile-time `SIMULATION_BUILD` constant. Release validation fails if it is true or if any forcing tag is referenced by the physical output mapper. A fresh power cycle initializes to UNINITIALIZED then STOPPED; an explicit reset and start edge are required.
