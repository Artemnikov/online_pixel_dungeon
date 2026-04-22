import {
  BACKEND_TILE,
  QUADRANT,
  QUADRANT_NEIGHBORS,
  TERRAIN_INDEX,
  WALL_INDEX,
  hashCell,
  isGrassTile,
  isWallTile,
  isWaterTile,
} from './constants.js';

const getTile = (grid, x, y) => {
  if (y < 0 || y >= grid.length) return BACKEND_TILE.VOID.id;
  if (x < 0 || x >= grid[y].length) return BACKEND_TILE.VOID.id;
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

const tileInstr = (asset) => ({
  srcIndex: asset.atlasIndex,
  quadrant: QUADRANT.FULL,
  ...(asset.rotate    != null && { rotate:    asset.rotate }),
  ...(asset.srcOffset != null && { srcOffset: asset.srcOffset }),
  ...(asset.crop      != null && { crop:      asset.crop }),
});

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

export const getSewerTerrainInstructions = (grid, x, y, tile, frameIndex = 0, openDoors = new Set()) => {
  if (tile === BACKEND_TILE.WALL.id || tile === BACKEND_TILE.VOID.id) return [];

  if (tile === BACKEND_TILE.FLOOR.id) {
    return [{ srcIndex: getFloorBase(x, y), quadrant: QUADRANT.FULL }];
  }

  if (tile === BACKEND_TILE.FLOOR_WOOD.id) {
    return [{ srcIndex: BACKEND_TILE.FLOOR_WOOD.atlasIndex, quadrant: QUADRANT.FULL }];
  }

  if (tile === BACKEND_TILE.FLOOR_COBBLE.id) {
    return [{ srcIndex: BACKEND_TILE.FLOOR_COBBLE.atlasIndex, quadrant: QUADRANT.FULL }];
  }

  if (tile === BACKEND_TILE.STAIRS_UP.id || tile === BACKEND_TILE.STAIRS_DOWN.id) {
    return [
      { srcIndex: pickVariant(TERRAIN_INDEX.FLOOR_ALT_VARIANTS, x, y), quadrant: QUADRANT.FULL },
      {
        srcIndex: tile === BACKEND_TILE.STAIRS_UP.id ? BACKEND_TILE.STAIRS_UP.atlasIndex : BACKEND_TILE.STAIRS_DOWN.atlasIndex,
        quadrant: QUADRANT.FULL,
      },
    ];
  }

  if (tile === BACKEND_TILE.DOOR.id || tile === BACKEND_TILE.LOCKED_DOOR.id) {
    const base = tile === BACKEND_TILE.LOCKED_DOOR.id
      ? BACKEND_TILE.LOCKED_DOOR
      : (openDoors.has(`${x},${y}`) ? BACKEND_TILE.OPEN_DOOR : BACKEND_TILE.DOOR);
    const instructions = [tileInstr(base)];
    if (isWallTile(getTile(grid, x - 1, y))) {
      instructions.push({ srcIndex: WALL_INDEX.STITCH_LEFT[0], quadrant: QUADRANT.TL, alpha: 0.85 });
      instructions.push({ srcIndex: WALL_INDEX.STITCH_LEFT[0], quadrant: QUADRANT.BL, alpha: 0.85 });
    }
    if (isWallTile(getTile(grid, x + 1, y))) {
      instructions.push({ srcIndex: WALL_INDEX.STITCH_RIGHT[0], quadrant: QUADRANT.TR, alpha: 0.85 });
      instructions.push({ srcIndex: WALL_INDEX.STITCH_RIGHT[0], quadrant: QUADRANT.BR, alpha: 0.85 });
    }
    return instructions;
  }

  if (tile === BACKEND_TILE.FLOOR_WATER.id) {
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

  if (tile === BACKEND_TILE.FLOOR_GRASS.id) {
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

  if (tile === BACKEND_TILE.WALL_TOP.id) return [tileInstr(BACKEND_TILE.WALL_TOP)];
  if (tile === BACKEND_TILE.WALL_BOTTOM.id) {
    const instructions = [tileInstr(BACKEND_TILE.WALL_BOTTOM)];
    const west = getTile(grid, x - 1, y);
    const east = getTile(grid, x + 1, y);
    if (!isWallTile(west) && west !== BACKEND_TILE.VOID.id) {
      instructions.push({ srcIndex: WALL_INDEX.STITCH_LEFT[0], quadrant: QUADRANT.TL, alpha: 0.85 });
      instructions.push({ srcIndex: WALL_INDEX.STITCH_LEFT[0], quadrant: QUADRANT.BL, alpha: 0.85 });
    }
    if (!isWallTile(east) && east !== BACKEND_TILE.VOID.id) {
      instructions.push({ srcIndex: WALL_INDEX.STITCH_RIGHT[0], quadrant: QUADRANT.TR, alpha: 0.85 });
      instructions.push({ srcIndex: WALL_INDEX.STITCH_RIGHT[0], quadrant: QUADRANT.BR, alpha: 0.85 });
    }
    return instructions;
  }
  if (tile === BACKEND_TILE.WALL_LEFT.id) return [tileInstr(BACKEND_TILE.WALL_LEFT)];
  if (tile === BACKEND_TILE.WALL_RIGHT.id) return [
    { srcIndex: BACKEND_TILE.WALL_TOP.atlasIndex, quadrant: QUADRANT.FULL },
    tileInstr(BACKEND_TILE.WALL_RIGHT),
  ];
  if (tile === BACKEND_TILE.WALL_BOTTOM_LEFT.id) return [tileInstr(BACKEND_TILE.WALL_BOTTOM_LEFT)];
  if (tile === BACKEND_TILE.WALL_BOTTOM_RIGHT.id) return [tileInstr(BACKEND_TILE.WALL_BOTTOM_RIGHT)];

  return [];
};
