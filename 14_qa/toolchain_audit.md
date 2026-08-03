# Toolchain audit - Revision D.1

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

TIA Portal V20 executable version 2000.0.9501.1 was observed with SHA-256 `4AB4C76CFA956956187B4E1401DD11EED3473FE60CA121C13698F6918DA4354F`. The Siemens Engineering and HMI Openness assemblies are also 2000.0.9501.1, with SHA-256 `4593BDDCBBE92472B2FAC25955051066C39C9935A5E696359C6C5F2BD214FCD1` and `93FACFD3EE14536EC1640CEC5501BB2102444579901E713930E662950F4AC7C9`. STEP 7/WinCC components and the running Automation License Manager 6.2 SP1 service were observed, but the `Siemens TIA Openness` local group is empty and the current execution identity is not authorized. A usable STEP 7/WinCC entitlement and native Revision-D.1 compile remain unproven. Startdrive and PLCSIM/PLCSIM Advanced were not found.

No runnable QElectroTech, FreeCAD or FreeCADCmd executable was found by command, registry, App Paths/AppX/file-association inventory or standard-path inspection. Historical Revision-A QET/FCStd/exchange evidence is retained byte-exact; no Revision-D.1 native reopen/export/reimport is claimed.

An NVIDIA GeForce RTX 5060 Laptop GPU, driver 595.95, 8,151 MiB and compute capability 12.0 were observed. `nvidia-smi` reports CUDA compatibility 13.2, which is not CUDA Toolkit evidence. `nvcc`, CUDA Toolkit, Docker, NVIDIA Container Toolkit, TAO, DeepStream, TensorRT tools and OpenUSD/Omniverse tools were not found. Python `asyncua` 2.0 exists, but no live OPC UA endpoint/certificate integration was available. WSL enumeration was access-denied and is therefore unverified. No dataset, trained model or target Jetson evidence exists.
