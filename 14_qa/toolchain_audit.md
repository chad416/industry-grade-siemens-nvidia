# Toolchain audit - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Siemens

TIA Portal V20 executable version `2000.0.9501.1` was observed at `C:\Program Files\Siemens\Automation\Portal V20\Bin\Siemens.Automation.Portal.exe`, SHA-256 `4AB4C76CFA956956187B4E1401DD11EED3473FE60CA121C13698F6918DA4354F`. Engineering/Openness and HMI assemblies have SHA-256 `4593BDDCBBE92472B2FAC25955051066C39C9935A5E696359C6C5F2BD214FCD1` and `93FACFD3EE14536EC1640CEC5501BB2102444579901E713930E662950F4AC7C9`. STEP 7/WinCC components and Automation License Manager 6.2 SP1 are present. The active sandbox identity is not in TIA Engineer or TIA Openness groups, a V20 entitlement is unproven, Startdrive is absent and PLCSIM/PLCSIM Advanced are absent. No project/archive was fabricated and no compile result is claimed.

## FreeCAD

Portable FreeCAD `1.1.3`, revision `20260725 (Git shallow)`, is runnable through FreeCADCmd. The `FreeCADCmd.exe` SHA-256 is `B5551D26050ED64981C5767729BB35900FD4975FA7FD31714C17DD714B6FD44C` and is authoritative for the final reopen/reimport. The retained pre-clearance-metadata-correction GUI views were rendered by `FreeCAD.exe` of the same version, SHA-256 `D831ED7EEE385D5A370A83B078DD90B1F7621BB65BB7C427F06C736C8652D5F0`; their limited semantic-geometry provenance is recorded without claiming a second final GUI reopen. Exact native result and exchange-format behavior are recorded in `09_panel_cad/revision_e/native_verification.json`; the controlled output directory contains no backup/lock/autosave artifact.

## QElectroTech

The official Windows ready-to-use QElectroTech `0.100.0+git8590` package was used. Executable SHA-256: `FCC3465825CC6F1BF3997D9C8054858E647A2038C8C01B7A3335A914106DE926`; downloaded archive SHA-256: `552402198011F37633FFCFF4F9CE561A9ABAF22DC14F9CC09DDC231245B16445`. A superseded candidate reopened, but layout defects were found and corrected. The final corrected QET hash was not natively reopened/exported; no final native-QET pass is claimed.

## NVIDIA/runtime

An RTX 5060 Laptop GPU, driver `595.95`, 8,151 MiB and compute capability 12.0 were observed. `nvidia-smi` reports CUDA compatibility 13.2, not a CUDA Toolkit installation. CUDA Toolkit (`nvcc`), TensorRT, DeepStream, TAO, Docker, NVIDIA Container Toolkit, OpenUSD and Omniverse tools were not found. A temporary Python 3.12.13 environment with `asyncua 2.0.1`, `cryptography 50.0.0` and `pyOpenSSL 26.4.0` executed encrypted local integration tests; it is not a production target runtime.
