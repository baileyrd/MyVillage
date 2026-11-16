#!/usr/bin/env python3
"""Check that everything a building draws above its ground line can hide the walker.

Usage: python check_town.py
The page redraws a building over the walker only inside the boxes that
buildings.cover() lists. A mast, wire or puff of smoke outside those boxes would
be drawn under the walker instead of over them. Exits non-zero if any is found.
"""
import sys

import buildings
from kit import Canvas

KEY = (255, 0, 255)
PAD = 260                                                   # room around the building for wires and smoke
GROUND = 376                                                # local y of the foot of the front wall


def uncovered(i):
    """Local pixels house i draws above its ground line that no cover box contains."""
    c = Canvas(480 + 2 * PAD, 520 + 2 * PAD)
    c.rect(0, 0, c.w, c.h, KEY)
    buildings.house(c.at(PAD, PAD), i)
    boxes = buildings.cover(i)
    return [(x - PAD, y - PAD) for y in range(PAD + GROUND) for x in range(c.w)
            if c.p[x, y] != KEY
            and not any(bx <= x - PAD < bx + w and by <= y - PAD < by + h for bx, by, w, h in boxes)]


def main():
    failed = False
    for i, recipe in enumerate(buildings.BUILDINGS):
        stray = uncovered(i)
        if stray:
            xs, ys = [p[0] for p in stray], [p[1] for p in stray]
            print(f'{recipe.__name__}: {len(stray)} pixels outside cover, '
                  f'x {min(xs)}..{max(xs)}, y {min(ys)}..{max(ys)}')
            failed = True
    print('FAILED' if failed else f'ok: all {len(buildings.BUILDINGS)} buildings covered')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
