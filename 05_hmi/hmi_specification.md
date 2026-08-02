# WinCC Unified HMI specification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Screens

Overview/automatic, filling detail, manual/setup, recipe, alarm history, I/O diagnostics, drive diagnostics, NVIDIA inspection, counters/maintenance, and users/security screens are required. Native screen objects do not yet exist.

## Command contract

Every command writes only `DB_HMI.<Command>.Request` and increments `RequestSeq`. The PLC returns AcceptedSeq or RejectedSeq plus Allowed/Busy/DisabledReason. Start, controlled stop, reset, acknowledgement, mode, disposition and recipe apply are separate. Physical DO, PZD, stack lights, camera light and spare channels are never writable HMI tags.

## Security and audit

Operator may start/stop/ack/reset when permitted. Supervisor controls recipes and disposition. Maintenance may use hold-to-run manual requests subject to PLC interlocks and heartbeat. User changes, recipe changes, dispositions, alarm acknowledgements and rejected commands are audit-relevant. Native roles, bindings, trends and compile remain open.
