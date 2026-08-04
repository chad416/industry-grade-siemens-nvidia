import fs from "node:fs/promises";
import path from "node:path";
import { PNG } from "pngjs";

export const RASTER_TOLERANCE = Object.freeze({
  maxDifferingPixels: 16,
  maxBoundingBoxArea: 64,
  maxDifferingPixelRatio: 0.000005,
});

function decodePng(buffer, label) {
  try {
    return PNG.sync.read(buffer);
  } catch (error) {
    throw new Error(`Unable to decode controlled workbook render ${label}: ${error.message}`);
  }
}

export function comparePngBuffers(controlledBuffer, candidateBuffer) {
  const controlled = decodePng(controlledBuffer, "baseline");
  const candidate = decodePng(candidateBuffer, "candidate");
  if (controlled.width !== candidate.width || controlled.height !== candidate.height) {
    return {
      equivalent: false,
      reason: `dimension mismatch ${controlled.width}x${controlled.height} != ${candidate.width}x${candidate.height}`,
      differingPixels: null,
      boundingBoxArea: null,
      differingPixelRatio: null,
    };
  }

  let differingPixels = 0;
  let minX = controlled.width;
  let minY = controlled.height;
  let maxX = -1;
  let maxY = -1;
  for (let pixel = 0; pixel < controlled.width * controlled.height; pixel += 1) {
    const offset = pixel * 4;
    let differs = false;
    for (let channel = 0; channel < 4; channel += 1) {
      if (controlled.data[offset + channel] !== candidate.data[offset + channel]) {
        differs = true;
        break;
      }
    }
    if (differs) {
      differingPixels += 1;
      const x = pixel % controlled.width;
      const y = Math.floor(pixel / controlled.width);
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    }
  }

  const boundingBoxArea = differingPixels === 0 ? 0 : (maxX - minX + 1) * (maxY - minY + 1);
  const differingPixelRatio = differingPixels / (controlled.width * controlled.height);
  const equivalent =
    differingPixels <= RASTER_TOLERANCE.maxDifferingPixels &&
    boundingBoxArea <= RASTER_TOLERANCE.maxBoundingBoxArea &&
    differingPixelRatio <= RASTER_TOLERANCE.maxDifferingPixelRatio;
  return {
    equivalent,
    reason: equivalent ? "within controlled raster tolerance" : "material raster drift",
    differingPixels,
    boundingBoxArea,
    differingPixelRatio,
  };
}

export async function installControlledRender(candidatePath, controlledPath, options = {}) {
  const update = options.update === true;
  const allowTolerance = options.allowTolerance === true;
  const candidateBuffer = await fs.readFile(candidatePath);
  let controlledBuffer;
  try {
    controlledBuffer = await fs.readFile(controlledPath);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
    if (!update) {
      throw new Error(`Controlled workbook render is missing: ${controlledPath}. Set FC01_UPDATE_WORKBOOK_RENDERS=1 only after visual review.`);
    }
    await fs.mkdir(path.dirname(controlledPath), { recursive: true });
    await fs.copyFile(candidatePath, controlledPath);
    return { action: "created", message: "created by explicit baseline update" };
  }

  if (update) {
    await fs.copyFile(candidatePath, controlledPath);
    return { action: "updated", message: "replaced by explicit baseline update" };
  }
  if (controlledBuffer.equals(candidateBuffer)) {
    return { action: "retained", message: "byte-identical" };
  }

  const comparison = comparePngBuffers(controlledBuffer, candidateBuffer);
  if (!comparison.equivalent) {
    throw new Error(
      `Controlled workbook render changed materially: ${controlledPath}; ${comparison.reason}; ` +
      `differing_pixels=${comparison.differingPixels}; bounding_box_area=${comparison.boundingBoxArea}; ` +
      `differing_pixel_ratio=${comparison.differingPixelRatio}. ` +
      "Review the candidate visually, then set FC01_UPDATE_WORKBOOK_RENDERS=1 to authorize a baseline update."
    );
  }
  if (!allowTolerance) {
    throw new Error(
      `Controlled workbook render differs while the authoritative input/builder fingerprint is not approved: ${controlledPath}. ` +
      "A small semantic mark must never be accepted only because it fits the raster threshold."
    );
  }
  return {
    action: "retained",
    message:
      `retained authoritative baseline; differing_pixels=${comparison.differingPixels}; ` +
      `bounding_box_area=${comparison.boundingBoxArea}; differing_pixel_ratio=${comparison.differingPixelRatio}`,
  };
}

export async function verifyControlledRenderSet(controlledDir, expectedNames, options = {}) {
  const update = options.update === true;
  const expected = new Set(expectedNames);
  const entries = await fs.readdir(controlledDir, { withFileTypes: true });
  const byName = new Map(entries.map((entry) => [entry.name, entry]));
  const missing = expectedNames.filter((name) => !byName.get(name)?.isFile());
  const unexpected = entries.filter((entry) => !expected.has(entry.name) || !entry.isFile());
  if (missing.length > 0) {
    throw new Error(`Controlled workbook render set is missing: ${missing.join(", ")}`);
  }
  if (unexpected.length > 0 && update) {
    for (const entry of unexpected) await fs.rm(path.join(controlledDir, entry.name), { recursive: true, force: true });
    return { removed: unexpected.map((entry) => entry.name) };
  }
  if (unexpected.length > 0) {
    throw new Error(
      `Controlled workbook render set contains unexpected entries: ${unexpected.map((entry) => entry.name).join(", ")}. ` +
      "Set FC01_UPDATE_WORKBOOK_RENDERS=1 only after confirming the sheets are superseded."
    );
  }
  return { removed: [] };
}
