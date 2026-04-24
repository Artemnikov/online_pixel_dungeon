/*
 * Depth -> region mapping. Mirrors the SPD pattern of 5-floor regions
 * with a boss on the 5th floor of each region:
 *   1-5    sewers
 *   6-10   prison
 *   11-15  caves
 *   16-20  city
 *   21+    halls
 *
 * The atlas layout is identical across regions in SPD's tile sheets, so
 * the same wallMapper / terrainMapper logic works as long as we feed in
 * the right region's PNG.
 */
export const regionForDepth = (depth) => {
  if (depth <= 5) return 'sewers';
  if (depth <= 10) return 'prison';
  if (depth <= 15) return 'caves';
  if (depth <= 20) return 'city';
  return 'halls';
};

export const tilesForDepth = (assetImages, depth) => {
  const region = regionForDepth(depth);
  const fromRegion = assetImages.tilesByRegion?.[region];
  // Fall back to the sewers atlas (or `tiles` for back-compat) if the
  // region's PNG hasn't loaded yet — better than rendering nothing.
  return fromRegion || assetImages.tilesByRegion?.sewers || assetImages.tiles;
};
