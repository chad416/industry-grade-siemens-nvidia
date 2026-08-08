# Revision G secure execution architecture

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Two laboratory environments are separated from each other and from any plant/OT network.

## Environment A - Siemens engineering

A Windows engineering host provides TIA Portal V20, STEP 7 Professional, WinCC Unified, Startdrive, PLCSIM/PLCSIM Advanced and TIA Openness. The primary recommendation is a dedicated always-on engineering workstation or a Siemens-supported VMware/Hyper-V environment. Ordinary Google Compute Engine is retained only as a technically plausible **unsupported laboratory candidate** pending written Siemens confirmation; Siemens V20 installation documentation explicitly names VMware vSphere 8+, Workstation/Player 17+ and Hyper-V Server 2019+, not GCE.

## Environment B - NVIDIA engineering

A separate Ubuntu 24.04 GPU host is provisioned only after approval. DeepStream 9.1 currently requires Ubuntu 24.04, driver 595.58.03, CUDA 13.2 and TensorRT 10.16.0.72 on dGPU. A G2/L4-class VM is a capacity and price candidate, not a selected or provisioned target. Jetson deployment must use the exact DeepStream/JetPack platform matrix and regenerate TensorRT engines for the intended runtime/hardware.

## Network and evidence flow

- Dedicated VPC/subnet; no VM external IP.
- IAP TCP forwarding is the only administrative ingress; firewall source is `35.235.240.0/20` to RDP/SSH tags.
- Cloud NAT provides bounded installation egress; egress firewall permits DNS, NTP and TLS only.
- Separate keyless service accounts; no project-owner grants.
- Versioned, uniform-access, public-access-prevented evidence bucket; no secrets in objects or Terraform state.
- Project audit logging plus optional CPU alert policies; notification-channel IDs remain operator-supplied variables.
- OPC UA and PLC traffic are laboratory-only. No direct conduit to a real plant is created.

Official sources:

- https://support.industry.siemens.com/cs/attachments/109963850/Install_STEP7_WinCC_V20_enUS.pdf
- https://cloud.google.com/iap/docs/tcp-forwarding-overview
- https://cloud.google.com/compute/docs/instances/schedule-instance-start-stop
- https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Installation.html
