# NVIDIA edge-service source boundary

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

`protocol.py` is the edge-service protocol oracle. It defines the controlled target-fill bounds (0.1 through 1.0), request/result rules, exact model identity checks and a hexadecimal SHA-256 requirement. `service.py` adds fail-closed 1000 ms PLC-heartbeat supervision and compares every result to the backend's controlled identity. `service_config.json` records the same timeout, the intended secure OPC UA endpoint and atomic publication order.

No OPC UA runtime adapter, camera driver, model, ONNX file, TensorRT engine or DeepStream execution is delivered. Without a backend exposing a non-empty model ID and 64-character hexadecimal SHA-256, the service remains not ready and rejects every inspection. The tests include the simulator's normal request values and adversarial heartbeat/model-identity cases; actual target/runtime integration remains acceptance gate 18.
