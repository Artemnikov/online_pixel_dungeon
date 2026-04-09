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

export const BACKEND_TILE = {
  VOID: 0,
  WALL: 1,
  FLOOR: 2,
  DOOR: 3,
  STAIRS_UP: 4,
  STAIRS_DOWN: 5,
  FLOOR_WOOD: 6,
  FLOOR_WATER: 7,
  FLOOR_COBBLE: 8,
  FLOOR_GRASS: 9,
  LOCKED_DOOR: 10,
};

export const atlasIndex = (x, y) => y * ATLAS_COLUMNS + x;

export const toAtlasCoords = (index) => ({
  x: index % ATLAS_COLUMNS,
  y: Math.floor(index / ATLAS_COLUMNS),
});

export const hashCell = (x, y) => ((x * 73856093) ^ (y * 19349663)) >>> 0;

export const TERRAIN_INDEX = {
  FLOOR_VARIANTS: [atlasIndex(0, 0), atlasIndex(1, 0), atlasIndex(2, 0)],
  FLOOR_ALT_VARIANTS: [atlasIndex(6, 0), atlasIndex(7, 0), atlasIndex(8, 0)],
  FLOOR_WOOD: atlasIndex(4, 0),
  FLOOR_COBBLE: atlasIndex(1, 1),
  STAIRS_UP: atlasIndex(2, 1),
  STAIRS_DOWN: atlasIndex(3, 1),
  DOOR: atlasIndex(8, 3),
  DOOR_LINTEL: atlasIndex(9, 3),
  DOOR_SIDE_LEFT: atlasIndex(10, 3),
  DOOR_SIDE_RIGHT: atlasIndex(12, 3),
  LOCKED_DOOR: atlasIndex(8, 3),

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

export const isWallTile = (tile) => tile === BACKEND_TILE.WALL;
export const isWaterTile = (tile) => tile === BACKEND_TILE.FLOOR_WATER;
export const isGrassTile = (tile) => tile === BACKEND_TILE.FLOOR_GRASS;
