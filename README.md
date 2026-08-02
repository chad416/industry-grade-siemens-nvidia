# FC01 Siemens/NVIDIA compact filling cell — Revision C

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Revision C corrects the generator-origin SCL patch artifacts, replaces comment-only OB1 with a root instance call and startup OB, implements detailed fill diagnostics, separates HMI command handshakes from physical outputs, reconciles G120C control to PROFINET Standard Telegram 1, replaces the misidentified unmanaged switch with a managed switch/firewall architecture, expands BOM/point-to-point/panel/control documents, and replaces lookup-table simulation with a dynamic fault-injection model.

Run `python scripts/build_project.py`, the workbook/PDF builders, simulation tests, `python scripts/validate_project.py`, `python scripts/build_manifest.py`, then `python scripts/verify_manifest.py`. Native TIA/WinCC/Startdrive/PLCSIM, revision-C QET/FreeCAD, physical electrical calculations, real dataset/model/runtime, FAT/SAT and qualified safety gates remain open exactly as recorded.
