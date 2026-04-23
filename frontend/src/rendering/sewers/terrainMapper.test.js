import test from 'node:test';
import assert from 'node:assert/strict';

import { getSewerTerrainInstructions } from './terrainMapper.js';
import { BACKEND_TILE, QUADRANT, TERRAIN_INDEX, WALL_INDEX, isGrassTile, isWallTile } from './constants.js';

const gridOfIds = (tileId, width = 3, height = 3) =>
  Array.from({ length: height }, () => Array.from({ length: width }, () => tileId));

test('maps base terrain IDs to non-empty instruction sets', () => {
  const grid = gridOfIds(BACKEND_TILE.FLOOR.id);

  const mappedIds = [
    BACKEND_TILE.FLOOR.id,
    BACKEND_TILE.FLOOR_WATER.id,
    BACKEND_TILE.FLOOR_COBBLE.id,
    BACKEND_TILE.FLOOR_GRASS.id,
    BACKEND_TILE.DOOR.id,
    BACKEND_TILE.LOCKED_DOOR.id,
    BACKEND_TILE.STAIRS_UP.id,
    BACKEND_TILE.STAIRS_DOWN.id,
  ];

  for (const tileId of mappedIds) {
    const instructions = getSewerTerrainInstructions(grid, 1, 1, tileId);
    assert.ok(instructions.length > 0, `tile id ${tileId} should render`);
  }
});

test('water mapping produces quadrant composition and shoreline on isolated water', () => {
  const grid = gridOfIds(BACKEND_TILE.FLOOR.id);
  grid[1][1] = BACKEND_TILE.FLOOR_WATER.id;

  const instructions = getSewerTerrainInstructions(grid, 1, 1, BACKEND_TILE.FLOOR_WATER.id);
  const quadrantInstructions = instructions.filter((item) => item.quadrant !== QUADRANT.FULL);

  assert.equal(quadrantInstructions.length, 4);
  assert.ok(
    quadrantInstructions.some((item) => Object.values(TERRAIN_INDEX.WATER_EDGE).includes(item.srcIndex)),
    'isolated water should include shoreline quadrants'
  );
});

test('grass center uses center tiles when surrounded by grass', () => {
  const grid = gridOfIds(BACKEND_TILE.FLOOR_GRASS.id, 5, 5);
  const instructions = getSewerTerrainInstructions(grid, 2, 2, BACKEND_TILE.FLOOR_GRASS.id);
  const quadrants = instructions.filter((item) => item.quadrant !== QUADRANT.FULL);

  assert.equal(quadrants.length, 4);
  for (const inst of quadrants) {
    assert.ok(TERRAIN_INDEX.GRASS_CENTER.includes(inst.srcIndex));
  }
});

test('door with wall on west side only gets STITCH_LEFT overlay', () => {
  const grid = gridOfIds(BACKEND_TILE.FLOOR.id);
  grid[1][0] = BACKEND_TILE.WALL.id;

  const instructions = getSewerTerrainInstructions(grid, 1, 1, BACKEND_TILE.DOOR.id);

  assert.ok(instructions.some((item) => item.srcIndex === BACKEND_TILE.DOOR.atlasIndex));
  assert.ok(instructions.some((item) => WALL_INDEX.STITCH_LEFT.includes(item.srcIndex)));
  assert.ok(!instructions.some((item) => WALL_INDEX.STITCH_RIGHT.includes(item.srcIndex)));
});

test('door with wall on east side only gets STITCH_RIGHT overlay', () => {
  const grid = gridOfIds(BACKEND_TILE.FLOOR.id);
  grid[1][2] = BACKEND_TILE.WALL.id;

  const instructions = getSewerTerrainInstructions(grid, 1, 1, BACKEND_TILE.DOOR.id);

  assert.ok(instructions.some((item) => WALL_INDEX.STITCH_RIGHT.includes(item.srcIndex)));
  assert.ok(!instructions.some((item) => WALL_INDEX.STITCH_LEFT.includes(item.srcIndex)));
});

test('HIGH_GRASS renders floor base + grass quadrants using HIGH_GRASS_CENTER', () => {
  const grid = gridOfIds(BACKEND_TILE.HIGH_GRASS.id, 5, 5);
  const instructions = getSewerTerrainInstructions(grid, 2, 2, BACKEND_TILE.HIGH_GRASS.id);

  const full = instructions.filter((i) => i.quadrant === QUADRANT.FULL);
  const quadrants = instructions.filter((i) => i.quadrant !== QUADRANT.FULL);

  assert.equal(full.length, 1, 'one floor base full-quadrant');
  assert.equal(quadrants.length, 4, 'four terrain quadrants');
  for (const q of quadrants) {
    assert.ok(
      TERRAIN_INDEX.HIGH_GRASS_CENTER.includes(q.srcIndex),
      `HIGH_GRASS surrounded by HIGH_GRASS should use HIGH_GRASS_CENTER sprite, got ${q.srcIndex}`
    );
  }
});

test('EMPTY_DECO renders floor base + decoration overlay', () => {
  const grid = gridOfIds(BACKEND_TILE.FLOOR.id);
  grid[1][1] = BACKEND_TILE.EMPTY_DECO.id;
  const instructions = getSewerTerrainInstructions(grid, 1, 1, BACKEND_TILE.EMPTY_DECO.id);

  assert.equal(instructions.length, 2, 'floor base + deco overlay');
  assert.ok(
    instructions.some((i) => i.srcIndex === BACKEND_TILE.EMPTY_DECO.atlasIndex),
    'deco overlay uses EMPTY_DECO atlasIndex'
  );
});

test('isWallTile recognises WALL, WALL_DECO and SECRET_DOOR', () => {
  assert.equal(isWallTile(BACKEND_TILE.WALL.id), true);
  assert.equal(isWallTile(BACKEND_TILE.WALL_DECO.id), true);
  assert.equal(isWallTile(BACKEND_TILE.SECRET_DOOR.id), true);
  assert.equal(isWallTile(BACKEND_TILE.HIGH_GRASS.id), false);
  assert.equal(isWallTile(BACKEND_TILE.FLOOR.id), false);
});

test('isGrassTile accepts both regular and high grass', () => {
  assert.equal(isGrassTile(BACKEND_TILE.FLOOR_GRASS.id), true);
  assert.equal(isGrassTile(BACKEND_TILE.HIGH_GRASS.id), true);
  assert.equal(isGrassTile(BACKEND_TILE.FLOOR.id), false);
});
