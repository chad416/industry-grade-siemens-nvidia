# NVIDIA GPU build runbook

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

1. Confirm current DeepStream/TAO compatibility and selected model requirements before selecting G2/L4 or another GPU.
2. Require an approved plan, quota and price record. Use Spot only for resumable jobs.
3. Provision Ubuntu 24.04 with no external IP; connect through IAP SSH.
4. Install the NVIDIA driver/container stack strictly from official repositories; record version/digest and licence acceptance owner.
5. Pull only an approved digest-pinned DeepStream/TAO image. Generate SBOM and vulnerability report before execution.
6. Mount controlled dataset/artifact storage least-privilege; never embed credentials in an image.
7. Run data validation, synthetic smoke, then approved real training/evaluation. Record raw logs and hashes.
8. Stop the GPU immediately after each job; verify instance state and continuing storage costs.
