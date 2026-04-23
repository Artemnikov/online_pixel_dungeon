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
  VOID: { id: 0, atlasIndex: null, seethrough: true },
  WALL: { id: 1, atlasIndex: atlasIndex(0, 5), seethrough: false },
  FLOOR: { id: 2, atlasIndex: null, seethrough: true },
  DOOR: { id: 3, atlasIndex: atlasIndex(8, 3), seethrough: false },
  OPEN_DOOR: { id: 3, atlasIndex: atlasIndex(9, 3), seethrough: true },
  STAIRS_UP: { id: 4, atlasIndex: atlasIndex(0, 1), seethrough: true },
  STAIRS_DOWN: { id: 5, atlasIndex: atlasIndex(1, 1), seethrough: true },
  FLOOR_WOOD: { id: 6, atlasIndex: atlasIndex(4, 0), seethrough: true },
  FLOOR_WATER: { id: 7, atlasIndex: null, seethrough: true },
  FLOOR_COBBLE: { id: 8, atlasIndex: atlasIndex(12, 0), seethrough: true },
  FLOOR_GRASS: { id: 9, atlasIndex: null, seethrough: true },
  LOCKED_DOOR: { id: 10, atlasIndex: atlasIndex(8, 3), seethrough: false },
  WALL_DECO: { id: 17, atlasIndex: atlasIndex(1, 3), seethrough: false },
  EMPTY_DECO: { id: 18, atlasIndex: atlasIndex(3, 0), seethrough: true },
  HIGH_GRASS: { id: 19, atlasIndex: null, seethrough: false },
  SECRET_DOOR: { id: 20, atlasIndex: atlasIndex(0, 5), seethrough: false },
};

export const toAtlasCoords = (index) => ({
  x: index % ATLAS_COLUMNS,
  y: Math.floor(index / ATLAS_COLUMNS),
});

export const hashCell = (x, y) => ((x * 73856093) ^ (y * 19349663)) >>> 0;

export const TERRAIN_INDEX = {
  FLOOR_VARIANTS: [atlasIndex(0, 0), atlasIndex(1, 0), atlasIndex(2, 0)],
  FLOOR_ALT_VARIANTS: [atlasIndex(6, 0), atlasIndex(7, 0), atlasIndex(8, 0)],

  // SPD DungeonTileSheet: FLOOR_DECO = GROUND+1, FLOOR_DECO_ALT = GROUND+7.
  // EMPTY_DECO renders as one of these full-tile decorated floor variants,
  // picked by hashCell for per-cell but stable variation.
  EMPTY_DECO_VARIANTS: [atlasIndex(1, 0), atlasIndex(7, 0)],

  GRASS_CENTER: [atlasIndex(2, 4), atlasIndex(5, 4), atlasIndex(6, 4)],
  HIGH_GRASS_CENTER: [atlasIndex(10, 7), atlasIndex(13, 7)],
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
  DECO: [atlasIndex(1, 3), atlasIndex(5, 3)],
};

export const WATER_SCROLL_PX_PER_SEC = 10;

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
  tile === BACKEND_TILE.WALL_DECO.id ||
  tile === BACKEND_TILE.SECRET_DOOR.id;
export const isWaterTile = (tile) => tile === BACKEND_TILE.FLOOR_WATER.id;
export const isGrassTile = (tile) =>
  tile === BACKEND_TILE.FLOOR_GRASS.id ||
  tile === BACKEND_TILE.HIGH_GRASS.id;
