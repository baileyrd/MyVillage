#!/usr/bin/env python3
"""Draw the 1950s town at three times the detail (48-pixel tiles, 3840 x 2880).

Usage: python make_town_hd.py OUT_DIR
Needs Pillow and numpy, with make_maps.py, kit.py, buildings.py, props.py and smooth.py beside it. The layout
(houses, hall, square, paths, yards, tree positions) comes from make_maps.py
unchanged. Writes into OUT_DIR:
  town-1950s-hd.png       the finished map
  town-1950s-objects.png  only the things that stand up (see-through elsewhere),
                          so the page can draw them in front of a walker
  town-1950s.js           where the walker cannot go, and where those things are
  houses/NAME.png         each house and the town hall on its own, four times the detail with
                          smooth corners, for the page to lay over the map when zoomed in
  visitor.png             the walker: rows down, up, left, right; three steps each
"""
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops

import buildings
import make_maps as mm
import props
from kit import (FX, FY, GLOW, GRASS, GREY, PATH, PAVER, PX0, PX1, PY0, PY1, S, SQUARE, STONE, TH, TS,
                 YARD, Canvas, fleck)
from make_maps import OUTLINE, WOOD, H, W, darker, disc, mix, noise
from props import bench, fountain, lamp
from smooth import K, smooth4x

# ---------- ground ----------

