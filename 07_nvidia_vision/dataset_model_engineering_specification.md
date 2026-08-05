# FC01 dataset and model engineering specification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

No representative dataset, trained model, accuracy result or production threshold is delivered. Synthetic data is permitted only for pipeline tests and is never production validation evidence.

## Inspection strategy

The provisional architecture is hybrid: calibrated deterministic geometry estimates visible fill line and alignment inside verified bottle ROIs; a detector/segmenter localizes bottles, liquid/foam and visible spill evidence. This is more defensible than a single global pass/fail classifier because it preserves interpretable geometry and defect localization. Transparent bottles, specular glare and foam require polarized/diffuse lighting trials. Cap inspection is a downstream extension, not part of the released filling decision.

## Required collection matrix

Collect by independent production lot and acquisition session across every bottle SKU, nominal/under/over fill, liquid color/transmission/viscosity, foam severity, bottle lot, lighting drift, camera/lens replacement, focus and exposure limits, background, nozzle position, misalignment, occlusion, contamination, drip/spill, empty carrier, label state and environmental condition. Record true fill reference by a traceable independent method. Include clean negatives and hard negatives. Do not manufacture class balance by duplicating adjacent video frames.

## Storage and annotation

The dataset root contains `images/`, `annotations/`, `manifests/`, `calibration/`, `collection_records/` and `reviews/`. `dataset_manifest.csv` uses the exact v2 header enforced by `dataset_tool.py`; all paths are dataset-root-relative and every image/annotation has SHA-256. Production lot plus acquisition session is the leakage-control group. Real/synthetic provenance is mandatory.

Classes: bottle; bottle misalignment; visible bottle damage; liquid region; foam; drip; spill. Each bottle has a polygon/bounding box and two calibrated fill-line endpoints where visible. Occluded or ambiguous samples use `unknown`, never a forced pass/fail label. Two reviewers independently review release test/challenge data; disagreements are adjudicated by an authorized domain reviewer and the original labels are retained in history.

`dataset_tool.py validate` verifies schema, paths, hashes, exact duplicates, review state and split leakage. `split` makes a deterministic group-level assignment. Exact SHA duplicates are implemented; near-duplicate image embedding/perceptual review remains a required external extension once images exist.

## Evaluation and promotion

Freeze train/validation/test manifests before threshold selection. Select thresholds on validation only; run the held-out test once for the candidate. Report per-class precision, recall and F1, confusion matrices, under/overfill error against the physical reference, false accept and false reject by condition, calibration error, robustness slices and confidence coverage. `dataset_tool.py evaluate` computes binary confusion/false-accept/false-reject values from supplied predictions; unit-test rows are not performance evidence.

Model promotion requires: controlled model/framework/container/config/dataset/calibration hashes; independent test and challenge-set review; target camera-to-PLC latency distribution; thermal and reconnect soak; failure-mode test; cybersecurity review; named approval authority; rollback rehearsal; and PLC/HMI acceptance criteria. A signed bundle includes model, input/output tensor contract, preprocessing, class map, thresholds, dataset ID, calibration compatibility, SBOM and model card. Rollback disables production, restores the prior complete bundle, verifies hashes, repeats negative tests and never automatically restarts the machine.

## External closure criteria

Provide representative real images and traceable fill references; select camera/lens/light and target edge; approve privacy/retention; run collection and independent annotation; install a supported training/runtime stack; execute training/evaluation; and retain immutable logs/hashes. Only those results may populate `model_card.md` and `evaluation_report.md`.

THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.
