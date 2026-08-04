# Source audit report - Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Revision-F source review covers the inherited restart/replay/disposition invariants plus the additive 47-node contract, exact capture acknowledgement, processing state, health, model/dataset/calibration identity, immutable result publication, PLC-derived result age, confidence/reason/disposition checks and fail-closed restart/reconnect behavior.

The edge foundation executes its bounded configuration schema, records the runtime/contract/schema SHA-256 values in structured logs, requires an append/flush/fsync inspection-audit write before result publication, publishes terminal state before RESULT_VALID, rejects active recipe/context change and excessive clock discontinuity, and keeps the unimplemented ONNX/recorded-input path permanently unauthorized. Dataset split/hash/leakage checks, evaluation math, local health/metrics and certificate-backed asyncua tests are controlled. Synthetic fixtures prove plumbing only.

Native TIA/WinCC/Startdrive/PLCSIM, production PLC/Jetson/PKI, representative data, trained model, target CUDA/TensorRT/DeepStream/TAO runtime, physical optics, site electrical inputs and qualified safety review remain external.

The first GitHub clean-clone reproduction of candidate a036620c5332997647625b510675345a33a16261 exposed an intermittent secure-session disconnect: asyncua transport supervision was incorrectly tied to the 10 ms PLC poll cadence and used a 50 ms server-state probe timeout. Revision F now gives the transport watchdog at least the configured OPC UA operation budget and a one-second floor. The added regression check plus eight repeated two-test secure runs and the complete 86-test edge suite passed after correction.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
