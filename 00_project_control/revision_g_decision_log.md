# Revision G decision log

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| Decision | Disposition | Engineering rationale |
|---|---|---|
| DG-001 | Use two isolated cloud environments | Siemens does not need a GPU; NVIDIA training/runtime has different OS, driver and cost controls. |
| DG-002 | Keep all VM creation flags false by default | Repository validation must not create billable infrastructure. |
| DG-003 | Prefer a dedicated supported Windows workstation/Siemens-supported hypervisor for G1; retain ordinary GCE only as an explicitly unsupported-lab candidate pending written Siemens confirmation | Siemens V20 documentation names VMware vSphere/Workstation/Player and Hyper-V, not Google Compute Engine. |
| DG-004 | Use Ubuntu 24.04 and DeepStream 9.1 planning baseline for NVIDIA dGPU/Jetson work | Current NVIDIA DeepStream 9.1 documentation specifies Ubuntu 24.04, CUDA 13.2 and TensorRT 10.16 for dGPU, with JetPack 7.2 for Jetson. |
| DG-005 | Never let a synthetic backend assert service READY | Synthetic evidence can test plumbing but cannot support production disposition. |
| DG-006 | Do not re-author QET/CAD in G without a hardware/tag/envelope change | Revision-E native CAD remains valid; the known Revision-F electrical delta remains an explicit construction-readiness blocker rather than being hidden. |
| DG-007 | Requalify artifact-tool 2.8.39 instead of weakening the old lock | The private 2.8.31 package is unavailable; a lock change requires two full deterministic builds and complete visual review. |
