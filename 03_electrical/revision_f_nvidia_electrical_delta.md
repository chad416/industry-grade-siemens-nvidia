# Revision-F NVIDIA electrical integration delta

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

> THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.

## Purpose and authority

This controlled delta defines the Revision-F electrical work required around the existing Revision-E QElectroTech source. It does not alter or claim completion of the native QET project. The current aggregate 100 W vision allowance is partitioned into independently protected conceptual branches so a licensed electrical engineer can select actual devices and update QET without inferring missing site or vendor data.

Status: **PARTIAL - STANDALONE DELTA ONLY.** These records have not been incorporated into the canonical model, aggregate BOM, terminal plan, cable schedule, point-to-point schedule, panel CAD or a Revision-F native QET source/export. Until those cross-artifact changes are implemented and independently reconciled, this delta is an approved engineering input only and is not evidence of an installed or construction-ready electrical design.

## Provisional branch concept

| Branch | Reference | Load allowance | Conceptual protection/isolation | Required confirmation |
|---|---|---:|---|---|
| Edge computer | -F220 / -PC200 | 60 W, 2.50 A at 24 VDC | Dedicated electronic protection or fuse; lockable upstream maintenance isolation remains site decision | Carrier input range, steady/inrush current, conductor and protection data |
| Camera | -F221 / `=FC01+FLD-CAM200` | 12 W, 0.50 A at 24 VDC | Dedicated protected branch; do not assume PoE until camera is selected | Camera voltage, PoE class if used, connector and environmental rating |
| Lighting | -F222 / `=FC01+FLD-LT200` | 20 W, 0.83 A at 24 VDC | Dedicated protected branch switched through the existing -K213 command path | Light/strobe current, pulse duty, inrush and controller topology |
| Vision service/network auxiliaries | -F223 / -XS200 | 8 W, 0.33 A at 24 VDC | Dedicated service branch, disabled or isolated outside approved maintenance windows | Service outlet/interface type and site policy |
| Total controlled allowance | - | 100 W, 4.17 A at 24 VDC | Retains the Revision-E aggregate; no PSU up-rating is implied | Verify all selected loads, diversity, inrush, derating and voltage drop |

The 100 W total is a budget allocation, not a measurement or selected-device rating. The existing 20 A supply concept remains provisional. Final protection, conductor sizes, discrimination, SCCR, voltage drop and thermal compliance require the missing site and vendor inputs recorded in the input-request register.

## Terminal and cable delta

- Reserve `=FC01+CP01-X200:1..8` for edge, camera, lighting, service and PE/FE terminations. Final terminal family, bridges, disconnect/test features and grouping are open.
- Add `C200` edge DC power, `C201` camera DC power, `C202` edge Ethernet, `C203` lighting power/control, `C204` service power, `C205` camera Ethernet and `C206` maintenance Ethernet. Each physical path has a unique identifier; cable construction, core size, route, length, bend radius and glands remain provisional.
- Terminate camera/edge cable screens at the controlled cabinet FE/shield system in accordance with the selected manufacturer and site EMC plan. Do not create uncontrolled multipoint bonds.
- Maintain physical separation between mains/VFD motor conductors, 24 VDC control, analog/pulse instrumentation and Ethernet/camera cabling. Cross power conductors at approximately 90 degrees where separation cannot be maintained.

## Network-port reservation

The managed `-SW100` switch reserves P5/C202 for `-PC200`, P6/C205 for `=FC01+FLD-CAM200`, P7/C206 as the disabled-by-default maintenance path and P8 as an uncabled spare. The camera-to-edge topology may be direct or switched only after bandwidth, PTP/NTP, PoE, cyberzoning and diagnostics requirements are confirmed. No unmanaged service switch is authorized by this delta.

## Delta-item rationale

| Item | Engineering rationale |
|---|---|
| NED-001 | Isolate the highest vision load so an edge-computer fault does not remove PLC control power. |
| NED-002 | Reserve field-camera power independently while voltage and PoE selection remain open. |
| NED-003 | Separate the pulsed lighting load and preserve the existing PLC-controlled `-K213` enable path. |
| NED-004 | Reserve controlled service power without authorizing a continuously enabled maintenance interface. |
| NED-005 | Establish a defined termination boundary before terminal family and field hardware are selected. |
| NED-006 | Provide the edge computer with a dedicated managed quality-zone link using unique cable `C202`. |
| NED-007 | Give the field camera a distinct physical network identity `C205` for installation and diagnostics. |
| NED-008 | Give the disabled maintenance conduit unique identity `C206` so access control can be audited. |
| NED-009 | Preserve a managed spare port without authorizing an unidentified device or cable. |
| NED-010 | Reserve the FE/PE/shield interface needed for manufacturer- and site-specific EMC design. |

## Panel and field integration

The existing Revision-E CAD contains a provisional `-PC200` envelope. Carrier, cooling solution, keep-outs, connector access, cable bend space and heat loss are not final. Camera, lens, light and enclosure are field-mounted unless the controlled hardware decision states otherwise. Cable entries must preserve enclosure rating, strain relief, drip paths, shielding and maintainable separation.

## Native QET update instructions

1. Open the exact controlled Revision-E QET hash in QElectroTech 0.100.0 using an isolated configuration directory.
2. Copy the native project to a Revision-F filename; never overwrite historical evidence.
3. Add the four conceptual protected branches and the X200/C200-C206 reservations to the 24 VDC distribution, network, terminal and cable folios.
4. Reconcile reference designations and quantities against `10_schedules/nvidia_electrical_delta.csv`.
5. Run native cross-reference checks, save, close, reopen the exact final hash and export the complete PDF.
6. Visually inspect every page and record the executable version/hash, QET hash, export hash and all deviations.

Until those steps are evidenced, this document and schedule are the authoritative standalone Revision-F electrical delta only. Cross-artifact incorporation remains BLOCKED, the native Revision-F QET update remains BLOCKED, and no broader schedule or panel-layout completion is claimed.
