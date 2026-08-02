# Factory acceptance test procedure — planned, not executed

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Prerequisites: approved native TIA project and hardware catalog; PLC/HMI/drive compile reports; isolated PLCSIM or test panel; calibrated stimulus; approved risk controls. Record tool versions, hashes, tester, date and deviations.

Execute every `TC-*` row in `10_schedules/test_coverage.csv`, verify state/first-out/timing/output traces, restore without automatic restart, and reconcile result IDs. The deterministic Python regression evidence is a design check only and must not be entered as PLCSIM or FAT execution.
