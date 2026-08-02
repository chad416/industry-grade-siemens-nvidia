# Legacy source audit and disposition

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Primary electrical/CAD source

The primary package is the stronger engineering baseline and contains genuine QElectroTech and FreeCAD native files. Retained evidence identifies QElectroTech 0.100.1-dev with 24 sheets, 305 elements and 160 conductors, plus FreeCAD 1.1.3 with 130 objects/73 physical solids and matching 800 × 800 × 300 mm FCStd/STEP bounds. The inherited hashes are locked by `scripts/validate_project.py`.

It is not accepted as the revision-C electrical deliverable: its QET BOM has 305 rows but none populate label, designation, manufacturer, reference, quantity, location or function; the cross-reference export is empty; 160 conductors repeat only 16 wire numbers; cable/function/section properties are absent; and 911 terminals are reported free. The panel uses generic envelopes and omits the selected Siemens/NVIDIA devices.

Disposition: quarantine genuine Rev-A native files, retain the IEC 81346-style designation convention and functional two-channel baseline, rebuild native QET/CAD only in the qualified workstream, and keep OI-003/OI-004 blocking.

## Secondary controls/simulation source

The secondary package contributes useful canonical-data, generation, manifest, test-table, simulator-harness and HMI visual patterns. It is not reusable as Siemens control logic: the SCL is declared illustrative, centers on one CASE statement with undeclared helpers, and lacks deployable OB/FB/DB organization. The simulator controls one bottle and one fill measurement even though it shows two valves, and has no capper or NVIDIA subsystem. All native Siemens/PLCSIM evidence is absent.

The legacy address map is retired because it mixes physical addresses with pseudo-network strings and conflicts with the primary map. Its HMI contains member/type mismatches and is mock-up-only. Existing narrow tests pass but do not establish the required two-bottle process.

Disposition: reuse patterns, not implementation; rebuild canonical data, Siemens sources, two-channel simulator, HMI contract, capper and vision interfaces.

## Integration decision

Revision C uses Siemens as the only executable automation target, retains the primary device-designation scheme, uses uppercase semantic PLC symbols, removes any automatic reject behavior, and holds uncertain product for operator disposition. No legacy native source is modified.
