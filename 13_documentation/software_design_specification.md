# Software design specification - Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Ownership and scan order

The S7-1500 PLC owns machine sequence, permissives, interlocks, timeouts, actuator commands and disposition authorization. The non-safety NVIDIA service transports quality evidence only. `FB_CellMain` retains the established deterministic scan order and safe final output mapping.

## PLC-edge transaction

The controlled interface contains 47 typed OPC UA nodes. Session epoch, monotonic inspection ID, capture acknowledgement, terminal processing state, immutable payload, exact result acknowledgement and result-clear are separate invariants. The edge publishes BUSY false and state 4 before setting RESULT_VALID. The PLC derives result age from its monotonic timer and never trusts edge wall-clock time for release.

## Verification boundary

Source/static, deterministic simulator and certificate-backed local asyncua evidence is controlled. Native TIA/WinCC compilation, production endpoint behavior, target-runtime timing, hardware and physical commissioning remain blocked. The `E_VisionDiag` to UA UInt16 exposure requires confirmation during native TIA/OPC UA configuration.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
