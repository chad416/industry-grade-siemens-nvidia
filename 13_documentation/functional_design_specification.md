# Functional design specification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

The automatic sequence and state model are controlled by `02_system_architecture/state_and_sequence.md`. Equipment modules enforce feedback, timeout and contradiction diagnostics. Fill totals are independent; pump stops only after both valve commands close or immediately on a blocking condition. Failed or uncertain product remains clamped/gated for explicit disposition.
