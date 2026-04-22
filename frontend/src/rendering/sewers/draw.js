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

const applyCrop = (crop, sx, sy, sw, sh, dx, dy, dw, dh) => {
  if (!crop) return [sx, sy, sw, sh, dx, dy, dw, dh];
  let [nsx, nsy, nsw, nsh, ndx, ndy, ndw, ndh] = [sx, sy, sw, sh, dx, dy, dw, dh];
  if (crop.top    != null) { nsh = sh * crop.top; ndh = dh * crop.top; }
  if (crop.bottom != null) { nsy += sh * (1 - crop.bottom); nsh = sh * crop.bottom; ndy += dh * (1 - crop.bottom); ndh = dh * crop.bottom; }
  if (crop.left   != null) { nsw = sw * crop.left; ndw = dw * crop.left; }
  if (crop.right  != null) { nsx += sw * (1 - crop.right); nsw = sw * crop.right; ndx += dw * (1 - crop.right); ndw = dw * crop.right; }
  return [nsx, nsy, nsw, nsh, ndx, ndy, ndw, ndh];
};

export const drawInstructions = (ctx, atlasImage, instructions, x, y) => {
  if (!atlasImage || !instructions || instructions.length === 0) return;

  const dx = x * DEST_TILE_SIZE;
  const dy = y * DEST_TILE_SIZE;

  for (const instruction of instructions) {
    const { srcIndex, quadrant = QUADRANT.FULL, alpha, rotate, srcOffset, crop } = instruction;
    if (typeof srcIndex !== 'number') continue;

    const raw = getSourceXY(srcIndex);
    const sx = raw.sx + (srcOffset?.x ?? 0);
    const sy = raw.sy + (srcOffset?.y ?? 0);
    const needsRotation = rotate != null && rotate !== 0;
    const prevAlpha = ctx.globalAlpha;

    if (typeof alpha === 'number') ctx.globalAlpha = alpha;

    if (needsRotation) ctx.save();

    if (quadrant === QUADRANT.FULL) {
      if (needsRotation) {
        ctx.translate(dx + HALF_DEST, dy + HALF_DEST);
        ctx.rotate(rotate * Math.PI / 180);
        ctx.drawImage(atlasImage, sx, sy, SOURCE_TILE_SIZE, SOURCE_TILE_SIZE, -HALF_DEST, -HALF_DEST, DEST_TILE_SIZE, DEST_TILE_SIZE);
      } else {
        const [csx, csy, csw, csh, cdx, cdy, cdw, cdh] =
          applyCrop(crop, sx, sy, SOURCE_TILE_SIZE, SOURCE_TILE_SIZE, dx, dy, DEST_TILE_SIZE, DEST_TILE_SIZE);
        ctx.drawImage(atlasImage, csx, csy, csw, csh, cdx, cdy, cdw, cdh);
      }
    } else {
      const rect = QUADRANT_RECTS[quadrant];
      if (rect) {
        if (needsRotation) {
          const cx = dx + rect.dxOffset + rect.dw / 2;
          const cy = dy + rect.dyOffset + rect.dh / 2;
          ctx.translate(cx, cy);
          ctx.rotate(rotate * Math.PI / 180);
          ctx.drawImage(atlasImage, sx + rect.sxOffset, sy + rect.syOffset, rect.sw, rect.sh, -rect.dw / 2, -rect.dh / 2, rect.dw, rect.dh);
        } else {
          ctx.drawImage(atlasImage, sx + rect.sxOffset, sy + rect.syOffset, rect.sw, rect.sh, dx + rect.dxOffset, dy + rect.dyOffset, rect.dw, rect.dh);
        }
      }
    }

    if (needsRotation) ctx.restore();
    if (typeof alpha === 'number') ctx.globalAlpha = prevAlpha;
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
    tile === BACKEND_TILE.WALL.id
      ? getSewerWallInstructions(grid, x, y)
      : getSewerTerrainInstructions(grid, x, y, tile, waterFrameIndex);

  if (instructions.length === 0) return false;

  drawInstructions(ctx, atlasImage, instructions, x, y);

  const dx = x * DEST_TILE_SIZE;
  const dy = y * DEST_TILE_SIZE;
  if (true) {
    ctx.save();
    ctx.font = 'bold 8px monospace';
    ctx.fillStyle = 'black';
    ctx.fillText(String(tile), dx + 2, dy + 8);
    ctx.fillStyle = 'white';
    ctx.fillText(String(tile), dx + 1, dy + 7);
    ctx.restore();
  }

  if (tile === BACKEND_TILE.FLOOR_WATER.id && waterFrames && waterFrames.length > 0) {
    const frame = waterFrames[waterFrameIndex % waterFrames.length];
    drawWaterOverlay(ctx, frame, x, y);
  }

  return true;
};
