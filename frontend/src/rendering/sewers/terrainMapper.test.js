import test from 'node:test';
import assert from 'node:assert/strict';

import { getSewerTerrainInstructions } from './terrainMapper.js';
import { BACKEND_TILE, QUADRANT, TERRAIN_INDEX } from './constants.js';

const gridWith = (tile, width = 3, height = 3) =>
  Array.from({ length: height }, () => Array.from({ length: width }, () => tile));

test('maps base terrain IDs to non-empty instruction sets', () => {
  const grid = gridWith(BACKEND_TILE.FLOOR);

  const mappedTiles = [
    BACKEND_TILE.FLOOR,
    BACKEND_TILE.FLOOR_WATER,
    BACKEND_TILE.FLOOR_COBBLE,
    BACKEND_TILE.FLOOR_GRASS,
    BACKEND_TILE.DOOR,
    BACKEND_TILE.LOCKED_DOOR,
    BACKEND_TILE.STAIRS_UP,
    BACKEND_TILE.STAIRS_DOWN,
  ];

  for (const tile of mappedTiles) {
    const instructions = getSewerTerrainInstructions(grid, 1, 1, tile, 2);
    assert.ok(instructions.length > 0, `tile ${tile} should render`);
  }
});

test('water mapping produces quadrant composition and shoreline on isolated water', () => {
  const grid = gridWith(BACKEND_TILE.FLOOR);
  grid[1][1] = BACKEND_TILE.FLOOR_WATER;

  const instructions = getSewerTerrainInstructions(grid, 1, 1, BACKEND_TILE.FLOOR_WATER, 1);
  const quadrantInstructions = instructions.filter((item) => item.quadrant !== QUADRANT.FULL);

  assert.equal(quadrantInstructions.length, 4);
  assert.ok(
    quadrantInstructions.some((item) => Object.values(TERRAIN_INDEX.WATER_EDGE).includes(item.srcIndex)),
    'isolated water should include shoreline quadrants'
  );
});

test('grass center uses center tiles when surrounded by grass', () => {
  const grid = gridWith(BACKEND_TILE.FLOOR_GRASS, 5, 5);
  const instructions = getSewerTerrainInstructions(grid, 2, 2, BACKEND_TILE.FLOOR_GRASS, 0);
  const quadrants = instructions.filter((item) => item.quadrant !== QUADRANT.FULL);

  assert.equal(quadrants.length, 4);
  for (const inst of quadrants) {
    assert.ok(TERRAIN_INDEX.GRASS_CENTER.includes(inst.srcIndex));
  }
});

test('door composition adds lintel and side overlays near walls', () => {
  const grid = gridWith(BACKEND_TILE.FLOOR);
  grid[0][1] = BACKEND_TILE.WALL;
  grid[1][0] = BACKEND_TILE.WALL;
  grid[1][2] = BACKEND_TILE.WALL;

  const instructions = getSewerTerrainInstructions(grid, 1, 1, BACKEND_TILE.DOOR, 0);

  assert.ok(instructions.some((item) => item.srcIndex === TERRAIN_INDEX.DOOR));
  assert.ok(instructions.some((item) => item.srcIndex === TERRAIN_INDEX.DOOR_LINTEL));
  assert.ok(instructions.some((item) => item.srcIndex === TERRAIN_INDEX.DOOR_SIDE_LEFT));
  assert.ok(instructions.some((item) => item.srcIndex === TERRAIN_INDEX.DOOR_SIDE_RIGHT));
});
