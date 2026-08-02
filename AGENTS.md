# Project engineering controls

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Canonical control

- `00_project_control/canonical_model.json` owns requirements, tags, addresses, alarms, hardware, network nodes and tests.
- Device designations use `=FC01+<location>-<class><nnn>`; PLC symbols are uppercase snake case; addresses are unique and assigned only by the chief systems engineer.
- Alarm ranges: 1000 utilities/safety mirrors, 1100 drives, 1200 actuators, 1300 filling, 1400 capper, 1500 vision, 1600 communications.
- Native TIA, QET, WinCC and FreeCAD files outrank rendered or generated views only after their recorded native validation gate passes.
- Generated schedules may never override canonical data. A mismatch fails validation.

## Ownership and agent coordination

- `00`–`02`, `release`: chief systems engineer. `03`, `09`, electrical/panel engineer. `04`–`06`, Siemens engineer. `07`, vision engineer. `08`, `11`, simulation engineer. `12`, `14`, independent V&V engineer.
- No concurrent edit of controlled files. Controlled changes require an ECR stating reason, affected artifacts, compatibility, test impact, risk and migration action.
- A reviewer must not approve work it produced. Evidence is native reopen output, compile output, test logs, hashes, parsed schedules or rendered-page inspection—not confidence language.

## Toolchain and commands

- Authoritative target: **TIA Portal V20**, executable/product version `2000.0.9501.1`; STEP 7 V20 and WinCC V20 components are installed, but usable licence entitlement and native compile remain unproven. TIA Openness V20 assemblies exist, but the current identity is not authorized.
- Startdrive and PLCSIM/PLCSIM Advanced are not installed. QElectroTech portable baseline is 0.100.1-dev; FreeCAD 1.1.3 is retained as an archive/evidence baseline. NVIDIA runtime target is DeepStream 9.1 on Jetson Orin, but the CUDA/TAO/DeepStream/Omniverse stack is not installed.
- Build: `python scripts/build_project.py`; simulator: `python -m unittest discover -s 11_simulation/tests -v`; validate: `python scripts/validate_project.py`.

## Safety and AI boundaries

- Never create deployable safety logic or credit PLC/AI with safety. Safety status is monitoring only.
- AI is a quality device. Timeout, stale ID, result conflict, heartbeat loss, low confidence or fault always causes quality hold.
- No model/metrics/latency claim without named dataset and actual hardware evidence. No fake native extensions.

## Review gates

Requirements/architecture → electrical/I/O → Siemens sources → HMI/drives → vision → simulation → documents → independent final QA. All affected gates repeat after a controlled change.
