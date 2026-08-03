# Deterministic controls-process simulation

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

This directory contains an independent, deterministic Python verification model for the compact two-nozzle filling cell. It is not a Siemens PLC application, TIA Portal compile, PLCSIM run, validated fluid model, or physical commissioning record.

## Model boundary

`filling_cell_simulator.py` couples four explicit time-stepped models:

- A controller state machine with command arbitration, first-out diagnostics, quality holding, reset/start separation, and restart inhibition.
- A plant with bottle transport, gate/clamp travel, common pump ramp, independent fail-closed valves, pulse totals, analog flow, and physical fill volume.
- A vision endpoint implementing monotonic inspection IDs, ready/busy/result timing, result correlation, heartbeat supervision, and semantic result validation.
- A capper endpoint implementing ready/request/busy/complete/fault timing.

The default integration step is 20 ms. The simulated controller observes only field and interface signals. Physical volume is hidden plant state used by the simulated vision endpoint, allowing correlated meter-calibration faults to produce independent underfill/overfill quality results.

## Deterministic failure behavior

All faults are injected into the evolving model, not returned from a result lookup. Timed/state-dependent injections cover bottle sensing, gate/clamp motion, VFDs, air/product utilities, pulse and analog disagreement, valve feedback, HMI communication, power, capper handshaking, PLC/vision heartbeats, result timeout, stale inspection ID, low confidence, and bottle quality failure.

The following invariants are checked at every step:

- No pump command outside `FILLING`.
- No valve command without the common pump command.
- No conveyor command while clamp/filling commands are active.
- No energized motion/fill command while simulated power is absent.
- Gate and clamp feedback remain proven through filling, settle, and inspection.
- Release occurs only after the capper complete handshake.
- Recovery/reset does not synthesize a start edge.

## Run and inspect

From the project root:

```powershell
python -m unittest discover -s 11_simulation/tests -v
python 11_simulation/run_scenarios.py
```

The scenario runner writes:

- `outputs/scenario_results.csv`: one evidence summary per canonical scenario.
- `outputs/traces/<scenario>.csv`: every sampled state, command, feedback, flow, interface, and handshake value.
- `outputs/run_metadata.json`: time-step configuration and an explicit `native_plcsim = NOT RUN` limitation.

Tests include deterministic repeatability, a 10/20/40/50 ms integration-step sweep, a supported 400/500/700 ml recipe-target sweep, transition-order checks, channel-independent shutoff, restart-inhibition checks, and negative PLC–vision protocol cases.

## Truthfulness limitation

Passing these tests demonstrates consistency of this independent model and its declared properties only. It does not prove that the Siemens sources compile, execute equivalently, meet PLC scan-time constraints, or pass PLCSIM/native hardware tests. Those gates remain separate and incomplete until the native Siemens toolchain is used.
