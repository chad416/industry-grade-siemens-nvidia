# NVIDIA inspection fault-injection procedure - planned and software-modeled

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

The deterministic Revision-F structured behavioral fault-injection model covers 28 cases in `11_simulation/vision_fault_scenarios.json`. For each case record injected observations, exact session/inspection identity, timestamps, modeled PLC state, result/disposition, first-out diagnostic, physical commands and recovery sequence. This is software-only design evidence, not PLCSIM, HIL, FAT or physical evidence.

Required invariants are:

- the edge cannot energize an actuator or authorize hazardous motion;
- only a fresh coherent PASS can contribute to PLC transfer authorization;
- missing, stale, duplicate, future, delayed, malformed, contradictory, low-confidence or faulted data cannot become PASS;
- restart or reconnection cannot reuse a prior bottle/session result;
- pump and fill-valve commands are off for inspection fault/hold outcomes;
- reset never starts the machine; a new explicit start and, where required, new inspection are mandatory;
- diagnostics identify the initiating cause rather than a generic timeout when more specific evidence exists.

The structured behavioral fault-injection model is software-only design evidence. Repeat applicable cases in PLCSIM and then on isolated target hardware before FAT; label those records separately.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
