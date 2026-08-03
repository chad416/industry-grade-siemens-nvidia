# Digital twin and synthetic-data architecture

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

The deterministic Python simulator in `11_simulation` is the regression oracle for sequence/failure behavior; it is not the Siemens PLC and cannot satisfy PLCSIM gates. A separate OpenUSD/Omniverse workflow is specified for visualization and synthetic data, but no USD file is delivered because Omniverse/USD native validation was unavailable.

When available, import the validated STEP assembly, preserve SI units and source hashes, add non-authoritative joints/sensors, and parameterize bottle position, fill, color/transparency, light intensity/direction, camera angle, glare, foam, occlusion, background and bottle geometry. Each render must carry scene commit, source STEP hash, random seed and annotation provenance. A re-opened USD stage is necessary but not proof of physical fidelity.
