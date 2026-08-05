# FC01 vision commissioning, maintenance and cybersecurity runbook

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

This procedure is prepared for external execution; it is not FAT, SAT or commissioning evidence.

## Optical commissioning

1. Isolate the machine under the approved site procedure. Verify enclosure, bracket, lens lock, protective window, cable strain relief, service access and lighting thermal limits.
2. Mount a traceable calibration target at every bottle plane. Record camera, lens, filter, light, firmware and bracket IDs; working distance; field width/height; pixel/mm; distortion residual; focus metric; aperture; exposure; gain and strobe timing.
3. Confirm both bottle envelopes plus at least 10% framing margin. Measure worst-case motion blur, trigger-to-exposure jitter and depth of field. Lock focus/aperture and mark tamper positions.
4. Challenge clear/colored liquids, glare, foam, labels, bottle lots, background, condensation, contamination, misalignment, empty nests and spill evidence. A failed or ambiguous image-quality criterion prevents readiness.
5. Freeze `CALIBRATION_ID`, store calibration source and hash, set the PLC expected identity, and verify a wrong identity produces HOLD.

Image acceptance: no saturation at the fill boundary beyond the validated mask; both bottle ROIs wholly visible; required pixel density met; distortion residual within the validated bound; exposure margin at line-rate; no flicker/beating; repeatable trigger; focus metric above its controlled limit; and no unreviewed occlusion.

## Software, network and trust boundary

The edge belongs to the OT quality zone. It initiates TCP 4840 only to the PLC OPC UA server. Engineering/maintenance access traverses an approved jump path; health endpoints stay loopback-only. Deny inbound services by default. Use a non-login least-privilege account, read-only application files, external writable log/state directories, secure boot/disk controls where required, signed updates, allowlisted egress and centralized time/log monitoring.

Issue distinct application and user X.509 certificates from the site CA. Disable anonymous OPC UA. Restrict the identity to read PLC-owned and write NVIDIA-owned nodes. Protect private keys, load CRLs, monitor expiry and test revocation. Never put credentials, certificates, images or product data in Git or routine logs.

Before enable: verify package/config/model/dataset/calibration/SBOM hashes; `pip check`; all 47 NodeIds/types/directions/access; NTP/PTP offset; firewall; disk reserve; log rotation; GPU/camera health; PLC/HMI alarms; safe HOLD behavior; backup; and rollback. Record every version and responsible approver.

## Fault injection and recovery

Execute with hazardous motion disabled first, then under the qualified test plan: valid pass/fail/hold; timeout/late completion; heartbeat freeze/regression/wrap; camera removal; model absent/wrong hash; dataset/calibration mismatch; malformed/contradictory result; stale/duplicate/future/reordered IDs; trigger missed; result tamper; wrong ACK; OPC UA loss/reconnect; edge/PLC restart; recipe change; UTC clock step; log/disk failure; corrupt config; queue attempt; maintenance/bypass request; certificate expiry/revocation; thermal/load soak. For each, prove no edge command energizes an actuator, no invalid result becomes PASS, IDs remain correlated, restart does not start motion, and diagnostics identify first cause.

Recovery always puts production under PLC HOLD, records the affected ID/product, restores health/identity/time, performs disabled session synchronization and requires the documented operator disposition. No buffered image/result is assigned to another bottle. No automatic production restart is permitted.

## Maintenance, backup and replacement

Back up only controlled source/config, signed model bundle, public certificates/trust lists, calibration sources, manifests and release evidence; private-key backup follows site PKI rules. Test restore on an isolated spare. Camera/lens/light/bracket replacement invalidates calibration until optical acceptance is repeated. Model or threshold changes require a new immutable ID and full promotion evidence. Retention duration, image privacy classification and incident export destination remain site decisions.

External closure needs real hardware, licensed native Siemens execution, site PKI/network authority, approved model/data, qualified machinery-safety review and witnessed commissioning.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
