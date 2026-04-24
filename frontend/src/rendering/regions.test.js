import test from 'node:test';
import assert from 'node:assert/strict';

import { regionForDepth, tilesForDepth } from './regions.js';

test('regionForDepth maps SPD-style 5-floor regions', () => {
  for (const d of [1, 2, 3, 4, 5]) assert.equal(regionForDepth(d), 'sewers');
  for (const d of [6, 7, 8, 9, 10]) assert.equal(regionForDepth(d), 'prison');
  for (const d of [11, 12, 13, 14, 15]) assert.equal(regionForDepth(d), 'caves');
  for (const d of [16, 17, 18, 19, 20]) assert.equal(regionForDepth(d), 'city');
  for (const d of [21, 25, 50]) assert.equal(regionForDepth(d), 'halls');
});

test('tilesForDepth picks the matching region image', () => {
  const sewers = { tag: 'sewers' };
  const caves = { tag: 'caves' };
  const halls = { tag: 'halls' };
  const assets = {
    tilesByRegion: { sewers, prison: null, caves, city: null, halls },
  };
  assert.equal(tilesForDepth(assets, 1), sewers);
  assert.equal(tilesForDepth(assets, 12), caves);
  assert.equal(tilesForDepth(assets, 25), halls);
});

test('tilesForDepth falls back to sewers when region asset missing', () => {
  const sewers = { tag: 'sewers' };
  const assets = {
    tilesByRegion: { sewers, prison: null, caves: null, city: null, halls: null },
  };
  // Caves not loaded yet -> should fall back to sewers, not return null.
  assert.equal(tilesForDepth(assets, 12), sewers);
});

test('tilesForDepth falls back to legacy `tiles` field if no tilesByRegion', () => {
  const tiles = { tag: 'legacy' };
  const assets = { tiles };
  assert.equal(tilesForDepth(assets, 1), tiles);
  assert.equal(tilesForDepth(assets, 25), tiles);
});
