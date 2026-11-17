#!/usr/bin/env python3
"""Make the rooms the town page walks into: one per house, the last is the town hall.

Usage: python make_rooms.py OUT_DIR
Writes, for every room in interiors.ROOMS:
  room-NN-name.png          the room, 1024 x 768, same pixel size as the town
  room-NN-name-objects.png  only the standing furniture, see-through elsewhere, redrawn over
                            the walker when it is nearer the camera
and rooms.js: window.ROOMS, a list in house order of
  w, h, cell                size in pixels and the size of one collision square
  solid                     rows of '0'/'1': where the walker's feet cannot go
  things                    [x, y, w, h, ground line] for each piece of furniture
  enter                     where the walker stands after coming in, just inside the door
  out                       [x0, x1, y]: feet past y between x0 and x1 leave the room
  fires                     [x, y] of the hearth of every fireplace
"""
import json
import sys
from pathlib import Path

from PIL import ImageChops

import interiors
from interiors import DOOR, FRONT, H, SIDE, W, WALL_H
from make_town_hd import cut_out

K = 2                                                       # real pixels per draft pixel: a 64-pixel person is 1/12
CELL = 8
SHADOW = 3 * K                                              # furniture shadows reach this far right and down
BEHIND = 12 * K                                             # how far behind a piece the walker can tuck in


def parts(spec):
    """(room image, furniture-only image, things, solid grid) for one room."""
    c, furnish = interiors.room_parts(spec, K)
    bare, things = c.im.copy(), []
    before = [bare]

    def note(thing):
        box = ImageChops.difference(c.im, before[0]).getbbox()
        before[0] = c.im.copy()
        if box:
            things.append((box[0], box[1], box[2] - box[0], box[3] - box[1], thing[2] * K))
    furnish(note)

    cols, rows = W * K // CELL, H * K // CELL
    solid = [[False] * cols for _ in range(rows)]
    for cy in range(rows):
        for cx in range(cols):
            x, y = cx * CELL + CELL // 2, cy * CELL + CELL // 2
            in_door = DOOR[0] * K <= x < DOOR[1] * K
            solid[cy][cx] = (y < WALL_H * K or x < SIDE * K or x >= (W - SIDE) * K
                             or (y >= (H - FRONT) * K and not in_door))
    for x, y, w, h, ground in things:                       # the foot of each piece blocks; its top can be stood behind
        top = y + min(BEHIND, int((ground - y) * .4))
        for cy in range(max(0, top // CELL), min(rows, (ground - 1) // CELL + 1)):
            for cx in range(max(0, x // CELL), min(cols, (x + w - SHADOW - 1) // CELL + 1)):
                solid[cy][cx] = True
    return c.im, cut_out(c.im, bare), things, solid


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rooms = []
    for i, spec in enumerate(interiors.ROOMS):
        stem = f'room-{i:02d}-{spec["name"]}'
        im, objects, things, solid = parts(spec)
        im.save(out / (stem + '.png'), optimize=True)
        objects.save(out / (stem + '-objects.png'), optimize=True)
        mid = (DOOR[0] + DOOR[1]) // 2 * K
        rooms.append(dict(
            name=spec['name'], art=stem + '.png', objects=stem + '-objects.png', w=W * K, h=H * K, cell=CELL,
            solid=[''.join('1' if v else '0' for v in row) for row in solid], things=things,
            enter=[mid, (H - FRONT - 6) * K], out=[DOOR[0] * K, DOOR[1] * K, (H - FRONT + 5) * K],
            fires=[[x * K, y * K] for name, x, y, _ in spec['things'] if name == 'fireplace']))
        print('wrote', spec['name'])
    (out / 'rooms.js').write_text('window.ROOMS = ' + json.dumps(rooms, separators=(',', ':')) + ';\n')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'rooms')
