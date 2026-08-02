import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "file:///C:/Users/chand/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const root = process.cwd();
const scheduleDir = path.join(root, "10_schedules");
const previewDir = path.join(root, "14_qa", "workbook_renders");
await fs.mkdir(previewDir, { recursive: true });

const sheets = [
  ["siemens_hardware.csv", "Siemens Hardware"],
  ["plc_io.csv", "PLC I-O"],
  ["drive_interfaces.csv", "Drive PZD"],
  ["hmi_tags.csv", "HMI Tags"],
  ["alarms.csv", "Alarms"],
  ["vfd_parameters.csv", "VFD Parameters"],
  ["nvidia_interface_tags.csv", "NVIDIA Interface"],
  ["network_nodes.csv", "Network Nodes"],
  ["terminal_plan.csv", "Terminal Plan"],
  ["point_to_point_connections.csv", "Point-to-Point"],
  ["cable_schedule.csv", "Cable Schedule"],
  ["wire_list.csv", "Wire List"],
  ["bom.csv", "BOM"],
  ["load_budget.csv", "Load Budget"],
  ["panel_placement.csv", "Panel Placement"],
  ["requirements_traceability.csv", "Requirements Trace"],
  ["test_coverage.csv", "Test Coverage"],
  ["input_request_register.csv", "Input Requests"],
  ["acceptance_gates.csv", "Acceptance Gates"],
];

// IEC 81346 designations intentionally begin with "=".  Protect those CSV
// fields from being interpreted as spreadsheet formulas while retaining the
// visible designation text (the leading apostrophe is an Excel text marker).
function protectDesignationText(csvText) {
  return csvText.replace(/(^|,)(=FC01\+)/gm, "$1'$2");
}

const firstCsv = protectDesignationText(await fs.readFile(path.join(scheduleDir, sheets[0][0]), "utf8"));
const workbook = await Workbook.fromCSV(firstCsv, { sheetName: sheets[0][1] });
for (const [file, name] of sheets.slice(1)) {
  await workbook.fromCSV(protectDesignationText(await fs.readFile(path.join(scheduleDir, file), "utf8")), { sheetName: name });
}

function columnName(index) {
  let n = index + 1;
  let text = "";
  while (n > 0) {
    n -= 1;
    text = String.fromCharCode(65 + (n % 26)) + text;
    n = Math.floor(n / 26);
  }
  return text;
}

