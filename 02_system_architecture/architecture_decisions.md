# Architecture decision records

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## ADR-001: CPU family

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** S7-1200, S7-1500, ET 200SP CPU.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** S7-1500 CPU 1511-1 PN.
- **Justification:** Diagnostics, modular organization, OPC UA/PROFINET margin.
- **Consequences:** Higher cost and TIA catalog dependency.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-002: I/O location

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Distributed ET 200SP vs local S7-1500.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Local S7-1500 modules.
- **Justification:** Compact single-panel machine, fewer network dependencies.
- **Consequences:** Long field cables; review if machine expands.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-003: High-speed flow

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** CPU DI counters vs TM Count.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** TM Count 2x24V.
- **Justification:** Two independent dedicated channels and diagnostics.
- **Consequences:** Module configuration must be verified in TIA.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-004: HMI

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Basic/Comfort/Unified.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** MTP700 Unified Comfort.
- **Justification:** Diagnostics, roles, reusable faceplates.
- **Consequences:** WinCC Unified licensing and runtime learning curve.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-005: Drives

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Hardwired VFD vs G120C PN.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** G120C PN with hardwired external STO concept.
- **Justification:** Integrated diagnostics and Startdrive.
- **Consequences:** Motor/EMC/protection data still required.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-006: PLC organization

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Monolith vs equipment modules.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Modular FBs plus coordinator.
- **Justification:** Cohesion, instance ownership, unit review.
- **Consequences:** More interfaces and DBs.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-007: State strategy

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Implicit rungs vs explicit legal transitions.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Explicit coordinator states.
- **Justification:** Deterministic recovery and diagnostics.
- **Consequences:** Transition table must be maintained.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-008: Dose measurement

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Analog integration vs pulses.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Pulses for total; analog for plausibility.
- **Justification:** Independent totals and cross-check.
- **Consequences:** K-factor and cutoff compensation need trials.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-009: Vision model

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Single classifier vs detection + metrology heads.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Two-stage bottle/defect detection plus calibrated fill-line estimator.
- **Justification:** Separates presence/condition from fill geometry.
- **Consequences:** Requires representative labeled data.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-010: Optics

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Ambient/front light vs controlled backlight + diffuse front.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Controlled backlight with diffuse front fill.
- **Justification:** Improves liquid boundary and gross defect visibility.
- **Consequences:** Bottle/product-specific feasibility trial.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-011: PLC–AI protocol

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Digital I/O, TCP, MQTT, OPC UA.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** OPC UA with ID/heartbeat contract.
- **Justification:** Typed data, diagnostics, Siemens/edge support.
- **Consequences:** Certificate and namespace management.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-012: NVIDIA hardware

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** dGPU IPC, Jetson AGX, Orin NX.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Jetson Orin NX 16GB module on qualified industrial carrier.
- **Justification:** Compact edge inference and DeepStream support.
- **Consequences:** Carrier/thermal/EMC SKU open.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-013: Digital twin

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Custom 3D only vs OpenUSD.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Deterministic simulator plus optional OpenUSD.
- **Justification:** Separates regression truth from visualization/synthetic data.
- **Consequences:** No USD delivered without Omniverse validation.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-014: Network

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Flat vs zoned.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Control, quality and service zones.
- **Justification:** Limits blast radius and controls updates.
- **Consequences:** Managed routing/firewall design required.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-015: Data retention

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Unlimited images vs event policy.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Retain faults/low confidence and sampled passes with expiry.
- **Justification:** Supports model improvement while bounding storage/privacy.
- **Consequences:** Site policy and capacity needed.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.

## ADR-016: Failure recovery

- **Problem:** Select a maintainable bounded solution.
- **Alternatives:** Automatic retry/restart vs controlled hold.
- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.
- **Selected:** Hold + explicit disposition/reset to STOPPED.
- **Justification:** No unintended restart or quality bypass.
- **Consequences:** Operator procedure needed.
- **Risks/assumptions:** source data and licensed native tool support must be confirmed.
- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.
