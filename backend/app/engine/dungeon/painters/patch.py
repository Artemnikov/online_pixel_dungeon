"""Patch.generate: cellular-automaton "blob" generator for water/grass.

Port of SPD `levels/Patch.java`. Starts with random fill, runs N passes
of a 3x3-majority-including-self filter, then (if `force_fill_rate` is
on) nudges cells until the final fill rate matches the target — CA
smoothing on its own drifts aggressively toward 0 or 1.
"""

from __future__ import annotations

from typing import List


def generate_patch(rng, w: int, h: int, fill: float,
                   clustering: int, force_fill_rate: bool) -> List[List[bool]]:
    length = w * h
    off = [False] * length
    cur = [False] * length

    target_true = round(length * fill)

    # Pull initial fill toward 0.5 when smoothing is going to be applied, so
    # the CA doesn't immediately erase everything.
    seeded_fill = fill
    if force_fill_rate and clustering > 0:
        seeded_fill = fill + (0.5 - fill) * 0.5

    fill_diff = -target_true
    for i in range(length):
        off[i] = rng.random() < seeded_fill
        if off[i]:
            fill_diff += 1

    for _step in range(clustering):
        for y in range(h):
            for x in range(w):
                pos = x + y * w
                count = 0
                neighbours = 0

                for dy in (-1, 0, 1):
                    ny = y + dy
                    if ny < 0 or ny >= h:
                        continue
                    for dx in (-1, 0, 1):
                        nx = x + dx
                        if nx < 0 or nx >= w:
                            continue
                        neighbours += 1
                        if off[nx + ny * w]:
                            count += 1

                cur[pos] = 2 * count >= neighbours
                if cur[pos] != off[pos]:
                    fill_diff += 1 if cur[pos] else -1
        off, cur = cur, off

    # Force the final fill rate by painting into / out of non-border cells.
    if force_fill_rate and min(w, h) > 2:
        growing = fill_diff < 0
        offsets = (-w - 1, -w, -w + 1, -1, 0, 1, w - 1, w, w + 1)
        tries_cap = length
        while fill_diff != 0:
            tries = 0
            cell = 0
            while tries * 10 < tries_cap:
                cx = rng.randint(1, w - 2)
                cy = rng.randint(1, h - 2)
                cell = cx + cy * w
                if off[cell] == growing:
                    break
                tries += 1
            for ofs in offsets:
                if fill_diff == 0:
                    break
                idx = cell + ofs
                if 0 <= idx < length and off[idx] != growing:
                    off[idx] = growing
                    fill_diff += 1 if growing else -1

    # Reshape flat to 2D grid[y][x].
    out: List[List[bool]] = [[False] * w for _ in range(h)]
    for y in range(h):
        row = out[y]
        base = y * w
        for x in range(w):
            row[x] = off[base + x]
    return out
