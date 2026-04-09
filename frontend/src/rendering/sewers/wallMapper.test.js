import test from 'node:test';
import assert from 'node:assert/strict';

import { getSewerWallInstructions, getWallMask } from './wallMapper.js';
import { BACKEND_TILE, QUADRANT, WALL_INDEX } from './constants.js';

const blank = () => Array.from({ length: 5 }, () => Array.from({ length: 5 }, () => BACKEND_TILE.FLOOR));

test('wall bitmask uses NESW bit order', () => {
  const grid = blank();
  grid[2][2] = BACKEND_TILE.WALL;
  grid[1][2] = BACKEND_TILE.WALL; // N
  grid[2][3] = BACKEND_TILE.WALL; // E
  grid[3][2] = BACKEND_TILE.WALL; // S

  assert.equal(getWallMask(grid, 2, 2), 1 | 2 | 4);
});

test('single wall tile renders wall top + face + stitches', () => {
  const grid = blank();
  grid[2][2] = BACKEND_TILE.WALL;

  const instructions = getSewerWallInstructions(grid, 2, 2);

  assert.ok(instructions.some((item) => WALL_INDEX.TOP.includes(item.srcIndex)));
  assert.ok(instructions.some((item) => WALL_INDEX.FACE_OPEN_BOTH.includes(item.srcIndex)));
  assert.ok(instructions.some((item) => item.quadrant === QUADRANT.TL));
  assert.ok(instructions.some((item) => item.quadrant === QUADRANT.TR));
});

test('wall with wall below omits raised face', () => {
  const grid = blank();
  grid[2][2] = BACKEND_TILE.WALL;
  grid[3][2] = BACKEND_TILE.WALL;

  const instructions = getSewerWallInstructions(grid, 2, 2);

  assert.equal(
    instructions.some((item) =>
      WALL_INDEX.FACE_SOLID.includes(item.srcIndex) ||
      WALL_INDEX.FACE_OPEN_LEFT.includes(item.srcIndex) ||
      WALL_INDEX.FACE_OPEN_RIGHT.includes(item.srcIndex) ||
      WALL_INDEX.FACE_OPEN_BOTH.includes(item.srcIndex)
    ),
    false
  );
});
