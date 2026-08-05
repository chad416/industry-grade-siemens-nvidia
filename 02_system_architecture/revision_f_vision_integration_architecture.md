# Revision-F NVIDIA vision integration architecture

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

> THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.

## Functional boundary

The Siemens S7-1500 remains the sole owner of modes, sequence state, interlocks, timeouts, actuator and drive requests, restart behavior, product disposition and transfer permission. Process flow and level instrumentation remains the deterministic fill measurement. Vision supplies an independent quality observation only: bottle presence/alignment, visible fill band, underfill/overfill indication, severe foam or abnormal appearance and visible spill/leak where optics permit.

The provisional model approach is hybrid rather than generic object detection alone:

1. deterministic geometry and calibration locate the carrier, bottle ROIs and fill-reference band;
2. segmentation or calibrated level-line estimation measures visible liquid/foam regions;
3. detection localizes bottle/nozzle/spill anomalies where a global classifier would obscure cause;
4. a learned classifier or Visual ChangeNet-style comparison may provide an additional anomaly score against approved reference images;
5. the edge policy combines the observations conservatively and publishes PASS only when every required channel is present, coherent and above validated thresholds.

This approach is provisional until transparent-container feasibility, glare, liquid appearance, production variation and reject economics are measured.

## One-camera versus two-camera decision

| Criterion | One camera | Two cameras |
|---|---|---|
| Initial cost and integration | Lower | Higher |
| Two-bottle coverage | Possible with wider field and lower pixels/mm | Dedicated or overlapping views improve per-bottle resolution |
| Occlusion and parallax | Higher risk | Lower risk when views are selected independently |
| Glare management | One illumination/view compromise | More options for cross-polarized/backlight and oblique views |
| Calibration/maintenance | Simpler | Additional calibration, synchronization and spares |
| Current disposition | Provisional baseline for feasibility trial | Contingency if pixel, glare or occlusion margin fails |

No camera count, sensor, lens or enclosure is released for procurement. The optical feasibility trial must calculate field of view and pixels per smallest decision feature, then demonstrate focus, distortion, exposure and motion-blur margin at maximum line speed.

## Trigger and timing lifecycle

The PLC freezes recipe, carrier position, expected bottle count, target fill band, expected model/dataset/calibration identities and the nonzero session/inspection identity before asserting a level-held trigger. The edge publishes capture acknowledgement only after the correct request identity is accepted and an image is bound to it. Processing state then advances through acquired, preprocessing, inference and post-processing. Result payload fields are written first and `RESULT_VALID` last. The immutable publication remains until exact PLC acknowledgement.

Any timeout, heartbeat loss/regression, stale/duplicate/future identity, recipe mutation, clock discontinuity, camera/model/configuration fault, queue saturation, malformed or contradictory payload, insufficient confidence or expired result prevents PASS. Recovery never restarts the machine automatically.

## Failure containment

- The edge has no writable PLC node that energizes motion or bypasses a permissive.
- The PLC decommands pump and fill valves independently of vision communications.
- Offline buffering of inspection decisions is prohibited. At most one current immutable unacknowledged publication may be restored after restart.
- Log-storage failure is a blocking diagnostic because required traceability cannot be completed.
- Maintenance bypass is a request for controlled operator disposition, not an automatic quality acceptance.
- A recipe or calibration change invalidates an active transaction and requires a new inspection.

## Network and trust boundary

`-PC200` resides in VLAN 20 and acts as the OPC UA client to the PLC server in VLAN 10 through the deny-by-default `-FW100` boundary. Only TCP 4840 for the named application identities and approved namespace is permitted. Application and user certificates, pinned server identity, trust/revocation stores, least-privilege node rights, authenticated time and centralized security logging are required. Image transfer is not permitted across the PLC boundary.

## Time and records

The PLC correlation identity is authoritative even if clocks disagree. UTC capture and inference timestamps support diagnostics and result-age checks but never replace session/inspection correlation. The site must provide an authenticated NTP/PTP hierarchy, maximum permitted clock step, resynchronization rule and log-retention owner. Raw images are not retained by default; approved fault/challenge samples may be retained under a documented privacy, capacity and deletion policy.

## Maintainability

Camera, lens, lighting, carrier, edge image, model bundle, dataset baseline and calibration each have independent identifiers and hashes. Replacement requires mechanical datum restoration, focus/aperture lock, exposure/illumination verification, calibration challenge images, secure OPC UA smoke tests and a bounded rollback. A golden configuration alone is not proof that optics or process conditions remain acceptable.
