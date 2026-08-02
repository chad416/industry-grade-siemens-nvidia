# Legacy-to-final tag migration

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| Legacy source | Example | Final rule | Disposition |
|---|---|---|---|
| Primary IEC/ISO designation | `=FC01+OP01-B110` | Retained | Authoritative device tag |
| Secondary semantic tag | `PE_BOTTLE_1` | `BOTTLE_AT_NEST_1` | PLC symbol only; mapped to `-B110` |
| Secondary generic VFD | `VFD_CONVEYOR` | `=FC01+FD01-U100` | Device designation plus `CONVEYOR_*` PLC symbols |
| Secondary AI status | informal JSON fields | Exact ICD names | Replaced by controlled OPC UA data contract |

No legacy PLC address is inherited automatically. Revision-B addresses come only from `canonical_model.json`.
