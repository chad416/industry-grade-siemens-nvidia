# Network and cybersecurity design

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Zones

VLAN 10 is cell control (PLC, HMI, two drives), VLAN 20 is quality vision, and VLAN 99 is temporary engineering service. A managed SCALANCE XC208 provides port-based VLANs; a SCALANCE S615 routes only approved inter-zone flows. The former 6GK5008-0BA10-1AB2 selection was corrected: it is an unmanaged XB008 and is not used for zoning.

## Allow list

| Source | Destination | Service | Policy |
|---|---|---|---|
| Vision VLAN 20 | PLC VLAN 10 | OPC UA TCP 4840 | Allow only named client certificate and approved namespace |
| HMI/Drives VLAN 10 | PLC VLAN 10 | Native PROFINET/HMI traffic | Allow within control zone |
| Engineering VLAN 99 | Approved nodes | Native engineering services | Disabled in production; maintenance change window only |
| Any other | Any | Any | Deny and log |

## Identity and certificates

Use unique device certificates, site CA trust, encrypted private-key storage, expiry monitoring, revocation/change records and least-privilege OPC UA node rights. Anonymous access and shared engineering accounts are prohibited. Final cipher suites, time source, logging retention and vulnerability response require site OT approval.
