# Drive-control and Startdrive philosophy

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Two preliminary 0.75 kW SINAMICS G120C PN drives use cyclic PROFINET control/status and Startdrive commissioning when a compatible TIA toolchain is available. PLC run commands require external safety healthy mirror, drive ready, no fault, correct machine state and equipment interlocks. Fault reset is edge-triggered and inhibited while a run request exists.

Motor data, ramp times, minimum/maximum speed, current limits, braking method, EMC filter, line reactor, protective device, cable/shield and thermal selections are open until nameplates, pump curve, mechanics and site data are received. STO is shown only as an external conceptual safety interface and is never controlled or credited by standard PLC logic.
