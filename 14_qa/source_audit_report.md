# Source audit report - Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Revision-F source review covers the inherited restart/replay/disposition invariants plus the additive 47-node contract, exact capture acknowledgement, processing state, health, model/dataset/calibration identity, immutable result publication, PLC-derived result age, confidence/reason/disposition checks and fail-closed restart/reconnect behavior.

The edge foundation executes its bounded configuration schema, records the runtime/contract/schema SHA-256 values in structured logs, requires an append/flush/fsync inspection-audit write before result publication, publishes terminal state before RESULT_VALID, rejects active recipe/context change and excessive clock discontinuity, and keeps the unimplemented ONNX/recorded-input path permanently unauthorized. Dataset split/hash/leakage checks, evaluation math, local health/metrics and certificate-backed asyncua tests are controlled. Synthetic fixtures prove plumbing only.

Native TIA/WinCC/Startdrive/PLCSIM, production PLC/Jetson/PKI, representative data, trained model, target CUDA/TensorRT/DeepStream/TAO runtime, physical optics, site electrical inputs and qualified safety review remain external.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
