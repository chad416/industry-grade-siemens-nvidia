# FC01 vision architecture and provisional hardware trade study

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

No camera, lens, lighting or edge computer is selected. Dimensions, watts and thermal values remain controlled input fields until throughput, bottle envelope, environment and vendor data exist.

## Inspection requirement

The primary station verifies two-bottle presence/alignment, visible fill level, underfill/overfill, severe foam and visible spill/leak evidence where geometry permits. Flow and level instrumentation remain the deterministic filling-process measurements. Vision is an independent non-safety quality check. Cap inspection is downstream scope.

## One versus two cameras

| Criterion | One paired-bottle camera | Two bottle cameras |
|---|---|---|
| Cost, ports, power, calibration | Lower | Higher |
| Pixels per bottle and independent adjustment | Lower/shared | Higher/independent |
| Occlusion and nozzle accommodation | Harder | Easier |
| Common-cause camera failure | Both observations lost | Partial diagnostic availability, but cell still HOLDs unless the approved recipe permits otherwise |
| Maintenance | One spare/alignment | More spares and cross-camera consistency |

The provisional baseline is one fixed global-shutter color camera with a paired-bottle field of view, backlight for liquid boundary and separately controlled diffuse front light for gross visible defects/spill. Select two cameras if the measured pixel density, occlusion or depth-of-field trial fails. This decision cannot close without bottle/nozzle envelope and physical images.

## Optical calculations and timing

Required field width is `2 × maximum bottle width + centre spacing allowance + setup margins`, then at least 10% framing reserve. Pixel density is `horizontal pixels / calibrated field width`; validation must establish the minimum pixels needed for fill tolerance and defect dimensions. Thin-lens first estimate is `f ≈ sensor width × working distance / field width`; confirm with manufacturer lens data and working-distance trial.

The PLC freezes the indexed carrier, allows drip/foam settle, and raises the inspection request. Capture acknowledgement must match the request ID before processing. Exposure must limit blur to the validated pixel budget: `blur_px = image_velocity_mm_s × exposure_s × pixel_density_px_mm`. Record trigger jitter, exposure start, capture, processing and publication timing. Edge UTC timestamps are diagnostic only; PLC result-age acceptance uses the PLC monotonic/receipt clock.

## Edge platform criteria

| Criterion | Jetson Orin industrial module/carrier | Industrial x86 with NVIDIA GPU |
|---|---|---|
| Compactness/power | Usually favorable | Usually larger/higher |
| Service ecosystem | Embedded Linux/vendor carrier specific | Conventional industrial-PC service |
| GPU/runtime portability | JetPack/DeepStream constrained | Broader discrete-GPU options |
| Expansion/storage | Carrier dependent | Often broader |
| Lifecycle/environment | Requires selected industrial carrier evidence | Requires selected industrial PC/GPU evidence |

Selection requires measured camera rate, model memory/compute, worst-case latency, ambient/enclosure temperature, ingress/vibration, supply, lifecycle, cybersecurity support and spares strategy. Reserve separately protected power, service isolation, Ethernet switch port, grounded metal mounting, shield termination, cable entries, ventilation/heat allowance and maintenance clearance. The current panel allocation is provisional; no wattage or clearance is released from this trade study.

Network design uses the managed OT switch, one edge-to-PLC OPC UA conduit and separately governed maintenance access. Time uses the site NTP/PTP hierarchy with offset alarms; transaction correctness never depends solely on wall-clock agreement. Configuration/model/calibration are immutable bundles with hashes. Replacement requires identical or reviewed hardware, restored trust/config, new optical calibration where the imaging chain changes, negative tests and no automatic machine restart.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
