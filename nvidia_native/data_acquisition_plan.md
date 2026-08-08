# Vision data acquisition plan

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Inspection questions

The initial taxonomy separates: bottle present/positioned, correct bottle type, fill level per channel, gross foam/overflow/leak indication and cap/transfer observation. PLC flow and level measurement remains authoritative for deterministic filling; vision is a non-safety quality device.

## Controlled acquisition

Use a fixed camera/lens/light enclosure, locked focus/exposure/white balance and a calibration target. Capture multiple production lots, sessions, operators, expected ambient variation, bottle positions and difficult negative cases. Record camera/lens/light IDs, recipe, lot/session, timestamps, dimensions and SHA-256. Keep train/validation/test groups separated by lot and session. Do not collect people or confidential labels unless privacy approval and retention rules exist.

## Acceptance before training

The product owner approves taxonomy/tolerances; a data steward approves provenance/licence/privacy; two reviewers adjudicate safety-relevant false-pass candidates. An empty manifest is valid pipeline state but is not dataset evidence.
