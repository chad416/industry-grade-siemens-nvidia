# Repository and release-byte workflow - Revision D.1

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Authority and location

Git index blobs are authoritative while assembling a candidate; committed `HEAD` blobs are authoritative after commit. Build and final verification in a newly created directory outside OneDrive or another synchronization root. A synchronized folder may be used only as a convenience checkout after the release is accepted, never as manifest input.

## Controlled sequence

1. Start from the exact approved parent commit in a clean non-synchronized clone.
2. Generate source, schedules, workbook, PDF and renders with explicit LF or byte-exact policies.
3. Verify `release/reproduction_toolchain_lock.json`; Python/Node/Poppler executable hashes and required package versions are part of the controlled binary-reproduction environment.
4. Confirm no untracked, missing or superseded path exists; stage every intended non-manifest change.
5. Run `build_manifest.py`, which hashes only the complete staged index; stage both manifest files.
6. Verify the staged manifest, commit, then run the complete workflow from a brand-new clone of that commit.
7. Push only after the clean clone remains byte-for-byte clean and `HEAD` matches its upstream tracking commit.

## OneDrive containment

Revision D's OneDrive checkout resurrected ten obsolete Revision-C render PNGs and two Revision-C generators. All twelve match their parent-history blobs and are recoverable from Git, so they are superseded rather than hidden. The D.1 policy explicitly rejects those paths. If synchronization restores them, stop and relocate the clone; do not rebuild the manifest or use `git status` alone as release evidence.

## Recovery

Never repair a release by editing manifest hashes. Reproduce the mismatch against Git blobs, establish the intended source bytes, change the bytes or policy under an ECR, rebuild from staged index bytes, and repeat clean-clone verification.
