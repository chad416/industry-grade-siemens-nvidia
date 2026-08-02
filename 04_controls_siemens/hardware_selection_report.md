# Siemens hardware selection report

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Decision matrix

| Criterion | S7-1200 / local modules | S7-1500 / local modules | S7-1500 + ET 200SP | Selected rationale |
|---|---|---|---|---|
| Required I/O | Feasible with expansion | 32 DI, 32 DQ, 8 AI readily allocated | Feasible | S7-1500 local fits one compact panel |
| Two high-speed pulse channels | CPU/model-specific counters | Dedicated TM Count 2x24V | ET 200SP counter module possible | Dedicated S7-1500 TM isolates dose counting from ordinary DI |
| Analog quality | Module dependent | AI 8xU/I HF, individually grouped, diagnostics | Strong | Local HF module supports two isolated-style loop groups and six spares |
| Communications | PROFINET; OPC UA model dependent | PROFINET IRT and engineering margin | Strong | CPU 1511-1 PN supports selected modular architecture; native configuration still required |
| Diagnostics | Moderate | Strong channel/device diagnostics | Strong | S7-1500 supports maintainability and first-out investigation |
| Expansion | Moderate | Strong within rack/panel | Strongest geographically | Local rack has adequate spare channels; distributed I/O adds unnecessary network dependency now |
| Environment | Requires enclosure review | Requires enclosure review | Field enclosure options | All require confirmed ambient, EMC, vibration and enclosure data |
| Software compatibility | Exact CPU catalog dependent | Exact CPU catalog dependent | More catalog/GSD dependencies | TIA Portal V20 is target; device catalog compatibility is an open native gate |
| Lifecycle | Verify each MLFB | Selected CPU/modules shown active on official Siemens product pages | Verify each MLFB | Current order numbers selected where official status could be checked |
| Panel space / power | Lower | Moderate | More couplers/terminals | Existing 800 × 800 concept must be revised but local rack remains compact |
| Cost / complexity | Lowest | Moderate | Highest for this scale | Diagnostics and dedicated count functions justify S7-1500 cost |

## Selected bill of architecture

- CPU 1511-1 PN, `6ES7511-1AL03-0AB0`.
- TM Count 2x24V, `6ES7550-1AA01-0AB0`.
- DI 32x24V DC HF, `6ES7521-1BL00-0AB0`.
- DQ 32x24V DC/0.5A HF, `6ES7522-1BL01-0AB0`.
- AI 8xU/I HF, `6ES7531-7NF00-0AB0`.
- MTP700 Unified Comfort, `6AV2128-3GB06-0AX1`.
- Two G120C PN 0.75 kW, `6SL3210-1KE12-3UF2`, provisional pending motor/pump data.

Manufacturer references and front connectors, memory card, system power, load groups, shield terminals, switch, PSU and protective devices must be completed in the native V20 hardware configuration. Order numbers are not purchasing authorization.

Official verification sources are recorded in the decision log and include the Siemens Industry Mall pages for the [CPU](https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6ES7511-1AL03-0AB0), [counter module](https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6ES7550-1AA01-0AB0), [analog input](https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6ES7531-7NF00-0AB0), [HMI](https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6AV2128-3GB06-0AX1) and [drive](https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6SL3210-1KE12-3UF2).
