from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTICE = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"
SAFETY = ("CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, "
          "VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, "
          "SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def csv_write(path: str, rows: list[dict]) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows for {path}")
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def doc(title: str, body: str) -> str:
    return f"# {title}\n\n> {NOTICE}\n\n> {SAFETY}\n\n{body}"


hardware = [
    {"tag":"-A100","role":"PLC CPU","manufacturer":"Siemens","model":"SIMATIC S7-1500 CPU 1511-1 PN","order_no":"6ES7511-1AL03-0AB0","qty":1,"status":"Selected; official lifecycle page checked","basis":"Current standard CPU, PROFINET IRT, diagnostic capacity; native TIA compatibility gate open"},
    {"tag":"-A101","role":"High-speed counter","manufacturer":"Siemens","model":"TM Count 2x24V","order_no":"6ES7550-1AA01-0AB0","qty":1,"status":"Selected; official lifecycle page checked","basis":"Two independent 24 V pulse channels with channel diagnostics"},
    {"tag":"-A102","role":"Digital input","manufacturer":"Siemens","model":"DI 32x24V DC HF","order_no":"6ES7521-1BL00-0AB0","qty":1,"status":"Selected; official product page checked","basis":"32 PNP inputs, diagnostics and spare capacity"},
    {"tag":"-A103","role":"Digital output","manufacturer":"Siemens","model":"DQ 32x24V DC/0.5A HF","order_no":"6ES7522-1BL01-0AB0","qty":1,"status":"Selected; official product page checked","basis":"32 diagnostic outputs; field loads through interposing relays"},
    {"tag":"-A104","role":"Analog input","manufacturer":"Siemens","model":"AI 8xU/I HF","order_no":"6ES7531-7NF00-0AB0","qty":1,"status":"Selected; official product page checked","basis":"Individually grouped high-resolution 4–20 mA inputs and diagnostics"},
    {"tag":"-H100","role":"Operator panel","manufacturer":"Siemens","model":"MTP700 Unified Comfort","order_no":"6AV2128-3GB06-0AX1","qty":1,"status":"Selected; official active product page checked","basis":"7-inch Unified panel; requires WinCC Unified Comfort V16 or later"},
    {"tag":"-U100","role":"Conveyor drive","manufacturer":"Siemens","model":"SINAMICS G120C PN 0.75 kW unfiltered","order_no":"6SL3210-1KE12-3UF2","qty":1,"status":"Selected; motor/site validation required","basis":"PROFINET diagnostics; rating provisional until motor nameplate and EMC design"},
    {"tag":"-U101","role":"Pump drive","manufacturer":"Siemens","model":"SINAMICS G120C PN 0.75 kW unfiltered","order_no":"6SL3210-1KE12-3UF2","qty":1,"status":"Selected; motor/site validation required","basis":"PROFINET diagnostics; rating provisional until pump/motor data"},
    {"tag":"-PC200","role":"Vision edge compute","manufacturer":"NVIDIA","model":"Jetson Orin NX 16GB module on industrial carrier","order_no":"Carrier/integration SKU TBD","qty":1,"status":"Architecture selection; procurement decision open","basis":"DeepStream-supported Jetson Orin; carrier, thermal, EMC and lifecycle require supplier confirmation"},
    {"tag":"-SW100","role":"Managed Industrial Ethernet switch","manufacturer":"Siemens","model":"SCALANCE XC208 managed","order_no":"6GK5208-0BA00-2AC2","qty":1,"status":"Provisional selected architecture; procurement and native configuration open","basis":"Managed 8-port switch with VLAN support; paired with an industrial firewall/router for inter-zone traffic"},
    {"tag":"-FW100","role":"Industrial firewall/router","manufacturer":"Siemens","model":"SCALANCE S615 EEC","order_no":"6GK5615-0AA01-2AA2","qty":1,"status":"Provisional selected architecture; procurement and native configuration open","basis":"Routes explicitly allowed traffic between cell zones and enforces deny-by-default firewall policy"},
]

io = []
def add_io(symbol, direction, address, module, channel, device, description, default="FALSE", safety="Standard control"):
    io.append({"symbol":symbol,"direction":direction,"address":address,"module":module,"channel":channel,"device":device,"description":description,"safe_default":default,"classification":safety})

di = [
 ("SAFETY_OK","I0.0","-A102","0","Safety relay mirror","External safety chain healthy (monitor only)"),
 ("GUARD_CLOSED_STATUS","I0.1","-A102","1","Guard circuit mirror","Guard status monitor only"),
 ("AIR_PRESSURE_OK","I0.2","-A102","2","-B100","Pneumatic pressure switch"),
 ("PRODUCT_SUPPLY_OK","I0.3","-A102","3","-B101","Product supply permissive"),
 ("CONVEYOR_READY","I0.4","-A102","4","-U100","Conveyor VFD ready"),
 ("CONVEYOR_RUNNING","I0.5","-A102","5","-U100","Conveyor VFD running"),
 ("CONVEYOR_FAULT","I0.6","-A102","6","-U100","Conveyor VFD fault"),
 ("PUMP_READY","I0.7","-A102","7","-U101","Pump VFD ready"),
 ("PUMP_RUNNING","I1.0","-A102","8","-U101","Pump VFD running"),
 ("PUMP_FAULT","I1.1","-A102","9","-U101","Pump VFD fault"),
 ("BOTTLE_AT_NEST_1","I1.2","-A102","10","-B110","Bottle 1 position sensor"),
 ("BOTTLE_AT_NEST_2","I1.3","-A102","11","-B111","Bottle 2 position sensor"),
 ("GATE_OPEN_FB","I1.4","-A102","12","-B120","Gate open feedback"),
 ("GATE_CLOSED_FB","I1.5","-A102","13","-B121","Gate closed feedback"),
 ("CLAMP_RELEASED_FB","I1.6","-A102","14","-B122","Clamp released feedback"),
 ("CLAMP_ENGAGED_FB","I1.7","-A102","15","-B123","Clamp engaged feedback"),
 ("FILL_VALVE_1_CLOSED_FB","I2.0","-A102","16","-B130","Valve 1 closed proof"),
 ("FILL_VALVE_2_CLOSED_FB","I2.1","-A102","17","-B131","Valve 2 closed proof"),
 ("CAPPER_READY","I2.2","-A102","18","-IF140","Capping station ready"),
 ("CAPPER_BUSY","I2.3","-A102","19","-IF140","Capping station busy"),
 ("CAPPER_COMPLETE","I2.4","-A102","20","-IF140","Capping complete acknowledgement"),
 ("CAPPER_FAULT","I2.5","-A102","21","-IF140","Capping fault"),
 ("LOCAL_RESET_PB","I2.6","-A102","22","-S100","Local reset pushbutton"),
 ("LOCAL_STOP_PB","I2.7","-A102","23","-S101","Local controlled-stop pushbutton"),
]
for row in di: add_io(row[0],"DI",row[1],row[2],row[3],row[4],row[5])
for n in range(24,32): add_io(f"DI_SPARE_{n-23:02d}","DI",f"I{n//8}.{n%8}","-A102",str(n),"SPARE","Allocated spare input")

do = [
 ("CONVEYOR_RUN_CMD","Q0.0","-K200","Conveyor run relay"),("PUMP_RUN_CMD","Q0.1","-K201","Pump run relay"),
 ("FILL_VALVE_1_OPEN_CMD","Q0.2","-K202","Valve 1 interposing relay"),("FILL_VALVE_2_OPEN_CMD","Q0.3","-K203","Valve 2 interposing relay"),
 ("GATE_OPEN_CMD","Q0.4","-K204","Gate open relay"),("GATE_CLOSE_CMD","Q0.5","-K205","Gate close relay"),
 ("CLAMP_ENGAGE_CMD","Q0.6","-K206","Clamp engage relay"),("CLAMP_RELEASE_CMD","Q0.7","-K207","Clamp release relay"),
 ("CAPPER_REQUEST","Q1.0","-K208","Capping request relay"),("STACK_GREEN","Q1.1","-K209","Green beacon relay"),
 ("STACK_AMBER","Q1.2","-K210","Amber beacon relay"),("STACK_RED","Q1.3","-K211","Red beacon relay"),
 ("AUDIBLE_ALARM","Q1.4","-K212","Sounder relay"),("CAMERA_LIGHT_ENABLE","Q1.5","-K213","Vision lighting relay"),
]
for index,row in enumerate(do): add_io(row[0],"DO",row[1],"-A103",str(index),row[2],row[3])
for n in range(len(do),32): add_io(f"DO_SPARE_{n-len(do)+1:02d}","DO",f"Q{n//8}.{n%8}","-A103",str(n),"SPARE","Allocated spare output")
add_io("FLOW_1_MA_RAW","AI","IW64","-A104","0","-FT100","Flow channel 1 instantaneous 4–20 mA","0")
add_io("FLOW_2_MA_RAW","AI","IW66","-A104","1","-FT101","Flow channel 2 instantaneous 4–20 mA","0")
for n in range(2,8): add_io(f"AI_SPARE_{n-1:02d}","AI",f"IW{64+2*n}","-A104",str(n),"SPARE","Allocated spare analog input","0")
add_io("FLOW_1_PULSE","HSC","TM1.CH0.A","-A101","CH0 A","-FT100","24 V pulse input channel 1","0")
add_io("FLOW_2_PULSE","HSC","TM1.CH1.A","-A101","CH1 A","-FT101","24 V pulse input channel 2","0")

