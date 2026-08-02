# Panel design report

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Layout basis

The schedule reserves an 800 x 800 mm mounting plate with separate PLC/analog, network, 24 VDC, VFD heat, field-terminal and PE zones. The HMI is door-mounted, not placed on the backplate. Core Siemens envelopes use official data-sheet dimensions; unresolved drive, firewall and Jetson envelopes remain blank and explicitly block native CAD completion.

## Segregation and service

Mains/VFD input and motor output routes remain separated from 24 VDC, analog/HSC and Ethernet. Analog shields terminate at the panel shield-clamp rail. Drives reserve 100 mm top/bottom service airflow until exact model manuals are confirmed. Terminals reserve front service access and spare capacity.

## Open native evidence

The inherited FCStd/STEP/IGES/DXF files are historical baselines only. A Revision-D assembly, collision check, FCStd reopen and exchange-format reimport are mandatory before the panel gate can pass.
