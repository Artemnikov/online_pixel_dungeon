export const SOURCE_TILE_SIZE = 16;
export const DEST_TILE_SIZE = 32;
export const ATLAS_COLUMNS = 16;

export const QUADRANT = {
  FULL: 'full',
  TL: 'tl',
  TR: 'tr',
  BL: 'bl',
  BR: 'br',
};

export const atlasIndex = (x, y) => y * ATLAS_COLUMNS + x;

export const BACKEND_TILE = {
  VOID: { id: 0, atlasIndex: null },
  WALL: { id: 1, atlasIndex: null },
  FLOOR: { id: 2, atlasIndex: null },
  DOOR: { id: 3, atlasIndex: atlasIndex(8, 3) },
  STAIRS_UP: { id: 4, atlasIndex: atlasIndex(0, 1) },
  STAIRS_DOWN: { id: 5, atlasIndex: atlasIndex(1, 1) },
  FLOOR_WOOD: { id: 6, atlasIndex: atlasIndex(4, 0) },
  FLOOR_WATER: { id: 7, atlasIndex: null },
  FLOOR_COBBLE: { id: 8, atlasIndex: atlasIndex(1, 1) },
  FLOOR_GRASS: { id: 9, atlasIndex: null },
  LOCKED_DOOR: { id: 10, atlasIndex: atlasIndex(8, 3) },
  WALL_TOP: { id: 11, atlasIndex: atlasIndex(0, 5) },
  WALL_LEFT: { id: 12, atlasIndex: atlasIndex(3, 9) },
  WALL_RIGHT: { id: 13, atlasIndex: atlasIndex(4, 9) },
  WALL_BOTTOM: { id: 14, atlasIndex: atlasIndex(0, 12), rotate: 180, srcOffset: { y: -3 } },
  WALL_BOTTOM_LEFT:  { id: 15, atlasIndex: atlasIndex(3, 9) },
  WALL_BOTTOM_RIGHT: { id: 16, atlasIndex: atlasIndex(4, 9) },
};

export const toAtlasCoords = (index) => ({
  x: index % ATLAS_COLUMNS,
  y: Math.floor(index / ATLAS_COLUMNS),
});

export const hashCell = (x, y) => ((x * 73856093) ^ (y * 19349663)) >>> 0;

export const TERRAIN_INDEX = {
  FLOOR_VARIANTS: [atlasIndex(0, 0), atlasIndex(1, 0), atlasIndex(2, 0)],
  FLOOR_ALT_VARIANTS: [atlasIndex(6, 0), atlasIndex(7, 0), atlasIndex(8, 0)],
  DOOR_LINTEL: atlasIndex(9, 3),

  GRASS_CENTER: [atlasIndex(2, 4), atlasIndex(5, 4), atlasIndex(6, 4)],
  GRASS_EDGE: {
    tl: atlasIndex(1, 2),
    tr: atlasIndex(2, 2),
    bl: atlasIndex(3, 2),
    br: atlasIndex(4, 2),
  },

  WATER_CENTER: [atlasIndex(3, 7), atlasIndex(11, 3)],
  WATER_EDGE: {
    tl: atlasIndex(8, 7),
    tr: atlasIndex(9, 7),
    bl: atlasIndex(10, 7),
    br: atlasIndex(11, 7),
  },
};

export const WALL_INDEX = {
  TOP: [atlasIndex(0, 3), atlasIndex(4, 3)],
  FACE_SOLID: [atlasIndex(0, 5), atlasIndex(0, 6)],
  FACE_OPEN_RIGHT: [atlasIndex(1, 5), atlasIndex(1, 6)],
  FACE_OPEN_LEFT: [atlasIndex(2, 5), atlasIndex(2, 6)],
  FACE_OPEN_BOTH: [atlasIndex(3, 5), atlasIndex(3, 6)],
  STITCH_LEFT: [atlasIndex(4, 5), atlasIndex(4, 6)],
  STITCH_RIGHT: [atlasIndex(5, 5), atlasIndex(5, 6)],
  STITCH_TOP: [atlasIndex(6, 5), atlasIndex(6, 6)],
  STITCH_BOTTOM: [atlasIndex(7, 5), atlasIndex(7, 6)],
};

export const WATER_FRAME_DURATION_MS = 140;

export const QUADRANT_NEIGHBORS = {
  tl: [
    [0, 0],
    [-1, 0],
    [0, -1],
    [-1, -1],
  ],
  tr: [
    [0, 0],
    [1, 0],
    [0, -1],
    [1, -1],
  ],
  bl: [
    [0, 0],
    [-1, 0],
    [0, 1],
    [-1, 1],
  ],
  br: [
    [0, 0],
    [1, 0],
    [0, 1],
    [1, 1],
  ],
};

export const isWallTile = (tile) =>
  tile === BACKEND_TILE.WALL.id ||
  tile === BACKEND_TILE.WALL_TOP.id ||
  tile === BACKEND_TILE.WALL_LEFT.id ||
  tile === BACKEND_TILE.WALL_RIGHT.id ||
  tile === BACKEND_TILE.WALL_BOTTOM.id ||
  tile === BACKEND_TILE.WALL_BOTTOM_LEFT.id ||
  tile === BACKEND_TILE.WALL_BOTTOM_RIGHT.id;
export const isWaterTile = (tile) => tile === BACKEND_TILE.FLOOR_WATER.id;
export const isGrassTile = (tile) => tile === BACKEND_TILE.FLOOR_GRASS.id;
