import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { PNG } from "pngjs";
import { comparePngBuffers, installControlledRender, verifyControlledRenderSet } from "./workbook_render_stability.mjs";

function makePng(width, height, mutations = []) {
  const png = new PNG({ width, height });
  png.data.fill(255);
  for (const [x, y, rgba] of mutations) {
    const offset = (y * width + x) * 4;
    for (let channel = 0; channel < 4; channel += 1) png.data[offset + channel] = rgba[channel];
  }
  return PNG.sync.write(png);
}

const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "fc01-render-stability-test-"));
let passed = 0;
try {
  const width = 1531;
  const height = 2726;
  const baseline = makePng(width, height);
  const knownSixPixelDrift = makePng(width, height, [
    [1440, 974, [0, 0, 0, 255]], [1441, 974, [0, 0, 0, 255]],
    [1442, 974, [0, 0, 0, 255]], [1443, 974, [0, 0, 0, 255]],
    [1440, 975, [0, 0, 0, 255]], [1443, 975, [0, 0, 0, 255]],
  ]);
  const countLimitDrift = makePng(width, height, Array.from({ length: 17 }, (_, index) => [index, 0, [0, 0, 0, 255]]));
  const boundingBoxLimitDrift = makePng(width, height, [[10, 10, [0, 0, 0, 255]], [74, 10, [0, 0, 0, 255]]]);
  const ratioBaseline = makePng(100, 100);
  const ratioLimitDrift = makePng(100, 100, [[10, 10, [0, 0, 0, 255]]]);

  assert.equal(comparePngBuffers(baseline, baseline).equivalent, true); passed += 1;
  const knownComparison = comparePngBuffers(baseline, knownSixPixelDrift);
  assert.equal(knownComparison.equivalent, true);
  assert.equal(knownComparison.differingPixels, 6);
  assert.equal(knownComparison.boundingBoxArea, 8); passed += 1;
  assert.equal(comparePngBuffers(baseline, countLimitDrift).equivalent, false); passed += 1;
  assert.equal(comparePngBuffers(baseline, boundingBoxLimitDrift).equivalent, false); passed += 1;
  assert.equal(comparePngBuffers(ratioBaseline, ratioLimitDrift).equivalent, false); passed += 1;
  assert.equal(comparePngBuffers(baseline, makePng(width + 1, height)).equivalent, false); passed += 1;

  const controlledDir = path.join(tempRoot, "controlled");
  const candidateDir = path.join(tempRoot, "candidate");
  await fs.mkdir(controlledDir);
  await fs.mkdir(candidateDir);
  const controlledPath = path.join(controlledDir, "sheet.png");
  const candidatePath = path.join(candidateDir, "sheet.png");
  await fs.writeFile(controlledPath, baseline);
  await fs.writeFile(candidatePath, knownSixPixelDrift);
  const retained = await installControlledRender(candidatePath, controlledPath, { allowTolerance: true });
  assert.equal(retained.action, "retained");
  assert.deepEqual(await fs.readFile(controlledPath), baseline); passed += 1;

  await assert.rejects(() => installControlledRender(candidatePath, controlledPath, { allowTolerance: false }));
  assert.deepEqual(await fs.readFile(controlledPath), baseline); passed += 1;

  const missingControlledPath = path.join(controlledDir, "missing.png");
  await assert.rejects(() => installControlledRender(candidatePath, missingControlledPath));
  passed += 1;

  const materialCandidatePath = path.join(candidateDir, "material.png");
  await fs.writeFile(materialCandidatePath, countLimitDrift);
  await assert.rejects(() => installControlledRender(materialCandidatePath, controlledPath, { allowTolerance: true }));
  passed += 1;

  await installControlledRender(candidatePath, missingControlledPath, { update: true });
  assert.deepEqual(await fs.readFile(missingControlledPath), knownSixPixelDrift); passed += 1;

  await installControlledRender(materialCandidatePath, controlledPath, { update: true });
  assert.deepEqual(await fs.readFile(controlledPath), countLimitDrift); passed += 1;

  const unexpectedFile = path.join(controlledDir, "renderer.lock");
  await fs.writeFile(unexpectedFile, baseline);
  await assert.rejects(() => verifyControlledRenderSet(controlledDir, ["sheet.png", "missing.png"]));
  passed += 1;
  await fs.rm(unexpectedFile);

  const unexpectedDirectory = path.join(controlledDir, "__pycache__");
  await fs.mkdir(unexpectedDirectory);
  await fs.writeFile(path.join(unexpectedDirectory, "cache.bin"), baseline);
  await assert.rejects(() => verifyControlledRenderSet(controlledDir, ["sheet.png", "missing.png"]));
  passed += 1;

  const cleanup = await verifyControlledRenderSet(controlledDir, ["sheet.png", "missing.png"], { update: true });
  assert.deepEqual(cleanup.removed, ["__pycache__"]);
  await assert.rejects(() => fs.stat(unexpectedDirectory)); passed += 1;

  assert.deepEqual((await fs.readdir(controlledDir)).sort(), ["missing.png", "sheet.png"]);
  await verifyControlledRenderSet(controlledDir, ["sheet.png", "missing.png"]); passed += 1;

  console.log(`Workbook render stability tests: ${passed}/16 PASS`);
} finally {
  await fs.rm(tempRoot, { recursive: true, force: true });
}
