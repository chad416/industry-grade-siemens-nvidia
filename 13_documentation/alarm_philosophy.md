# Alarm philosophy

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Classes and behavior

Faults cause controlled stop, abort or quality hold according to the alarm schedule. Warnings never imply product acceptance. First-out records the initiating alarm; later alarms remain visible. Acknowledgement records awareness only. Reset is accepted only when the source condition has cleared and never creates motion.

## Alarm record requirements

Each alarm has unique ID, equipment source, cause, response, acknowledgement policy, reset condition and linked verification. Fill-channel reusable reason codes are mapped separately for channel 1 and channel 2. Communications, stale IDs and low confidence all prevent transfer.

## Shelving and suppression

Safety-status mirrors, drive faults, fill faults and quality holds are not shelvable by operators. Maintenance suppression is permitted only in stopped maintenance state, is time limited, role controlled and logged in the eventual native HMI.
