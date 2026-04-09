import { BACKEND_TILE, QUADRANT, WALL_INDEX, hashCell, isWallTile } from './constants.js';

const getTile = (grid, x, y) => {
  if (y < 0 || y >= grid.length) return BACKEND_TILE.VOID;
  if (x < 0 || x >= grid[y].length) return BACKEND_TILE.VOID;
  return grid[y][x];
};

export const getWallMask = (grid, x, y) => {
  let mask = 0;
  if (isWallTile(getTile(grid, x, y - 1))) mask |= 1;
  if (isWallTile(getTile(grid, x + 1, y))) mask |= 2;
  if (isWallTile(getTile(grid, x, y + 1))) mask |= 4;
  if (isWallTile(getTile(grid, x - 1, y))) mask |= 8;
  return mask;
};

export const getSewerWallInstructions = (grid, x, y) => {
  if (!isWallTile(getTile(grid, x, y))) return [];

  const variant = hashCell(x, y) % WALL_INDEX.TOP.length;
  const mask = getWallMask(grid, x, y);

  const hasNorth = (mask & 1) !== 0;
  const hasEast = (mask & 2) !== 0;
  const hasSouth = (mask & 4) !== 0;
  const hasWest = (mask & 8) !== 0;

  const instructions = [{ srcIndex: WALL_INDEX.TOP[variant], quadrant: QUADRANT.FULL }];

  if (!hasSouth) {
    let face = WALL_INDEX.FACE_SOLID[variant];
    if (!hasEast && !hasWest) {
      face = WALL_INDEX.FACE_OPEN_BOTH[variant];
    } else if (!hasWest) {
      face = WALL_INDEX.FACE_OPEN_LEFT[variant];
    } else if (!hasEast) {
      face = WALL_INDEX.FACE_OPEN_RIGHT[variant];
    }
    instructions.push({ srcIndex: face, quadrant: QUADRANT.FULL });
  }

  if (!hasNorth) {
    instructions.push({ srcIndex: WALL_INDEX.STITCH_TOP[variant], quadrant: QUADRANT.FULL, alpha: 0.85 });
  }
  if (!hasWest) {
    instructions.push({ srcIndex: WALL_INDEX.STITCH_LEFT[variant], quadrant: QUADRANT.TL, alpha: 0.85 });
    instructions.push({ srcIndex: WALL_INDEX.STITCH_LEFT[variant], quadrant: QUADRANT.BL, alpha: 0.85 });
  }
  if (!hasEast) {
    instructions.push({ srcIndex: WALL_INDEX.STITCH_RIGHT[variant], quadrant: QUADRANT.TR, alpha: 0.85 });
    instructions.push({ srcIndex: WALL_INDEX.STITCH_RIGHT[variant], quadrant: QUADRANT.BR, alpha: 0.85 });
  }
  if (hasSouth && !hasWest) {
    instructions.push({ srcIndex: WALL_INDEX.STITCH_BOTTOM[variant], quadrant: QUADRANT.BL, alpha: 0.8 });
  }
  if (hasSouth && !hasEast) {
    instructions.push({ srcIndex: WALL_INDEX.STITCH_BOTTOM[variant], quadrant: QUADRANT.BR, alpha: 0.8 });
  }

  return instructions;
};
