from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from revision_c_scl import sources as scl_sources

NOTICE = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"
SAFETY = ("CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, "
          "VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, "
          "SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.")


def _write(root: Path, rel: str, text: str) -> None:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.rstrip() + "\n", encoding="utf-8")


def _csv(root: Path, rel: str, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows supplied for {rel}")
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _doc(title: str, body: str) -> str:
    return f"# {title}\n\n> {NOTICE}\n\n> {SAFETY}\n\n{body}"


def _designation(tag: str, location: str) -> str:
    clean = tag if tag.startswith("-") else "-" + "".join(ch if ch.isalnum() else "_" for ch in tag).strip("_").upper()
    return f"=FC01+{location}{clean}"


def _hardware() -> list[dict]:
    return [
        {"tag":"-A100","role":"PLC CPU","manufacturer":"Siemens","model":"SIMATIC S7-1500 CPU 1511-1 PN","order_no":"6ES7511-1AL03-0AB0","qty":1,"selection":"Selected baseline","firmware":"FS03 / FW V4.0 for native TIA V20 engineering","width_mm":35,"height_mm":147,"depth_mm":129,"status":"Native catalog/configuration and delivered hardware state not yet verified","source_url":"https://support.industry.siemens.com/cs/attachments/109977233/s71500_cpu1511_1_pn_dtc_manual_en-US_en-US.pdf","source_accessed":"2026-08-02"},
        {"tag":"-A101","role":"High-speed counter","manufacturer":"Siemens","model":"TM Count 2x24V","order_no":"6ES7550-1AA01-0AB0","qty":1,"selection":"Selected baseline","firmware":"Native catalog selection required","width_mm":35,"height_mm":147,"depth_mm":129,"status":"Two channels selected; TO configuration and K-factor inputs open","source_url":"https://support.industry.siemens.com/teddatasheet/?caller=SIOS&format=pdf&language=en&mlfbs=6ES7550-1AA01-0AB0","source_accessed":"2026-08-02"},
        {"tag":"-A102","role":"Digital input","manufacturer":"Siemens","model":"DI 32x24V DC HF","order_no":"6ES7521-1BL00-0AB0","qty":1,"selection":"Selected baseline","firmware":"Native catalog selection required","width_mm":35,"height_mm":147,"depth_mm":129,"status":"Front connector and channel parameters included separately","source_url":"https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6ES7521-1BL00-0AB0","source_accessed":"2026-08-02"},
        {"tag":"-A103","role":"Digital output","manufacturer":"Siemens","model":"DQ 32x24V DC/0.5A HF","order_no":"6ES7522-1BL01-0AB0","qty":1,"selection":"Selected baseline","firmware":"Native catalog selection required","width_mm":35,"height_mm":147,"depth_mm":129,"status":"Field loads use interposing relays","source_url":"https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6ES7522-1BL01-0AB0","source_accessed":"2026-08-02"},
        {"tag":"-A104","role":"Analog input","manufacturer":"Siemens","model":"AI 8xU/I HF","order_no":"6ES7531-7NF00-0AB0","qty":1,"selection":"Selected baseline","firmware":"Native catalog selection required","width_mm":35,"height_mm":147,"depth_mm":129,"status":"4-20 mA channel diagnostics require native parameterization","source_url":"https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6ES7531-7NF00-0AB0","source_accessed":"2026-08-02"},
        {"tag":"-H100","role":"Operator panel","manufacturer":"Siemens","model":"MTP700 Unified Comfort","order_no":"6AV2128-3GB06-0AX1","qty":1,"selection":"Selected baseline","firmware":"WinCC Unified V20 target","width_mm":214,"height_mm":158,"depth_mm":63.6,"status":"Door cutout 198.3 x 142 mm; native HMI project/compile open","source_url":"https://support.industry.siemens.com/teddatasheet/?caller=SIOS&format=pdf&language=en&mlfbs=6AV2128-3GB06-0AX1","source_accessed":"2026-08-02"},
        {"tag":"-U100","role":"Conveyor drive","manufacturer":"Siemens","model":"SINAMICS G120C PN 0.75 kW unfiltered","order_no":"6SL3210-1KE12-3UF2","qty":1,"selection":"Provisional","firmware":"Startdrive selection open","width_mm":"","height_mm":"","depth_mm":"","status":"Rating, envelope and clearances blocked by motor/mechanics and native Startdrive","source_url":"https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6SL3210-1KE12-3UF2","source_accessed":"2026-08-02"},
        {"tag":"-U101","role":"Pump drive","manufacturer":"Siemens","model":"SINAMICS G120C PN 0.75 kW unfiltered","order_no":"6SL3210-1KE12-3UF2","qty":1,"selection":"Provisional","firmware":"Startdrive selection open","width_mm":"","height_mm":"","depth_mm":"","status":"Rating, envelope and clearances blocked by pump curve and motor data","source_url":"https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6SL3210-1KE12-3UF2","source_accessed":"2026-08-02"},
        {"tag":"-SW100","role":"Managed Ethernet switch","manufacturer":"Siemens","model":"SCALANCE XC208 managed","order_no":"6GK5208-0BA00-2AC2","qty":1,"selection":"Selected network baseline","firmware":"Native configuration open","width_mm":60,"height_mm":147,"depth_mm":125,"status":"VLAN-capable Layer 2 switch; firewall/router required for inter-zone traffic","source_url":"https://support.industry.siemens.com/teddatasheet/?caller=SIOS&format=pdf&language=en&mlfbs=6GK5208-0BA00-2AC2","source_accessed":"2026-08-02"},
        {"tag":"-FW100","role":"Industrial firewall/router","manufacturer":"Siemens","model":"SCALANCE S615 EEC","order_no":"6GK5615-0AA01-2AA2","qty":1,"selection":"Selected network baseline","firmware":"Native configuration open","width_mm":"","height_mm":147,"depth_mm":127,"status":"Exact width and site policy remain procurement/native gates","source_url":"https://mall.industry.siemens.com/mall/en/oeii/Catalog/Product?SiepCountryCode=OE&mlfb=6GK5615-0AA01-2AA2","source_accessed":"2026-08-02"},
        {"tag":"-PC200","role":"Vision edge compute","manufacturer":"NVIDIA","model":"Jetson Orin NX 16GB on industrial carrier","order_no":"","qty":1,"selection":"Architecture only","firmware":"JetPack/DeepStream image not selected","width_mm":"","height_mm":"","depth_mm":"","status":"Carrier, thermals, power, EMC and lifecycle are open","source_url":"https://developer.nvidia.com/deepstream-sdk","source_accessed":"2026-08-02"},
    ]


def _reconcile_io(io: list[dict]) -> list[dict]:
    hardwired_drive = {"CONVEYOR_READY","CONVEYOR_RUNNING","CONVEYOR_FAULT","PUMP_READY","PUMP_RUNNING","PUMP_FAULT","CONVEYOR_RUN_CMD","PUMP_RUN_CMD"}
    spare_index = defaultdict(int)
    result = []
    for row in io:
        new = dict(row)
        if row["symbol"] in hardwired_drive:
            spare_index[row["direction"]] += 1
            new["symbol"] = f"{row['direction']}_SPARE_DRIVE_REMOVED_{spare_index[row['direction']]:02d}"
            new["device"] = "SPARE"
            new["description"] = "Spare channel; hardwired drive run/status removed because Standard Telegram 1 PROFINET is primary"
        elif row["symbol"] == "SAFETY_OK":
            new["device"] = "-K100"
            new["description"] = "Dry-contact mirror from the external safety interface; monitoring only, never a safety control channel"
        elif row["symbol"] == "GUARD_CLOSED_STATUS":
            new["device"] = "-S102"
            new["description"] = "Dry-contact guard-status mirror; monitoring only, never a safety control channel"
        result.append(new)
    return result


def _drive_interfaces() -> list[dict]:
    rows = []
    for tag, name, iw, qw in [("-U100","CONVEYOR",256,256),("-U101","PUMP",260,260)]:
        rows.extend([
            {"drive":tag,"name":name,"telegram":"Standard Telegram 1","direction":"Drive_to_PLC","pzd":1,"address":f"IW{iw}","signal":"ZSW1 status word","data_type":"WORD","scaling":"Bit-coded per SINAMICS","status":"Native Startdrive/TIA confirmation open"},
            {"drive":tag,"name":name,"telegram":"Standard Telegram 1","direction":"Drive_to_PLC","pzd":2,"address":f"IW{iw+2}","signal":"NIST_A actual speed","data_type":"INT","scaling":"16384 = 100% reference speed","status":"Native Startdrive/TIA confirmation open"},
            {"drive":tag,"name":name,"telegram":"Standard Telegram 1","direction":"PLC_to_Drive","pzd":1,"address":f"QW{qw}","signal":"STW1 control word","data_type":"WORD","scaling":"Bit-coded per SINAMICS","status":"Native Startdrive/TIA confirmation open"},
            {"drive":tag,"name":name,"telegram":"Standard Telegram 1","direction":"PLC_to_Drive","pzd":2,"address":f"QW{qw+2}","signal":"NSOLL_A speed setpoint","data_type":"INT","scaling":"16384 = 100% reference speed","status":"Native Startdrive/TIA confirmation open"},
        ])
    return rows


def _hmi_tags(io: list[dict]) -> list[dict]:
    rows = []
    status_sources = [
        ("MACHINE_STATE","DB_HMI.StateCode","Overview"),("AUTO_STEP","DB_HMI.AutoStepCode","Overview"),("QUALITY_HOLD","DB_HMI.QualityHold","Overview"),("FIRST_OUT_ALARM","DB_HMI.FirstOutAlarm","Alarms"),
        ("SAFETY_OK","DB_IO.Inputs.SafetyOk","Diagnostics"),("GUARD_CLOSED_STATUS","DB_IO.Inputs.GuardClosed","Diagnostics"),("AIR_PRESSURE_OK","DB_IO.Inputs.AirPressureOk","Diagnostics"),("PRODUCT_SUPPLY_OK","DB_IO.Inputs.ProductSupplyOk","Diagnostics"),
        ("BOTTLE_AT_NEST_1","DB_IO.Inputs.Bottle1Present","Overview"),("BOTTLE_AT_NEST_2","DB_IO.Inputs.Bottle2Present","Overview"),("GATE_OPEN_FB","DB_IO.Inputs.GateOpen","Diagnostics"),("GATE_CLOSED_FB","DB_IO.Inputs.GateClosed","Diagnostics"),
        ("CLAMP_RELEASED_FB","DB_IO.Inputs.ClampReleased","Diagnostics"),("CLAMP_ENGAGED_FB","DB_IO.Inputs.ClampEngaged","Diagnostics"),("FILL_VALVE_1_CLOSED_FB","DB_IO.Inputs.Valve1Closed","Filling"),("FILL_VALVE_2_CLOSED_FB","DB_IO.Inputs.Valve2Closed","Filling"),
        ("FLOW_1_MA_RAW","DB_IO.Inputs.Flow1Raw","Filling"),("FLOW_2_MA_RAW","DB_IO.Inputs.Flow2Raw","Filling"),("FLOW_1_DELIVERED_ML","DB_CellMain.FillCh1.DeliveredMl","Filling"),("FLOW_2_DELIVERED_ML","DB_CellMain.FillCh2.DeliveredMl","Filling"),
        ("FILL_1_DIAG","DB_CellMain.FillCh1.DiagReason","Filling"),("FILL_2_DIAG","DB_CellMain.FillCh2.DiagReason","Filling"),("CONVEYOR_READY","DB_Drives.Conveyor.Ready","Drives"),("CONVEYOR_RUNNING","DB_Drives.Conveyor.Running","Drives"),
        ("CONVEYOR_FAULT","DB_Drives.Conveyor.Fault","Drives"),("CONVEYOR_SPEED_PCT","DB_Drives.Conveyor.ActualSpeedPct","Drives"),("PUMP_READY","DB_Drives.Pump.Ready","Drives"),("PUMP_RUNNING","DB_Drives.Pump.Running","Drives"),
        ("PUMP_FAULT","DB_Drives.Pump.Fault","Drives"),("PUMP_SPEED_PCT","DB_Drives.Pump.ActualSpeedPct","Drives"),("VISION_READY","DB_VisionComms.Ready","Vision"),("VISION_BUSY","DB_VisionComms.Busy","Vision"),
        ("VISION_RESULT_ID","DB_VisionComms.Result.ResultId","Vision"),("VISION_LOW_CONFIDENCE","DB_VisionComms.Result.LowConfidence","Vision"),("VISION_FAULT","DB_VisionComms.Result.Fault","Vision"),("VISION_MODEL_ID","DB_VisionComms.Result.ModelId","Vision"),
        ("CAPPER_READY","DB_IO.Inputs.CapperReady","Diagnostics"),("CAPPER_BUSY","DB_IO.Inputs.CapperBusy","Diagnostics"),("CAPPER_COMPLETE","DB_IO.Inputs.CapperComplete","Diagnostics"),("CAPPER_FAULT","DB_IO.Inputs.CapperFault","Diagnostics"),("HMI_COMMUNICATIONS_HEALTHY","DB_HMI.CommunicationsHealthy","Diagnostics"),
    ]
    for name,source,screen in status_sources:
        rows.append({"hmi_tag":f"STATUS_{name}","plc_source":source,"access":"Read only","command":"No","request_seq":"","accepted_seq":"","rejected_seq":"","disabled_reason":"","role":"Operator","screen":screen})
    commands = [
        ("START","DB_HMI.Start","Operator","Overview"),("CONTROLLED_STOP","DB_HMI.ControlledStop","Operator","Overview"),("RESET","DB_HMI.Reset","Operator","Overview"),("ALARM_ACK","DB_HMI.AlarmAck","Operator","Alarms"),("AUTO_MODE","DB_HMI.AutoMode","Operator","Overview"),("MANUAL_MODE","DB_HMI.ManualMode","Maintenance","Manual"),("DISPOSITION_REMOVED","DB_HMI.DispositionRemoved","Supervisor","Holding"),("RECIPE_APPLY","DB_HMI.RecipeApply","Supervisor","Recipes")
    ]
    for name, base, role, screen in commands:
        rows.append({"hmi_tag":f"CMD_{name}","plc_source":f"{base}.Request","access":"Write request only","command":"Yes","request_seq":f"{base}.RequestSeq","accepted_seq":f"{base}.AcceptedSeq","rejected_seq":f"{base}.RejectedSeq","disabled_reason":f"{base}.DisabledReason","role":role,"screen":screen})
    for name in ["ManualConveyorJog","ManualPumpJog","ManualValve1","ManualValve2","ManualSecure"]:
        rows.append({"hmi_tag":f"HOLD_{name.upper()}","plc_source":f"DB_HMI.{name}.Request","access":"Write while pressed; PLC heartbeat supervised","command":"Yes - hold to run","request_seq":"","accepted_seq":"","rejected_seq":"","disabled_reason":f"DB_HMI.{name}.DisabledReason","role":"Maintenance","screen":"Manual"})
    for field in ["RecipeId","TargetMlCh1","TargetMlCh2","PulsesPerLitreCh1","PulsesPerLitreCh2","UnderToleranceMl","OverToleranceMl","NoFlowTimeout","FillTimeout","ValveOpenTimeout","ValveCloseTimeout","PlausibilityTime","PulseWindowTimeS","DripSettleTime","VisionTimeout","TargetFillLevel"]:
        rows.append({"hmi_tag":f"RECIPE_CANDIDATE_{field.upper()}","plc_source":f"DB_Recipe.Candidate.{field}","access":"Supervisor write; committed only by sequenced RecipeApply","command":"No","request_seq":"","accepted_seq":"","rejected_seq":"","disabled_reason":"DB_HMI.RecipeApply.DisabledReason","role":"Supervisor","screen":"Recipes"})
    rows.append({"hmi_tag":"HMI_COMMAND_HEARTBEAT","plc_source":"DB_HMI.CommandHeartbeat","access":"Write heartbeat counter only","command":"No","request_seq":"","accepted_seq":"","rejected_seq":"","disabled_reason":"","role":"System","screen":"System"})
    return rows


def _bom(hardware: list[dict], io: list[dict]) -> list[dict]:
    rows = [{"item":f"BOM-{i:03d}","tag":h["tag"],"description":h["model"],"manufacturer":h["manufacturer"],"order_no":h["order_no"],"qty":h["qty"],"selection_status":h["selection"],"scope":"Panel/field hardware","basis_or_blocker":h["status"]} for i,h in enumerate(hardware,1)]
    seed = [
        ("-MC100","SIMATIC memory card; capacity to be selected after compiled project sizing","Siemens","",1,"TBD","Panel","Native compiled project size unavailable"),
        ("-RA100","S7-1500 mounting rail and fixing hardware","Siemens","",1,"TBD","Panel","Rail length depends on final cabinet layout"),
        ("-FC100","Front connector for DI module","Siemens","",1,"TBD","Panel","Exact accessory to be confirmed in TIA Selection Tool"),
        ("-FC101","Front connector for DQ module","Siemens","",1,"TBD","Panel","Exact accessory to be confirmed in TIA Selection Tool"),
        ("-FC102","Front connector for AI module","Siemens","",1,"TBD","Panel","Exact accessory to be confirmed in TIA Selection Tool"),
        ("-FC103","Front connector for TM Count module","Siemens","",1,"TBD","Panel","Exact accessory to be confirmed in TIA Selection Tool"),
        ("-QS100","Main door-coupled isolator","","",1,"TBD","Panel","Supply, fault current and regulatory basis missing"),
        ("-QF100","Main protective device","","",1,"TBD","Panel","Fault level, load and selectivity study missing"),
        ("-PS100","24 VDC 20 A power supply","","",1,"Provisional","Panel","Demand estimate includes margin; inrush and derating open"),
        ("-QF110","24 VDC electronic branch protection","","",1,"TBD","Panel","Branch currents and discrimination require device data"),
        ("-K100","Main control enable contactor / external safety interface with dry monitoring contact","","",1,"TBD","Panel","Qualified safety design external"),
        ("-K202..-K213","Interposing relays with bases and status indication","","",12,"TBD","Panel","Twelve active output relays; coil/contact/load ratings and approved supplier missing"),
        ("-D202..-D213","Coil suppression modules","","",12,"TBD","Panel","One device per active relay; match relay coil technology"),
        ("-X100..-X199","DIN-rail terminal blocks, disconnect/test where required","","",160,"Provisional quantity","Panel","Final QET continuity and terminal-family selection open"),
        ("-PE100","Copper protective-earth bar and bonding hardware","","",1,"TBD","Panel","PE sizing requires supply/earthing inputs"),
        ("-SC100","Shield-clamp rail and spring clamps","","",12,"Provisional quantity","Panel","Cable OD and final shield count open"),
        ("-ENC100","IP-rated enclosure with mounting plate","","",1,"TBD","Panel","Environment, IP rating and thermal calculation open"),
        ("-WD100","Slotted wiring duct set","","",1,"TBD","Panel","Duct fill pending final conductors"),
        ("-DR100","35 mm DIN rail set","","",1,"TBD","Panel","Final layout open"),
        ("-GL100","Cable glands and EMC glands","","",1,"TBD","Installation","Cable OD and IP rating open"),
        ("-FAN100","Filter fan / cooling solution","","",1,"TBD","Panel","Thermal model and ambient inputs open"),
        ("-M100","Conveyor motor","","",1,"TBD","Field","Nameplate, duty, cable and mechanical data required"),
        ("-M101","Pump motor","","",1,"TBD","Field","Pump curve, nameplate, dead-head and cable data required"),
        ("-YV100","Gate valve/cylinder solenoid","","",1,"TBD","Field","Coil current, response and fail state required"),
        ("-YV101","Clamp valve/cylinder solenoid","","",1,"TBD","Field","Coil current, response and fail state required"),
        ("-YV102","Fill valve channel 1, fail closed","","",1,"TBD","Field","Wetted materials, Kv, coil and closing time required"),
        ("-YV103","Fill valve channel 2, fail closed","","",1,"TBD","Field","Wetted materials, Kv, coil and closing time required"),
        ("-FT100","Pulse plus 4-20 mA flowmeter channel 1","","",1,"TBD","Field","K-factor, max pulse rate and analog diagnostics required"),
        ("-FT101","Pulse plus 4-20 mA flowmeter channel 2","","",1,"TBD","Field","K-factor, max pulse rate and analog diagnostics required"),
        ("-S100","Local reset pushbutton","","",1,"TBD","Field","Operator-station family and IP rating open"),
        ("-S101","Local controlled-stop pushbutton","","",1,"TBD","Field","Not a safety stop; operator-station family open"),
        ("-S102","Guard-status dry-contact monitoring interface","","",1,"TBD","Field","Monitoring only; qualified guard-interlocking design remains external"),
        ("-H101","Three-color stack light with sounder","","",1,"TBD","Field","Lens, sound level and mounting open"),
        ("-IF140","Capper interface terminals/relays","","",1,"TBD","Field","Interface specification missing"),
        ("-CAM200","Industrial camera","","",1,"TBD","Vision","Vision physical basis and target interface open"),
        ("-LENS200","C-mount lens","","",1,"TBD","Vision","Sensor, FOV, working distance and DoF open"),
        ("-LT200","Machine-vision backlight/front-light assembly","","",1,"TBD","Vision","Optical trials and exposure limits open"),
        ("-CB200","Industrial Jetson carrier","","",1,"TBD","Vision","Power, lifecycle, thermal and EMC selection open"),
        ("-W900","Industrial Ethernet patch cables/connectors","","",7,"Provisional quantity","Installation","Lengths and routing open"),
        ("-W901","Shielded VFD motor cables and EMC termination kits","","",2,"TBD","Installation","Motor cable lengths and drive EMC design open"),
        ("-CONS100","Markers, ferrules, lugs, ties and installation consumables","","",1,"TBD","Installation","Quantity after detailed design"),
    ]
    start = len(rows) + 1
    for offset, row in enumerate(seed):
        tag, desc, mfr, part, qty, status, scope, basis = row
        rows.append({"item":f"BOM-{start+offset:03d}","tag":tag,"description":desc,"manufacturer":mfr,"order_no":part,"qty":qty,"selection_status":status,"scope":scope,"basis_or_blocker":basis})
    covered = " ".join(r["tag"] for r in rows)
    for row in io:
        device = row["device"]
        if device != "SPARE" and device and not (device.startswith("-K2") and "-K202..-K213" in covered) and device not in covered:
            rows.append({"item":f"BOM-{len(rows)+1:03d}","tag":device,"description":row["description"],"manufacturer":"","order_no":"","qty":1,"selection_status":"TBD","scope":"Field","basis_or_blocker":"Automatically added from canonical I/O; exact device selection open"})
            covered += " " + device
    return rows


def _connections(io: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    active = [r for r in io if r["device"] != "SPARE" and "SPARE" not in r["symbol"]]
    rows: list[dict] = []
    terminal_rows: list[dict] = []
    device_cable: dict[str, str] = {}
    core_no = defaultdict(int)
    common_done: set[str] = set()
    cable_seq = terminal_seq = wire_seq = 1

    capper_pins = {"CAPPER_READY":"4", "CAPPER_BUSY":"5", "CAPPER_COMPLETE":"6", "CAPPER_FAULT":"7"}
    load_map = {
        "FILL_VALVE_1_OPEN_CMD":("-YV102","1","2"), "FILL_VALVE_2_OPEN_CMD":("-YV103","1","2"),
        "GATE_OPEN_CMD":("-YV100","1","2"), "GATE_CLOSE_CMD":("-YV100","3","4"),
        "CLAMP_ENGAGE_CMD":("-YV101","1","2"), "CLAMP_RELEASE_CMD":("-YV101","3","4"),
        "CAPPER_REQUEST":("-IF140","8","9"), "STACK_GREEN":("-H101","G","COM-G"),
        "STACK_AMBER":("-H101","A","COM-A"), "STACK_RED":("-H101","R","COM-R"),
        "AUDIBLE_ALARM":("-H101","S","COM-S"), "CAMERA_LIGHT_ENABLE":("-LT200","1","2"),
    }

    def full(tag: str, location: str) -> str:
        return _designation(tag, location)

    def add(row: dict, function: str, device: str, pin: str, potential: str, destination: str,
            color: str, shield: str = "", external: bool = True, interposing: str = "") -> None:
        nonlocal cable_seq, terminal_seq, wire_seq
        cable = core = panel_terminal = ""
        if external:
            if device not in device_cable:
                device_cable[device] = f"C{cable_seq:03d}"; cable_seq += 1
            cable = device_cable[device]; core_no[device] += 1; core = str(core_no[device])
            panel_terminal = f"X{100 + (terminal_seq-1)//24}:{(terminal_seq-1)%24+1}"; terminal_seq += 1
        wire = f"W{wire_seq:04d}"; wire_seq += 1
        module = row["module"]
        record = {
            "signal":row["symbol"], "function":function, "field_device":device, "field_designation":full(device,"FLD") if external else full(device,"CP01"),
            "field_pin":pin, "cable_id":cable, "cable_core":core, "field_terminal":f"{device}:{pin}", "panel_terminal":panel_terminal,
            "internal_wire":wire, "interposing_device":interposing, "module":module, "module_designation":full(module,"CP01"),
            "module_terminal":row["channel"], "plc_address":row["address"], "potential":potential,
            "return_common":"X0:0V" if "0V" in potential else "", "shield_termination":shield,
            "conductor_mm2":"0.5" if row["direction"] in {"AI","HSC"} else "0.75", "color":color,
            "destination":destination, "status":"Controlled Rev-C connection; native QET continuity verification remains open"
        }
        rows.append(record)
        if external:
            terminal_rows.append({"terminal":panel_terminal,"full_designation":full(panel_terminal.split(':')[0],"CP01"),"signal":row["symbol"],"function":function,"cable_id":cable,"core":core,"field_device":device,"field_designation":full(device,"FLD"),"field_pin":pin,"module":module,"module_designation":full(module,"CP01"),"module_terminal":row["channel"],"plc_address":row["address"],"potential":potential,"wire_no":wire,"shield_or_common":shield or record["return_common"],"status":record["status"]})

    for row in active:
        device = row["device"]
        common_key = device
        if row["direction"] == "DI":
            if row["symbol"] == "SAFETY_OK":
                add(row,"Safety-interface monitor contact supply",device,"13","+24VDC fused","=FC01+CP01-X24:+24V","RD",external=False)
                add(row,"Safety-interface monitor contact signal",device,"14","24 VDC switched",f"{full(row['module'],'CP01')}:{row['channel']}","BK",external=False)
            elif row["symbol"] == "GUARD_CLOSED_STATUS":
                add(row,"Guard-monitor contact signal",device,"2","24 VDC switched",f"{full(row['module'],'CP01')}:{row['channel']}","BK")
                add(row,"Guard-monitor contact supply",device,"1","+24VDC fused","=FC01+CP01-X24:+24V","RD")
            else:
                signal_pin = capper_pins.get(row["symbol"], "4")
                add(row,"PNP signal",device,signal_pin,"24 VDC switched",f"{full(row['module'],'CP01')}:{row['channel']}","BK")
                if common_key not in common_done:
                    add(row,"Sensor/interface supply",device,"1","+24VDC fused","=FC01+CP01-X24:+24V","BN")
                    add(row,"Sensor/interface return",device,"2" if device == "-IF140" else "3","0V","=FC01+CP01-X0:0V","BU")
        elif row["direction"] == "DO":
            relay = device; load, load_pin, return_pin = load_map[row["symbol"]]
            add(row,"PLC output to relay coil",relay,"A1","24 VDC switched",f"{full(row['module'],'CP01')}:{row['channel']}","BK",external=False,interposing=relay)
            add(row,"Relay coil return",relay,"A2","0V","=FC01+CP01-X0:0V","BU",external=False,interposing=relay)
            add(row,"Relay contact supply",relay,"13","+24VDC fused","=FC01+CP01-X24:+24V","RD",external=False,interposing=relay)
            add(row,"Relay contact 14 to field load",load,load_pin,"+24VDC switched",f"{full(relay,'CP01')}:14", "BK",interposing=relay)
            add(row,"Field load return",load,return_pin,"0V","=FC01+CP01-X0:0V","BU",interposing=relay)
        elif row["direction"] == "AI":
            add(row,"4-20 mA signal positive",device,"SIG+","4-20mA",f"{full(row['module'],'CP01')}:{row['channel']} AI+","WH")
            if common_key not in common_done:
                add(row,"Instrument supply",device,"+","+24VDC fused","=FC01+CP01-X24:+24V","RD")
                add(row,"Analog signal return",device,"SIG-","0V analog",f"{full(row['module'],'CP01')}:{row['channel']} MANA","BU")
                add(row,"Cable shield",device,"SH","FE","=FC01+CP01-SC100:1","GN","SC100 panel-end only")
        elif row["direction"] == "HSC":
            add(row,"Counter pulse",device,"PULSE","24 V pulse",f"{full(row['module'],'CP01')}:{row['channel']} CLK","WH")
            if common_key not in common_done:
                add(row,"Instrument supply",device,"+","+24VDC fused","=FC01+CP01-X24:+24V","RD")
                add(row,"Cable shield",device,"SH","FE","=FC01+CP01-SC100:1","GN","SC100 panel-end only")
            add(row,"Counter reference",device,"0V","0V",f"{full(row['module'],'CP01')}:{row['channel']} M","BU")
        common_done.add(common_key)

    reference_template = {k:"" for k in terminal_rows[0]}
    for terminal, function, potential in [("X24:+24V","Fused 24 VDC distribution reference","+24VDC"),("X0:0V","0 V distribution reference","0V"),("X0:MANA","Analog reference","0V analog"),("SC100:1","Panel-end shield-clamp reference","FE")]:
        ref = dict(reference_template); ref.update({"terminal":terminal,"full_designation":full(terminal.split(':')[0],"CP01"),"signal":terminal,"function":function,"potential":potential,"status":"Reference terminal/bar; final product family and bridge plan open"}); terminal_rows.append(ref)

    cable_rows = []
    for device, cable in sorted(device_cable.items(), key=lambda item: item[1]):
        used = core_no[device]; installed = 4 if used <= 3 else 8 if used <= 7 else 12 if used <= 11 else 16
        device_rows = [r for r in rows if r["field_device"] == device and r["cable_id"] == cable]
        cable_rows.append({"cable_id":cable,"from_location":"=FC01+CP01 panel terminals","to_device":device,"to_designation":full(device,"FLD"),"cable_type":"Shielded instrumentation" if any(r["shield_termination"] for r in device_rows) else "Industrial control","installed_cores":installed,"allocated_cores":used,"spare_cores":installed-used,"core_range":f"1-{used}","shield":"Panel-end clamp only where scheduled","route_zone":"Analog/instrument" if any(r["function"].startswith(("4-20","Counter","Cable shield")) for r in device_rows) else "24 VDC control","status":"Length and final cable family open"})
    return rows, terminal_rows, cable_rows


def _panel(hardware: list[dict]) -> list[dict]:
    rows = []
    coordinates = {
        "-A100":(90,90,"DIN rail R1","Controls"),"-A101":(130,90,"DIN rail R1","Controls"),"-A102":(170,90,"DIN rail R1","Controls"),"-A103":(210,90,"DIN rail R1","Controls"),"-A104":(250,90,"DIN rail R1","Analog"),
        "-SW100":(330,90,"DIN rail R1","Network"),"-FW100":(400,90,"DIN rail R1","Network"),"-H100":(290,200,"Door cutout","HMI"),"-U100":(90,430,"Mounting plate","VFD heat zone"),"-U101":(340,430,"Mounting plate","VFD heat zone"),"-PC200":(560,250,"DIN rail / shelf","Vision")
    }
    for h in hardware:
        x,y,mount,zone = coordinates[h["tag"]]
        rows.append({"tag":h["tag"],"x_mm":x,"y_mm":y,"width_mm":h["width_mm"],"height_mm":h["height_mm"],"depth_mm":h["depth_mm"],"mounting":mount,"orientation":"Vertical unless manufacturer requires otherwise","zone":zone,"top_clearance_mm":100 if h["tag"].startswith("-U") else 25,"bottom_clearance_mm":100 if h["tag"].startswith("-U") else 25,"side_clearance_mm":50 if h["tag"].startswith("-U") else 15,"heat_w":"TBD" if h["tag"].startswith(("-U","-PC")) else "Manufacturer data required","dimension_basis":"Official Siemens data sheet" if h["width_mm"] != "" else "OPEN - exact selected-device envelope unavailable","placement_status":"Coordinate reserved; native CAD and clearance verification open"})
    rows.extend([
        {"tag":"-PE100","x_mm":70,"y_mm":730,"width_mm":650,"height_mm":25,"depth_mm":25,"mounting":"Mounting plate","orientation":"Horizontal","zone":"PE","top_clearance_mm":20,"bottom_clearance_mm":20,"side_clearance_mm":20,"heat_w":0,"dimension_basis":"Provisional bar envelope","placement_status":"Final PE sizing open"},
        {"tag":"-X100..-X199","x_mm":70,"y_mm":650,"width_mm":680,"height_mm":50,"depth_mm":70,"mounting":"DIN rail R4","orientation":"Horizontal terminal row","zone":"Field termination","top_clearance_mm":40,"bottom_clearance_mm":40,"side_clearance_mm":20,"heat_w":0,"dimension_basis":"Reserved terminal-row envelope","placement_status":"Terminal family and count open"},
        {"tag":"-WD100","x_mm":50,"y_mm":50,"width_mm":40,"height_mm":650,"depth_mm":60,"mounting":"Mounting plate","orientation":"Vertical duct","zone":"24 VDC routing","top_clearance_mm":0,"bottom_clearance_mm":0,"side_clearance_mm":15,"heat_w":0,"dimension_basis":"Provisional routing reserve","placement_status":"Duct fill calculation open"},
    ])
    return rows


def _inputs_required() -> list[dict]:
    items = [
        ("IR-001","Country/market and applicable regulatory basis","Owner / legal authority","Electrical, documentation, conformity"),
        ("IR-002","Site supply voltage/frequency, earthing system and available fault current","Site electrical engineer","Protection, SCCR, PE, conductor sizing"),
        ("IR-003","Ambient temperature, altitude, contamination and required enclosure IP","Site engineering","Panel thermal/enclosure"),
        ("IR-004","Conveyor motor nameplate, duty, speed/torque and cable length","Mechanical/vendor","Drive sizing and protection"),
        ("IR-005","Pump curve, motor nameplate, duty, dead-head behavior and cable length","Process/vendor","Drive, process and overpressure design"),
        ("IR-006","Valve coil voltage/current, response time and fail state","Valve vendor","Output/relay sizing and timeout values"),
        ("IR-007","Sensor types, connectors and electrical characteristics","Machine designer","Point-to-point wiring"),
        ("IR-008","Flowmeter model, K-factor, maximum pulse frequency and 4-20 mA diagnostics","Instrument vendor","TM Count, scaling and diagnostics"),
        ("IR-009","Bottle drawings/materials, recipes, fill targets and tolerances","Process owner","Sequence, recipe and optics"),
        ("IR-010","Required throughput and cycle-time allocation","Production owner","Performance sizing"),
        ("IR-011","Capper electrical protocol and timing specification","Capper vendor","Handshake and terminals"),
        ("IR-012","Camera working envelope, line constraints and optical trial samples","Machine/process owner","Camera/lens/light selection"),
        ("IR-013","Representative labeled real dataset with lot/SKU/session provenance","Quality owner","AI training/evaluation"),
        ("IR-014","Approved Jetson module/carrier and lifecycle policy","IT/OT owner","Edge hardware, power and thermal"),
        ("IR-015","Site network, certificate, identity and cybersecurity policy","OT security","Firewall and OPC UA deployment"),
        ("IR-016","Usable licensed TIA Portal V20 / WinCC Unified access","Controls owner","Native PLC/HMI project and compile"),
        ("IR-017","Startdrive installation and licensed access","Controls owner","Drive native configuration"),
        ("IR-018","PLCSIM or PLCSIM Advanced installation","Controls owner","Native software-in-loop traces"),
        ("IR-019","FreeCAD installation and qualified panel-CAD reviewer","Electrical owner","Revision-C FCStd/exchange validation"),
        ("IR-020","Qualified machinery-safety engineer risk assessment and validation plan","Project authority","External safety architecture"),
    ]
    return [{"request_id":a,"required_input":b,"owner":c,"blocks":d,"status":"OPEN","date_requested":"2026-08-02","evidence_required":"Approved source document or native evidence"} for a,b,c,d in items]


def _gates() -> list[dict]:
    gates = [
        (1,"Requirements/interfaces traceable","PARTIAL","Controlled model and tests present; owner approval absent"),
        (2,"Canonical model reconciles schedules","PASS","VAL-C-STATIC passed 238/238 checks; independent package audit found zero mismatches across all 19 schedules"),
        (3,"Siemens hardware baseline confirmed","PARTIAL","V20/FW4.0 design baseline documented; native catalog and delivered state open"),
        (4,"Native TIA project opens","BLOCKED","No genuine AP20 project created"),
        (5,"Native TIA archive restores","BLOCKED","No genuine ZAP20 archive created"),
        (6,"PLC compiles zero errors","BLOCKED","Static source lint only; native compile not run"),
        (7,"HMI compiles zero errors","BLOCKED","WinCC project not created"),
        (8,"Startdrive configured/reviewed","BLOCKED","Startdrive not installed and motor data absent"),
        (9,"PLCSIM traces pass","BLOCKED","PLCSIM not installed; Python simulator is independent evidence"),
        (10,"Revision-C QET reopens and reconciles","BLOCKED","Historical revision-A native baseline only"),
        (11,"Schematics visual review","BLOCKED","Revision-C schematics not yet created"),
        (12,"Revision-C FCStd reopens","BLOCKED","Historical baseline only"),
        (13,"STEP/IGES/DXF reimport","BLOCKED","Revision-C exchange files not created"),
        (14,"Full BOM/panel layout reconcile","PARTIAL","Expanded controlled schedules; unresolved selections and native CAD remain open"),
        (15,"Electrical calculations confirmed","BLOCKED","Site supply, fault current, loads and environmental inputs missing"),
        (16,"Real NVIDIA dataset controlled","BLOCKED","No real dataset supplied"),
        (17,"Genuine model training/evaluation","BLOCKED","No dataset or TAO runtime"),
        (18,"TensorRT/DeepStream target runtime","BLOCKED","No selected target carrier/runtime"),
        (19,"PLC-NVIDIA failure tests","PASS","Local source-design scope: 20 simulator tests, 32 scenarios, 11 edge tests and 6 interface-harness tests pass; native integration remains blocked under gates 9 and 18"),
        (20,"FAT/SAT/commissioning","OPEN","Procedures issued, never executed"),
        (21,"Qualified safety activities","BLOCKED","External qualified work required"),
        (22,"Manifest independently verifies","PASS","Final deterministic JSON/CSV verifier reports zero missing, unlisted or mismatched files on the frozen release tree; regenerate after any file change"),
    ]
    return [{"gate":a,"acceptance_gate":b,"status":c,"evidence_or_blocker":d} for a,b,c,d in gates]


def _write_control(root: Path, model: dict) -> None:
    _csv(root,"00_project_control/revision_history.csv",[
        {"revision":"A","date":"2026-06-28","status":"Historical baseline","description":"Inherited QET/FreeCAD evidence baseline"},
        {"revision":"B","date":"2026-08-01","status":"Published preliminary","description":"Initial Siemens/NVIDIA architecture and schedules"},
        {"revision":"C","date":"2026-08-02","status":"Controlled partial release","description":"Corrected generator/SCL/HMI/drive/network/manifest; dynamic simulation and expanded schedules/docs"},
    ])
    _csv(root,"00_project_control/engineering_change_register.csv",[
        {"ecr":"ECR-C-001","reason":"Correct malformed Siemens sources and implement cyclic integration","affected":"scripts/build_project.py; 04_controls_siemens/scl","compatibility":"TIA V20 source design; native compile open","test_impact":"Static SCL lint and call-graph checks","risk":"Uncompiled source may require TIA syntax correction","migration":"Import in documented order; compile before use"},
        {"ecr":"ECR-C-002","reason":"Separate HMI commands from physical outputs","affected":"Canonical HMI model; HMI schedule; command manager","compatibility":"WinCC tag import must be rebuilt","test_impact":"Direct-output-write negative checks","risk":"HMI project absent","migration":"Bind only DB_HMI command requests and response fields"},
        {"ecr":"ECR-C-003","reason":"Make PROFINET Standard Telegram 1 the drive primary interface","affected":"PLC I/O; drive PZD schedule; FB_VFD","compatibility":"Hardwired run/status removed","test_impact":"Telegram reconciliation","risk":"Startdrive/native addresses unconfirmed","migration":"Confirm PZD in native TIA/Startdrive before commissioning"},
        {"ecr":"ECR-C-004","reason":"Replace unmanaged/misidentified switch architecture","affected":"Hardware, network, BOM, panel","compatibility":"Adds XC208 and S615","test_impact":"Network allow-list review","risk":"Site cyber policy absent","migration":"Native firewall/switch configuration required"},
        {"ecr":"ECR-C-005","reason":"Replace lookup-table simulation and expand electrical control data","affected":"11_simulation; canonical schedules; QA","compatibility":"CSV schemas changed","test_impact":"Dynamic properties, traces, manifest","risk":"No native/physical proof","migration":"Use independent evidence only"},
    ])
    _csv(root,"00_project_control/input_request_register.csv",model["input_requests"])
    _csv(root,"00_project_control/acceptance_gates.csv",model["acceptance_gates"])
    _csv(root,"00_project_control/decision_register.csv",[
        {"decision_id":"ADR-C-001","decision":"TIA Portal V20 remains authoritative; CPU baseline is 1AL03 FS03/FW4.0","rationale":"Official manual identifies native V20 support for FW4.0; later FW4.1 requires reviewed handling","consequence":"Delivered CPU state must be checked; FS04/FW4.1 may require V21 or predecessor-mode validation"},
        {"decision_id":"ADR-C-002","decision":"G120C Standard Telegram 1 is primary control","rationale":"Removes contradictory hardwired run/status architecture","consequence":"STO remains external; native Startdrive confirmation is mandatory"},
        {"decision_id":"ADR-C-003","decision":"XC208 plus S615 implements three network zones","rationale":"XB008 6GK5008-0BA10-1AB2 is unmanaged and cannot implement VLAN/firewall policy","consequence":"Exact configuration and site approval remain open"},
        {"decision_id":"ADR-C-004","decision":"Quality uncertainty always holds product","rationale":"NVIDIA is non-safety quality inspection and cannot grant transfer without matched result","consequence":"Operator disposition confirms removal; reset never releases held product"},
    ])
    _csv(root,"00_project_control/ownership.csv",[
        {"workstream":"00-02/release","author":"Chief systems integrator","reviewer":"Independent package reviewer","status":"Integrated"},
        {"workstream":"04-06","author":"Chief systems integrator","reviewer":"Independent Siemens reviewer","status":"Source-design APPROVE; native TIA/WinCC/Startdrive/PLCSIM review open"},
        {"workstream":"11 simulation","author":"Simulation/vision workstream","reviewer":"Independent vision reviewer","status":"20 simulator, 11 edge and 6 interface-harness tests passed; independent of PLC/native runtime"},
        {"workstream":"03/09/10/13","author":"Chief systems integrator","reviewer":"Independent electrical/package reviewer","status":"Canonical schedule/package APPROVE; native QET/CAD and physical calculations open"},
    ])


def _write_documents(root: Path) -> None:
    docs = {
        "13_documentation/functional_design_specification.md": ("Functional design specification", """## Scope and state model

The machine indexes exactly two bottles, proves conveyor stopped, closes the gate, engages the clamp, fills two independently metered channels from one pump, settles drips, obtains a matched non-safety vision result, then handshakes the accepted pair to the capper. States are UNINITIALIZED, INITIALIZING, STOPPED, READY, AUTOMATIC, MANUAL_SETUP, HOLDING, CONTROLLED_STOPPING, FAULTED and RECOVERY_RESET.

## Automatic sequence

| Step | Entry condition | Commands | Completion | Failure response |
|---|---|---|---|---|
| Index | New Start edge in READY | Conveyor speed request | Two nest sensors true | Stop/hold on missing or contradictory sensing |
| Secure | Conveyor stopped | Gate close, clamp engage | Both feedbacks true | Equipment timeout fault |
| Fill | Secured pair and valid recipe | Pump, two independent valves | Both close-confirmed in tolerance | Close valves, stop pump, hold |
| Drip | Both channels complete | Pump/valves off | Recipe timer expires | Controlled stop on blocking fault |
| Inspect | Fresh monotonic ID | Camera light and trigger | Matched, valid, high-confidence result | HOLDING on late/stale/uncertain/fail |
| Transfer | Process and quality accepted | Capper request | Busy then complete | HOLDING/FAULTED on order/timeout/fault |
| Release | Capper complete | Gate open, clamp release | Pair absent and actuators released | No new cycle until confirmed |

## Recovery rules

Reset clears eligible latches only. Power or communication recovery sets a recovery-required condition and returns to STOPPED; a new reset release and new Start edge are mandatory. Held product requires supervised physical removal and a disposition sequence. Reset cannot accept uncertain quality."""),
        "13_documentation/software_design_specification.md": ("Software design specification", """## Ownership and scan order

`Main` calls the single `DB_CellMain` instance. `FB_CellMain` owns command sequencing, two VFD instances, gate, clamp, two fill channels, recipe, vision, capper, alarm and coordinator instances. The cyclic order is input normalization, command arbitration, equipment status/control, sequencing, alarm mapping and final physical output mapping.

## Data separation

`DB_IO.Inputs` is the normalized field image; `DB_IO.Commands` is written only by the final mapper. `DB_HMI` contains request/sequence/accept/reject/disabled-reason structures and never aliases physical outputs. `DB_Drives` carries Standard Telegram 1 PZD. `DB_VisionComms` is the OPC UA contract. `DB_Recipe` separates candidate and active data.

## Diagnostic policy

Reusable blocks emit reason codes; the cell maps reason plus equipment identity to unique alarm IDs. Timers and edges are instance-owned. All standard outputs de-energize on loss of release permissive. Simulation forcing is absent from release sources. Static checks are not native compile proof."""),
        "13_documentation/alarm_philosophy.md": ("Alarm philosophy", """## Classes and behavior

Faults cause controlled stop, abort or quality hold according to the alarm schedule. Warnings never imply product acceptance. First-out records the initiating alarm; later alarms remain visible. Acknowledgement records awareness only. Reset is accepted only when the source condition has cleared and never creates motion.

## Alarm record requirements

Each alarm has unique ID, equipment source, cause, response, acknowledgement policy, reset condition and linked verification. Fill-channel reusable reason codes are mapped separately for channel 1 and channel 2. Communications, stale IDs and low confidence all prevent transfer.

## Shelving and suppression

Safety-status mirrors, drive faults, fill faults and quality holds are not shelvable by operators. Maintenance suppression is permitted only in stopped maintenance state, is time limited, role controlled and logged in the eventual native HMI."""),
        "13_documentation/network_cybersecurity.md": ("Network and cybersecurity design", """## Zones

VLAN 10 is cell control (PLC, HMI, two drives), VLAN 20 is quality vision, and VLAN 99 is temporary engineering service. A managed SCALANCE XC208 provides port-based VLANs; a SCALANCE S615 routes only approved inter-zone flows. The former 6GK5008-0BA10-1AB2 selection was corrected: it is an unmanaged XB008 and is not used for zoning.

## Allow list

| Source | Destination | Service | Policy |
|---|---|---|---|
| Vision VLAN 20 | PLC VLAN 10 | OPC UA TCP 4840 | Allow only named client certificate and approved namespace |
| HMI/Drives VLAN 10 | PLC VLAN 10 | Native PROFINET/HMI traffic | Allow within control zone |
| Engineering VLAN 99 | Approved nodes | Native engineering services | Disabled in production; maintenance change window only |
| Any other | Any | Any | Deny and log |

## Identity and certificates

Use unique device certificates, site CA trust, encrypted private-key storage, expiry monitoring, revocation/change records and least-privilege OPC UA node rights. Anonymous access and shared engineering accounts are prohibited. Final cipher suites, time source, logging retention and vulnerability response require site OT approval."""),
        "13_documentation/electrical_calculation_report.md": ("Electrical calculation report", """## Status

No construction calculation is released because supply system, fault current, motor data, cable lengths, ambient, IP rating and regulatory basis are missing. The controlled load schedule is a design estimate only.

## Required calculations

| Calculation | Method/input | Acceptance | Status |
|---|---|---|---|
| 24 VDC PSU | Sum steady loads + inrush + derating + 25% design margin | Worst-case voltage remains within every device range | Preliminary 20 A concept; open |
| Branch protection | Load current, conductor ampacity, device withstand | Coordinated protection and documented interrupt rating | Open |
| Voltage drop | 2 x length x current x conductor resistance | Within device/valve minimum voltage | Open |
| Fault/SCCR | Site available current and component ratings | Assembly rating approved for site | Blocked |
| Thermal | Device losses, enclosure, ambient and altitude | Internal temperature below derated limits | Blocked |
| Duct fill | Actual conductor OD/area and bend requirements | Supplier fill and bend limits met | Open |

False precision is prohibited; values remain open until approved inputs and manufacturer data are attached."""),
        "13_documentation/panel_design_report.md": ("Panel design report", """## Layout basis

The schedule reserves an 800 x 800 mm mounting plate with separate PLC/analog, network, 24 VDC, VFD heat, field-terminal and PE zones. The HMI is door-mounted, not placed on the backplate. Core Siemens envelopes use official data-sheet dimensions; unresolved drive, firewall and Jetson envelopes remain blank and explicitly block native CAD completion.

## Segregation and service

Mains/VFD input and motor output routes remain separated from 24 VDC, analog/HSC and Ethernet. Analog shields terminate at the panel shield-clamp rail. Drives reserve 100 mm top/bottom service airflow until exact model manuals are confirmed. Terminals reserve front service access and spare capacity.

## Open native evidence

The inherited FCStd/STEP/IGES/DXF files are historical baselines only. A revision-C assembly, collision check, FCStd reopen and exchange-format reimport are mandatory before the panel gate can pass."""),
        "13_documentation/backup_recovery.md": ("Backup and recovery procedure", """## Create

After native gates pass, record TIA/WinCC/Startdrive versions, compile reports and warnings; create a TIA archive; export sources, tag/alarm tables, drive parameters and certificates without private keys; archive HMI configuration and the signed edge bundle; generate the final manifest.

## Restore test

Restore into an isolated clean environment, confirm device catalogs and firmware, compile PLC/HMI, compare hardware/network settings, restore drive parameters only to identified test hardware, verify OPC UA trust and execute smoke/negative tests. Record operator, reviewer, date, hashes and deviations.

## Acceptance

An untested backup is not a recovery capability. Production release requires a successful restore record, access-control review and rollback path. No native archive exists in this revision."""),
        "13_documentation/commissioning_maintenance.md": ("Commissioning and maintenance manual", """## Commissioning stages

1. Approve documents, open issues and qualified safety work.
2. Perform de-energized construction inspection, PE continuity and torque verification.
3. Energize by branch with approved instruments and temporary controls.
4. Execute point-to-point I/O checkout, drive rotation, actuator dry tests and fault injection.
5. Perform wet calibration, flowmeter comparison, recipe tuning and leakage/closure tests.
6. Complete optical calibration, real-product challenge testing and capper integration.
7. Compile/archive/backup, train users and obtain signed FAT/SAT deviations.

## Preventive tasks

Maintain terminal torque per manufacturer, filters/fans, earth/shield bonds, valve leakage, flowmeter calibration, camera/lights/optics, drive faults and model/certificate versions. Energy isolation and external safety procedures are site responsibilities."""),
        "13_documentation/operator_training.md": ("Operator training document", """## Learning objectives

Operators distinguish Stop, Reset, Start and Alarm Acknowledge; interpret state/disabled reason/first-out; manage recipes; recognize quality holds; and document physical disposition. Maintenance users understand role-controlled manual requests and field diagnostics.

## Prohibited assumptions

Reset does not start. Vision is neither a safety function nor legal metrology. A low-confidence, late, stale or mismatched inspection cannot permit transfer. Standard PLC/HMI diagnostics do not replace energy isolation or qualified safety procedures.

## Training record

Record trainee, role, trainer, date, revision, practical exercise, result and retraining due date. Training remains unexecuted until the native HMI and machine are available."""),
        "13_documentation/model_deployment_rollback.md": ("NVIDIA model deployment and rollback procedure", """## Preconditions

A controlled real dataset, approved model card, held-out metrics, target Jetson/JetPack/DeepStream compatibility, signed bundle, security approval and measured latency/thermal evidence are mandatory. None exists in this revision.

## Deployment

Verify bundle signature and SHA-256, confirm model ID/hash namespace, install in an inactive slot, run challenge-set and interface smoke tests, switch during an approved window, then monitor heartbeat, latency, dropped frames and false decisions.

## Rollback

On health, semantic, latency or quality failure, force PLC quality hold, restore the previous signed bundle, repeat smoke tests and record reason/operator/time/hashes. Never fabricate an engine, metric or acceptance result."""),
    }
    for rel,(title,body) in docs.items():
        _write(root,rel,_doc(title,body))


def _write_test_procedures(root: Path, tests: list[dict]) -> None:
    lines = ["## Preconditions", "", "Approved design inputs; isolated simulator or approved test system; named software versions; calibrated stimuli where physical; deviation log; reviewer assigned.", "", "## Controlled test records", "", "| Test ID | Scenario | Initial state | Action | Expected result | Actual result | Status | Evidence | Tester/date | Reviewer/date |", "|---|---|---|---|---|---|---|---|---|---|"]
    for test in tests:
        lines.append(f"| {test['test_id']} | {test['scenario']} | STOPPED, outputs off | Inject at controlled scenario time; inspect intermediate transitions and latches | {test['expected']} | Not entered in FAT | NOT EXECUTED | Python trace is design evidence only |  |  |")
    _write(root,"12_testing/FAT_procedure.md",_doc("Factory acceptance test procedure — planned, not executed","\n".join(lines)))
    sat = """## Preconditions

Approved FAT deviations, released native projects, qualified safety validation plan, construction inspection, calibrated instruments, site permits and owner witnesses.

## Records

| Test ID | Initial state | Step-by-step action | Expected/acceptance | Actual | Pass/fail | Deviation | Tester/date | Reviewer/date | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| SAT-001 | De-energized | Inspect nameplates, conductors, terminals, PE, shields and torque | Matches released drawings/schedules |  |  |  |  |  |  |
| SAT-002 | Branches isolated | Measure PE continuity and insulation using approved methods | Project/site acceptance criteria met |  |  |  |  |  |  |
| SAT-003 | Controlled power-up | Energize branches and record voltage/current/inrush | Within approved calculation limits |  |  |  |  |  |  |
| SAT-004 | STOPPED | Stimulate every I/O and diagnostic | Exactly one correct tag changes; outputs remain controlled |  |  |  |  |  |  |
| SAT-005 | Test product present | Execute dry and wet normal/fault cycles | Sequence, accuracy, holds and recovery meet approved requirements |  |  |  |  |  |  |
| SAT-006 | Vision calibrated | Execute held-out challenge set on target | Approved metrics/latency/thermal limits met |  |  |  |  |  |  |
| SAT-007 | Backup available | Restore to isolated target and run smoke tests | Restore/compile/hash checks pass |  |  |  |  |  |  |

No SAT, physical commissioning or safety validation has been executed."""
    _write(root,"12_testing/SAT_procedure.md",_doc("Site acceptance test procedure — planned, not executed",sat))


def apply_revision_c(root: Path) -> None:
    model_path = root / "00_project_control/canonical_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    hardware = _hardware()
    for row in hardware:
        row["full_designation"] = _designation(row["tag"], "CP01")
    io = _reconcile_io(model["io"])
    drives = _drive_interfaces()
    hmi = _hmi_tags(io)
    bom = _bom(hardware, io)
    connections, terminals, cables = _connections(io)
    panel = _panel(hardware)
    for row in panel:
        row["full_designation"] = _designation(row["tag"], "CP01")
    for row in bom:
        row["full_designation"] = _designation(row["tag"], "CP01" if row["scope"] in {"Panel","Panel/field hardware"} else "FLD")
    load_budget = [
        {"load":"PLC CPU and I/O","voltage":"24 VDC","nominal_w":55,"demand_factor":1.0,"demand_w":55,"basis":"Preliminary allowance; verify Siemens configuration"},
        {"load":"HMI","voltage":"24 VDC","nominal_w":24,"demand_factor":1.0,"demand_w":24,"basis":"Maximum-current allowance from product data"},
        {"load":"Relays, sensors and solenoids","voltage":"24 VDC","nominal_w":150,"demand_factor":0.8,"demand_w":120,"basis":"Duty-cycle allowance; inrush not finalized"},
        {"load":"Vision edge + camera + lighting","voltage":"24 VDC","nominal_w":100,"demand_factor":1.0,"demand_w":100,"basis":"Placeholder pending selected carrier/camera"},
        {"load":"24 VDC subtotal","voltage":"24 VDC","nominal_w":329,"demand_factor":1.0,"demand_w":299,"basis":"12.46 A demand; retain >=25% margin; provisional 20 A PSU after inrush check"},
        {"load":"Conveyor drive","voltage":"400 VAC","nominal_w":750,"demand_factor":1.0,"demand_w":750,"basis":"Motor nameplate not supplied"},
        {"load":"Pump drive","voltage":"400 VAC","nominal_w":750,"demand_factor":1.0,"demand_w":750,"basis":"Pump curve/motor nameplate not supplied"},
    ]
    vfd_parameters = [
        {"drive":"-U100/-U101","parameter":"Primary control","value":"PROFINET Standard Telegram 1","status":"Design baseline; native confirmation open"},
        {"drive":"-U100/-U101","parameter":"PZD","value":"STW1/NSOLL_A and ZSW1/NIST_A, 2 words each direction","status":"Addresses controlled in drive interface schedule"},
        {"drive":"-U100/-U101","parameter":"Scaling","value":"Signed 16384 = 100 percent reference speed","status":"Reference speed/motor data open"},
        {"drive":"-U100/-U101","parameter":"Hardwired standard I/O","value":"None for run/ready/running/fault","status":"Removed from PLC physical I/O"},
        {"drive":"-U100/-U101","parameter":"STO","value":"External conceptual safety interface only","status":"Qualified safety design required"},
        {"drive":"-U100/-U101","parameter":"Ramps/current/min/max/braking/EMC","value":"Not selected","status":"Motor, mechanics, supply and cable inputs required"},
    ]
    alarms = []
    def alarm(alarm_id: int, message: str, response: str, alarm_class: str = "Fault") -> None:
        alarms.append({"alarm_id":alarm_id,"message":message,"class":alarm_class,"response":response,"ack_required":"Yes","reset_condition":"Cause cleared and explicit reset; never automatic restart"})
    alarm(1001,"Emergency/safety chain not healthy","De-energize controlled outputs; external safety restoration and reset required")
    alarm(1002,"Air pressure lost","Abort fill, close valves, stop pump and hold")
    alarm(1003,"Product supply lost","Abort fill, close valves, stop pump and hold")
    alarm(1004,"Guard status not closed","De-energize standard motion/process commands; qualified safety design remains external")
    alarm(1101,"Conveyor VFD fault or PN I/O invalid","Stop motion and hold")
    alarm(1102,"Pump VFD fault or PN I/O invalid","Close valves, stop pump request and hold")
    alarm(1201,"Gate feedback contradiction or travel timeout","Stop conveyor and hold")
    alarm(1202,"Clamp feedback contradiction or travel timeout","Close valves, stop pump and hold")
    fill_reasons = [(1,"no flow"),(3,"pulse/analog disagreement"),(4,"underfill"),(5,"overfill"),(6,"valve close mismatch"),(7,"analog channel broken wire"),(8,"valve open mismatch"),(9,"continued flow after close"),(10,"invalid configuration/fill timeout/abort")]
    for channel, base in [(1,1300),(2,1310)]:
        for suffix, reason in fill_reasons:
            alarm(base+suffix,f"Fill channel {channel} {reason}",f"Close channel {channel}; stop pump when both valves closed; quality hold")
    alarm(1401,"Capper not ready, acceptance timeout or completion timeout","Keep pair controlled; operator disposition")
    alarm(1402,"Capper reported fault or invalid handshake order","Keep pair controlled; operator disposition")
    for alarm_id, message in [(1501,"Vision not ready"),(1502,"Vision result timeout"),(1503,"Vision stale/mismatched result ID"),(1504,"Vision blocking quality result or low confidence"),(1505,"Vision heartbeat lost"),(1506,"Vision protocol contradiction")]:
        alarm(alarm_id,message,"Do not transfer; quality hold")
    alarm(1601,"HMI command heartbeat lost","Reject new HMI commands and enter controlled fault handling")
    for index, test in enumerate(model["tests"], 1):
        scenario = test["scenario"]
        if scenario == "normal_two_bottle_cycle":
            test["expected"] = "Exactly one pair releases only after independent fill completion, matched passing vision result and capper completion; no invariant violation"
        else:
            test["expected"] = f"Inject {scenario.replace('_',' ')}; no product release, pump/valves decommand on first-out condition, controlled HOLD/FAULT outcome and no automatic restart"
        test["evidence"] = f"11_simulation/outputs/traces/{scenario}.csv; 11_simulation/outputs/scenario_results.csv"
    trace = {
        "SYS-001":("04_controls_siemens/scl/FB_MachineCoordinator.scl","TC-001; TC-002; TC-003","normal and missing-bottle traces"),
        "SYS-002":("04_controls_siemens/scl/FB_MachineCoordinator.scl","TC-002; TC-003; TC-004; TC-005","bottle-sensor fault traces"),
        "SYS-003":("04_controls_siemens/scl/FB_MachineCoordinator.scl","TC-001; TC-015","normal and conveyor-fault traces"),
        "SYS-004":("04_controls_siemens/scl/FB_Actuator2Pos.scl","TC-006; TC-007; TC-008","actuator timeout/contradiction traces"),
        "SYS-005":("04_controls_siemens/scl/FB_FillChannel.scl; 04_controls_siemens/scl/DB_Global.scl","TC-009; TC-010","no-pulse and pulse/analog traces; native TM Count binding remains open"),
        "SYS-006":("04_controls_siemens/scl/FB_CellMain.scl","TC-014; TC-016; TC-017","pump/utilities fault traces"),
        "SYS-007":("04_controls_siemens/scl/FB_FillChannel.scl","TC-001; TC-012; TC-013","normal, overfill and valve-close traces"),
        "SYS-008":("04_controls_siemens/scl/FB_FillChannel.scl; 10_schedules/plc_io.csv","TC-010","pulse/analog disagreement trace; native AI diagnostics remain open"),
        "SYS-009":("04_controls_siemens/scl/FB_FillChannel.scl","TC-009; TC-010; TC-011; TC-012; TC-013","five fill-fault traces"),
        "SYS-010":("04_controls_siemens/scl/FB_CellMain.scl; 04_controls_siemens/scl/FB_RecipeManager.scl","TC-001","normal trace includes drip-settle state"),
        "SYS-011":("04_controls_siemens/scl/FB_VisionInterface.scl","TC-001; TC-024","normal and stale-ID traces"),
        "SYS-012":("04_controls_siemens/scl/FB_VisionInterface.scl","TC-023; TC-024","vision timeout and stale-ID traces"),
        "SYS-013":("04_controls_siemens/scl/FB_VisionInterface.scl","TC-022; TC-023; TC-025; TC-026; TC-027","vision uncertainty/failure traces"),
        "SYS-014":("04_controls_siemens/scl/FB_MachineCoordinator.scl","TC-001; TC-022; TC-025; TC-026","normal release and quality-hold traces"),
        "SYS-015":("04_controls_siemens/scl/FB_CapperInterface.scl","TC-018; TC-019; TC-020","capper not-ready/busy/fault traces"),
        "SYS-016":("04_controls_siemens/scl/OB100_Startup.scl; 04_controls_siemens/scl/FB_MachineCoordinator.scl","TC-029; TC-030; TC-031","power-loss/restoration/reset traces"),
        "SYS-017":("04_controls_siemens/scl/00_types.scl; 04_controls_siemens/scl/FB_MachineCoordinator.scl","TC-001; TC-031; TC-032","normal/recovery/manual traces"),
        "SYS-018":("04_controls_siemens/scl/00_types.scl; 04_controls_siemens/scl/FB_CellMain.scl","VAL-C-STATIC","automated_validation_report.md source/data checks"),
        "SYS-019":("04_controls_siemens/scl/FB_CellMain.scl; 00_project_control/design_basis.md","TC-029; SAFETY-OPEN","power-loss trace; qualified safety validation remains blocked"),
        "SYS-020":("04_controls_siemens/scl/FB_AlarmManager.scl; 10_schedules/alarms.csv","TC-006; TC-009; TC-014; TC-020","first-out fault traces across equipment classes"),
        "SYS-021":("04_controls_siemens/scl/FB_HMICommandManager.scl; 05_hmi/hmi_specification.md","TC-021; TC-032","HMI-loss and manual-interlock traces"),
        "SYS-022":("11_simulation/filling_cell_simulator.py; 11_simulation/tests","TC-001..TC-032","32 scenario traces and 20 unit/property tests"),
        "SYS-023":("00_project_control/canonical_model.json; scripts/validate_project.py","VAL-C-STATIC","Revision-C canonical/source/schedule validation suite; the executed report records the current check count"),
        "SYS-024":("13_documentation/backup_restore.md; scripts/build_manifest.py; scripts/verify_manifest.py","PROC-RESTORE-OPEN; MANIFEST-VERIFY-001","restore execution remains open; final deterministic manifest verification required"),
        "SYS-025":("04_controls_siemens/scl/FB_MachineCoordinator.scl; 13_documentation/functional_design_specification.md","TC-025; TC-026","low-confidence/failed-bottle traces enter HOLDING pending disposition"),
    }
    for requirement in model["requirements"]:
        artifact, test_ids, evidence = trace[requirement["requirement_id"]]
        requirement["design_artifact"] = artifact
        requirement["test_ids"] = test_ids
        requirement["evidence"] = evidence
    network = [
        {"node":"PLC-A100","ip":"192.168.10.10","vlan":10,"switch_port":"XC208 P1","zone":"CONTROL","owner":"Controls","role":"PROFINET controller / OPC UA server","allowed_services":"PROFINET local; OPC UA TCP 4840 from named vision client"},
        {"node":"HMI-H100","ip":"192.168.10.20","vlan":10,"switch_port":"XC208 P2","zone":"CONTROL","owner":"Controls","role":"Unified operator panel","allowed_services":"HMI-to-PLC only"},
        {"node":"VFD-U100","ip":"192.168.10.31","vlan":10,"switch_port":"XC208 P3","zone":"CONTROL","owner":"Drives","role":"Conveyor G120C PN","allowed_services":"PROFINET cyclic/diagnostic only"},
        {"node":"VFD-U101","ip":"192.168.10.32","vlan":10,"switch_port":"XC208 P4","zone":"CONTROL","owner":"Drives","role":"Pump G120C PN","allowed_services":"PROFINET cyclic/diagnostic only"},
        {"node":"VISION-PC200","ip":"192.168.20.10","vlan":20,"switch_port":"XC208 P5","zone":"QUALITY","owner":"Vision","role":"OPC UA client + inference","allowed_services":"OPC UA TCP 4840 to PLC; authenticated time/logging per site policy"},
        {"node":"ENG-SERVICE","ip":"192.168.99.0/24","vlan":99,"switch_port":"XC208 P6","zone":"ENGINEERING","owner":"OT","role":"Temporary service","allowed_services":"Disabled in production; approved maintenance window only"},
        {"node":"FW-S615","ip":"Zone gateways","vlan":"10/20/99","switch_port":"XC208 P7 trunk","zone":"BOUNDARY","owner":"OT security","role":"Router/firewall","allowed_services":"Deny by default; explicit stateful allow list"},
    ]
    model["project"] = {"id":"FC01","revision":"C","date":"2026-08-02","notice":NOTICE,"safety_boundary":SAFETY,"status":"PARTIALLY COMPLETE — ACHIEVABLE DESIGN/QA GATES CLOSED; NATIVE AND PHYSICAL GATES OPEN"}
    model.update({"hardware":hardware,"io":io,"drive_interfaces":drives,"hmi_tags":hmi,"alarms":alarms,"bom":bom,"connections":connections,"terminals":terminals,"cables":cables,"panel_placement":panel,"network":network,"load_budget":load_budget,"vfd_parameters":vfd_parameters,"input_requests":_inputs_required(),"acceptance_gates":_gates()})
    model_path.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    schedules = {
        "siemens_hardware.csv":hardware,"plc_io.csv":io,"drive_interfaces.csv":drives,"hmi_tags.csv":hmi,"alarms.csv":alarms,"bom.csv":bom,"point_to_point_connections.csv":connections,"terminal_plan.csv":terminals,"cable_schedule.csv":cables,"wire_list.csv":connections,"panel_placement.csv":panel,"network_nodes.csv":network,"load_budget.csv":load_budget,"vfd_parameters.csv":vfd_parameters,"requirements_traceability.csv":model["requirements"],"test_coverage.csv":model["tests"],"input_request_register.csv":model["input_requests"],"acceptance_gates.csv":model["acceptance_gates"]
    }
    for name,rows in schedules.items(): _csv(root,f"10_schedules/{name}",rows)

    for name,text in scl_sources().items(): _write(root,f"04_controls_siemens/scl/{name}",text)
    _write(root,"04_controls_siemens/import_order.txt","""1. 00_types.scl
2. FB_Actuator2Pos.scl, FB_VFD.scl, FB_FillChannel.scl, FB_VisionInterface.scl, FB_CapperInterface.scl, FB_RecipeManager.scl, FB_AlarmManager.scl, FB_HMICommandManager.scl, FB_MachineCoordinator.scl
3. DB_Global.scl
4. FB_CellMain.scl
5. DB_CellMain.scl
6. OB1_Call_Structure.scl
7. OB100_Startup.scl

Static design order only. Import and compile in TIA Portal V20 before any deployability claim.
""")
    _write(root,"04_controls_siemens/software_architecture.md",_doc("Siemens PLC software architecture", """`Main` calls the single `DB_CellMain` root instance. The root owns command arbitration, two PROFINET drive blocks, gate, clamp, two fill-channel blocks, vision, capper, recipe, alarm, drip timer and coordinator. Input normalization occurs before equipment calls; the physical-output mapper is last and applies a release permissive.

Physical drives use Standard Telegram 1 at IW/QW 256-263. The explicit `DB_NativeBindings` adapter contract receives PROFINET I/O-valid diagnostics and TM Count technology-object totals/channel faults from native TIA networks; `FB_CellMain` consumes every field. Those native networks are not fabricated and remain gate 6 work. Analog channels are scaled from the Siemens 4-20 mA raw range and include channel-fault/range supervision. `OB100` decommands outputs and sets recovery required.

These are reviewable/import-oriented sources, not a compiled native program. TIA V20 import, hardware configuration, cross-reference review and zero-error compile remain mandatory."""))
    _write(root,"05_hmi/hmi_specification.md",_doc("WinCC Unified HMI specification", """## Screens

Overview/automatic, filling detail, manual/setup, recipe, alarm history, I/O diagnostics, drive diagnostics, NVIDIA inspection, counters/maintenance, and users/security screens are required. Native screen objects do not yet exist.

## Command contract

Every command writes only `DB_HMI.<Command>.Request` and increments `RequestSeq`. The PLC returns AcceptedSeq or RejectedSeq plus Allowed/Busy/DisabledReason. Start, controlled stop, reset, acknowledgement, mode, disposition and recipe apply are separate. Physical DO, PZD, stack lights, camera light and spare channels are never writable HMI tags.

## Security and audit

Operator may start/stop/ack/reset when permitted. Supervisor controls recipes and disposition. Maintenance may use hold-to-run manual requests subject to PLC interlocks and heartbeat. User changes, recipe changes, dispositions, alarm acknowledgements and rejected commands are audit-relevant. Native roles, bindings, trends and compile remain open."""))
    _write(root,"06_drives/drive_control_philosophy.md",_doc("Drive-control and Startdrive philosophy", """Both G120C PN drives use PROFINET Standard Telegram 1 as the sole standard-control path: STW1 and normalized speed reference from PLC; ZSW1 and normalized actual speed to PLC. Comms health, ready, running, stopped and fault are decoded in `FB_VFD`. Hardwired run/ready/running/fault signals have been removed from physical PLC I/O.

External STO remains a conceptual interface owned by qualified safety design and is neither controlled nor credited by the standard PLC. Motor nameplates, overload duty, ramps, speed/current limits, braking, line protection, EMC accessories, cable/shield and loss data are open. Startdrive is not installed, so parameter and compile evidence are not claimed."""))
    _write_control(root, model)
    _write_documents(root)
    _write_test_procedures(root, model["tests"])

    _write(root,"README.md",_doc("FC01 Siemens/NVIDIA compact filling cell — Revision C", """Revision C corrects the generator-origin SCL patch artifacts, replaces comment-only OB1 with a root instance call and startup OB, implements detailed fill diagnostics, separates HMI command handshakes from physical outputs, reconciles G120C control to PROFINET Standard Telegram 1, replaces the misidentified unmanaged switch with a managed switch/firewall architecture, expands BOM/point-to-point/panel/control documents, and replaces lookup-table simulation with a dynamic fault-injection model.

Run `python scripts/build_project.py`, the workbook/PDF builders, simulation tests, `python scripts/validate_project.py`, `python scripts/build_manifest.py`, then `python scripts/verify_manifest.py`. Native TIA/WinCC/Startdrive/PLCSIM, revision-C QET/FreeCAD, physical electrical calculations, real dataset/model/runtime, FAT/SAT and qualified safety gates remain open exactly as recorded."""))
    _write(root,"release/RELEASE_NOTES.md",_doc("Revision C release notes", """This controlled partial release includes corrected source, schedule, dynamic-simulation and documentation evidence plus deterministic manifest build/verification tools. Manifest integrity is asserted only by the final verifier command after all artifacts stop changing; no hard-coded file count is used.

Native Siemens compilation, HMI project, Startdrive, PLCSIM, revised QET/FreeCAD, confirmed electrical calculations, trained NVIDIA model/runtime and physical acceptance remain blocked. No construction, deployability, compliance, safety-performance, FAT, SAT or AI-performance claim is made."""))
    _write(root,"00_project_control/final_release_checklist.md",_doc("Final release checklist - Revision C", """- [x] Revision-C canonical schedules regenerate from one owner.
- [x] Review-oriented SCL source set has 15 generator-owned files and no simulation forcing.
- [ ] Native TIA V20/WinCC/Startdrive projects open and compile.
- [ ] Revision-C QET metadata, continuity, BOM and cross-references pass.
- [ ] Revision-C FCStd and exchange formats reopen with selected device envelopes.
- [ ] Physical electrical calculations, qualified safety validation, AI target execution, FAT and SAT pass.
- [ ] Final manifest verifier passes after every artifact and review record is frozen.

Unchecked items are release blockers for construction or deployment, not missing claims."""))
    _write(root,"00_project_control/dependency_graph.mmd", """flowchart TD
  R[Approved requirements and site inputs] --> C[Revision-C canonical model]
  C --> S[Controlled schedules]
  C --> PLC[Siemens source design]
  C --> HMI[HMI tag/command contract]
  C --> V[Vision protocol and simulator]
  S --> QET[Revision-C QET - blocked]
  S --> CAD[Revision-C panel CAD - blocked]
  PLC --> TIA[Native TIA compile - blocked]
  HMI --> WINCC[Native WinCC compile - blocked]
  V --> TARGET[Dataset/model/Jetson validation - blocked]
  QET --> PHYSICAL[Construction/commissioning - blocked]
  CAD --> PHYSICAL
  TIA --> PHYSICAL
""")
    _write(root,"14_qa/toolchain_audit.md",_doc("Toolchain audit - Revision C", """TIA Portal V20/STEP 7/WinCC components are installed, but license, TIA Openness group membership and a native revision-C compile are not proven. Startdrive and PLCSIM are absent.

A portable QElectroTech 0.100.1-dev executable and inherited historical native evidence exist, but no revision-C schematic was authored or reopened. FreeCAD is not installed; only historical evidence is retained. Revision-C CAD/reimport gates remain blocked.

The NVIDIA GPU/driver are observable, while CUDA Toolkit, Docker, TAO, DeepStream, TensorRT and Omniverse/OpenUSD authoring tools are absent. No dataset, trained model or target Jetson evidence exists."""))
    _write(root,"01_requirements/legacy_tag_migration.md",_doc("Legacy tag migration", """No legacy PLC address is inherited automatically. Revision-C addresses and migration decisions come only from `00_project_control/canonical_model.json` and its generated schedules. Any revision-B reference is historical and must not be imported without review."""))
    _write(root,"03_electrical/README.md",_doc("Electrical design boundary - Revision C", """Revision-C terminal, cable, wire, I/O, load and BOM schedules are in `10_schedules`. They include explicit relay coil/contact/load paths and reference terminals, but are not a construction schematic. Closing the electrical gate requires qualified QElectroTech authoring, native reopen, manufacturer metadata/BOM/xrefs, continuity reconciliation and page-by-page review."""))
    _write(root,"14_qa/acceptance_gate_status.md",_doc("Acceptance gate status — Revision C", "\n".join([f"- Gate {g['gate']}: **{g['status']}** — {g['acceptance_gate']}: {g['evidence_or_blocker']}" for g in model["acceptance_gates"]])))
