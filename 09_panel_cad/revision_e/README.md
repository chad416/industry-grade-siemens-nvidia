# FC01 Revision-E native panel CAD

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

This directory is the genuine Revision-E FreeCAD package built and reopened with the controlled portable FreeCAD 1.1.3 command-line executable. It does not replace the quarantined Revision-A baseline in `../native_baseline`.

## Native boundary

- `FC01_control_panel_revision_e.FCStd` is the authoritative native model.
- STEP and IGES are full-panel physical-shape exports; non-physical clearance/segregation volumes are excluded. Independent native verification confirms STEP solid retention and a valid IGES face-compound/envelope; IGES solid retention is not claimed.
- `FC01_mounting_plate_revision_e.dxf` is a FreeCAD-exported local-coordinate mounting-plate outline and hole pattern.
- The placement and hole schedules distinguish selected manufacturer envelopes from provisional and architecture-only assumptions.
- The four PNGs are genuine FreeCAD GUI views rendered from the same physical geometry-definition source before a rejected post-save generic ZIP-repack attempt. A later controlled correction changed only the SW100/FW100/PC200 side-clearance metadata and its dimension-basis text; x/y/z/width/height/depth geometry and mounting holes did not change. The headless build requires the exact controlled PNG hashes and an invariant physical-geometry fingerprint. No final FCStd byte identity or second GUI reopen is claimed.
- General-arrangement and mounting-plate PDFs use those genuine views plus the final controlled geometry/schedules.

## Reproduction

Run the headless generator with isolated FreeCAD configuration files, then run the independent command-line verification in a second process:

```powershell
& $env:FC01_FREECAD_CMD -u $env:FC01_FREECAD_USER_CFG -s $env:FC01_FREECAD_SYSTEM_CFG scripts/freecad_revision_e.py
& $env:FC01_FREECAD_CMD -u $env:FC01_FREECAD_VERIFY_USER_CFG -s $env:FC01_FREECAD_VERIFY_SYSTEM_CFG scripts/verify_freecad_revision_e.py
```

The model is not a supplier-approved production model. The enclosure, protection, PSU, relay, terminal, duct, PE, Jetson carrier and cooling solution remain selection-dependent. Drive mounting coordinates require final confirmation against order-number CAx before drilling. Site supply, fault current, thermal environment, cable routes, maintenance access and qualified safety work remain external gates.