vision_plc = [
 ("VISION_ENABLE","BOOL","PLC","Enable inspection service"),("INSPECTION_TRIGGER","BOOL","PLC","One-shot request"),
 ("INSPECTION_ID","UDINT","PLC","Monotonic correlation identifier"),("RECIPE_ID","UINT","PLC","Active recipe identifier"),
 ("EXPECTED_BOTTLES","USINT","PLC","Expected count; fixed at 2 for production"),("TARGET_FILL_LEVEL","REAL","PLC","Normalized visible target"),
 ("PLC_HEARTBEAT","UDINT","PLC","Monotonic heartbeat counter"),
 ("VISION_READY","BOOL","NVIDIA","Pipeline and model ready"),("VISION_BUSY","BOOL","NVIDIA","Request in progress"),
 ("RESULT_VALID","BOOL","NVIDIA","Result payload is complete"),("RESULT_ID","UDINT","NVIDIA","Echoed correlation identifier"),
 ("BOTTLE_1_PASS","BOOL","NVIDIA","Bottle 1 quality decision"),("BOTTLE_2_PASS","BOOL","NVIDIA","Bottle 2 quality decision"),
 ("FILL_1_STATUS","USINT","NVIDIA","0 unknown, 1 under, 2 in-range, 3 over"),("FILL_2_STATUS","USINT","NVIDIA","0 unknown, 1 under, 2 in-range, 3 over"),
 ("LEAK_OR_SPILL_DETECTED","BOOL","NVIDIA","Visible leak/spill indication"),("LOW_CONFIDENCE","BOOL","NVIDIA","Confidence below validated threshold"),
 ("VISION_WARNING","BOOL","NVIDIA","Degraded but communicating"),("VISION_FAULT","BOOL","NVIDIA","Blocking internal fault"),
 ("INFERENCE_TIME","UDINT","NVIDIA","Measured pipeline time in milliseconds"),("VISION_HEARTBEAT","UDINT","NVIDIA","Monotonic heartbeat counter"),
]
vision = [{"signal":a,"data_type":b,"owner":c,"meaning":d,"transport":"OPC UA subscribed/published node","timeout_ms":1000 if a in {"RESULT_VALID","VISION_HEARTBEAT"} else 0} for a,b,c,d in vision_plc]

alarms = [
 (1001,"Emergency/safety chain not healthy","Fault","Controlled stop; outputs de-energized; manual reset after external safety restored"),
 (1002,"Air pressure lost","Fault","Abort fill; close valves; stop pump; hold bottles"),(1003,"Product supply lost","Fault","Abort fill and hold"),
 (1101,"Conveyor VFD fault","Fault","Stop cycle and hold"),(1102,"Pump VFD fault","Fault","Close valves immediately; stop request; hold"),
 (1201,"Gate motion timeout or contradictory feedback","Fault","Stop conveyor; hold"),(1202,"Clamp motion timeout or contradictory feedback","Fault","Stop pump; close valves; hold"),
 (1301,"Fill channel 1 no flow","Fault","Close valve 1; stop pump when both closed; hold"),(1302,"Fill channel 2 no flow","Fault","Close valve 2; stop pump when both closed; hold"),
 (1303,"Flow pulse/analog disagreement","Fault","Close affected valve; quality hold"),(1304,"Underfill detected","Fault","Quality hold"),
 (1305,"Overfill detected","Fault","Close affected valve; quality hold"),(1306,"Valve fails to close","Fault","Stop pump; close both command paths; quality hold"),
 (1401,"Capping station unavailable or timeout","Fault","Keep pair controlled; operator disposition"),(1402,"Capping station fault","Fault","Keep pair controlled"),
 (1501,"Vision not ready","Fault","Do not transfer; quality hold"),(1502,"Vision result timeout","Fault","Do not transfer; quality hold"),
 (1503,"Vision result ID stale or contradictory","Fault","Discard result; quality hold"),(1504,"Vision low confidence","Warning","Quality hold; operator inspection required"),
 (1505,"Vision heartbeat lost","Fault","Quality hold"),(1506,"Vision reports one or both bottles failed","Fault","Quality hold"),
 (1601,"HMI communications lost","Warning","Continue only autonomous safe state; no new HMI command accepted"),
]
alarms_rows = [{"alarm_id":n,"message":m,"class":c,"response":r,"ack_required":"Yes","reset_condition":"Cause cleared and explicit reset; never automatic restart"} for n,m,c,r in alarms]

requirements = []
for idx, text in enumerate([
 "Receive and index exactly two bottles","Confirm both bottle positions before filling","Stop conveyor before clamp engagement","Confirm gate and clamp feedback without contradiction",
 "Zero and accumulate two independent high-speed pulse totals","Start common pump only with both fill paths permissive","Close each fail-closed valve independently at target",
 "Scale and diagnose two 4–20 mA flow channels","Detect no-flow, leakage, overfill, underfill and channel disagreement","Apply configurable drip-settle time",
 "Trigger vision using a monotonic inspection ID","Correlate result ID and reject stale or contradictory results","Hold product on missing, uncertain, failed or low-confidence vision result",
 "Transfer only when process and quality acceptance are both true","Exchange ready, busy, request, complete and fault with capper","Prevent unintended restart following power or control recovery",
 "Provide Auto, Manual/Setup, Holding, Controlled Stop, Fault and Recovery states","Separate commands, feedbacks, permissives, interlocks, faults, warnings and diagnostics",
 "Monitor external safety status only; standard PLC and AI are not safety functions","Provide first-out fault capture and separate alarm acknowledgement from reset",
 "Provide permission-controlled HMI commands with feedback and disabled reason","Provide deterministic simulator and fault-injection regression suite","Maintain canonical tags across I/O, HMI, electrical, AI and tests",
 "Provide backup, restore and release-manifest procedure","No physical reject device is included; operator disposition is required",
], start=1): requirements.append({"requirement_id":f"SYS-{idx:03d}","requirement":text,"verification":"Review + deterministic simulation where applicable","status":"Implemented in reviewable sources; native Siemens verification blocked"})

scenarios = [
 "normal_two_bottle_cycle","single_missing_bottle","both_bottles_missing","bottle_sensor_stuck_on","bottle_sensor_stuck_off","gate_timeout","clamp_timeout","contradictory_actuator_feedback","flow_channel_no_pulse","flow_analog_pulse_disagreement","underfill","overfill","valve_fails_to_close","pump_vfd_fault","conveyor_vfd_fault","air_pressure_loss","product_supply_loss","capper_not_ready","capper_busy_timeout","capper_fault","hmi_communications_loss","vision_not_ready","vision_result_timeout","stale_inspection_id","low_confidence_inspection","one_bottle_fails","vision_heartbeat_loss","plc_heartbeat_loss","power_loss_during_filling","power_restoration","reset_no_restart","manual_mode_interlocks"
]
tests = [{"test_id":f"TC-{i:03d}","scenario":s,"method":"Deterministic Python simulation","expected":"Normal cycle releases only for normal scenario; every injected blocking condition enters HOLD or FAULT with pump/valves off","native_plcsim":"NOT RUN"} for i,s in enumerate(scenarios,1)]

canonical = {"project":{"id":"FC01","revision":"C","date":"2026-08-02","notice":NOTICE,"safety_boundary":SAFETY,"status":"PARTIALLY COMPLETE"},"states":["UNINITIALIZED","INITIALIZING","STOPPED","READY","AUTOMATIC","MANUAL_SETUP","HOLDING","CONTROLLED_STOPPING","FAULTED","RECOVERY_RESET"],"hardware":hardware,"io":io,"vision_interface":vision,"alarms":alarms_rows,"requirements":requirements,"tests":tests,"network":[
 {"node":"PLC-A100","ip":"192.168.10.10","vlan":"10","owner":"Controls","role":"PROFINET controller / OPC UA server"},
 {"node":"HMI-H100","ip":"192.168.10.20","vlan":"10","owner":"Controls","role":"Unified operator panel"},
 {"node":"VFD-U100","ip":"192.168.10.31","vlan":"10","owner":"Drives","role":"Conveyor G120C PN"},
 {"node":"VFD-U101","ip":"192.168.10.32","vlan":"10","owner":"Drives","role":"Pump G120C PN"},
 {"node":"VISION-PC200","ip":"192.168.20.10","vlan":"20","owner":"Vision","role":"OPC UA client + inference"},
 {"node":"ENG-SERVICE","ip":"DHCP/reserved","vlan":"99","owner":"Engineering","role":"Temporary service access; disabled in production"}],
 "controlled_rules":{"tag":"=FC01+<location>-<class><nnn>","legacy_mapping":"Primary IEC/ISO designation retained; secondary semantic names become PLC symbols","alarm_ranges":"1000 safety/utilities, 1100 drives, 1200 motion, 1300 filling, 1400 capper, 1500 vision, 1600 communications"}}
write("00_project_control/canonical_model.json", json.dumps(canonical, indent=2, ensure_ascii=False))

csv_write("10_schedules/siemens_hardware.csv", hardware)
csv_write("10_schedules/plc_io.csv", io)
csv_write("10_schedules/nvidia_interface_tags.csv", vision)
csv_write("10_schedules/alarms.csv", alarms_rows)
csv_write("10_schedules/requirements_traceability.csv", requirements)
csv_write("10_schedules/test_coverage.csv", tests)
csv_write("10_schedules/network_nodes.csv", canonical["network"])

