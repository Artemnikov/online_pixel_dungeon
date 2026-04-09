import {
  ATLAS_COLUMNS,
  BACKEND_TILE,
  DEST_TILE_SIZE,
  QUADRANT,
  SOURCE_TILE_SIZE,
  WATER_FRAME_DURATION_MS,
} from './constants.js';
import { getSewerTerrainInstructions } from './terrainMapper.js';
import { getSewerWallInstructions } from './wallMapper.js';

const HALF_SOURCE = SOURCE_TILE_SIZE / 2;
const HALF_DEST = DEST_TILE_SIZE / 2;

const QUADRANT_RECTS = {
  [QUADRANT.TL]: {
    sxOffset: 0,
    syOffset: 0,
    sw: HALF_SOURCE,
    sh: HALF_SOURCE,
    dxOffset: 0,
    dyOffset: 0,
    dw: HALF_DEST,
    dh: HALF_DEST,
  },
  [QUADRANT.TR]: {
    sxOffset: HALF_SOURCE,
    syOffset: 0,
    sw: HALF_SOURCE,
    sh: HALF_SOURCE,
    dxOffset: HALF_DEST,
    dyOffset: 0,
    dw: HALF_DEST,
    dh: HALF_DEST,
  },
  [QUADRANT.BL]: {
    sxOffset: 0,
    syOffset: HALF_SOURCE,
    sw: HALF_SOURCE,
    sh: HALF_SOURCE,
    dxOffset: 0,
    dyOffset: HALF_DEST,
    dw: HALF_DEST,
    dh: HALF_DEST,
  },
  [QUADRANT.BR]: {
    sxOffset: HALF_SOURCE,
    syOffset: HALF_SOURCE,
    sw: HALF_SOURCE,
    sh: HALF_SOURCE,
    dxOffset: HALF_DEST,
    dyOffset: HALF_DEST,
    dw: HALF_DEST,
    dh: HALF_DEST,
  },
};

const getSourceXY = (srcIndex) => ({
  sx: (srcIndex % ATLAS_COLUMNS) * SOURCE_TILE_SIZE,
  sy: Math.floor(srcIndex / ATLAS_COLUMNS) * SOURCE_TILE_SIZE,
});

export const drawInstructions = (ctx, atlasImage, instructions, x, y) => {
  if (!atlasImage || !instructions || instructions.length === 0) return;

  const dx = x * DEST_TILE_SIZE;
  const dy = y * DEST_TILE_SIZE;

  for (const instruction of instructions) {
    const { srcIndex, quadrant = QUADRANT.FULL, alpha } = instruction;
    if (typeof srcIndex !== 'number') continue;

    const { sx, sy } = getSourceXY(srcIndex);
    const prevAlpha = ctx.globalAlpha;
    if (typeof alpha === 'number') {
      ctx.globalAlpha = alpha;
    }

    if (quadrant === QUADRANT.FULL) {
      ctx.drawImage(
        atlasImage,
        sx,
        sy,
        SOURCE_TILE_SIZE,
        SOURCE_TILE_SIZE,
        dx,
        dy,
        DEST_TILE_SIZE,
        DEST_TILE_SIZE
      );
    } else {
      const rect = QUADRANT_RECTS[quadrant];
      if (rect) {
        ctx.drawImage(
          atlasImage,
          sx + rect.sxOffset,
          sy + rect.syOffset,
          rect.sw,
          rect.sh,
          dx + rect.dxOffset,
          dy + rect.dyOffset,
          rect.dw,
          rect.dh
        );
      }
    }

    if (typeof alpha === 'number') {
      ctx.globalAlpha = prevAlpha;
    }
  }
};

export const getAnimatedWaterFrameIndex = (
  nowMs,
  frameCount,
  frameDurationMs = WATER_FRAME_DURATION_MS
) => {
  if (!frameCount || frameCount <= 0) return 0;
  return Math.floor(nowMs / frameDurationMs) % frameCount;
};

const drawWaterOverlay = (ctx, waterFrame, x, y) => {
  if (!waterFrame) return;
  const dx = x * DEST_TILE_SIZE;
  const dy = y * DEST_TILE_SIZE;

  ctx.save();
  ctx.globalAlpha = 0.6;
  ctx.drawImage(waterFrame, 0, 0, waterFrame.width, waterFrame.height, dx, dy, DEST_TILE_SIZE, DEST_TILE_SIZE);
  ctx.restore();
};

export const drawSewerTile = (ctx, atlasImage, waterFrames, grid, x, y, tile, waterFrameIndex) => {
  const instructions =
    tile === BACKEND_TILE.WALL
      ? getSewerWallInstructions(grid, x, y)
      : getSewerTerrainInstructions(grid, x, y, tile, waterFrameIndex);

  if (instructions.length === 0) return false;

  drawInstructions(ctx, atlasImage, instructions, x, y);

  if (tile === BACKEND_TILE.FLOOR_WATER && waterFrames && waterFrames.length > 0) {
    const frame = waterFrames[waterFrameIndex % waterFrames.length];
    drawWaterOverlay(ctx, frame, x, y);
  }

  return true;
};
