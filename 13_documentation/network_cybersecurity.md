# Network and cybersecurity design

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Zones

VLAN 10 is cell control (PLC, HMI, two drives), VLAN 20 is quality vision, and VLAN 99 is temporary engineering service. A managed SCALANCE XC208 provides port-based VLANs; a SCALANCE S615 routes only approved inter-zone flows. The former 6GK5008-0BA10-1AB2 selection was corrected: it is an unmanaged XB008 and is not used for zoning.

## Allow list

| Source | Destination | Service | Policy |
|---|---|---|---|
| 192.168.20.10 | 192.168.10.10 | TCP/4840 | Stateful allow only for the named vision-client certificate/application URI and approved namespace; return traffic only |
| HMI/Drives VLAN 10 | PLC VLAN 10 | Native PROFINET/HMI traffic | Allow within control zone |
| Engineering VLAN 99 | Approved nodes | Native engineering services | Disabled in production; maintenance change window only |
| Any other | Any | Any | Deny and log |

## Identity, rights and certificates

Default deny and log applies at the S615 boundary. Pin PLC-server and vision-client application URIs/certificates to the site trust list; maintain issuance, revocation and expiry records; protect private keys in platform-backed or encrypted storage under named OT ownership. The vision client receives read-only rights to enable/request/recipe/heartbeat/session nodes and write-only rights to ready/busy/result/model/diagnostic nodes; unrestricted browse, anonymous access and shared engineering accounts are prohibited. Result writes are ordered payload first and `RESULT_VALID` last; clear `RESULT_VALID` first after matching `RESULT_ACK_ID`.

NTP, PKI, syslog and engineering-workstation addresses, cipher policy, log retention and vulnerability-response owners remain blocked inputs. Structured logs must correlate session epoch, inspection ID, PLC/vision heartbeat, model ID/hash, diagnostic code and duration without retaining images by default.
