import test from 'node:test';
import assert from 'node:assert/strict';

import { drawInstructions, drawSewerTile, getAnimatedWaterFrameIndex } from './draw.js';
import { BACKEND_TILE, QUADRANT } from './constants.js';

const makeCtx = () => {
  const calls = [];
  return {
    calls,
    globalAlpha: 1,
    drawImage: (...args) => {
      calls.push(args);
    },
    save: () => {},
    restore: () => {},
  };
};

test('water frame index wraps over frame count', () => {
  assert.equal(getAnimatedWaterFrameIndex(0, 5), 0);
  assert.equal(getAnimatedWaterFrameIndex(700, 5), 0);
  assert.equal(getAnimatedWaterFrameIndex(141, 5), 1);
});

test('drawInstructions renders full and quarter tiles', () => {
  const ctx = makeCtx();
  const image = { width: 256, height: 256 };

  drawInstructions(
    ctx,
    image,
    [
      { srcIndex: 0, quadrant: QUADRANT.FULL },
      { srcIndex: 1, quadrant: QUADRANT.TR, alpha: 0.5 },
    ],
    2,
    3
  );

  assert.equal(ctx.calls.length, 2);

  const full = ctx.calls[0];
  assert.equal(full[5], 64);
  assert.equal(full[6], 96);

  const quarter = ctx.calls[1];
  assert.equal(quarter[5], 80);
  assert.equal(quarter[6], 96);
});

test('drawSewerTile applies water overlay for water cells', () => {
  const ctx = makeCtx();
  const atlas = { width: 256, height: 256 };
  const waterFrame = { width: 32, height: 32 };
  const grid = [[BACKEND_TILE.FLOOR_WATER]];

  const drawn = drawSewerTile(ctx, atlas, [waterFrame], grid, 0, 0, BACKEND_TILE.FLOOR_WATER, 0);

  assert.equal(drawn, true);
  assert.ok(ctx.calls.length >= 2, 'base terrain + water overlay should draw at least twice');
});
