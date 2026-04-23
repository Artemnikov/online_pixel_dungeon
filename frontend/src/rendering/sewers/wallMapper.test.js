import test from 'node:test';
import assert from 'node:assert/strict';

import { getSewerWallInstructions, getWallMask } from './wallMapper.js';
import { BACKEND_TILE, QUADRANT, WALL_INDEX } from './constants.js';

const blank = () => Array.from({ length: 5 }, () => Array.from({ length: 5 }, () => BACKEND_TILE.FLOOR.id));

test('wall bitmask uses NESW bit order', () => {
  const grid = blank();
  grid[2][2] = BACKEND_TILE.WALL.id;
  grid[1][2] = BACKEND_TILE.WALL.id; // N
  grid[2][3] = BACKEND_TILE.WALL.id; // E
  grid[3][2] = BACKEND_TILE.WALL.id; // S

  assert.equal(getWallMask(grid, 2, 2), 1 | 2 | 4);
});

test('single wall tile renders wall top + face + stitches', () => {
  const grid = blank();
  grid[2][2] = BACKEND_TILE.WALL.id;

  const instructions = getSewerWallInstructions(grid, 2, 2);

  assert.ok(instructions.some((item) => WALL_INDEX.TOP.includes(item.srcIndex)));
  assert.ok(instructions.some((item) => WALL_INDEX.FACE_OPEN_BOTH.includes(item.srcIndex)));
  assert.ok(instructions.some((item) => item.quadrant === QUADRANT.TL));
  assert.ok(instructions.some((item) => item.quadrant === QUADRANT.TR));
});

test('wall with wall below omits raised face', () => {
  const grid = blank();
  grid[2][2] = BACKEND_TILE.WALL.id;
  grid[3][2] = BACKEND_TILE.WALL.id;

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

test('WALL_DECO substitutes drain sprite for the wall top layer', () => {
  const grid = blank();
  grid[2][2] = BACKEND_TILE.WALL_DECO.id;

  const instructions = getSewerWallInstructions(grid, 2, 2);

  const topLayer = instructions[0];
  assert.ok(
    WALL_INDEX.DECO.includes(topLayer.srcIndex),
    `expected top layer to be a DECO sprite, got ${topLayer.srcIndex}`
  );
  assert.ok(
    !WALL_INDEX.TOP.includes(topLayer.srcIndex),
    'top layer must not be the plain TOP sprite when tile is WALL_DECO'
  );
});

test('SECRET_DOOR uses plain TOP sprite via wallMapper', () => {
  const grid = blank();
  grid[2][2] = BACKEND_TILE.SECRET_DOOR.id;

  const instructions = getSewerWallInstructions(grid, 2, 2);

  const topLayer = instructions[0];
  assert.ok(
    WALL_INDEX.TOP.includes(topLayer.srcIndex),
    'SECRET_DOOR should render with plain TOP sprite so it looks like a wall'
  );
});
