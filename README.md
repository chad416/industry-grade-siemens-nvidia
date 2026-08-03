# FC01 Siemens/NVIDIA compact filling cell — Revision D.1

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Revision D.1 is a release-integrity and native-readiness hardening candidate. It preserves Revision D's fail-closed PLC/vision and electrical design while making Git objects authoritative, force-readding the verified native QET/DXF bytes, rejecting superseded artifacts, retaining PLC transaction identity, requiring post-fault product disposition and preserving immutable edge results until exact acknowledgement.

Run `powershell -ExecutionPolicy Bypass -File scripts/reproduce_validation.ps1` only from a clean clone outside a synchronization folder. Native TIA/WinCC/Startdrive/PLCSIM, Revision-D.1 QET/FreeCAD, confirmed site-dependent electrical calculations, real dataset/model/target runtime, FAT/SAT and qualified safety gates remain open exactly as recorded.

Maturity: **Professional controlled engineering-development package; construction and deployment release pending the explicitly listed native, physical and qualified acceptance gates.**
