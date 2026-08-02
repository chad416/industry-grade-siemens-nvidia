# Software design specification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

The reviewable SCL is split by equipment responsibility. Interfaces are statically typed; instance FBs own timers and edges; the coordinator owns legal transitions; the final output mapper applies permissives. First-out is latched before acknowledgement; acknowledgement and reset are distinct.
