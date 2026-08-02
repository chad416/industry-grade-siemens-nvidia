# Software design specification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Ownership and scan order

`Main` calls the single `DB_CellMain` instance. `FB_CellMain` owns command sequencing, two VFD instances, gate, clamp, two fill channels, recipe, vision, capper, alarm and coordinator instances. The cyclic order is input normalization, command arbitration, equipment status/control, sequencing, alarm mapping and final physical output mapping.

## Data separation

`DB_IO.Inputs` is the normalized field image; `DB_IO.Commands` is written only by the final mapper. `DB_HMI` contains request/sequence/accept/reject/disabled-reason structures and never aliases physical outputs. `DB_Drives` carries Standard Telegram 1 PZD. `DB_VisionComms` is the OPC UA contract. `DB_Recipe` separates candidate and active data.

## Diagnostic policy

Reusable blocks emit reason codes; the cell maps reason plus equipment identity to unique alarm IDs. Timers and edges are instance-owned. All standard outputs de-energize on loss of release permissive. Simulation forcing is absent from release sources. Static checks are not native compile proof.
