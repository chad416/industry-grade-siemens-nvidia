# CPU 1511-1 PN / TIA Portal V20 compatibility decision

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Controlled baseline

The target remains TIA Portal V20. The selected CPU is `6ES7511-1AL03-0AB0`, explicitly baselined as hardware functional status FS03 with firmware V4.0 for native V20 engineering. Siemens' November 2024 product manual states that FW V4.0 is configurable/integrated from TIA Portal V20 and FW V3.0 from V18; it also documents predecessor-mode configuration as `6ES7511-1AK02-0AB0` for older TIA versions.

Current Siemens technical data dated 2026 identifies FS04 / FW V4.1 and lists V21 for native FW V4.1 engineering, while continuing to describe earlier-version handling. Therefore procurement must not assume every newly delivered `1AL03` unit matches the FS03/FW4.0 baseline.

## Decision path

| Delivered state | Engineering action | Gate |
|---|---|---|
| FS03 / FW4.0 | Select exact device in TIA V20; compile hardware/software | Preferred baseline; native proof required |
| Compatible unit operated at supported FW3.x | Select exact supported catalog version in V20 | Vendor-approved firmware/change record required |
| FS04 / FW4.1 | Upgrade the controlled engineering target to V21, or use Siemens-documented predecessor mode only after feature/diagnostic review | Formal change and native compile required |
| Unknown | Quarantine from release selection | Obtain nameplate, HW/FW display and supplier confirmation |

No native TIA project or hardware compile has been performed, so acceptance gate 3 remains partial and gates 4–6 remain blocked.

Official sources accessed 2026-08-02:

- Siemens CPU 1511-1 PN product manual, November 2024: https://support.industry.siemens.com/cs/attachments/109977233/s71500_cpu1511_1_pn_dtc_manual_en-US_en-US.pdf
- Siemens current technical data: https://support.industry.siemens.com/teddatasheet/?caller=SIOS&format=pdf&language=en&mlfbs=6ES7511-1AL03-0AB0
