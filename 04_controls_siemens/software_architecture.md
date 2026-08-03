# Siemens software architecture - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

`FB_CellMain` remains the sole cell-level cyclic composition. The PLC owns all sequence, permissives, interlocks, timers, physical commands, result acceptance and transfer authorization. `FB_VisionInterface` now exposes `RequestInProgress`, latches the active request identity and holds `Trigger` until coherent edge observation/result so a polling OPC UA client cannot miss the request. Duplicate request pulses cannot advance the active ID.

All 15 SCL exports are generator-controlled and import together in the documented order. The added source contracts verify generator parity, held-trigger semantics, immutable session/ID, duplicate suppression, result-before-BUSY handling and fail-closed reset/fault behavior. These checks are source-design evidence only. TIA Portal V20 compile, native retentivity review and PLCSIM remain blocked by authorization/licensing/tool availability.