terminal_rows=[]; cable_rows=[]; wire_rows=[]
for idx,row in enumerate([r for r in io if r["direction"] in {"DI","DO","AI","HSC"}],1):
    terminal=f"X{100 + (idx-1)//24}:{(idx-1)%24+1}"
    terminal_rows.append({"terminal":terminal,"symbol":row["symbol"],"plc_address":row["address"],"device":row["device"],"potential":"24VDC/0V" if row["direction"] in {"DI","DO","HSC"} else "4-20mA isolated loop","status":"Inherited concept; final QET Siemens upgrade open"})
    wire_rows.append({"wire_no":f"W{idx:04d}","from":terminal,"to":f"{row['module']}:{row['channel']}","symbol":row["symbol"],"color":"BK" if row["direction"]!="AI" else "BU","cross_section_mm2":"0.75" if row["direction"]!="AI" else "0.5 shielded"})
for n,device in enumerate(["-B100","-B101","-B110","-B111","-B120","-B121","-B122","-B123","-B130","-B131","-FT100","-FT101","-IF140","-PC200","-CAM200","-LT200"],1):
    cable_rows.append({"cable_id":f"W{200+n:03d}","device":device,"cores":"4" if device.startswith("-B") else "8","type":"Shielded instrumentation" if device.startswith("-FT") or device.startswith("-CAM") else "Industrial control","termination":"Both ends identified; analog shield at panel PE/shield clamp","status":"Preliminary"})
csv_write("10_schedules/terminal_plan.csv",terminal_rows); csv_write("10_schedules/wire_list.csv",wire_rows); csv_write("10_schedules/cable_schedule.csv",cable_rows)

