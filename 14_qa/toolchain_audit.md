# Toolchain and access audit

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Siemens

- Authoritative target: **TIA Portal V20**, executable/product version `2000.0.9501.1`.
- Installed component evidence: STEP 7 V20 `20.00.0000`, WinCC V20 `20.00.0000`, TIA Openness V20 assemblies `2000.0.9501.1`.
- Secondary installed environment: TIA Portal V16 `1600.0.3102.1`.
- Automation License Manager V6.2 SP1 service is running and a licence store exists, but usable STEP 7/WinCC entitlements were not observable; no licence claim is made.
- The local `Siemens TIA Openness` group has no listed members and the current automation identity is not authorized. Automated native project creation/compile is blocked.
- Startdrive and PLCSIM/PLCSIM Advanced are absent. Adapter DLLs are not treated as simulator installation.

## Electrical/CAD

- A portable QElectroTech executable is available in the primary source package and reports `0.100.1-dev`; the inherited native baseline has retained prior reopen/export evidence. The revision-B schematic was not rebuilt.
- FreeCAD is not installed; only the verified FreeCAD 1.1.3 archive and prior native evidence exist. Revision-B CAD and fresh reimport gates are blocked.

## NVIDIA

- Hardware: NVIDIA GeForce RTX 5060 Laptop GPU, driver `595.95`, 8151 MiB VRAM, compute capability `12.0`.
- Driver-reported CUDA compatibility is not a CUDA Toolkit installation. CUDA Toolkit/`nvcc`, Docker, TAO, DeepStream, TensorRT, Omniverse and OpenUSD utilities are absent.
- No real labeled dataset is available. No training, export, benchmark, metric, engine or USD claim is made.

## Supported non-native validation

Bundled Python 3.12.13, Node 24.14, `@oai/artifact-tool` 2.8.31, ReportLab 4.4.9, Poppler 26.05.0 and spreadsheet/PDF parsers support canonical checks, deterministic simulation, workbook generation, PDF rendering and visual inspection.
