import {
  BACKEND_TILE,
  QUADRANT,
  QUADRANT_NEIGHBORS,
  TERRAIN_INDEX,
  hashCell,
  isGrassTile,
  isWallTile,
  isWaterTile,
} from './constants.js';

const getTile = (grid, x, y) => {
  if (y < 0 || y >= grid.length) return BACKEND_TILE.VOID;
  if (x < 0 || x >= grid[y].length) return BACKEND_TILE.VOID;
  return grid[y][x];
};

const pickVariant = (variants, x, y, salt = 0) => {
  const idx = (hashCell(x + salt, y - salt) + salt) % variants.length;
  return variants[idx];
};

const shouldUseCornerType = (grid, x, y, matcher, quadrant) => {
  const cells = QUADRANT_NEIGHBORS[quadrant];
  let matches = 0;
  for (const [dx, dy] of cells) {
    if (matcher(getTile(grid, x + dx, y + dy))) matches += 1;
  }
  return matches >= 3;
};

const getFloorBase = (x, y) => pickVariant(TERRAIN_INDEX.FLOOR_VARIANTS, x, y);

const getTerrainQuadrants = (grid, x, y, matcher, centerVariants, edgeByQuadrant, salt) => {
  const center = pickVariant(centerVariants, x, y, salt);
  const out = [];
  for (const quadrant of [QUADRANT.TL, QUADRANT.TR, QUADRANT.BL, QUADRANT.BR]) {
    out.push({
      srcIndex: shouldUseCornerType(grid, x, y, matcher, quadrant) ? center : edgeByQuadrant[quadrant],
      quadrant,
    });
  }
  return out;
};

export const getSewerTerrainInstructions = (grid, x, y, tile, frameIndex = 0) => {
  if (tile === BACKEND_TILE.WALL || tile === BACKEND_TILE.VOID) return [];

  if (tile === BACKEND_TILE.FLOOR) {
    return [{ srcIndex: getFloorBase(x, y), quadrant: QUADRANT.FULL }];
  }

  if (tile === BACKEND_TILE.FLOOR_WOOD) {
    return [{ srcIndex: TERRAIN_INDEX.FLOOR_WOOD, quadrant: QUADRANT.FULL }];
  }

  if (tile === BACKEND_TILE.FLOOR_COBBLE) {
    return [{ srcIndex: TERRAIN_INDEX.FLOOR_COBBLE, quadrant: QUADRANT.FULL }];
  }

  if (tile === BACKEND_TILE.STAIRS_UP || tile === BACKEND_TILE.STAIRS_DOWN) {
    return [
      { srcIndex: pickVariant(TERRAIN_INDEX.FLOOR_ALT_VARIANTS, x, y), quadrant: QUADRANT.FULL },
      {
        srcIndex: tile === BACKEND_TILE.STAIRS_UP ? TERRAIN_INDEX.STAIRS_UP : TERRAIN_INDEX.STAIRS_DOWN,
        quadrant: QUADRANT.FULL,
      },
    ];
  }

  if (tile === BACKEND_TILE.DOOR || tile === BACKEND_TILE.LOCKED_DOOR) {
    const instructions = [
      { srcIndex: getFloorBase(x, y), quadrant: QUADRANT.FULL },
      {
        srcIndex: tile === BACKEND_TILE.LOCKED_DOOR ? TERRAIN_INDEX.LOCKED_DOOR : TERRAIN_INDEX.DOOR,
        quadrant: QUADRANT.FULL,
      },
    ];

    if (isWallTile(getTile(grid, x, y - 1))) {
      instructions.push({ srcIndex: TERRAIN_INDEX.DOOR_LINTEL, quadrant: QUADRANT.FULL, alpha: 0.95 });
    }
    if (isWallTile(getTile(grid, x - 1, y))) {
      instructions.push({ srcIndex: TERRAIN_INDEX.DOOR_SIDE_LEFT, quadrant: QUADRANT.TL, alpha: 0.9 });
      instructions.push({ srcIndex: TERRAIN_INDEX.DOOR_SIDE_LEFT, quadrant: QUADRANT.BL, alpha: 0.9 });
    }
    if (isWallTile(getTile(grid, x + 1, y))) {
      instructions.push({ srcIndex: TERRAIN_INDEX.DOOR_SIDE_RIGHT, quadrant: QUADRANT.TR, alpha: 0.9 });
      instructions.push({ srcIndex: TERRAIN_INDEX.DOOR_SIDE_RIGHT, quadrant: QUADRANT.BR, alpha: 0.9 });
    }

    return instructions;
  }

  if (tile === BACKEND_TILE.FLOOR_WATER) {
    const instructions = [{ srcIndex: getFloorBase(x, y), quadrant: QUADRANT.FULL }];
    instructions.push(
      ...getTerrainQuadrants(
        grid,
        x,
        y,
        isWaterTile,
        TERRAIN_INDEX.WATER_CENTER,
        TERRAIN_INDEX.WATER_EDGE,
        frameIndex
      )
    );
    return instructions;
  }

  if (tile === BACKEND_TILE.FLOOR_GRASS) {
    const instructions = [{ srcIndex: getFloorBase(x, y), quadrant: QUADRANT.FULL }];
    instructions.push(
      ...getTerrainQuadrants(
        grid,
        x,
        y,
        isGrassTile,
        TERRAIN_INDEX.GRASS_CENTER,
        TERRAIN_INDEX.GRASS_EDGE,
        31
      )
    );
    return instructions;
  }

  return [];
};
