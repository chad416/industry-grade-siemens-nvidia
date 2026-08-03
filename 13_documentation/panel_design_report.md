# Panel design report - Revision E

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Native layout basis

The current package contains a genuine FreeCAD 1.1.3 selected-architecture assembly in an 800 x 800 x 300 mm provisional enclosure with a 750 x 750 x 3 mm drilled mounting plate. It includes enclosure/door, DIN rails, ducts, main and 24 V protection envelopes, 24 VDC supply, CPU/DI/DQ/AI/TM Count modules, MTP700 door representation, two G120C PN FSA envelopes, managed switch, firewall, relay bank, terminal/PE/shield infrastructure and a controlled provisional NVIDIA edge-compute envelope. Reference designations follow the `=FC01+CP01-...` structure.

The native schedule places heat-producing drives in the separated left zone and reserves 80 mm top / 100 mm bottom keep-outs based on the controlled Siemens catalog assumption. PLC, network/vision, control-power, relay/protection, terminal and PE zones are spatially separated. Ducts identify mains/drive, control and network routing. HMI/isolator door geometry, terminal access, service access, spare I/O space and the provisional edge envelope are explicitly represented.

## Native verification boundary

When `09_panel_cad/revision_e/native_verification.json` reports PASS, the final FCStd has been independently reopened by FreeCADCmd, controlled shapes checked, STEP reimported as solids, IGES reimported as valid bounded face geometry, and DXF structure/hole coordinates reconciled to the 30-hole schedule. STEP is the solid-retention exchange proof; no IGES solid-retention claim is made. The general-arrangement and mounting-plate PDFs and four major views retain explicit provenance.

## Open construction inputs

Enclosure series/IP, final protective devices, 24 V branch-protection family, relay/terminal accessories, NVIDIA carrier/cooling, cable entry/glands, duct fill, thermal rise, PE/bonding, EMC, short-circuit rating, vendor drilling, site clearances and qualified-human construction review remain open. The CAD gate is dimensional/native engineering evidence only, not fabrication authorization.
