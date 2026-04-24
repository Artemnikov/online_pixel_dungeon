import { TILE_SIZE } from '../../constants';
import { drawSpriteTile, fallbackTileMap } from '../sprites';
import { drawSewerTile } from '../sewers/draw';
import { tilesForDepth } from '../regions';

export function drawGrid(ctx, { grid, depth, assetImages, visionRef, openDoorsRef }) {
  // SPD tile-sheets share the same atlas layout per region — pick the
  // right PNG for this depth, then run the same autotiler pipeline.
  const regionTiles = tilesForDepth(assetImages, depth);

  for (let y = 0; y < grid.length; y++) {
    for (let x = 0; x < grid[y].length; x++) {
      const tile = grid[y][x];
      if (tile === 0) {
        ctx.fillStyle = 'black';
        ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        continue;
      }

      const key = `${x},${y}`;
      const isVisible = visionRef.current.visible.has(key);
      const isDiscovered = visionRef.current.discovered.has(key);

      if (!isDiscovered) {
        ctx.fillStyle = 'black';
        ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        continue;
      }

      let tileDrawn = false;

      if (regionTiles) {
        tileDrawn = drawSewerTile(
          ctx,
          regionTiles,
          grid,
          x,
          y,
          tile,
          openDoorsRef.current
        );
      }

      if (!tileDrawn) {
        const tileCoords = fallbackTileMap[tile];
        if (tileCoords && regionTiles) {
          drawSpriteTile(ctx, regionTiles, tileCoords, x, y);
          tileDrawn = true;
        }
      }

      if (!tileDrawn) {
        if (tile === 3) ctx.fillStyle = '#855';
        else if (tile === 4) ctx.fillStyle = '#aa4';
        else if (tile === 5) ctx.fillStyle = '#4aa';
        else if (tile === 6) ctx.fillStyle = '#6f5234';
        else if (tile === 7) ctx.fillStyle = '#2f5f7a';
        else if (tile === 8) ctx.fillStyle = '#666';
        else if (tile === 9) ctx.fillStyle = '#3f7f3f';
        else if (tile === 10) ctx.fillStyle = '#8a5d23';
        else ctx.fillStyle = '#222';
        ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
      }

      if (!isVisible) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
      }
    }
  }
}
