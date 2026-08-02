# Managed network and firewall decision

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Revision B incorrectly named `6GK5008-0BA10-1AB2` as an XB208. Siemens identifies that order number as a SCALANCE XB008 unmanaged 8-port 10/100 Mbit/s switch. It cannot implement the controlled VLAN 10/20/99 architecture and is removed from the design.

Revision C selects a SCALANCE XC208 managed Layer-2 switch `6GK5208-0BA00-2AC2` and SCALANCE S615 EEC firewall/router `6GK5615-0AA01-2AA2`. XC208 provides managed VLAN-capable switching; S615 provides routed, stateful, deny-by-default inter-zone enforcement. Site OT must approve addresses, certificate authority, time/log sources, management hardening and exact rules before native configuration.

The only planned cross-zone production flow is an authenticated, encrypted OPC UA client session from the named vision edge host to the PLC server on TCP 4840, restricted to the versioned FC01 namespace. Engineering VLAN access is disabled in production and enabled only in an approved maintenance window. Anonymous access, shared certificates and unrestricted any-to-any routing are prohibited.

Official sources accessed 2026-08-02:

- XB008 product page: https://mall.industry.siemens.com/mall/de/b1/Catalog/Product/6GK5008-0BA10-1AB2
- XC208 technical data: https://support.industry.siemens.com/teddatasheet/?caller=SIOS&format=pdf&language=en&mlfbs=6GK5208-0BA00-2AC2
- S615 product page: https://mall.industry.siemens.com/mall/en/oeii/Catalog/Product?SiepCountryCode=OE&mlfb=6GK5615-0AA01-2AA2
- S615 configuration manual: https://support.industry.siemens.com/cs/attachments/109976097/PH_SCALANCE-S615-WBM_76.pdf
