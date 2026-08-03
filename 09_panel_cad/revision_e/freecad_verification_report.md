# FC01 Revision-E native FreeCAD verification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Result: **PASS** — 80 passed checks, 0 failed checks.

## Native reopen

- FreeCAD: `1.1.3`, revision `20260725 (Git shallow)`.
- FCStd document objects: 165.
- Controlled physical objects / solids: 148 / 148.
- Invalid controlled shapes: 0.
- Physical assembly bounding box: `{"xlen": 800.0, "xmax": 800.0, "xmin": 0.0, "ylen": 800.0, "ymax": 800.0, "ymin": 0.0, "zlen": 327.0, "zmax": 327.0, "zmin": 0.0}` mm.
- Scheduled/native/DXF mounting holes: 30 / 30 / 30.

## Exchange reimport

- STEP: 150 shape objects, 148 solids, 0 invalid; matching bounding box.
- IGES: native Part.read produced 1 valid face compound with 923 faces and matching bounding box; solid retention is not claimed.
- DXF: 4 LINE and 30 CIRCLE entities; structural entity envelope is 750 × 750 mm; native Part-solid retention is not claimed.

## Native-view provenance

- Genuine FreeCAD GUI renders from the same physical geometry-definition source before a rejected post-save generic ZIP-repack attempt. A controlled correction later changed only SW100/FW100/PC200 side-clearance metadata and dimension-basis text; x/y/z/width/height/depth geometry and mounting holes are unchanged. The final headless rebuild matches the invariant physical-geometry fingerprint and exact controlled PNG hashes. No final FCStd byte identity or second GUI reopen is claimed.
- Physical-geometry fingerprint: `4a9d3fac2f04c302ead3ed6e386bbd318c64514c03eb718e2df87196c392fd3b`.
- Hole schedule SHA-256: `931b1e6fc09841f6fb924c483200eeaee1a16dd99f7a8c5a4abdd3da76e4fa3f`.
- No FCStd byte identity or second GUI reopen is claimed; final native geometry is proven by independent FreeCADCmd reopen/reimport.

## Controlled limitations

- No manufacturer/supplier approval, fabrication authorization or construction release
- Enclosure, protection, PSU, relays, terminals, ducts, PE system, Jetson carrier and cooling remain selection-dependent
- Drive drilling orientation requires confirmation against order-number CAx before manufacture
- No site thermal, cable-route, short-circuit, EMC, qualified safety or physical commissioning evidence

## Failed checks

- None.
