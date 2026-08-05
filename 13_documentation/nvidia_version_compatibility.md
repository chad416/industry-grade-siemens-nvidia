# NVIDIA version and compatibility baseline - Revision F

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION


Verified against official NVIDIA documentation on 2026-08-03:

| Domain | Current official information | Revision-F use |
|---|---|---|
| DeepStream | DeepStream SDK 9.1 supports Jetson Orin and Jetson Thor and Ubuntu 24.04. NVIDIA documents Jetson installation with JetPack 7.2 GA. | Retain DeepStream 9.1 as the provisional target family. Do not pin a deployable image until carrier, Jetson module and site lifecycle are selected. |
| Jetson DeepStream inference | DeepStream 9.1 migration documentation identifies TensorRT 10.16.1.7 on Jetson; x86 uses TensorRT 10.16.0.72. | Use the platform-specific DeepStream matrix for target compatibility. Do not substitute the latest generic TensorRT release. |
| TAO | TAO 7.0.1 is the current agent/skill-bank line and is built on the NGC 26.03 stack with CUDA 13.2. | Evaluate TAO 7.0.1 only in an approved Linux/container environment. No compatible local TAO skill bank or runtime was found. |
| Generic TensorRT | TensorRT 11.1 is current generic documentation, with breaking 10.x-to-11.x migration requirements. | Track for x86 development only. It is not evidence that a DeepStream 9.1 Jetson deployment may use TensorRT 11.1. |

Official sources:

- https://docs.nvidia.com/metropolis/deepstream/9.1/text/DS_Release_notes.html
- https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Installation.html
- https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Migration_guide.html
- https://docs.nvidia.com/tao/tao-toolkit/latest/text/release_notes.html
- https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/release-notes-11/11.1.0.html

## Inspected local environment

- NVIDIA GeForce RTX 5060 Laptop GPU, driver 595.95, 8,151 MiB, compute capability 12.0.
- `nvidia-smi` is available. `nvcc`, `trtexec`, `deepstream-app`, `tao`, Docker, OpenUSD and Omniverse tools are absent.
- WSL is present but distribution enumeration is denied under the active execution identity; no Linux execution claim is made.
- No NVIDIA TAO or DeepStream skill package is installed in the available Codex skills.

Therefore no CUDA build, TAO training, ONNX export, TensorRT engine, DeepStream pipeline, GPU latency or model metric is claimed. The laptop GPU/driver is useful only for future approved environment preparation; it does not close target-runtime or representative-data gates.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
