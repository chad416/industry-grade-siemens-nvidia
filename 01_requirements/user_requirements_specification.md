# User requirements specification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

- **SYS-001** — Receive and index exactly two bottles
- **SYS-002** — Confirm both bottle positions before filling
- **SYS-003** — Stop conveyor before clamp engagement
- **SYS-004** — Confirm gate and clamp feedback without contradiction
- **SYS-005** — Zero and accumulate two independent high-speed pulse totals
- **SYS-006** — Start common pump only with both fill paths permissive
- **SYS-007** — Close each fail-closed valve independently at target
- **SYS-008** — Scale and diagnose two 4–20 mA flow channels
- **SYS-009** — Detect no-flow, leakage, overfill, underfill and channel disagreement
- **SYS-010** — Apply configurable drip-settle time
- **SYS-011** — Trigger vision using a monotonic inspection ID
- **SYS-012** — Correlate result ID and reject stale or contradictory results
- **SYS-013** — Hold product on missing, uncertain, failed or low-confidence vision result
- **SYS-014** — Transfer only when process and quality acceptance are both true
- **SYS-015** — Exchange ready, busy, request, complete and fault with capper
- **SYS-016** — Prevent unintended restart following power or control recovery
- **SYS-017** — Provide Auto, Manual/Setup, Holding, Controlled Stop, Fault and Recovery states
- **SYS-018** — Separate commands, feedbacks, permissives, interlocks, faults, warnings and diagnostics
- **SYS-019** — Monitor external safety status only; standard PLC and AI are not safety functions
- **SYS-020** — Provide first-out fault capture and separate alarm acknowledgement from reset
- **SYS-021** — Provide permission-controlled HMI commands with feedback and disabled reason
- **SYS-022** — Provide deterministic simulator and fault-injection regression suite
- **SYS-023** — Maintain canonical tags across I/O, HMI, electrical, AI and tests
- **SYS-024** — Provide backup, restore and release-manifest procedure
- **SYS-025** — No physical reject device is included; operator disposition is required

Acceptance is governed by the traceability and validation matrices; reviewable source is not equivalent to native Siemens verification.
