import csv
import json
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


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


with (ROOT / "00_project_control/acceptance_gates.csv").open(encoding="utf-8-sig", newline="") as stream:
    gate_rows = list(csv.DictReader(stream))
gate_counts = {name: sum(row["status"] == name for row in gate_rows) for name in ("PASS", "PARTIAL", "BLOCKED", "OPEN")}
cad_evidence = load_json("09_panel_cad/revision_e/native_verification.json")
qet_f_path = ROOT / "03_electrical/revision_f_native_qet/native_reopen_export_evidence.json"
qet_evidence = load_json("03_electrical/revision_f_native_qet/native_reopen_export_evidence.json") if qet_f_path.is_file() else load_json("03_electrical/revision_e/native_verification.json")
qet_sha = qet_evidence.get("controlled_source", {}).get("sha256_before_and_after", qet_evidence.get("controlled_source", {}).get("qet_sha256", "UNAVAILABLE"))
validation_report = (ROOT / "14_qa/automated_validation_report.md").read_text(encoding="utf-8")
validation_passes = sum(line.startswith("- ") for line in validation_report.split("## Errors", 1)[0].splitlines())

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
    canvas.drawString(18 * mm, 10 * mm, "FC01 | Revision F | 2026-08-03 | Evidence summary - not a native acceptance certificate")
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


