# WinCC Unified HMI specification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| Screen | Purpose | Key faceplates |
|---|---|---|
| Overview / automatic | Mode, state, pair flow, disposition | machine state, actuator, fill channel, vision |
| Filling detail | Pulses, mA, targets, valve state, diagnostics | two fill-channel instances |
| Manual/setup | Permission-controlled jogs | actuator and drive faceplates |
| Recipes | Staged values, validation, apply handshake | recipe editor/change record |
| Alarms/history | first-out, active, acknowledged, cleared | alarm summary/history |
| I/O diagnostics | module/channel/address/raw/scaled | diagnostic table |
| Drives | status word, reference, actuals, faults | G120C faceplate |
| NVIDIA inspection | ready/busy/ID/result/confidence/model identity | vision faceplate |
| Maintenance/production | counters, service due, good/held pairs | counter tiles |
| Users/config/system | roles, audit, network health, backups | administration |

Commands use a sequence-number/accepted/rejected handshake. Operator commands require Operator role; manual actuator/drive commands require Maintenance and MANUAL_SETUP; recipe/security changes require Engineer or Administrator. Every disabled control displays the blocking state, permissive or interlock. No HMI command writes a physical output tag directly.
