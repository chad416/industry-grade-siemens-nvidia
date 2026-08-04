# PLC-NVIDIA interface control document - Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Ownership and transaction

The PLC freezes session epoch, inspection ID, recipe, bottle count, fill target and expected model/dataset/calibration identities before raising the level-held request. The edge validates the complete snapshot, publishes capture acknowledgement and processing state, then writes one complete immutable result before `RESULT_VALID`. The PLC accepts only the exact current session/ID, coherent capture acknowledgement, healthy service/camera/model, approved identities, allowed disposition/reasons/confidence and PLC-derived age. Exact acknowledgement clears the result but never authorizes transfer.

The 47 typed nodes, OPC UA types, owner, update rule and invalid action are controlled in `10_schedules/nvidia_interface_tags.csv`. OPC UA typed scalars abstract byte order; no application byte swapping is permitted. Disconnect, restart, recipe change, clock jump, stale/duplicate/future ID, malformed/contradictory payload, low confidence, fault, queue saturation or maintenance state fails closed.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.

Local encrypted asyncua tests are not production S7/Jetson/PKI evidence. Native TIA/WinCC compilation and target endpoint commissioning remain blocked.