for (const sheet of workbook.worksheets.items) {
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  const used = sheet.getUsedRange();
  const values = used.values;
  const rowCount = values.length;
  const colCount = values[0].length;
  if (rowCount > 30 || colCount > 10) sheet.freezePanes.freezeColumns(1);
  const last = columnName(colCount - 1);
  used.format = {
    font: { size: 9, color: "#15232D" },
    verticalAlignment: "top",
    wrapText: true,
    borders: { preset: "insideHorizontal", style: "thin", color: "#D5DEE5" },
  };
  sheet.getRange(`A1:${last}1`).format = {
    fill: "#12304A",
    font: { bold: true, color: "#FFFFFF", size: 9 },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${last}1`).format.rowHeightPx = 42;
  if (rowCount > 1) sheet.getRange(`A2:${last}${rowCount}`).format.rowHeightPx = 36;
  for (let col = 0; col < colCount; col += 1) {
    const header = String(values[0][col] ?? "").toLowerCase();
    let width = 155;
    if (header.includes("description") || header.includes("requirement") || header.includes("response") || header.includes("basis") || header.includes("expected")) width = 270;
    else if (header.includes("status") || header.includes("meaning") || header.includes("address") || header.includes("symbol")) width = 180;
    else if (header.includes("sha") || header.includes("path")) width = 240;
    else if (header.includes("qty") || header.includes("id") || header.includes("channel")) width = 85;
    sheet.getRange(`${columnName(col)}1:${columnName(col)}${rowCount}`).format.columnWidthPx = width;
  }
  const safeTable = `${sheet.name.replace(/[^A-Za-z0-9]/g, "")}Table`;
  const table = sheet.tables.add(`A1:${last}${rowCount}`, true, safeTable);
  table.style = "TableStyleMedium2";
  table.showBandedRows = true;
  table.showFilterButton = true;
}

const summary = workbook.worksheets.add("Release Summary");
summary.showGridLines = false;
summary.getRange("A1:H2").merge();
summary.getRange("A1").values = [["FC01 — SIEMENS / NVIDIA ENGINEERING SCHEDULES"]];
summary.getRange("A1:H2").format = { fill: "#12304A", font: { bold: true, color: "#FFFFFF", size: 18 }, verticalAlignment: "center" };
summary.getRange("A3:H3").merge();
summary.getRange("A3").values = [["FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION | Revision C | Overall status: PARTIALLY COMPLETE"]];
summary.getRange("A3:H3").format = { fill: "#EAF1F5", font: { bold: true, color: "#324B5C", size: 10 }, wrapText: true };
summary.getRange("A5:B13").values = [
  ["Controlled metric", "Value"],
  ["PLC I/O rows", null],
  ["Physical DI", null],
  ["Physical DO", null],
  ["Analog inputs", null],
  ["High-speed counters", null],
  ["Vision contract signals", null],
  ["Controlled tests", null],
  ["Open/blocked gates", null],
];
summary.getRange("B6").formulas = [["=COUNTA('PLC I-O'!A2:A200)"]];
summary.getRange("B7").formulas = [["=COUNTIF('PLC I-O'!B2:B200,\"DI\")"]];
summary.getRange("B8").formulas = [["=COUNTIF('PLC I-O'!B2:B200,\"DO\")"]];
summary.getRange("B9").formulas = [["=COUNTIF('PLC I-O'!B2:B200,\"AI\")"]];
summary.getRange("B10").formulas = [["=COUNTIF('PLC I-O'!B2:B200,\"HSC\")"]];
summary.getRange("B11").formulas = [["=COUNTA('NVIDIA Interface'!A2:A100)"]];
summary.getRange("B12").formulas = [["=COUNTA('Test Coverage'!A2:A100)"]];
summary.getRange("A5:B5").format = { fill: "#1F6F9F", font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A6:A13").format = { fill: "#EAF1F5", font: { bold: true, color: "#12304A" } };
summary.getRange("A5:A13").format.columnWidthPx = 220;
summary.getRange("B5:B13").format.columnWidthPx = 130;
summary.getRange("D5:H5").merge();
summary.getRange("D5").values = [["Release boundary"]];
summary.getRange("D5:H5").format = { fill: "#C43D3D", font: { bold: true, color: "#FFFFFF" } };
summary.getRange("D6:H13").merge();
summary.getRange("B13").formulas = [["=COUNTIF('Acceptance Gates'!C2:C100,\"BLOCKED\")+COUNTIF('Acceptance Gates'!C2:C100,\"OPEN\")"]];
summary.getRange("D6").values = [["Native TIA/WinCC/Startdrive/PLCSIM, trained NVIDIA model, revision-C QElectroTech upgrade and revision-C panel CAD remain blocked. Historical native electrical/CAD files are quarantined baselines. No construction, safety, native compile, FAT, SAT or model-performance claim is made."]];
summary.getRange("D6:H13").format = { fill: "#FFF1F1", font: { color: "#642F36", size: 10 }, wrapText: true, verticalAlignment: "center" };
for (const col of ["D", "E", "F", "G", "H"]) summary.getRange(`${col}5:${col}13`).format.columnWidthPx = 110;

const sheetInfo = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 6000 });
console.log(sheetInfo.ndjson);
const formulaErrors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan" });
console.log(formulaErrors.ndjson);
if (formulaErrors.ndjson.includes('"kind":"match"')) {
  throw new Error("Workbook formula-error scan found one or more invalid cells");
}

for (const sheet of workbook.worksheets.items) {
  const preview = await workbook.render({ sheetName: sheet.name, autoCrop: "all", scale: 1, format: "png" });
  const safe = sheet.name.replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
  await fs.writeFile(path.join(previewDir, `${safe}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(scheduleDir, "FC01_engineering_schedules.xlsx"));
console.log(`Saved workbook and ${workbook.worksheets.items.length} sheet renders`);