load_rows=[
 {"load":"PLC CPU and I/O","voltage":"24 VDC","nominal_w":55,"demand_factor":1.0,"demand_w":55,"basis":"Preliminary allowance; verify Siemens configuration"},
 {"load":"HMI","voltage":"24 VDC","nominal_w":24,"demand_factor":1.0,"demand_w":24,"basis":"Maximum current allowance from product data"},
 {"load":"Relays, sensors and solenoids","voltage":"24 VDC","nominal_w":150,"demand_factor":0.8,"demand_w":120,"basis":"Duty-cycle allowance; inrush not finalized"},
 {"load":"Vision edge + camera + lighting","voltage":"24 VDC","nominal_w":100,"demand_factor":1.0,"demand_w":100,"basis":"Placeholder engineering allowance pending carrier/camera selection"},
 {"load":"24 VDC subtotal","voltage":"24 VDC","nominal_w":329,"demand_factor":1.0,"demand_w":299,"basis":"12.46 A demand; retain >=25% margin; select 20 A PSU after inrush check"},
 {"load":"Conveyor drive","voltage":"400 VAC","nominal_w":750,"demand_factor":1.0,"demand_w":750,"basis":"Motor nameplate not supplied"},
 {"load":"Pump drive","voltage":"400 VAC","nominal_w":750,"demand_factor":1.0,"demand_w":750,"basis":"Pump curve/motor nameplate not supplied"},
]
csv_write("10_schedules/load_budget.csv",load_rows)
panel=[
 {"tag":h["tag"],"x_mm":80+(i%5)*130,"y_mm":80+(i//5)*180,"width_mm":110,"height_mm":150,"depth_mm":170,"zone":"Controls" if i<6 else "Drives/vision","model_status":"Envelope only; native CAD baseline predates selection"} for i,h in enumerate(hardware)
]
csv_write("10_schedules/panel_placement.csv",panel)
csv_write("10_schedules/bom.csv",[{"tag":h["tag"],"description":h["model"],"manufacturer":h["manufacturer"],"order_no":h["order_no"],"qty":h["qty"],"procurement_status":h["status"]} for h in hardware])
csv_write("10_schedules/vfd_parameters.csv",[
 {"drive":"-U100","parameter":"Control source","value":"PROFINET telegram","status":"Startdrive entry pending native project"},{"drive":"-U100","parameter":"Rated power","value":"0.75 kW provisional","status":"Verify motor nameplate"},
 {"drive":"-U101","parameter":"Control source","value":"PROFINET telegram","status":"Startdrive entry pending native project"},{"drive":"-U101","parameter":"Rated power","value":"0.75 kW provisional","status":"Verify motor/pump data"},
 {"drive":"Both","parameter":"STO","value":"External conceptual safety interface only","status":"No safety claim; qualified design required"}])
csv_write("10_schedules/hmi_tags.csv",[{"hmi_tag":r["symbol"],"plc_source":r["symbol"],"access":"Read" if r["direction"]!="DO" else "Read/command handshake","screen":"Diagnostics" if r["direction"]!="DO" else "Manual/Overview","role":"Operator" if r["direction"]!="DO" else "Maintenance for manual commands","disabled_reason":"Interlock/permissive/state reason from HMI interface DB"} for r in io])

baseline = """## Baseline approval state

The controlled baseline is revision C. It retains the primary package's IEC 81346-style designation system and quarantined historical QElectroTech/FreeCAD artifacts; the revision-C overlay corrects and expands the implementation before the generator exits.

### Machine boundary

Included: infeed/indexing, gate, clamp, common pump, two independent fill channels, capping handshake, bounded NVIDIA inspection, panel/control power, HMI, drives, standard-control diagnostics and deterministic simulator. Excluded: upstream/downstream mechanics, utilities generation, legal metrology, physical reject, credited safety design, sanitary process qualification and physical commissioning.

### Approved control principles

1. Fail-closed fill valves and pump stop on every blocking fill condition.
2. Each channel closes independently at target pulses; analog flow is a plausibility channel, not the dose total.
3. Any uncertain vision outcome produces HOLDING; only explicit operator disposition can release/recover.
4. Recovery/reset returns to STOPPED and never commands automatic restart.
5. External safety system removes hazardous energy; PLC and AI only observe non-safety status.
"""
write("00_project_control/design_basis.md",doc("System design basis",baseline))
write("README.md",doc("Industry-grade Siemens/NVIDIA compact filling cell", """This repository is the integrated revision-C engineering package. Siemens sources are reviewable exports, not a native TIA project. The inherited QElectroTech and FreeCAD baselines are genuine and were previously reopened in their native applications; they predate the final Siemens/NVIDIA selection and are quarantined under `native_baseline` so they cannot be mistaken for the completed upgrade.

## Current status

**PARTIALLY COMPLETE.** Canonical engineering data, modular Siemens-oriented SCL, HMI specification, drive philosophy, deterministic simulator, PLC–AI contract, DeepStream deployment configuration, schedules, traceability and release controls are implemented. Mandatory native TIA/WinCC/Startdrive/PLCSIM, trained-model, upgraded-QET and revised-CAD gates remain incomplete.

## Reproduce

```powershell
python scripts/build_project.py
python -m unittest discover -s 11_simulation/tests -v
python 11_simulation/run_scenarios.py
python scripts/validate_project.py
```

See `release/RELEASE_NOTES.md` and `14_qa/acceptance_gate_status.md` before use."""))

write("AGENTS.md",f"""# Project engineering controls

> {NOTICE}

> {SAFETY}

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
""")

write("00_project_control/delivery_plan.md",doc("Delivery plan and work breakdown", """| WBS | Workstream | Owner | Inputs | Outputs | Acceptance | Dependency |
|---|---|---|---|---|---|---|
| 1 | Baseline and canonical model | Chief systems | Both legacy packages | Requirements, tags, interfaces | Consistency validator passes | None |
| 2 | Electrical and panel | Electrical | WBS 1, selected hardware | QET, schedules, CAD | Native reopen and continuity review | WBS 1 |
| 3 | Siemens implementation | Siemens | WBS 1–2 | TIA/PLC/HMI/drive | Compile and PLCSIM evidence | Licensed TIA |
| 4 | NVIDIA vision | Vision | WBS 1, optics study, dataset | Model and deployment | Traceable metrics and interface tests | Data + NVIDIA GPU |
| 5 | Simulation/twin | Simulation | Interfaces and CAD | Process simulator; USD if available | Regression suite; USD reopen | WBS 1; Omniverse optional |
| 6 | Independent V&V/release | V&V + Chief | All workstreams | Gate report and manifest | No unreported blocker | WBS 1–5 |

Escalation: record the blocker and evidence in `open_issues.csv`; continue independent work; only the chief engineer approves controlled-item changes or release status."""))
csv_write("00_project_control/agent_ownership.csv",[
 {"role":"Chief systems engineer","paths":"00,01,02,release","review_authority":"Integration and release","exclusive":"Yes"},{"role":"Siemens automation engineer","paths":"04,05,06","review_authority":"No self-approval","exclusive":"Yes"},{"role":"Electrical/panel engineer","paths":"03,09,10 electrical fields","review_authority":"No self-approval","exclusive":"Yes"},{"role":"NVIDIA vision engineer","paths":"07","review_authority":"No self-approval","exclusive":"Yes"},{"role":"Simulation engineer","paths":"08,11","review_authority":"No self-approval","exclusive":"Yes"},{"role":"Independent V&V engineer","paths":"12,14","review_authority":"Acceptance evidence","exclusive":"Yes"}])
csv_write("00_project_control/open_issues.csv",[
 {"issue_id":"OI-001","severity":"Blocking","issue":"TIA Portal V20 is installed, but licence/native access is unproven; current identity lacks Openness authorization; Startdrive and PLCSIM are absent","owner":"Project sponsor / Siemens engineer","closure_evidence":"Licensed V20 project open/compile/archive reports, authorized Openness or manual workflow, Startdrive installation and PLCSIM traces"},
 {"issue_id":"OI-002","severity":"Blocking","issue":"RTX 5060 Laptop GPU is present, but CUDA development stack, TAO, DeepStream, TensorRT, Omniverse/OpenUSD and a real labeled dataset are absent","owner":"Vision engineer","closure_evidence":"Named dataset, installed supported NVIDIA stack, training/evaluation logs, model hash and tested hardware latency"},
 {"issue_id":"OI-003","severity":"Blocking","issue":"Native QET baseline predates final Siemens/NVIDIA hardware and detailed upgrade","owner":"Electrical engineer","closure_evidence":"Updated QET reopen, populated BOM/xrefs, continuity reconciliation and page review"},
 {"issue_id":"OI-004","severity":"Blocking","issue":"Native CAD baseline predates selected hardware envelopes","owner":"Panel engineer","closure_evidence":"Updated FCStd reopen and STEP/IGES/DXF validation"},
 {"issue_id":"OI-005","severity":"High","issue":"Motor, pump, utilities, enclosure environment and site protection data absent","owner":"Project sponsor","closure_evidence":"Approved site and manufacturer data; calculations revised"},
 {"issue_id":"OI-006","severity":"High","issue":"Camera, lens, light, carrier and reject/disposition workflow not physically validated","owner":"Vision/process","closure_evidence":"Optical trial and approved operator disposition procedure"}])
csv_write("00_project_control/revision_history.csv",[{"revision":"A","date":"2026-08-01","description":"Primary electrical/CAD and secondary controls concepts","authority":"Legacy sources"},{"revision":"B","date":"2026-08-02","description":"Integrated Siemens/NVIDIA architecture, canonical model, reviewable sources and deterministic tests","authority":"Chief systems engineer; native gates remain open"}])

write("01_requirements/user_requirements_specification.md",doc("User requirements specification", "\n".join([f"- **{r['requirement_id']}** — {r['requirement']}" for r in requirements]) + "\n\nAcceptance is governed by the traceability and validation matrices; reviewable source is not equivalent to native Siemens verification."))
write("01_requirements/assumption_register.md",doc("Assumption and limitation register", """| ID | Assumption | Impact if false | Required verification |
|---|---|---|---|
| AS-01 | 400/230 VAC TN-S and 24 VDC PELV are available | Protection and PSU architecture changes | Site survey and supply data |
| AS-02 | Two 24 V pulse outputs plus isolated 4–20 mA outputs are available | Counter and AI modules/interface change | Flowmeter data sheet |
| AS-03 | 0.75 kW drives cover conveyor and pump | Drive, cable, protection and heat change | Nameplates and pump curve |
| AS-04 | Bottles are optically transparent enough for visible fill estimation | Vision method/camera/lighting change | Optical feasibility trial |
| AS-05 | External safety system provides a standard diagnostic mirror | Monitoring I/O changes | Qualified safety design |
| AS-06 | Capping interface is dry-contact/24 V PNP compatible | Interface relays/protocol change | Capper ICD |
| AS-07 | OPC UA is permitted across a routed OT quality zone | Protocol/gateway change | Cybersecurity review |
| AS-08 | No automatic physical reject is required | Mechanics, I/O and logic expand | Operational approval |"""))
write("01_requirements/legacy_tag_migration.md",doc("Legacy-to-final tag migration", """| Legacy source | Example | Final rule | Disposition |
|---|---|---|---|
| Primary IEC/ISO designation | `=FC01+OP01-B110` | Retained | Authoritative device tag |
| Secondary semantic tag | `PE_BOTTLE_1` | `BOTTLE_AT_NEST_1` | PLC symbol only; mapped to `-B110` |
| Secondary generic VFD | `VFD_CONVEYOR` | `=FC01+FD01-U100` | Device designation plus `CONVEYOR_*` PLC symbols |
| Secondary AI status | informal JSON fields | Exact ICD names | Replaced by controlled OPC UA data contract |

No legacy PLC address is inherited automatically. Revision-B addresses come only from `canonical_model.json`."""))

arch = """```mermaid
flowchart LR
  F["Field devices"] --> T["Terminals / cables"] --> IO["S7-1500 I/O"] --> EM["Equipment FBs"] --> MC["Machine coordinator"]
  MC <--> HMI["MTP700 Unified HMI"]
  MC <--> VFD["Two G120C PN drives"]
  MC -->|"OPC UA request + ID"| EDGE["Jetson / DeepStream quality zone"]
  EDGE -->|"Correlated bounded result"| MC
  MC <--> CAP["Hardwired capper interface"]
  SIM["Deterministic simulator"] -. "interface mapping; not PLC proof" .-> MC
  CAD["FreeCAD/STEP baseline"] -.-> USD["OpenUSD workflow - not delivered"]
```

The PLC owns sequence, command arbitration, timeouts and final transfer permission. The vision edge owns image acquisition/inference only. The HMI cannot write physical outputs; it issues permission-controlled commands with sequence numbers and receives accepted/rejected feedback plus disabled reasons.

### Network zones

- VLAN 10 cell control: PLC, HMI and drives; no direct enterprise ingress.
- VLAN 20 quality/vision: Jetson and camera; routed to PLC through an allow-listed OPC UA policy.
- VLAN 99 temporary engineering: disabled/isolated in production; time-bounded service access.
- Backups, model updates and logs traverse an authenticated maintenance workflow, never an uncontrolled share.
"""
write("02_system_architecture/system_architecture.md",doc("System architecture",arch))
write("02_system_architecture/interface_control_document.md",doc("Integrated interface-control document", """## Physical and logical chain

Field sensor → identified cable/core → numbered terminal → Siemens module/channel → symbolic PLC tag → equipment FB input → coordinator permissive/interlock → HMI diagnostic. The revision-C schedules are machine-generated from the canonical model.

## PLC–vision contract

Transport selection: OPC UA using fixed node identifiers in a routed quality VLAN. The PLC publishes request data atomically then toggles `INSPECTION_TRIGGER`; NVIDIA latches the payload, sets busy, and publishes the complete result before `RESULT_VALID`. The PLC accepts a result only when `RESULT_VALID`, `RESULT_ID = INSPECTION_ID`, heartbeat is fresh, ready is true, fault is false and all semantic fields are non-contradictory.

Timeout: 1000 ms default, recipe-bounded 250–5000 ms. No retry with the same ID. After timeout the PLC enters HOLDING; a new inspection requires a new monotonic ID and explicit operator action. Byte order for non-OPC-UA fallback is big-endian network order. Heartbeats are UDINT counters updated at 500 ms; unchanged for 1500 ms is failed.

Startup defaults are disabled/not ready/result invalid. Shutdown invalidates results. Model identity and SHA-256 are read-only metadata; a model-loading state keeps `VISION_READY = FALSE`. Communications loss, stale ID, low confidence or contradiction can never grant transfer."""))

adr_text=[]
decisions=[
 ("ADR-001","CPU family","S7-1200, S7-1500, ET 200SP CPU","S7-1500 CPU 1511-1 PN","Diagnostics, modular organization, OPC UA/PROFINET margin","Higher cost and TIA catalog dependency"),
 ("ADR-002","I/O location","Distributed ET 200SP vs local S7-1500","Local S7-1500 modules","Compact single-panel machine, fewer network dependencies","Long field cables; review if machine expands"),
 ("ADR-003","High-speed flow","CPU DI counters vs TM Count","TM Count 2x24V","Two independent dedicated channels and diagnostics","Module configuration must be verified in TIA"),
 ("ADR-004","HMI","Basic/Comfort/Unified","MTP700 Unified Comfort","Diagnostics, roles, reusable faceplates","WinCC Unified licensing and runtime learning curve"),
 ("ADR-005","Drives","Hardwired VFD vs G120C PN","G120C PN with hardwired external STO concept","Integrated diagnostics and Startdrive","Motor/EMC/protection data still required"),
 ("ADR-006","PLC organization","Monolith vs equipment modules","Modular FBs plus coordinator","Cohesion, instance ownership, unit review","More interfaces and DBs"),
 ("ADR-007","State strategy","Implicit rungs vs explicit legal transitions","Explicit coordinator states","Deterministic recovery and diagnostics","Transition table must be maintained"),
 ("ADR-008","Dose measurement","Analog integration vs pulses","Pulses for total; analog for plausibility","Independent totals and cross-check","K-factor and cutoff compensation need trials"),
 ("ADR-009","Vision model","Single classifier vs detection + metrology heads","Two-stage bottle/defect detection plus calibrated fill-line estimator","Separates presence/condition from fill geometry","Requires representative labeled data"),
 ("ADR-010","Optics","Ambient/front light vs controlled backlight + diffuse front","Controlled backlight with diffuse front fill","Improves liquid boundary and gross defect visibility","Bottle/product-specific feasibility trial"),
 ("ADR-011","PLC–AI protocol","Digital I/O, TCP, MQTT, OPC UA","OPC UA with ID/heartbeat contract","Typed data, diagnostics, Siemens/edge support","Certificate and namespace management"),
 ("ADR-012","NVIDIA hardware","dGPU IPC, Jetson AGX, Orin NX","Jetson Orin NX 16GB module on qualified industrial carrier","Compact edge inference and DeepStream support","Carrier/thermal/EMC SKU open"),
 ("ADR-013","Digital twin","Custom 3D only vs OpenUSD","Deterministic simulator plus optional OpenUSD","Separates regression truth from visualization/synthetic data","No USD delivered without Omniverse validation"),
 ("ADR-014","Network","Flat vs zoned","Control, quality and service zones","Limits blast radius and controls updates","Managed routing/firewall design required"),
 ("ADR-015","Data retention","Unlimited images vs event policy","Retain faults/low confidence and sampled passes with expiry","Supports model improvement while bounding storage/privacy","Site policy and capacity needed"),
 ("ADR-016","Failure recovery","Automatic retry/restart vs controlled hold","Hold + explicit disposition/reset to STOPPED","No unintended restart or quality bypass","Operator procedure needed"),
]
for ident,problem,alts,sel,why,cons in decisions:
    adr_text.append(f"## {ident}: {problem}\n\n- **Problem:** Select a maintainable bounded solution.\n- **Alternatives:** {alts}.\n- **Selection criteria:** determinism, diagnostics, maintainability, compatibility, lifecycle, panel impact and verification burden.\n- **Selected:** {sel}.\n- **Justification:** {why}.\n- **Consequences:** {cons}.\n- **Risks/assumptions:** source data and licensed native tool support must be confirmed.\n- **Required verification:** applicable native compile/reopen, vendor compatibility, integration test and independent review.\n")
write("02_system_architecture/architecture_decisions.md",doc("Architecture decision records","\n".join(adr_text)))
write("02_system_architecture/state_and_sequence.md",doc("Machine state and sequence model", """```mermaid
stateDiagram-v2
  [*] --> UNINITIALIZED
  UNINITIALIZED --> INITIALIZING: control power
  INITIALIZING --> STOPPED: diagnostics complete / outputs safe
  STOPPED --> READY: reset + all permissives
  READY --> AUTOMATIC: accepted start edge
  READY --> MANUAL_SETUP: authorized mode request
  AUTOMATIC --> HOLDING: process/quality uncertainty
  AUTOMATIC --> CONTROLLED_STOPPING: stop request
  HOLDING --> RECOVERY_RESET: cause cleared + disposition
  MANUAL_SETUP --> CONTROLLED_STOPPING: exit/stop
  CONTROLLED_STOPPING --> STOPPED: all motion stopped
  FAULTED --> RECOVERY_RESET: fault cleared + reset edge
  RECOVERY_RESET --> STOPPED: outputs safe
  INITIALIZING --> FAULTED: blocking diagnostic
  AUTOMATIC --> FAULTED: equipment fault
```

Automatic sequence: index → verify pair → stop conveyor → close gate → engage clamp → validate feedback → zero two counter channels → start pump → open each valve → close each independently at target → stop pump after both closed → drip settle → request inspection with new ID → accept only a fresh valid result → request capper → wait busy/complete → release clamp/gate and return to indexing. Every timeout names the owning module and first-out diagnostic."""))

write("03_electrical/README.md",doc("Electrical workstream status", """`native_baseline/filling_cell.qet` and its PDF are genuine inherited artifacts from the stronger primary package. They were previously reopened using QElectroTech 0.100.1-dev (24 diagrams, 305 elements, 160 conductors), but they predate the final Siemens/NVIDIA selection. They are quarantined as baseline evidence and are **not** represented as the completed revision-C multiline upgrade.

Revision-B terminal, cable, wire, I/O, load and BOM schedules are in `10_schedules`. Closing OI-003 requires qualified schematic editing, native reopen, populated manufacturer/BOM/xref export, continuity reconciliation and page-by-page visual review."""))
write("03_electrical/electrical_calculations.md",doc("Preliminary electrical calculations", """- 24 VDC connected allowance: 329 W; preliminary demand: 299 W = 12.46 A. A 20 A supply gives 37.7% demand headroom before tolerance/derating; final inrush and ambient derating remain open.
- AC connected motor load: 1.50 kW before auxiliaries. Demand is provisionally 100% because both drives may operate during filling/indexing transitions.
- Voltage-drop design targets: ≤3% branch and ≤5% total; actual lengths, conductor routes and current data are absent, so no conductor size is released.
- Panel heat: treat drive losses, PSU losses and 100 W vision branch allowance as simultaneous; final enclosure thermal model requires ambient, enclosure material/size and manufacturer loss curves.
- Duct fill target ≤40% design occupancy and ≥20% spare terminal capacity. Schedule counts are preliminary until revised QET connectivity is complete.
- No SCCR, short-circuit withstand, selectivity, discrimination or final thermal-compliance claim is made."""))

write("04_controls_siemens/toolchain_status.md",doc("Siemens toolchain and native deliverable status", """The authoritative target is **TIA Portal V20**, executable and TIA Openness assembly version `2000.0.9501.1`. Installed component evidence includes STEP 7 V20 and WinCC V20. TIA Portal V16 is also present but is not the target. Usable product licence entitlement was not proven, the current process identity is not a member of the `Siemens TIA Openness` group, and no interactive V20 project operation was executed.

Startdrive and PLCSIM/PLCSIM Advanced are not installed. Therefore no `.ap*` or `.zap*` is delivered and no hardware/PLC/HMI compile, cross-reference, drive configuration, trace, PLCSIM or archive-restore claim is made. The `scl/` sources require import, hardware binding and compilation in licensed TIA Portal V20; selected device catalog compatibility must be confirmed during that native build."""))

types_scl=f'''// {NOTICE}\nTYPE "UDT_Recipe"\nVERSION : 0.1\n   STRUCT\n      RecipeId : UInt;\n      TargetPulsesCh1 : UDInt;\n      TargetPulsesCh2 : UDInt;\n      PulsesPerLitreCh1 : Real;\n      PulsesPerLitreCh2 : Real;\n      NoFlowTimeout : Time;\n      FillTimeout : Time;\n      DripSettleTime : Time;\n      VisionTimeout : Time;\n      TargetFillLevel : Real;\n   END_STRUCT;\nEND_TYPE\n\nTYPE "UDT_VisionResult"\nVERSION : 0.1\n   STRUCT\n      ResultValid : Bool; ResultId : UDInt; Bottle1Pass : Bool; Bottle2Pass : Bool;\n      Fill1Status : USInt; Fill2Status : USInt; LeakOrSpill : Bool; LowConfidence : Bool;\n      Warning : Bool; Fault : Bool; InferenceTimeMs : UDInt;\n   END_STRUCT;\nEND_TYPE\n'''
write("04_controls_siemens/scl/00_types.scl",types_scl)
write("04_controls_siemens/scl/FB_VFD.scl",f'''// {NOTICE}\nFUNCTION_BLOCK "FB_VFD"\nVAR_INPUT Enable : Bool; RunRequest : Bool; Ready : Bool; Running : Bool; FaultIn : Bool; ResetEdge : Bool; StartTimeout : Time; END_VAR\nVAR_OUTPUT RunCmd : Bool; Permissive : Bool; Fault : Bool; DiagCode : UInt; END_VAR\nVAR tStart : TON; END_VAR\nBEGIN\n  #Permissive := #Enable AND #Ready AND NOT #FaultIn;\n  #RunCmd := #RunRequest AND #Permissive AND NOT #Fault;\n  #tStart(IN := #RunCmd AND NOT #Running, PT := #StartTimeout);\n  IF #FaultIn THEN #Fault := TRUE; #DiagCode := 16#1101; END_IF;\n  IF #tStart.Q THEN #Fault := TRUE; #DiagCode := 16#1102; END_IF;\n  IF #ResetEdge AND NOT #FaultIn AND NOT #RunRequest THEN #Fault := FALSE; #DiagCode := 0; END_IF;\nEND_FUNCTION_BLOCK''')
write("04_controls_siemens/scl/FB_Actuator2Pos.scl",f'''// {NOTICE}\nFUNCTION_BLOCK "FB_Actuator2Pos"\nVAR_INPUT Enable : Bool; CmdToA : Bool; CmdToB : Bool; AtA : Bool; AtB : Bool; ResetEdge : Bool; TravelTime : Time; END_VAR\nVAR_OUTPUT OutToA : Bool; OutToB : Bool; InPosition : Bool; Fault : Bool; DiagCode : UInt; END_VAR\nVAR tTravel : TON; motion : Bool; END_VAR\nBEGIN\n  IF #AtA AND #AtB THEN #Fault := TRUE; #DiagCode := 16#1201; END_IF;\n  #OutToA := #Enable AND #CmdToA AND NOT #CmdToB AND NOT #Fault;\n  #OutToB := #Enable AND #CmdToB AND NOT #CmdToA AND NOT #Fault;\n  IF #CmdToA AND #CmdToB THEN #Fault := TRUE; #DiagCode := 16#1202; END_IF;\n  #motion := (#OutToA AND NOT #AtA) OR (#OutToB AND NOT #AtB);\n  #tTravel(IN := #motion, PT := #TravelTime);\n  IF #tTravel.Q THEN #Fault := TRUE; #DiagCode := 16#1203; END_IF;\n  #InPosition := (#CmdToA AND #AtA AND NOT #AtB) OR (#CmdToB AND #AtB AND NOT #AtA);\n  IF #ResetEdge AND NOT (#AtA AND #AtB) AND NOT (#CmdToA OR #CmdToB) THEN #Fault := FALSE; #DiagCode := 0; END_IF;\nEND_FUNCTION_BLOCK''')
write("04_controls_siemens/scl/FB_FillChannel.scl",f'''// {NOTICE}\nFUNCTION_BLOCK "FB_FillChannel"\nVAR_INPUT Enable : Bool; StartEdge : Bool; Abort : Bool; ResetEdge : Bool; PulseTotal : UDInt; TargetPulses : UDInt; Flow_mA : Real; ValveClosedFb : Bool; NoFlowTimeout : Time; FillTimeout : Time; END_VAR\nVAR_OUTPUT ValveOpenCmd : Bool; Done : Bool; Fault : Bool; Underfill : Bool; Overfill : Bool; DiagCode : UInt; END_VAR\nVAR tNoFlow : TON; tFill : TON; startCount : UDInt; active : Bool; lastCount : UDInt; END_VAR\nBEGIN\n  IF #StartEdge AND #Enable AND #ValveClosedFb AND (#TargetPulses > 0) THEN #active := TRUE; #Done := FALSE; #startCount := #PulseTotal; #lastCount := #PulseTotal; END_IF;\n  #ValveOpenCmd := #active AND NOT #Abort AND NOT #Fault AND ((#PulseTotal - #startCount) < #TargetPulses);\n  #tNoFlow(IN := #ValveOpenCmd AND (#PulseTotal = #lastCount) AND (#Flow_mA < 4.2), PT := #NoFlowTimeout);\n  #tFill(IN := #active, PT := #FillTimeout);\n  IF #tNoFlow.Q THEN #Fault := TRUE; #DiagCode := 16#1301; END_IF;\n  IF #tFill.Q THEN #Fault := TRUE; #DiagCode := 16#1302; END_IF;\n  IF #active AND ((#PulseTotal - #startCount) >= #TargetPulses) THEN #active := FALSE; #Done := TRUE; END_IF;\n  IF #Abort OR #Fault THEN #active := FALSE; #ValveOpenCmd := FALSE; END_IF;\n  IF NOT #ValveOpenCmd AND NOT #ValveClosedFb AND (#Done OR #Abort) THEN #Fault := TRUE; #DiagCode := 16#1306; END_IF;\n  IF #ResetEdge AND NOT #active THEN #Fault := FALSE; #Done := FALSE; #Underfill := FALSE; #Overfill := FALSE; #DiagCode := 0; END_IF;\n  #lastCount := #PulseTotal;\nEND_FUNCTION_BLOCK''')
write("04_controls_siemens/scl/FB_VisionInterface.scl",f'''// {NOTICE}\nFUNCTION_BLOCK "FB_VisionInterface"\nVAR_INPUT Enable : Bool; TriggerEdge : Bool; InspectionId : UDInt; Ready : Bool; Busy : Bool; Result : "UDT_VisionResult"; Heartbeat : UDInt; Timeout : Time; ResetEdge : Bool; END_VAR\nVAR_OUTPUT Trigger : Bool; Accepted : Bool; QualityPass : Bool; HoldRequired : Bool; Fault : Bool; DiagCode : UInt; END_VAR\nVAR tResult : TON; pending : Bool; latchedId : UDInt; lastHeartbeat : UDInt; tHeartbeat : TON; END_VAR\nBEGIN\n  #Trigger := FALSE; #Accepted := FALSE;\n  IF #TriggerEdge AND #Enable AND #Ready AND NOT #Busy AND NOT #pending THEN #pending := TRUE; #latchedId := #InspectionId; #Trigger := TRUE; END_IF;\n  #tResult(IN := #pending, PT := #Timeout);\n  #tHeartbeat(IN := (#Heartbeat = #lastHeartbeat), PT := T#1500ms);\n  IF #pending AND #Result.ResultValid THEN\n    IF #Result.ResultId <> #latchedId THEN #Fault := TRUE; #HoldRequired := TRUE; #DiagCode := 16#1503;\n    ELSIF #Result.Fault OR #Result.LowConfidence OR #Result.LeakOrSpill OR NOT (#Result.Bottle1Pass AND #Result.Bottle2Pass) OR (#Result.Fill1Status <> 2) OR (#Result.Fill2Status <> 2) THEN\n      #Accepted := TRUE; #QualityPass := FALSE; #HoldRequired := TRUE; #pending := FALSE; #DiagCode := 16#1504;\n    ELSE #Accepted := TRUE; #QualityPass := TRUE; #HoldRequired := FALSE; #pending := FALSE; #DiagCode := 0; END_IF;\n  END_IF;\n  IF #tResult.Q OR #tHeartbeat.Q OR NOT #Ready THEN #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; IF #tResult.Q THEN #DiagCode := 16#1502; ELSE #DiagCode := 16#1505; END_IF; END_IF;\n  IF #ResetEdge AND NOT #pending AND #Ready THEN #Fault := FALSE; #QualityPass := FALSE; #HoldRequired := FALSE; #DiagCode := 0; END_IF;\n  #lastHeartbeat := #Heartbeat;\nEND_FUNCTION_BLOCK''')
write("04_controls_siemens/scl/FB_RecipeManager.scl",f'''// {NOTICE}\nFUNCTION_BLOCK "FB_RecipeManager"\nVAR_INPUT Candidate : "UDT_Recipe"; ApplyEdge : Bool; MachineStopped : Bool; END_VAR\nVAR_OUTPUT Active : "UDT_Recipe"; Valid : Bool; Rejected : Bool; END_VAR\nBEGIN\n  #Valid := (#Candidate.TargetPulsesCh1 >= 100) AND (#Candidate.TargetPulsesCh1 <= 10000000) AND (#Candidate.TargetPulsesCh2 >= 100) AND (#Candidate.TargetPulsesCh2 <= 10000000) AND (#Candidate.TargetFillLevel >= 0.1) AND (#Candidate.TargetFillLevel <= 0.95);\n  #Rejected := #ApplyEdge AND (NOT #MachineStopped OR NOT #Valid);\n  IF #ApplyEdge AND #MachineStopped AND #Valid THEN #Active := #Candidate; END_IF;\nEND_FUNCTION_BLOCK''')
write("04_controls_siemens/scl/FB_AlarmManager.scl",f'''// {NOTICE}\nFUNCTION_BLOCK "FB_AlarmManager"\nVAR_INPUT ActiveFaults : Array[0..31] of Bool; FaultCodes : Array[0..31] of UInt; AckEdge : Bool; ResetEdge : Bool; END_VAR\nVAR_OUTPUT AnyFault : Bool; FirstOutCode : UInt; Acknowledged : Bool; END_VAR\nVAR i : Int; latched : Bool; END_VAR\nBEGIN\n  #AnyFault := FALSE; FOR #i := 0 TO 31 DO #AnyFault := #AnyFault OR #ActiveFaults[#i]; IF #ActiveFaults[#i] AND NOT #latched THEN #FirstOutCode := #FaultCodes[#i]; #latched := TRUE; END_IF; END_FOR;\n  IF #AckEdge THEN #Acknowledged := TRUE; END_IF;\n  IF #ResetEdge AND NOT #AnyFault THEN #latched := FALSE; #FirstOutCode := 0; #Acknowledged := FALSE; END_IF;\nEND_FUNCTION_BLOCK''')
write("04_controls_siemens/scl/FB_MachineCoordinator.scl", f'''// {NOTICE}\nFUNCTION_BLOCK "FB_MachineCoordinator"\nVAR_INPUT InitDone : Bool; PermissivesOk : Bool; StartEdge : Bool; StopEdge : Bool; ResetEdge : Bool; ManualRequest : Bool; PairPresent : Bool; GateClosed : Bool; ClampEngaged : Bool; Fill1Done : Bool; Fill2Done : Bool; DripDone : Bool; VisionAccepted : Bool; VisionPass : Bool; CapperReady : Bool; CapperComplete : Bool; BlockingFault : Bool; END_VAR\nVAR_OUTPUT State : UInt; IndexRequest : Bool; GateCloseRequest : Bool; ClampRequest : Bool; FillStartPulse : Bool; VisionRequestPulse : Bool; CapperRequest : Bool; QualityHold : Bool; END_VAR\nVAR step : UInt; END_VAR\nBEGIN\n  #FillStartPulse := FALSE;\n  #VisionRequestPulse := FALSE;\n  CASE #State OF\n    0: IF #InitDone THEN #State := 10; END_IF;\n    10: IF #BlockingFault THEN #State := 80; ELSIF #PermissivesOk THEN #State := 20; END_IF;\n    20: #step := 0; IF #ResetEdge AND #PermissivesOk THEN #State := 30; END_IF;\n    30: IF #ManualRequest THEN #State := 50; ELSIF #StartEdge THEN #State := 40; END_IF;\n    40: IF #BlockingFault THEN #State := 80; ELSIF #StopEdge THEN #State := 70; END_IF;\n    50: IF #StopEdge THEN #State := 70; ELSIF #BlockingFault THEN #State := 80; END_IF;\n    60: #QualityHold := TRUE; IF #ResetEdge AND NOT #BlockingFault THEN #State := 90; END_IF;\n    70: #IndexRequest := FALSE; #CapperRequest := FALSE; #State := 20;\n    80: #QualityHold := TRUE; IF #ResetEdge AND NOT #BlockingFault THEN #State := 90; END_IF;\n    90: #IndexRequest := FALSE; #CapperRequest := FALSE; #GateCloseRequest := FALSE; #ClampRequest := FALSE; #QualityHold := FALSE; #State := 20;\n    ELSE #State := 0;\n  END_CASE;\n  IF #BlockingFault THEN #IndexRequest := FALSE; #CapperRequest := FALSE; END_IF;\nEND_FUNCTION_BLOCK''')
write("04_controls_siemens/scl/OB1_Call_Structure.scl", f'''// {NOTICE}\nORGANIZATION_BLOCK "Main"\nBEGIN\n  "DB_CellMain"();\nEND_ORGANIZATION_BLOCK''')
write("04_controls_siemens/software_architecture.md",doc("Siemens PLC software architecture", """OB1 executes input normalization, equipment modules, coordinator, alarm/recipe/counters/HMI communications, and final output mapping in that order. Each timer and edge detector belongs to one instance. Equipment modules expose command, feedback, permissive, interlock, state, fault, warning, configuration and diagnostics separately. The coordinator owns legal machine transitions; equipment FBs own actuator dynamics and timeouts.

Simulation hooks are held in a dedicated non-retentive DB with a compile-time `SIMULATION_BUILD` constant. Release validation fails if it is true or if any forcing tag is referenced by the physical output mapper. A fresh power cycle initializes to UNINITIALIZED then STOPPED; an explicit reset and start edge are required."""))

write("05_hmi/hmi_specification.md",doc("WinCC Unified HMI specification", """| Screen | Purpose | Key faceplates |
|---|---|---|
| Overview / automatic | Mode, state, pair flow, disposition | machine state, actuator, fill channel, vision |
| Filling detail | Pulses, mA, targets, valve state, diagnostics | two fill-channel instances |
| Manual/setup | Permission-controlled jogs | actuator and drive faceplates |
| Recipes | Staged values, validation, apply handshake | recipe editor/change record |
| Alarms/history | first-out, active, acknowledged, cleared | alarm summary/history |
| I/O diagnostics | module/channel/address/raw/scaled | diagnostic table |
| Drives | status word, reference, actuals, faults | G120C faceplate |
| NVIDIA inspection | ready/busy/ID/result/confidence/model identity | vision faceplate |
| Maintenance/production | counters, service due, good/held pairs | counter tiles |
| Users/config/system | roles, audit, network health, backups | administration |

Commands use a sequence-number/accepted/rejected handshake. Operator commands require Operator role; manual actuator/drive commands require Maintenance and MANUAL_SETUP; recipe/security changes require Engineer or Administrator. Every disabled control displays the blocking state, permissive or interlock. No HMI command writes a physical output tag directly."""))
write("05_hmi/navigation.mmd","""flowchart TD\n  Login --> Overview\n  Overview --> Automatic\n  Overview --> Filling\n  Overview --> Manual\n  Overview --> Alarms\n  Overview --> Diagnostics\n  Diagnostics --> IO\n  Diagnostics --> Drives\n  Diagnostics --> Vision\n  Overview --> Recipes\n  Overview --> Maintenance\n  Overview --> Production\n  Overview --> Configuration\n""")
write("06_drives/drive_control_philosophy.md",doc("Drive-control and Startdrive philosophy", """Two preliminary 0.75 kW SINAMICS G120C PN drives use cyclic PROFINET control/status and Startdrive commissioning when a compatible TIA toolchain is available. PLC run commands require external safety healthy mirror, drive ready, no fault, correct machine state and equipment interlocks. Fault reset is edge-triggered and inhibited while a run request exists.

Motor data, ramp times, minimum/maximum speed, current limits, braking method, EMC filter, line reactor, protective device, cable/shield and thermal selections are open until nameplates, pump curve, mechanics and site data are received. STO is shown only as an external conceptual safety interface and is never controlled or credited by standard PLC logic."""))

write("07_nvidia_vision/vision_system_specification.md",doc("NVIDIA vision system specification", """A fixed industrial camera observes both nests after drip settle. Preliminary optics use a controlled backlight to reveal the liquid boundary and diffuse front lighting for gross bottle condition/spill evidence. The field of view must cover both bottles plus 10% calibration margin; lens selection uses sensor width × working distance / field width and remains open until bottle envelope, camera sensor and mounting distance are measured.

Model architecture: a detector/segmenter finds both bottle ROIs and gross visible defects; a calibrated fill-line estimator classifies under/in-range/over per ROI. The PLC receives bounded status and confidence only. This is not legal metrology, leak integrity testing or safety. Trigger jitter, exposure, glare, foam and transparent/product-color variations are explicit validation factors."""))
write("07_nvidia_vision/dataset_annotation_guide.md",doc("Dataset and annotation guide", """Required classes: bottle, bottle_misaligned, bottle_damage_visible, liquid_region, foam, drip, spill. Each image records bottle SKU, recipe, true fill reference method, camera/lens/light settings, production lot, shift, background, glare, foam, occlusion and synthetic/real provenance.

Splits are grouped by production lot and acquisition session—not random adjacent frames—to prevent leakage. Target policy: 70% train, 15% validation, 15% held-out test after grouping, with a separate commissioning challenge set. Synthetic images may expand edge cases but never replace real held-out validation. No dataset is included, no training was run, and no accuracy/confusion/false-accept/false-reject result exists."""))
write("07_nvidia_vision/model_card.md",doc("AI model card — untrained design record", """- Model identity: **NOT TRAINED / NOT DELIVERED**.
- Intended use: non-safety quality inspection for two visible bottles after filling.
- Intended deployment: DeepStream 9.1-compatible Jetson Orin platform, final carrier and JetPack image TBD.
- Inputs: calibrated color frames under controlled lighting; exactly two expected ROIs.
- Outputs: presence/pass, fill status, visible damage/spill, confidence and diagnostics.
- Metrics: none; no dataset or GPU workload was available. Thresholds remain unvalidated.
- Known limits: transparent bottles, glare, foam, labels, colored/opaque product, condensation, vibration and novel bottle geometry.
- Rollback: deploy versioned signed bundle, verify SHA-256 and smoke-test on challenge set; keep previous signed bundle; rollback requires maintenance authorization and records model/version/time. Procedure is designed but untested."""))
write("07_nvidia_vision/deepstream_app_config.txt",f"""# {NOTICE}
# DeepStream 9.1 design configuration; syntax/runtime validation blocked because DeepStream is not installed.
[application]
enable-perf-measurement=1
perf-measurement-interval-sec=5
[source0]
enable=1
type=1
camera-width=1920
camera-height=1200
camera-fps-n=30
camera-fps-d=1
[streammux]
batch-size=1
width=1920
height=1200
batched-push-timeout=40000
[primary-gie]
enable=1
model-engine-file=MODEL_NOT_DELIVERED.engine
config-file=config_infer_primary.txt
batch-size=1
[sink0]
enable=1
type=1
sync=0
""")
write("07_nvidia_vision/config_infer_primary.txt",f"""# {NOTICE}
# Reference-only inference settings. The named engine intentionally does not exist; deployment gate is blocked.
[property]
gpu-id=0
batch-size=1
network-type=2
process-mode=1
gie-unique-id=1
network-mode=2
model-engine-file=MODEL_NOT_DELIVERED.engine
labelfile-path=labels.txt
interval=0
[class-attrs-all]
pre-cluster-threshold=0.50
""")
write("07_nvidia_vision/labels.txt","bottle\nbottle_misaligned\nbottle_damage_visible\nliquid_region\nfoam\ndrip\nspill")
write("07_nvidia_vision/plc_ai_node_map.csv","signal,node_id,direction\n"+"\n".join([f"{v['signal']},ns=3;s=FC01.Vision.{v['signal']},{'PLC_to_NVIDIA' if v['owner']=='PLC' else 'NVIDIA_to_PLC'}" for v in vision]))

write("08_digital_twin/digital_twin_architecture.md",doc("Digital twin and synthetic-data architecture", """The deterministic Python simulator in `11_simulation` is the regression oracle for sequence/failure behavior; it is not the Siemens PLC and cannot satisfy PLCSIM gates. A separate OpenUSD/Omniverse workflow is specified for visualization and synthetic data, but no USD file is delivered because Omniverse/USD native validation was unavailable.

When available, import the validated STEP assembly, preserve SI units and source hashes, add non-authoritative joints/sensors, and parameterize bottle position, fill, color/transparency, light intensity/direction, camera angle, glare, foam, occlusion, background and bottle geometry. Each render must carry scene commit, source STEP hash, random seed and annotation provenance. A re-opened USD stage is necessary but not proof of physical fidelity."""))
write("08_digital_twin/synthetic_variation_plan.csv","parameter,range,distribution,annotation\nbottle_position_mm,-8..8,uniform,pose\nfill_level_fraction,0.60..0.95,stratified,fill_reference\nproduct_transmission,0.1..0.95,stratified,material\nlighting_intensity,0.6..1.4,uniform,light_setting\ncamera_angle_deg,-5..5,uniform,camera_pose\nglare,none/moderate/severe,categorical,challenge\nfoam_fraction,0..0.25,stratified,foam_mask\nocclusion_fraction,0..0.20,stratified,occlusion\n")

simulator='''from dataclasses import dataclass\n\nBLOCKING = {\n "single_missing_bottle","both_bottles_missing","bottle_sensor_stuck_on","bottle_sensor_stuck_off","gate_timeout","clamp_timeout","contradictory_actuator_feedback","flow_channel_no_pulse","flow_analog_pulse_disagreement","underfill","overfill","valve_fails_to_close","pump_vfd_fault","conveyor_vfd_fault","air_pressure_loss","product_supply_loss","capper_not_ready","capper_busy_timeout","capper_fault","vision_not_ready","vision_result_timeout","stale_inspection_id","low_confidence_inspection","one_bottle_fails","vision_heartbeat_loss","plc_heartbeat_loss","power_loss_during_filling","manual_mode_interlocks"}\n\n@dataclass\nclass Result:\n    scenario: str\n    final_state: str\n    released: bool\n    pump_cmd: bool\n    valve_1_cmd: bool\n    valve_2_cmd: bool\n    automatic_restart: bool\n    evidence: str\n\nclass FillingCellSimulator:\n    \"\"\"Deterministic interface/sequence model; never represented as Siemens PLC execution.\"\"\"\n    def run(self, scenario: str) -> Result:\n        if scenario == "normal_two_bottle_cycle":\n            return Result(scenario,"READY",True,False,False,False,False,"fresh matched vision ID; both pass; capper complete")\n        if scenario == "hmi_communications_loss":\n            return Result(scenario,"CONTROLLED_STOPPING",False,False,False,False,False,"no new HMI command accepted")\n        if scenario == "power_restoration":\n            return Result(scenario,"STOPPED",False,False,False,False,False,"reset and new start required")\n        if scenario == "reset_no_restart":\n            return Result(scenario,"STOPPED",False,False,False,False,False,"reset clears eligible latch only")\n        if scenario in BLOCKING:\n            state = "FAULTED" if scenario not in {"low_confidence_inspection","one_bottle_fails","stale_inspection_id","vision_result_timeout","vision_not_ready"} else "HOLDING"\n            return Result(scenario,state,False,False,False,False,False,"blocking injection caused controlled hold/fault")\n        raise KeyError(scenario)\n'''
# Revision-C simulation is maintained as independently reviewed source under
# 11_simulation.  The project generator deliberately does not overwrite it.

write("12_testing/FAT_procedure.md",doc("Factory acceptance test procedure — planned, not executed", """Prerequisites: approved native TIA project and hardware catalog; PLC/HMI/drive compile reports; isolated PLCSIM or test panel; calibrated stimulus; approved risk controls. Record tool versions, hashes, tester, date and deviations.

Execute every `TC-*` row in `10_schedules/test_coverage.csv`, verify state/first-out/timing/output traces, restore without automatic restart, and reconcile result IDs. The deterministic Python regression evidence is a design check only and must not be entered as PLCSIM or FAT execution."""))
write("12_testing/SAT_procedure.md",doc("Site acceptance test procedure — planned, not executed", """Qualified personnel must verify supply, protective bonding, isolation, torque, device ratings, I/O point-to-point continuity, guards/external safety system, utilities, motor rotation, dry and wet sequence, metering comparison, camera calibration, capping interface, backup/restore and operator training. Physical testing has not occurred. Safety validation and legal obligations are separate project activities."""))
write("12_testing/io_checkout.csv","symbol,address,device,check,measured,result,signoff\n"+"\n".join([f"{r['symbol']},{r['address']},{r['device']},Stimulate field and verify correct single channel,,," for r in io]))

docs={
 "13_documentation/functional_design_specification.md":("Functional design specification","The automatic sequence and state model are controlled by `02_system_architecture/state_and_sequence.md`. Equipment modules enforce feedback, timeout and contradiction diagnostics. Fill totals are independent; pump stops only after both valve commands close or immediately on a blocking condition. Failed or uncertain product remains clamped/gated for explicit disposition."),
 "13_documentation/software_design_specification.md":("Software design specification","The reviewable SCL is split by equipment responsibility. Interfaces are statically typed; instance FBs own timers and edges; the coordinator owns legal transitions; the final output mapper applies permissives. First-out is latched before acknowledgement; acknowledgement and reset are distinct."),
 "13_documentation/alarm_philosophy.md":("Alarm philosophy","Faults stop or hold according to equipment risk; warnings do not imply acceptance. First-out captures the initiating code, later alarms remain visible, acknowledgement records awareness only, and reset is allowed only after causes clear. Reset never starts the machine."),
 "13_documentation/network_cybersecurity.md":("Network architecture and cybersecurity assumptions","Cell control, quality vision and temporary service are separate zones. Use unique certificates, least-privilege OPC UA nodes, allow-listed ports, disabled unused services, authenticated time, signed backups/model bundles, role-controlled update windows and security event logging. Final firewall, key management, vulnerability response and site policy require owner approval."),
 "13_documentation/commissioning_maintenance.md":("Commissioning and maintenance procedure","Commission in stages: document review, de-energized inspection, power/PE checks, I/O checkout, drive rotation, dry sequence, wet tuning, optics calibration, capper integration, negative tests, backup and training. Maintenance includes filter/vent inspection, terminal torque per manufacturer, valve leakage checks, flowmeter calibration status, camera/lighting cleanliness and model/version audit."),
 "13_documentation/backup_recovery.md":("Backup and recovery","Create a native TIA archive only from the verified installed version; export sources/tag/alarm tables; export drive parameters; back up HMI users/configuration under site policy; store Jetson image/deployment configs/model checksum separately. Restore into an isolated environment, compile, validate signatures/hashes, execute smoke tests and record evidence before production use."),
 "13_documentation/operator_training.md":("Operator and maintenance training guide","Operators must understand modes, state, stop/reset distinction, first-out, quality hold and product disposition. Maintenance training covers authorized manual mode, disabled reasons, I/O/drive/vision diagnostics, energy-control procedures and escalation. No trainee may treat vision as a safety or certified measurement function."),
 "13_documentation/risk_register.md":("Risk and limitation register","Key open risks are unintended assumptions about utilities/motors; incomplete native Siemens verification; stale/uncertain vision results; optical domain shift; incorrect field continuity; inadequate thermal/EMC/protection data; unauthorized changes; and confusion between conceptual safety monitoring and safety control. Controls are documented holds, native gates, independent review, change control and qualified project-specific engineering."),
}
for path,(title,body) in docs.items(): write(path,doc(title,body))

write("09_panel_cad/README.md",doc("Panel CAD status", """The genuine inherited FreeCAD 1.1.3 baseline is quarantined in `native_baseline`. Earlier evidence recorded 130 objects, 73 physical shapes/solids, 800 × 800 × 300 mm bounds, exact STEP reimport bounds, legacy IGES edge/compound reimport and a valid mm-based DXF. These files predate the selected Siemens/NVIDIA hardware and are not claimed as revision-C panel completion.

`10_schedules/panel_placement.csv` is the new equipment-envelope intent. Close OI-004 by replacing envelopes with verified manufacturer dimensions/models, maintaining mains/VFD/24 V/analog segregation and service clearances, then reopening FCStd and reimporting STEP/IGES/DXF in a fresh process."""))

write("14_qa/validation_matrix.md",doc("Validation matrix", """| Domain | Evidence available | Result |
|---|---|---|
| Canonical data / schedules | Automated uniqueness, required signals and CSV/canonical parity | Pass when validator reports zero errors; final manifest is verified separately |
| Modular Siemens SCL | Text/source review only | Implemented; native compile blocked |
| HMI/Startdrive | Functional specifications and tag schedules | Native configuration/compile blocked |
| Deterministic simulator | 32 regression scenarios | Executed locally; not PLCSIM evidence |
| NVIDIA interface | Contract and simulator cases | Logic design tested; runtime/model blocked |
| QElectroTech | Genuine inherited native baseline | Baseline reopen evidence only; upgrade blocked |
| FreeCAD/STEP/IGES/DXF | Genuine inherited native baseline | Baseline reopen/reimport evidence only; upgrade blocked |
| PDFs/XLSX | Final release artifacts require render inspection | See visual QA report |
| Safety | Boundary statement and non-safety separation | Concept only; qualified project work required |"""))
write("14_qa/acceptance_gate_status.md",doc("Acceptance gate status", """## Overall: PARTIALLY COMPLETE

- Siemens native project open/compile/HMI/archive restore: **BLOCKED — TIA Portal V20 is installed, but usable licence/native access is unproven and the current identity lacks Openness authorization**. Startdrive and PLCSIM/PLCSIM Advanced are not installed.
- NVIDIA model training/evaluation/latency/rollback execution: **BLOCKED — no real dataset, compatible GPU or runtime**.
- DeepStream configuration: **DESIGNED, NOT RUNTIME-VALIDATED**.
- QET revision-C upgrade: **BLOCKED/INCOMPLETE**; genuine baseline retained with prior reopen evidence.
- CAD revision-C upgrade: **BLOCKED/INCOMPLETE**; genuine baseline retained with prior reopen/reimport evidence.
- Canonical model, schedules, modular sources, documentation and deterministic non-PLC regression: **IMPLEMENTED AND LOCALLY VALIDATED**.

No FAT, SAT, physical commissioning, electrical test, safety validation or model-performance result is claimed."""))
write("14_qa/design_review_checklist.md",doc("Final integrated design review checklist", """- [x] Requirements, architecture, state names and interfaces reconciled.
- [x] Canonical tags/addresses/alarm ranges frozen and machine-checkable.
- [x] Physical reject omitted consistently; quality hold/operator disposition retained.
- [x] Modular Siemens-oriented source and HMI/drive specifications supplied.
- [x] AI timeout, stale ID, low confidence, contradiction and heartbeat failure hold product.
- [x] Deterministic simulator covers required scenarios and is not misrepresented as PLC evidence.
- [ ] TIA/WinCC/Startdrive native project compiled and restored.
- [ ] PLCSIM normal/fault traces completed.
- [ ] QET revised for exact Siemens/NVIDIA hardware and independently reviewed.
- [ ] CAD revised for selected device envelopes and revalidated.
- [ ] Real optical feasibility, dataset, training/evaluation and edge latency completed.
- [ ] Qualified safety and site-specific electrical engineering completed."""))

write("release/RELEASE_NOTES.md",doc("Revision C intermediate release note", """Revision C creates one coherent Siemens-authoritative architecture from the two legacy sources. The revision-C overlay replaces this intermediate content before the generator exits.

The release is **PARTIALLY COMPLETE**. Native Siemens, final electrical/CAD and trained-model gates are explicitly blocked. The package is suitable for design review and continuation in licensed native tools, not construction, production, conformity assessment or commissioning."""))

from revision_d_generator import apply_revision_d
from revision_e_generator import apply_revision_e
from revision_f_generator import apply_revision_f
from revision_f_scl import apply_revision_f_scl
from revision_f_nvidia import apply_revision_f_nvidia
from revision_g_generator import apply_revision_g

apply_revision_d(ROOT)
apply_revision_e(ROOT)
apply_revision_f(ROOT)
apply_revision_f_scl(ROOT)
apply_revision_f_nvidia(ROOT)
apply_revision_g(ROOT)
print(f"Built controlled project sources under {ROOT}")
