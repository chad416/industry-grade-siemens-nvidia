# Drive-control and Startdrive philosophy

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Both G120C PN drives use PROFINET Standard Telegram 1 as the sole standard-control path: STW1 and normalized speed reference from PLC; ZSW1 and normalized actual speed to PLC. Comms health, ready, running, stopped and fault are decoded in `FB_VFD`. Hardwired run/ready/running/fault signals have been removed from physical PLC I/O.

External STO remains a conceptual interface owned by qualified safety design and is neither controlled nor credited by the standard PLC. Motor nameplates, overload duty, ramps, speed/current limits, braking, line protection, EMC accessories, cable/shield and loss data are open. Startdrive is not installed, so parameter and compile evidence are not claimed.
