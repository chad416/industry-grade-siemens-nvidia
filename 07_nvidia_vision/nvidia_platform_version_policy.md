# NVIDIA platform version policy — verified 2026-08-03

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Official-source review confirms DeepStream 9.1 as the current documented NVIDIA SDK line for supported x86/dGPU and Jetson Orin/Thor platforms. Its Jetson package is based on JetPack 7.2 GA, DeepStream Python `pyds` bindings are deprecated, and NVIDIA recommends Service Maker Python APIs. Source: <https://docs.nvidia.com/metropolis/deepstream/9.1/text/DS_Release_notes.html>.

Official TAO release notes identify 7.0.1 as the current maintenance release on the agent-based 7.0 line. The user-facing workflow is the TAO skill bank plus Execution SDK; the legacy launcher/FTMS/TAO Deploy CLI surfaces are removed. Sources: <https://docs.nvidia.com/tao/tao-toolkit/latest/text/release_notes.html> and <https://docs.nvidia.com/tao/tao-toolkit/latest/text/migration_guides/migrating_to_tao_7.0.html>.

Official TensorRT documentation lists 11.1.0 as the latest general documentation release, but serialized engines remain platform-specific and compatibility depends on selected CUDA, OS, GPU architecture and JetPack. Revision F therefore does **not** pin TensorRT 11.1.0 for the undecided Jetson/industrial-x86 target. Select and freeze the TensorRT version only from the chosen platform's support matrix and DeepStream/JetPack compatibility, then build the engine on that target-compatible stack. Sources: <https://docs.nvidia.com/deeplearning/tensorrt/latest/> and <https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/support-matrix.html>.

These are compatibility design references, not installed-tool evidence. The inspected engineering environment still lacks a controlled CUDA Toolkit, TensorRT, DeepStream, TAO, Docker/NVIDIA Container Toolkit and target Jetson image. No container build, model training/export, TensorRT engine, GPU timing or DeepStream execution is claimed.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
