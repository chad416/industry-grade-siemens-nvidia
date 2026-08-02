# Siemens PLC software architecture

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

`Main` calls the single `DB_CellMain` root instance. The root owns command arbitration, two PROFINET drive blocks, gate, clamp, two fill-channel blocks, vision, capper, recipe, alarm, drip timer and coordinator. Input normalization occurs before equipment calls; the physical-output mapper is last and applies a release permissive.

Physical drives use Standard Telegram 1 at IW/QW 256-263. The explicit `DB_NativeBindings` adapter contract receives PROFINET I/O-valid diagnostics and TM Count technology-object totals/channel faults from native TIA networks; `FB_CellMain` consumes every field. Those native networks are not fabricated and remain gate 6 work. Analog channels are scaled from the Siemens 4-20 mA raw range and include channel-fault/range supervision. `OB100` decommands outputs and sets recovery required.

These are reviewable/import-oriented sources, not a compiled native program. TIA V20 import, hardware configuration, cross-reference review and zero-error compile remain mandatory.
