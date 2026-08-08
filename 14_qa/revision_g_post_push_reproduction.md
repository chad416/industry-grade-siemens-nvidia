# Revision G published-candidate reproduction

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Outcome

**PASS** — commit `38ab54deace5e6b71479bb4a347cd39c0233f37d` on `codex/revision-g-native-cloud-execution` was fetched from GitHub into a new clone outside the development worktree and completed the controlled reproduction workflow with exit code 0. The clone remained clean after reproduction.

This record attests the published engineering candidate, not the later commit that contains this record. That attestation commit is reverified after publication and its outcome is reported externally without rewriting the verified commit.

## Exact evidence

| Check | Result |
|---|---:|
| Manifest | 504 controlled files; 0 discrepancies |
| Release-integrity checks | 871 passed; 0 failed |
| Engineering validator | 551 passed; 0 failed |
| Revision-F successor-aware verifier | 96 passed; 0 failed |
| Revision-G verifier | 113 passed; 0 failed |
| Siemens/simulator/source/native-contract tests | 99 passed; 0 failed |
| NVIDIA edge/OPC UA tests | 86 passed; 0 failed |
| PLC-AI interface-harness tests | 17 passed; 0 failed |
| Timed process scenarios | 32 passed; 0 failed |
| Vision fault scenarios | 28 passed; 1 intended release; 0 unsafe outputs |
| QET Revision-E static checks | 24 passed; 0 failed |
| QET Revision-F static checks | 19 passed; 0 failed |
| FreeCAD native checks | 80 passed; 0 failed |
| Deterministic outputs | 350 compared; 0 missing; 0 extra; 0 mismatched |
| Workbook | 27 sheets; 0 formula errors; visual review PASS |
| Release-evidence PDF | 6 pages; visual review PASS |

FreeCAD evidence comprised 165 document objects, 148 solids, zero invalid shapes, 148 STEP shapes, 34 DXF shapes, 30 DXF circles and 30 reconciled mounting holes. The workbook SHA-256 was `0589860dc2e5dcad681517b596ca9c347abf044937c76209a85d3b038a21565b`; the PDF SHA-256 was `71c6e60d6632a692250f0709e25436f18f6b7c35f203494900acc87f2d5f447d`.

## Boundaries

QElectroTech Revision-G native execution was not run because no executable was available; exact-hash inherited native evidence and static checks remain clearly distinguished. No native Siemens compile, WinCC compile, Startdrive work or PLCSIM run was performed. No representative dataset, trained model, production NVIDIA runtime, hardware FAT/SAT, commissioning, construction release, qualified safety validation or qualified-human approval is claimed. The review records are software-agent self-audits and are not independent professional certification.
