#!/usr/bin/env python3
"""Check that a walker can reach every front door and that nothing stands in front of one.

Usage: python check_doors.py
Three rules, checked on the same data the page uses (make_town_hd.town_data):
  1. the lane from each door down through its yard holds nothing solid;
  2. nothing standing level with a door or nearer the camera is drawn across that door or lane;
  3. the walker can get from the spawn point to every doorstep, and no path tile is blocked.
Exits non-zero if any rule is broken.
"""
import sys
from collections import deque

import buildings
import make_town_hd as town
from kit import TS

LANE = (192, 288)                                           # local x of the walk up to a house door
HOUSE_GROUND = 376                                          # local y of the foot of a house's front wall
HALL_LANE, HALL_GROUND = (240, 432), 432
YARD = 3 * TS                                               # depth of the open ground in front of a door
DOOR_H = 96                                                 # how much of the wall above the ground a door takes
FOOT_W, FOOT_H = 22, 12                                     # the walker's foot box, as in index.html


def lanes(sc):
    """(name, x0, x1, ground y, the building's own boxes) in map pixels for every front door."""
    out = [(recipe.__name__, ox + LANE[0], ox + LANE[1], oy + HOUSE_GROUND,
            {(ox + x, oy + y, w, h, oy + HOUSE_GROUND) for x, y, w, h in buildings.cover(i)})
           for i, (recipe, (ox, oy)) in enumerate(zip(buildings.BUILDINGS, sc['homes']))]
    hx, hy = sc['hall']
    own = {t for t in town.town_data(sc)['things'] if t[:2] == (hx - 14, hy - 2)}
    return out + [('town_hall', hx + HALL_LANE[0], hx + HALL_LANE[1], hy + HALL_GROUND, own)]


def solid_in(data, x0, y0, x1, y1):
    """Blocked cells touching the pixel box, as (x, y) of each cell's corner."""
    cell = data['cell']
    return [(cx * cell, cy * cell)
            for cy in range(y0 // cell, (y1 - 1) // cell + 1)
            for cx in range(x0 // cell, (x1 - 1) // cell + 1)
            if data['solid'][cy][cx] == '1']


def blocked(data, x, y):
    return bool(solid_in(data, x - FOOT_W // 2, y - FOOT_H, x + FOOT_W // 2, y))


def reachable(data, step=6):
    """Every spot, on a grid of `step` pixels, the walker's feet can get to from the spawn point."""
    start = (data['spawn'][0] // step, data['spawn'][1] // step)
    seen, todo = {start}, deque([start])
    while todo:
        gx, gy = todo.popleft()
        for nxt in ((gx + 1, gy), (gx - 1, gy), (gx, gy + 1), (gx, gy - 1)):
            x, y = nxt[0] * step, nxt[1] * step
            if nxt in seen or not (FOOT_W <= x < data['w'] - FOOT_W and FOOT_H <= y < data['h']):
                continue
            if not blocked(data, x, y):
                seen.add(nxt)
                todo.append(nxt)
    return seen, step


def problems(sc, data):
    found = []
    seen, step = reachable(data)
    for name, x0, x1, ground, own in lanes(sc):
        hit = solid_in(data, x0, ground, x1, ground + YARD)
        if hit:
            found.append(f'{name}: something solid in the lane at {hit[:3]}')
        for thing in data['things']:
            tx, ty, tw, th, tground = thing
            # Things on the same ground line as the door are drawn after the building, so they count too.
            if thing not in own and tground >= ground and tx < x1 and tx + tw > x0 and ty < ground + YARD and ty + th > ground - DOOR_H:
                found.append(f'{name}: thing at ({tx}, {ty}) {tw}x{th} is drawn across the door or lane')
        if ((x0 + x1) // 2 // step, (ground + FOOT_H + step) // step) not in seen:
            found.append(f'{name}: the walker cannot reach the doorstep')
    for ty, row in enumerate(sc['g']):
        for tx, kind in enumerate(row):
            if kind == 'P' and solid_in(data, tx * TS, ty * TS, tx * TS + TS, ty * TS + TS):
                found.append(f'path tile ({tx}, {ty}) is blocked')
    return found


def self_test(sc):
    """The check must catch a tree in a lane and a tree level with a door whose leaves cover it."""
    ox, oy = sc['homes'][0]
    pal = sc['trees'][0][2]
    for tree in ((oy + HOUSE_GROUND + 100, ox + 240, pal), (oy + HOUSE_GROUND, ox + 310, pal)):
        planted = dict(sc, trees=sc['trees'] + [tree])
        if not problems(planted, town.town_data(planted)):
            return [f'self-test: a tree planted at {tree[1]}, {tree[0]} was not caught']
    return []


def main():
    sc = town.scene()
    found = problems(sc, town.town_data(sc)) + self_test(sc)
    print('\n'.join(found + ['FAILED']) if found else 'ok: every front door has a clear way in')
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
