# FC01 Siemens/NVIDIA compact filling cell - Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Revision F advances the verified Revision-E native-engineering baseline into NVIDIA implementation readiness. It adds a 47-node typed PLC-AI contract, production-structured acquisition/configuration/model-adapter foundations, dataset and evaluation tooling, durable audit behavior, 28 named structured behavioral fault injections, expanded Siemens/HMI import artifacts, a controlled electrical delta, current NVIDIA version policy and refreshed release evidence.

The PLC remains authoritative for sequence, interlocks, outputs, disposition and transfer. THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.

Run `powershell -ExecutionPolicy Bypass -File scripts/reproduce_validation.ps1` only from a clean clone outside synchronization folders. No native Siemens compile, representative dataset, trained model, CUDA/TAO/TensorRT/DeepStream execution, GPU latency, physical optics, electrical measurement, FAT/SAT, safety validation or construction readiness is claimed.