def grass_px(pal, x, y, lawn):
    """Clean grass: mown stripes on a lawn, flat green elsewhere, with a few two-pixel flecks."""
    base = (pal[3] if (x // 24) % 2 else pal[1]) if lawn else pal[1]
    f = fleck(x, y, 5, .007)
    return pal[2] if f < 0 else pal[0] if f > 0 else base


def slab_px(pal, x, y, checker=False):
    L, M, D, E = pal
    lx, ly = x % 96, y % 96
    if lx < 2 or ly < 2:
        return E
    if lx < 4 or ly < 4:
        return L
    if lx >= 94 or ly >= 94:
        return D
    t = noise(x // 96, y // 96, 2)
    base = mix(M, L, .4) if t > .7 else mix(M, D, .3) if t < .25 else M
    if checker and (x // 96 + y // 96) % 2:
        base = mix(base, D, .22)
    return base


def paver_px(u, v):
    """Brick pavers; u runs along the band, v across it."""
    L, M, D, E = PAVER
    r = v // 12
    uu = u + (12 if r % 2 else 0)
    if v % 12 < 2 or uu % 24 < 2:
        return E
    t = noise(uu // 24, r, 12)
    return L if t > .7 else D if t < .2 else M


def square_px(x, y):
    edge = min(x - PX0, PX1 - 1 - x, y - PY0, PY1 - 1 - y)
    if 12 <= edge < 36:                                     # paver border
        along = x if min(y - PY0, PY1 - 1 - y) == edge else y
        return paver_px(along, edge - 12)
    rr = math.hypot(x - FX, (y - FY) * 1.3)
    if 138 <= rr < 174:                                     # paver ring round the fountain
        a = math.atan2((y - FY) * 1.3, x - FX)
        return paver_px(int(a * 150), int(rr - 138))
    return slab_px(SQUARE, x, y, checker=True)


def draw_ground(c, g):
    paved, R = 'PQB', 9

    def open_side(x, y):
        return g[min(H - 1, max(0, y))][min(W - 1, max(0, x))] not in paved

    for ty in range(H):
        for tx in range(W):
            k = g[ty][tx]
            hard = k in 'PQ'
            if hard:
                l, r = open_side(tx - 1, ty), open_side(tx + 1, ty)
                u, d = open_side(tx, ty - 1), open_side(tx, ty + 1)
            for oy in range(TS):
                y = ty * TS + oy
                for ox in range(TS):
                    x = tx * TS + ox
                    if not hard:
                        c.p[x, y] = grass_px(YARD if k == 'Y' else GRASS, x, y, k == 'Y')
                        continue
                    hx = min(ox if l else 99, TS - 1 - ox if r else 99)
                    vy = min(oy if u else 99, TS - 1 - oy if d else 99)
                    de = R - math.hypot(R - hx, R - vy) if hx < R and vy < R else min(hx, vy)
                    if de < 0:
                        col = grass_px(GRASS, x, y, False)
                    elif de < 2:
                        col = OUTLINE                       # bold edge, like the rooms
                    elif de < 5:
                        col = STONE[0]
                    elif de < 6:
                        col = PATH[2]
                    else:
                        col = square_px(x, y) if k == 'Q' else slab_px(PATH, x, y)
                    c.p[x, y] = col


def draw_decor(c, g, rng):
    """Grass tufts, flowers and pebbles on open ground."""
    for _ in range(3000):
        x, y = rng.randrange(8, c.w - 8), rng.randrange(8, c.h - 8)
        if any(g[(y + dy) // TS][(x + dx) // TS] not in 'GY' for dx in (-7, 7) for dy in (-7, 7)):
            continue
        pal, roll = (YARD if g[y // TS][x // TS] == 'Y' else GRASS), rng.random()
        if roll < .55:                                      # tuft
            for dx, hgt in ((-4, 4), (0, 8), (4, 6)):
                c.rect(x + dx, y - hgt, x + dx + 2, y, pal[2])
                c.rect(x + dx, y - hgt, x + dx + 2, y - hgt + 2, pal[0])
        elif roll < .9:                                     # flower
            petal = rng.choice(TH['flowers'])
            c.rect(x, y + 2, x + 1, y + 7, pal[2])
            for dx, dy in ((0, -3), (-3, 0), (3, 0), (0, 3)):
                c.rect(x - 1 + dx, y - 1 + dy, x + 2 + dx, y + 2 + dy, petal)
            c.rect(x - 1, y - 1, x + 2, y + 2, (250, 214, 110))
        else:
            c.ball(x, y, rng.randrange(3, 6), rng.randrange(2, 4), STONE)


# ---------- trees (benches, lamps, the fountain and the small props are in props.py) ----------

def tree(c, cx, by, pal, seed):
    """A trunk and five smooth lobes of leaves, each with a bold outline and a glint."""
    rng = random.Random(seed)
    for y in range(by - 44, by):                            # trunk with root flare
        half = 7 + max(0, y - by + 8) // 2
        for x in range(cx - half, cx + half + 1):
            edge = abs(x - cx) >= half - 1
            c.put(x, y, OUTLINE if edge else WOOD[0] if x < cx - 3 else WOOD[2] if x > cx + 3 else WOOD[1])
    c.rect(cx - 11, by, cx + 12, by + 2, OUTLINE)
    j = [rng.randint(-3, 3) for _ in range(6)]
    lobes = ((0, -92, 28, 24), (-30, -70 + j[0], 28, 24), (30, -68 + j[1], 28, 24),
             (-18 + j[2], -50, 26, 20), (20 + j[3], -48, 26, 20), (j[4], -66, 32, 26))
    for dx, dy, rx, ry in lobes:
        c.ball(cx + dx, by + dy, rx, ry, pal)


# Small props around the town as (name, x, y), the middle of each one's foot. None may sit
# on a path or in front of a door: check_doors.py fails the build if one does.
PLACED = [
    ('flower_bush', 2444, 584), ('bush', 2946, 584), ('bush', 3020, 584), ('flower_bush', 236, 1352),
    ('bush', 3116, 1352), ('flower_bush', 3618, 1352), ('bush', 738, 2120), ('bush', 3116, 2120),
    ('bush', 1410, 2408), ('flower_bush', 2946, 2408), ('barrel', 2412, 2354), ('crate', 800, 2128),
    ('crate', 2988, 530), ('barrel', 204, 1298), ('vending', 2330, 1262), ('vending', 1510, 1262),
    ('flower_bed', 1620, 1142), ('flower_bed', 2110, 1142), ('flower_bed', 2220, 1142), ('flower_bed', 1560, 1960),
    ('flower_bed', 1700, 1960), ('flower_bed', 2140, 1960), ('flower_bed', 2280, 1960), ('flower_bed', 2420, 1960),
    ('flower_bed', 1650, 1062), ('flower_bed', 2190, 1062), ('bush', 1306, 1250), ('bush', 2534, 1250),
    ('bush', 1306, 1700), ('bush', 1306, 1880), ('bench', 1000, 862), ('bench', 2840, 862),
    ('bench', 3040, 1470), ('bench', 1600, 1262), ('bench', 2240, 1262), ('bench', 1700, 1880),
    ('bench', 2140, 1880), ('bench', 3240, 2500), ('lamp', 864, 712), ('lamp', 1414, 860),
    ('lamp', 2426, 860), ('lamp', 1840, 2300), ('lamp', 2000, 2300), ('lamp', 2140, 2528),
    ('lamp', 1840, 2700), ('lamp', 3140, 1640), ('fence', 760, 2528), ('fence', 1300, 2528),
    ('fence', 1700, 2528), ('fence', 2260, 2528), ('fence', 2980, 2528),
]


def scene():
    """Where every standing thing is, in map pixels."""
    g = mm.layout()
    rng = random.Random(104)                                # same seed as the 1x 1950s map
    mm.draw_flowers(mm.Canvas(), g, TH, rng)                # replay its draws so trees land in the same spots
    return dict(
        g=g,
        trees=[(by * S, cx * S, pal) for by, cx, _, pal in mm.place_trees(g, TH, rng)],
        lamps=[(PX0 + 72, PY0 + 120), (PX1 - 72, PY0 + 120), (PX0 + 72, PY1 - 36), (PX1 - 72, PY1 - 36)],
        benches=[(FX - 228, FY + 12), (FX + 228, FY + 12)],
        homes=[(tx * TS - 48, ty * TS - 40) for tx, ty in mm.HOUSES],
        hall=(mm.HALL[0] * TS, mm.HALL[1] * TS),
        props=PLACED)


def draw_town(sc):
    """Return (finished map, the same map before anything was stood on it, the buildings).
    The buildings are (name, x, y, ground line, picture): each house with its yard, and the town hall,
    cut out of the finished map, so a picture holds exactly the pixels of it that can be seen."""
    c = Canvas(W * TS, H * TS)
    draw_ground(c, sc['g'])
    draw_decor(c, sc['g'], random.Random(7))
    for i, origin in enumerate(sc['homes']):                # every ground shadow first
        buildings.house_shadow(c.at(*origin), i)
    buildings.hall_shadow(c.at(*sc['hall']))
    c.at(0, 0)
    c.cast(disc(FX + 24, FY + 18, 105, 80))
    for by, cx, _ in sc['trees']:
        c.cast(disc(cx + 15, by - 3, 40, 15))
    for x, y in sc['lamps']:
        c.cast(disc(x + 10, y, 16, 5))
    for x, y in sc['benches']:
        c.cast(disc(x + 8, y + 14, 46, 6))
    for name, x, y in sc['props']:
        c.cast(disc(x + 6, y, props.PROPS[name][0] // 2, 4))
    c.apply_shadow()
    bare = c.im.copy()

    jobs = [(oy + 376, lambda i=i, o=(ox, oy): buildings.house(c.at(*o), i), f'house-{i:02d}')
            for i, (ox, oy) in enumerate(sc['homes'])]
    jobs.append((sc['hall'][1] + 432, lambda: buildings.hall(c.at(*sc['hall'])), 'town-hall'))
    jobs.append((FY + 60, lambda: fountain(c.at(0, 0), FX, FY)))
    jobs += [(y, lambda x=x, y=y: lamp(c.at(0, 0), x, y)) for x, y in sc['lamps']]
    jobs += [(y + 12, lambda x=x, y=y: bench(c.at(0, 0), x, y)) for x, y in sc['benches']]
    jobs += [(by, lambda i=i, t=(cx, by, pal): tree(c.at(0, 0), *t, i))
             for i, (by, cx, pal) in enumerate(sc['trees'])]
    jobs += [(y, lambda n=name, x=x, y=y: props.PROPS[n][3](c.at(0, 0), x, y)) for name, x, y in sc['props']]
    drawn = []                                              # name, box, ground, the map just after it was drawn
    for ground, draw, *name in sorted(jobs, key=lambda job: job[0]):    # far things first, near things over them
        before = c.im.copy() if name else None
        draw()
        if name:
            box = ImageChops.difference(c.im, before).getbbox()
            drawn.append((name[0], box, ground, before.crop(box), c.im.crop(box)))
    pieces = []
    for name, box, ground, before, after in drawn:
        seen = same(after, c.im.crop(box))                  # not hidden by a tree or prop drawn later
        mine = ImageChops.invert(same(after, before))       # changed by this building
        piece = after.convert('RGBA')
        piece.putalpha(ImageChops.multiply(seen, mine))
        pieces.append((name, box[0], box[1], ground, piece))
    return c.im, bare, pieces


def same(a, b):
    """White where two pictures hold the same pixel, black elsewhere."""
    return ImageChops.difference(a, b).convert('L').point(lambda v: 0 if v else 255)


def town_data(sc, pieces=()):
    """Blocked half-tiles, and a box plus ground line for each standing thing."""
    cell = TS // 2
    solid = [[sc['g'][y // 2][x // 2] == 'B' for x in range(W * 2)] for y in range(H * 2)]
    things = []                                             # x, y, w, h, ground line

    def block_px(x0, y0, x1, y1):
        for cy in range(max(0, y0 // cell), min(H * 2, (y1 - 1) // cell + 1)):
            for cx in range(max(0, x0 // cell), min(W * 2, (x1 - 1) // cell + 1)):
                solid[cy][cx] = True

    def stand(x, y, w, h, depth):                           # a thing whose foot is centred on (x, y)
        things.append((x - w // 2 - 2, y - h - 2, w + 4, h + 4, y))
        block_px(x - w // 2 + 2, y - depth, x + w // 2 - 2, y)

    for i, (ox, oy) in enumerate(sc['homes']):
        things += [(ox + x, oy + y, w, h, oy + 376) for x, y, w, h in buildings.cover(i)]
        stand(ox + buildings.MAILBOX[0], oy + buildings.MAILBOX[1], 26, 42, 10)
        for name, x, y in buildings.YARDS[i]:
            w, h, depth, _ = buildings.PROPS[name]
            stand(ox + x, oy + y, w, h, depth)
    hx, hy = sc['hall']
    things.append((hx - 14, hy - 2, 700, 448, hy + 432))
    fx, fy = hx + buildings.HALL_FLAG[0], hy + buildings.HALL_FLAG[1]
    things.append((fx - 12, fy - 212, 90, 214, fy))         # flagpole
    block_px(fx - 8, fy - 10, fx + 8, fy)
    for bx in (hx + 204, hx + 468):                         # planters
        block_px(bx - 17, hy + 432, bx + 17, hy + 444)
    things.append((FX - 107, FY - 114, 214, 196, FY + 60))
    for cy in range(H * 2):
        for cx in range(W * 2):
            if math.hypot((cx * cell + 12 - FX) / 108, (cy * cell + 12 - FY) / 80) <= 1:
                solid[cy][cx] = True
    for x, y in sc['lamps']:
        things.append((x - 17, y - 130, 34, 131, y))
        block_px(x - 9, y - 10, x + 9, y)
    for x, y in sc['benches']:
        things.append((x - 46, y - 31, 92, 46, y + 12))
        block_px(x - 42, y - 12, x + 42, y + 12)
    for by, cx, _ in sc['trees']:
        things.append((cx - 62, by - 128, 124, 130, by))
        block_px(cx - 14, by - 22, cx + 14, by + 2)
    for name, x, y in sc['props']:
        w, h, depth, _ = props.PROPS[name]
        stand(x, y, w, h, depth)
    return dict(w=W * TS, h=H * TS, cell=cell, spawn=[FX, H * TS - 150],
                solid=[''.join('1' if v else '0' for v in row) for row in solid], things=things, fx=effects(sc),
                doors=doors(sc), houses=[[x, y, im.width, im.height, ground, f'houses/{name}.png']
                                         for name, x, y, ground, im in pieces])


def doors(sc):
    """[x, ground y, half width, room] for every doorway: walking up into one enters that room (see rooms/rooms.js)."""
    found = [[ox + 240, oy + 376, 24, i] for i, (ox, oy) in enumerate(sc['homes'])]
    return found + [[sc['hall'][0] + 336, sc['hall'][1] + 432, 40, len(found)]]


def effects(sc):
    """Where the page draws its moving effects, in map pixels. Lamps, flag and fountain end with their
    ground line, so the page can draw them behind a walker standing in front of them."""
    def spots(table):
        return [[ox + x, oy + y, *rest] for i, (ox, oy) in enumerate(sc['homes']) for x, y, *rest in
                (table.get(i, []) if isinstance(table.get(i, []), list) else [table[i]])]
    fx, fy = sc['hall'][0] + buildings.HALL_FLAG[0], sc['hall'][1] + buildings.HALL_FLAG[1]
    lamps = list(sc['lamps']) + [(x, y) for name, x, y in sc['props'] if name == 'lamp']
    return dict(
        smoke=spots(buildings.CHIMNEYS), bulbs=spots(buildings.BULBS), lights=spots(buildings.LIGHTS),
        blink=spots(buildings.BLINK), lamps=[[x, y - 100, y] for x, y in lamps],
        flag=[fx + buildings.FLAG[0], fy + buildings.FLAG[1], buildings.FLAG[2], buildings.FLAG[3], fy],
        fountain=[FX, FY, FY + 60])


# ---------- the visitor (cell 48 x 64, feet at the bottom centre) ----------

SKIN = ((250, 214, 178), (232, 186, 150), (196, 146, 116))
COAT = ((218, 186, 138), (192, 158, 112), (150, 118, 84))
PANTS = ((122, 92, 80), (96, 70, 62), (70, 50, 48))
HAT = ((152, 110, 78), (122, 84, 60), (86, 58, 44))
SHOE = (58, 40, 36)
KEY = (255, 0, 255)


def person(c, facing, step):
    side, f = facing in ('left', 'right'), (-1 if facing == 'left' else 1)
    lift = ((0, 0), (3, 0), (0, 3))[step]

    def leg(x, up):
        c.box(x, 45, x + 9, 60 - up, PANTS)
        c.rect(x - (f < 0 and side) * 3, 58 - up, x + 9 + (f > 0 and side) * 3, 62 - up, SHOE)

    def arm(x, sw):
        c.box(x, 29 + sw, x + 6, 44 + sw, COAT)
        c.box(x, 43 + sw, x + 6, 48 + sw, SKIN)

    if side:
        stride = (0, 5, -5)[step]
        if step:
            leg(20 - f * stride, 2)                         # back leg
        leg(20 + f * stride, 0)
        c.box(16, 27, 32, 49, COAT)
        c.rect(17, 40, 31, 42, COAT[2])
        arm(21 - f * stride, 0)
    else:
        for k, x in enumerate((14, 25)):
            leg(x, lift[k])
        for k, x in enumerate((7, 35)):
            arm(x, 2 if lift[1 - k] else -1 if lift[k] else 0)
        c.box(12, 27, 36, 49, COAT)
        c.rect(13, 40, 35, 42, COAT[2])
        if facing == 'down':
            c.rect(21, 28, 27, 34, (250, 244, 226))         # shirt, tie, lapels
            c.rect(23, 28, 25, 37, (198, 84, 62))
            c.rect(19, 28, 21, 38, COAT[2])
            c.rect(27, 28, 29, 38, COAT[2])
        else:
            c.rect(24, 30, 25, 48, COAT[2])
    hx = 24 + (f if side else 0)
    head = disc(hx, 19, 8 if side else 9, 9)
    for x, y in head:
        c.put(x, y, SKIN[0] if x < hx - 3 and y < 21 else SKIN[2] if x > hx + 5 or y > 25 else SKIN[1])
    for x, y in head:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in head:
                c.put(*q, OUTLINE)
    hair = (84, 56, 44)
    if facing == 'up':
        c.rect(16, 15, 33, 26, hair)
    elif side:
        c.rect(hx - f * 8 - 1, 15, hx - f * 8 + 3, 26, hair)
        c.rect(hx + f * 4 - 1, 19, hx + f * 4 + 1, 23, OUTLINE)
        c.put(hx + f * 9, 22, SKIN[2])
    else:
        c.rect(19, 19, 21, 23, OUTLINE)
        c.rect(27, 19, 29, 23, OUTLINE)
        c.rect(22, 25, 26, 26, (176, 100, 88))
    brim = disc(hx + (f * 2 if side else 0), 13, 14, 3)
    for x, y in brim:
        c.put(x, y, HAT[2] if y > 13 else HAT[1])
    for x, y in brim:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in brim:
                c.put(*q, OUTLINE)
    c.box(hx - 9, 2, hx + 9, 13, HAT)
    c.rect(hx - 8, 9, hx + 8, 12, SHOE)


def visitor_sheet():
    c = Canvas(48 * 3, 64 * 4)
    c.rect(0, 0, c.w, c.h, KEY)
    for row, facing in enumerate(('down', 'up', 'left', 'right')):
        for step in range(3):
            person(c.at(step * 48, row * 64), facing, step)
    return cut_out(c.im, Image.new('RGB', c.im.size, KEY))


def cut_out(im, backdrop):
    """Make every pixel that matches the backdrop see-through."""
    mask = ImageChops.difference(im, backdrop).convert('L').point(lambda v: 255 if v else 0)
    out = im.convert('RGBA')
    out.putalpha(mask)
    return Image.composite(out, Image.new('RGBA', im.size, (0, 0, 0, 0)), mask)   # no hidden colour: smaller file


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sc = scene()
    town, bare, pieces = draw_town(sc)
    town.save(out / 'town-1950s-hd.png', optimize=True)
    cut_out(town, bare).save(out / 'town-1950s-objects.png', optimize=True)
    (out / 'town-1950s.js').write_text('window.TOWN = ' + json.dumps(town_data(sc, pieces), separators=(',', ':')) + ';\n')
    visitor_sheet().save(out / 'visitor.png')
    (out / 'houses').mkdir(exist_ok=True)
    for name, _, _, _, im in pieces:
        smooth4x(im).save(out / 'houses' / f'{name}.png', optimize=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'maps')
