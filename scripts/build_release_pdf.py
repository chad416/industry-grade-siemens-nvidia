from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release/FC01_release_evidence.pdf"
NOTICE = "FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION"
SAFETY = ("CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, "
          "VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, "
          "SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.")

font_path = Path(r"C:\Windows\Fonts\arial.ttf")
bold_path = Path(r"C:\Windows\Fonts\arialbd.ttf")
pdfmetrics.registerFont(TTFont("ProjectSans", str(font_path)))
pdfmetrics.registerFont(TTFont("ProjectSans-Bold", str(bold_path)))

navy = colors.HexColor("#12304A")
blue = colors.HexColor("#1F6F9F")
light = colors.HexColor("#EAF1F5")
red = colors.HexColor("#C43D3D")
dark = colors.HexColor("#17242E")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="PTitle", fontName="ProjectSans-Bold", fontSize=23, leading=27, textColor=navy, alignment=TA_LEFT, spaceAfter=8))
styles.add(ParagraphStyle(name="PHead", fontName="ProjectSans-Bold", fontSize=15, leading=19, textColor=navy, spaceBefore=8, spaceAfter=8))
styles.add(ParagraphStyle(name="PBody", fontName="ProjectSans", fontSize=9.2, leading=13, textColor=dark, spaceAfter=6))
styles.add(ParagraphStyle(name="PSmall", fontName="ProjectSans", fontSize=7.2, leading=10, textColor=dark))
styles.add(ParagraphStyle(name="PWarn", fontName="ProjectSans-Bold", fontSize=8, leading=11, textColor=red, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="PTable", fontName="ProjectSans", fontSize=7.2, leading=9.2, textColor=dark))
styles.add(ParagraphStyle(name="PTableHead", fontName="ProjectSans-Bold", fontSize=7.2, leading=9.2, textColor=colors.white))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("ProjectSans", 7)
    canvas.setFillColor(colors.HexColor("#526875"))
    canvas.drawString(18 * mm, 10 * mm, "FC01 | Revision D | 2026-08-02 | Evidence summary - not a native acceptance certificate")
    canvas.drawRightString(279 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def table(data, widths):
    wrapped = []
    for row_index, row in enumerate(data):
        wrapped.append([Paragraph(str(cell), styles["PTableHead"] if row_index == 0 else styles["PTable"]) for cell in row])
    t = Table(wrapped, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "ProjectSans-Bold"), ("FONTNAME", (0, 1), (-1, -1), "ProjectSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("LEADING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C6CF")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


doc = SimpleDocTemplate(str(OUT), pagesize=landscape(A4), leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=16*mm, title="FC01 Revision D release evidence", invariant=1, pageCompression=1)
story = [
    Paragraph("FC01 compact two-nozzle filling cell", styles["PTitle"]),
    Paragraph("Siemens-authoritative controls and bounded NVIDIA quality architecture", styles["PHead"]),
    Spacer(1, 5*mm),
    Paragraph(NOTICE, styles["PWarn"]), Spacer(1, 3*mm), Paragraph(SAFETY, styles["PWarn"]), Spacer(1, 7*mm),
    table([["Release status", "What is implemented", "What remains blocked"],
           ["CONTROLLED ENGINEERING DEVELOPMENT", "Canonical Revision-D model; fail-closed interface recovery; explicit flow windows; separated HMI commands; PROFINET PZD design; expanded rationale/electrical data; 32 timed scenarios; deterministic manifest build/verification.", "Native TIA/WinCC compile/archive; Startdrive; PLCSIM; Revision-D QET/CAD; confirmed electrical inputs; real dataset; TAO/DeepStream/TensorRT execution; physical FAT/SAT."]], [45*mm, 105*mm, 105*mm]),
    Spacer(1, 8*mm),
    Paragraph("This report is an evidence index. It is not proof of construction readiness, functional safety, native compile, FAT, SAT, electrical test, physical commissioning or AI performance.", styles["PBody"]),
    PageBreak(),
    Paragraph("Integrated architecture and deterministic ownership", styles["PTitle"]),
    Paragraph("The PLC owns all machine sequence, interlocks, timeouts and transfer permission. NVIDIA is a standard quality-inspection device and cannot perform or bypass safety functions.", styles["PBody"]),
    table([["Layer", "Owner", "Deterministic responsibility", "Failure behavior"],
           ["Field / power", "Electrical", "Identified device, cable/core, terminal and I/O channel", "Fail-closed valves; external safety removes hazardous energy"],
           ["Equipment control", "S7-1500 FB instances", "Gate, clamp, two fill channels, conveyor/pump VFD, capper", "Module timeout/contradiction fault; outputs safe"],
           ["Machine coordinator", "S7-1500", "Legal states, accepted command edges, no automatic restart", "HOLDING, CONTROLLED_STOPPING or FAULTED"],
           ["Operator interface", "MTP700 Unified", "Role-checked handshake; feedback and disabled reason", "No direct physical-output writes"],
           ["Quality vision", "Jetson / DeepStream", "Acquire, infer and publish correlated result", "Timeout/stale ID/low confidence/fault -> quality hold"],
           ["Regression", "Python simulator", "Interface and sequence fault injection", "Design evidence only; never PLCSIM proof"]], [38*mm, 42*mm, 105*mm, 70*mm]),
    Spacer(1, 7*mm),
    Paragraph("Machine states: UNINITIALIZED, INITIALIZING, STOPPED, READY, AUTOMATIC, MANUAL_SETUP, HOLDING, CONTROLLED_STOPPING, FAULTED and RECOVERY_RESET. Reset returns to STOPPED and never initiates motion.", styles["PBody"]),
    PageBreak(),
    Paragraph("Selected Siemens and edge hardware baseline", styles["PTitle"]),
    table([["Function", "Selected item", "Order number / status", "Verification boundary"],
           ["PLC", "SIMATIC S7-1500 CPU 1511-1 PN", "6ES7511-1AL03-0AB0", "Current official lifecycle checked; V20 device catalog/compile open"],
           ["Pulse counting", "TM Count 2x24V", "6ES7550-1AA01-0AB0", "Two independent 24 V pulse channels; TIA configuration open"],
           ["DI / DO / AI", "DI 32 HF; DQ 32 HF; AI 8xU/I HF", "6ES7521-1BL00-0AB0; 6ES7522-1BL01-0AB0; 6ES7531-7NF00-0AB0", "Front connectors, wiring and catalog compatibility open"],
           ["HMI", "MTP700 Unified Comfort", "6AV2128-3GB06-0AX1", "WinCC V20 compile/licence open"],
           ["Drives", "Two SINAMICS G120C PN 0.75 kW", "6SL3210-1KE12-3UF2", "Ratings provisional; Startdrive absent"],
           ["Network", "SCALANCE XC208 managed plus S615 firewall", "6GK5208-0BA00-2AC2; 6GK5615-0AA01-2AA2", "VLAN/firewall architecture selected; native policy and site approval open"],
           ["Vision", "Jetson Orin NX 16GB on industrial carrier", "Carrier/integration SKU TBD", "Carrier, thermals, EMC, camera and real dataset open"]], [38*mm, 68*mm, 82*mm, 67*mm]),
    Spacer(1, 6*mm),
    Paragraph("Authoritative engineering target: TIA Portal V20, executable/product version 2000.0.9501.1. Installed STEP 7 and WinCC V20 components do not prove usable licence entitlement. Current identity is not authorized for TIA Openness. Startdrive and PLCSIM are absent.", styles["PBody"]),
    PageBreak(),
    Paragraph("PLC-AI acceptance contract", styles["PTitle"]),
    Paragraph("Transport selection: OPC UA across a routed quality zone. The PLC publishes an atomic request and one-shot trigger. Results are accepted only with the current ID, fresh heartbeat, ready state, valid flag and non-contradictory payload.", styles["PBody"]),
    table([["PLC -> NVIDIA", "NVIDIA -> PLC", "Acceptance rule"],
           ["VISION_ENABLE; INSPECTION_TRIGGER; INSPECTION_ID; SESSION_EPOCH; RECIPE_ID; EXPECTED_BOTTLES; TARGET_FILL_LEVEL; PLC_HEARTBEAT; RESULT_ACK_ID", "VISION_READY; VISION_BUSY; RESULT_VALID; RESULT_ID; bottle/fill semantics; warning/fault; MODEL_ID; MODEL_SHA256; INFERENCE_TIME; VISION_HEARTBEAT", "Payload publishes before RESULT_VALID and remains immutable until matching ACK. ID must be fresh/nonzero; heartbeat fresh; no contradiction/uncertainty. Otherwise HOLDING."]], [75*mm, 112*mm, 68*mm]),
    Spacer(1, 7*mm),
    Paragraph("No model is delivered. No training, ONNX export, TensorRT engine, DeepStream execution, metric, confusion matrix, false-accept/false-reject analysis or latency benchmark is claimed. The available RTX 5060 Laptop GPU does not substitute for the absent CUDA/TAO/DeepStream stack or representative dataset.", styles["PBody"]),
    PageBreak(),
    Paragraph("Validation evidence and release blockers", styles["PTitle"]),
    table([["Gate", "Evidence", "Status"],
           ["Canonical consistency", "VAL-D-STATIC covers Revision-D source-generator parity, UDT/DB semantics, schedules, HMI isolation, drive/native-adapter contracts, relay paths, baseline hashes and no-fake artifacts", "PASS"],
           ["Deterministic regression", "48 simulator/interface-oracle + 35 edge-service + 15 interface-harness tests; 32 timed scenarios; one release; zero invariant violations/restarts", "PASS - not PLCSIM"],
           ["Workbook", "20 schedule/summary sheets rendered; formula-error scan returned zero matches; contact-sheet and detailed visual review", "PASS"],
           ["QElectroTech", "Audited inherited hash and structure only; no runnable QET found and no Revision-D reopen/export", "REVISION-D GATE BLOCKED"],
           ["Panel CAD", "Audited inherited FCStd/STEP/IGES/DXF hashes only; no runnable FreeCAD and no Revision-D reopen/reimport", "REVISION-D GATE BLOCKED"],
           ["TIA / WinCC / drives", "V20 installed; no native project, compile, cross-reference, archive restore or Startdrive evidence", "BLOCKED"],
           ["PLCSIM", "Not installed", "BLOCKED"],
           ["NVIDIA model/runtime", "Hardware detected; runtime stack and dataset absent", "BLOCKED"]], [56*mm, 142*mm, 57*mm]),
    Spacer(1, 7*mm),
    Paragraph("Release use: controlled design review and continuation in qualified native tools only. Read release/RELEASE_NOTES.md, release/manifest.json, 14_qa/acceptance_gate_status.md and 00_project_control/open_issues.csv before work.", styles["PBody"]),
]

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"Created {OUT}")
