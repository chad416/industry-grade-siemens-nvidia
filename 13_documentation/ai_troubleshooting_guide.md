# NVIDIA inspection troubleshooting guide

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

| Symptom | First checks | PLC disposition | Closure evidence |
|---|---|---|---|
| Vision not ready | Configuration signature, camera/model health, certificate trust, storage and time | HOLD; no transfer | Healthy startup log and controlled identity snapshot |
| Capture not acknowledged | Trigger identity, camera connection, exposure/trigger mode, queue depth | HOLD then fault at deadline | Correlated capture record |
| Low confidence | Optics cleanliness, glare, focus, bottle/liquid lot, lighting and threshold provenance | Operator disposition | Challenge-set rerun; do not lower threshold without approval |
| Wrong/stale/duplicate ID | Session epoch, restart/reconnect record and retained publication | Reject result; HOLD/FAULT | Exact transaction reconciliation |
| Model hash mismatch | Active bundle, configuration and rollback slot | FAULT | Approved signature/SHA and model card |
| Excessive latency | Input rate, queue, GPU/thermal/storage load and pipeline stages | HOLD | Representative target benchmark |
| OPC UA disconnect | Network/VLAN/firewall, certificates, endpoint and time | FAULT; preserve current product | Secure reconnect and disabled synchronization |
| Log storage failure | Capacity, permissions, media health and retention service | FAULT | Durable audit write and recovery test |

Do not bypass quality or change model/threshold/calibration values as a troubleshooting shortcut. The HMI maintenance mode provides diagnostics and controlled disposition only; it cannot bypass PLC interlocks or safety functions.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
