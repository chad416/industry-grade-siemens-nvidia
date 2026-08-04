# Vision model evaluation report — NOT EXECUTED

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

Model: not trained or delivered. Dataset: not available. Target hardware: not available. Evaluation date: not executed.

| Required evidence | Status |
|---|---|
| Named train/validation/test manifest and hashes | Missing |
| Per-class precision, recall and F1 | Not measured |
| Confusion matrix | Not measured |
| Underfill/overfill error distribution against physical reference | Not measured |
| False-accept analysis by defect/fill class | Not measured |
| False-reject analysis and throughput impact | Not measured |
| Confidence-threshold curve and rationale | Not established |
| End-to-end inference latency distribution on target | Not measured |
| Thermal soak and dropped-frame results | Not measured |
| Model checksum and deployment bundle | Not available |

Acceptance requires traceable results on representative real data. Synthetic results alone cannot close the gate.

`dataset_tool.py evaluate` is available to compute a supplied binary confusion matrix, false-accept rate and false-reject rate without inventing observations. `edge_service/benchmark_harness.py` provides explicitly development-only timing mechanics. Neither tool has been run on a production dataset/model/target in this release.