doc = SimpleDocTemplate(str(OUT), pagesize=landscape(A4), leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=16*mm, title="FC01 Revision F release evidence", invariant=1, pageCompression=1)
story = [
    Paragraph("FC01 compact two-nozzle filling cell", styles["PTitle"]),
    Paragraph("Siemens-authoritative controls and bounded NVIDIA quality architecture", styles["PHead"]),
    Spacer(1, 5*mm),
    Paragraph(NOTICE, styles["PWarn"]), Spacer(1, 3*mm), Paragraph(SAFETY, styles["PWarn"]), Spacer(1, 7*mm),
    table([["Release status", "What is implemented", "What remains blocked"],
           ["NVIDIA IMPLEMENTATION-READINESS RELEASE CANDIDATE", "Revision-F canonical model; Git-object byte authority; 47-node immutable PLC/AI contract; production-shaped edge and dataset tools; 32 process scenarios plus 28 structured behavioral vision fault injections; inherited native CAD/QET evidence.", "TIA/WinCC compile/archive; Startdrive; PLCSIM; final site electrical inputs; real dataset/model/target runtime; physical FAT/SAT and qualified safety work."]], [45*mm, 105*mm, 105*mm]),
    Spacer(1, 8*mm),
    Paragraph("This report is an evidence index. It is not proof of construction readiness, functional safety, native compile, FAT, SAT, electrical test, physical commissioning or AI performance.", styles["PBody"]),
    PageBreak(),
    Paragraph("Integrated architecture and deterministic ownership", styles["PTitle"]),
    Paragraph("The PLC owns all machine sequence, interlocks, timeouts, product disposition and transfer permission. THE NVIDIA VISION SUBSYSTEM IS NON-SAFETY-RELATED AND MUST NOT BE USED AS THE SOLE MEANS OF PERSONNEL PROTECTION, SAFE STOP, GUARD MONITORING OR HAZARDOUS-MOTION CONTROL.", styles["PBody"]),
    table([["Layer", "Owner", "Deterministic responsibility", "Failure behavior"],
           ["Field / power", "Electrical", "Identified device, cable/core, terminal and I/O channel", "Fail-closed valves; external safety removes hazardous energy"],
           ["Equipment control", "S7-1500 FB instances", "Gate, clamp, two fill channels, conveyor/pump VFD, capper", "Module timeout/contradiction fault; outputs safe"],
           ["Machine coordinator", "S7-1500", "Legal states, accepted command edges, no automatic restart", "HOLDING, CONTROLLED_STOPPING or FAULTED"],
           ["Operator interface", "MTP700 Unified", "Role-checked handshake; feedback and disabled reason", "No direct physical-output writes"],
           ["Quality vision", "NVIDIA edge service", "Securely acquire request and publish one correlated immutable result", "Malformed/stale/low-confidence/fault -> quality hold"],
           ["Regression", "Python + asyncua", "Sequence fault injection and encrypted real server/client transport", "Design evidence only; never PLCSIM or production-endpoint proof"]], [38*mm, 42*mm, 105*mm, 70*mm]),
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
    Paragraph("PLC-AI v3 acceptance contract", styles["PTitle"]),
    Paragraph("Transport selection: encrypted OPC UA across a routed quality zone. The PLC publishes one immutable request and holds its request until coherent capture acknowledgement or a terminal result. Results are accepted only for the current session/ID with fresh heartbeat, healthy service/camera/model, approved model/dataset/calibration identities, allowed disposition and reasons, sufficient confidence, valid timing and a non-contradictory payload.", styles["PBody"]),
    table([["PLC-owned nodes (13)", "NVIDIA-owned nodes (34)", "Acceptance rule"],
           ["Enable, trigger, inspection/session identity, recipe/count/fill target, PLC heartbeat, exact result ACK, maintenance mode and expected dataset/calibration IDs", "Ready/busy/capture/state/health; immutable quality payload; disposition/reasons/confidence; model/dataset/calibration identities; diagnostic timestamps/timing; edge heartbeat/diagnostics/queue", "Payload publishes before RESULT_VALID and remains immutable until exact ACK. PLC-derived monotonic result age is authoritative; edge UTC is diagnostic. Any stale, malformed, unhealthy, uncertain or contradictory condition enters HOLD/FAULT."]], [75*mm, 112*mm, 68*mm]),
    Spacer(1, 7*mm),
    Paragraph("The adapter requires Basic256Sha256 SignAndEncrypt, X.509 application/user identity, controlled trust/CRL stores and an exact 47-node typed map. Local certificate-backed asyncua tests use a synthetic endpoint. No model is delivered. No training, ONNX export, TensorRT engine, DeepStream execution, accuracy, confusion matrix, false-accept/reject analysis or production latency is claimed. The RTX 5060 Laptop GPU does not substitute for the absent CUDA/TAO/DeepStream target stack or representative dataset.", styles["PBody"]),
    PageBreak(),
    Paragraph("NVIDIA implementation-readiness engineering", styles["PTitle"]),
    table([["Work package", "Revision-F controlled result", "Open acceptance boundary"],
           ["Acquisition/runtime", "Exactly-once recorded-image source, bounded preprocessing, production-prohibited mock backend and hash-gated ONNX adapter boundary", "Physical camera/lens/light, actual tensor contract and target runtime"],
           ["Dataset/evaluation", "Versioned annotation/manifest schemas, file hashes, lot/session split controls, duplicate/leakage checks and FAR/FRR evaluation math", "Representative independently labeled multi-lot data, approved thresholds and model-change approval"],
           ["Platform policy", "DeepStream 9.1 and TAO 7.0.1 tracked; generic TensorRT 11.1 is not treated as a Jetson compatibility lock", "Selected JetPack/carrier image, CUDA/TensorRT/DeepStream/TAO execution and deployment validation"],
           ["Electrical delta", "Separate provisional 24 V branches: 60 W edge, 12 W camera, 20 W lighting and 8 W service/network; X200 and switch-port reservations", "Selected devices, inrush, protection, cable, voltage-drop, thermal, EMC and native schematic/CAD incorporation"],
           ["Service lifecycle", "Schema-controlled configuration, structured diagnostics, durable event-store boundary, health/metrics, rollback and troubleshooting procedures", "Site PKI/time/retention/privacy policy, production endpoint and operational acceptance"]], [52*mm, 122*mm, 81*mm]),
    Spacer(1, 6*mm),
    Paragraph("Synthetic fixtures and local timing harnesses prove software plumbing only. They cannot authorize production READY, establish optical feasibility, or support any accuracy, false-accept, false-reject, throughput or latency claim.", styles["PWarn"]),
    PageBreak(),
    Paragraph("Validation evidence and release blockers", styles["PTitle"]),
    table([["Gate", "Evidence", "Status"],
           ["Canonical consistency", f"{validation_passes} engineering-validator checks plus 96 dedicated Revision-F checks cover generator parity, schedules, ownership, edge behavioral fault injection, safety boundaries and prohibited artifacts. The standalone electrical delta is not incorporated into every authority.", "PARTIAL"],
           ["Deterministic regression", "99 Siemens/simulator/source/native-contract + 86 edge-service + 17 interface-harness tests; 32 process and 28 structured behavioral fault-injection cases", "SOURCE/LOCAL PASS - not PLCSIM/HIL"],
           ["Workbook", "26 summary/schedule sheets; deterministic normalized build, formula-error scan and all-sheet rendered review", "PASS after final freeze"],
           ["QElectroTech", f"Corrected 26-folio QET {qet_sha[:12]}... reopened at the exact hash and exported natively to 26 pages. All pages reviewed; folio 25 has one clipped in-body safety sentence and automatic cross-reference resolution is unsupported", "NATIVE REOPEN/EXPORT PASS; OVERALL PARTIAL"],
           ["Panel CAD", f"FreeCADCmd reopened {cad_evidence['fcstd']['document_objects']} objects / {cad_evidence['fcstd']['controlled_physical_solids']} controlled solids; STEP solid, IGES bounded-face and DXF/hole reimports verified", cad_evidence['result']],
           ["TIA / WinCC / drives", "V20 installed; no native project, compile, cross-reference, archive restore or Startdrive evidence", "BLOCKED"],
           ["PLCSIM", "Not installed", "BLOCKED"],
           ["NVIDIA software", "86/86 edge tests including 10 certificate-backed local asyncua cases; 47-node map, terminal-before-valid ordering, durable-audit failure interlock and 28-case behavioral injection pass", "PARTIAL - production endpoint/native binding open"],
           ["NVIDIA model/runtime", "Production PLC/PKI, representative dataset, trained model and CUDA/TensorRT/DeepStream target stack absent", "MODEL/RUNTIME BLOCKED"]], [56*mm, 142*mm, 57*mm]),
    Spacer(1, 7*mm),
    Paragraph(f"Gate totals: {gate_counts['PASS']} PASS, {gate_counts['PARTIAL']} PARTIAL, {gate_counts['BLOCKED']} BLOCKED, {gate_counts['OPEN']} OPEN. Release use: controlled design review and continuation in qualified native tools only. Read the manifest, acceptance-gate report and open-input register before work.", styles["PBody"]),
]

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"Created {OUT}")
