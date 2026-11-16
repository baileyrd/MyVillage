#!/usr/bin/env python3
"""Draw the 1950s town at three times the detail (48-pixel tiles, 3840 x 2880).

Usage: python make_town_hd.py OUT_DIR
Needs Pillow, with make_maps.py, kit.py and buildings.py beside it. The layout
(houses, hall, square, paths, yards, tree positions) comes from make_maps.py
unchanged. Writes into OUT_DIR:
  town-1950s-hd.png       the finished map
  town-1950s-objects.png  only the things that stand up (see-through elsewhere),
                          so the page can draw them in front of a walker
  town-1950s.js           where the walker cannot go, and where those things are
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
from kit import (FX, FY, GLOW, GRASS, GREY, PATH, PAVER, PX0, PX1, PY0, PY1, S, SQUARE, STONE, TH, TS,
                 YARD, Canvas)
from make_maps import OUTLINE, WOOD, H, W, darker, disc, mix, noise

# ---------- ground ----------

def grass_px(pal, x, y, lawn):
    base = (pal[3] if (x // 24) % 2 else pal[1]) if lawn else (
        pal[3] if noise(x // 22, y // 22, 6) > .55 else pal[1])
    n = noise(x, y // 3, 5)
    col = pal[2] if n < .05 else pal[0] if n > .955 else base
    return mix(col, pal[2], .45) if noise(x, y, 7) < .06 else col


def slab_px(pal, x, y, checker=False):
    L, M, D, E = pal
    lx, ly = x % 96, y % 96
    if lx == 0 or ly == 0:
        return E
    if lx == 1 or ly == 1:
        return L
    if lx == 95 or ly == 95:
        return D
    t, n = noise(x // 96, y // 96, 2), noise(x, y, 8)
    base = mix(M, L, .4) if t > .7 else mix(M, D, .3) if t < .25 else M
    if checker and (x // 96 + y // 96) % 2:
        base = mix(base, D, .22)
    return mix(base, D, .5) if n < .04 else L if n > .965 else base


def paver_px(u, v):
    """Brick pavers; u runs along the band, v across it."""
    L, M, D, E = PAVER
    r = v // 12
    uu = u + (12 if r % 2 else 0)
    if v % 12 == 0 or uu % 24 == 0:
        return E
    t = noise(uu // 24, r, 12)
    return L if t > .66 else D if t < .24 else M


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
                    elif de < 1.2:
                        col = darker(PATH[3], .8)           # kerb
                    elif de < 4:
                        col = STONE[0]
                    elif de < 5:
                        col = PATH[2]
                    else:
                        col = square_px(x, y) if k == 'Q' else slab_px(PATH, x, y)
                    c.p[x, y] = col


def draw_decor(c, g, rng):
    """Grass tufts, flowers and pebbles on open ground."""
    for _ in range(5200):
        x, y = rng.randrange(8, c.w - 8), rng.randrange(8, c.h - 8)
        if any(g[(y + dy) // TS][(x + dx) // TS] not in 'GY' for dx in (-7, 7) for dy in (-7, 7)):
            continue
        pal, roll = (YARD if g[y // TS][x // TS] == 'Y' else GRASS), rng.random()
        if roll < .55:                                      # tuft
            for dx, hgt in ((-3, 5), (0, 8), (3, 6)):
                for k in range(hgt):
                    c.put(x + dx + (k // 4) * (1 if dx > 0 else -1 if dx < 0 else 0), y - k,
                          pal[0] if k >= hgt - 2 else pal[2])
        elif roll < .9:                                     # flower
            petal = rng.choice(TH['flowers'])
            c.rect(x, y + 2, x + 1, y + 7, pal[2])
            for dx, dy in ((0, -3), (-3, 0), (3, 0), (0, 3)):
                c.rect(x - 1 + dx, y - 1 + dy, x + 2 + dx, y + 2 + dy, petal)
            c.rect(x - 1, y - 1, x + 2, y + 2, (250, 214, 110))
        else:
            c.blob(disc(x, y, rng.randrange(3, 6), rng.randrange(2, 4)), STONE, x, y, 5, x)


# ---------- square furniture ----------

def fountain(c, cx, cy):
    water = mm.WATER
    outer, inner = disc(cx, cy, 105, 80), disc(cx, cy - 3, 84, 62)
    c.blob(outer, STONE, cx, cy, 100, 10)
    for x, y in outer - inner:                              # rim blocks
        a = math.atan2((y - cy) * 1.3, x - cx) * 14 / math.pi
        if abs(a - round(a)) < .07:
            c.put(x, y, STONE[2])
    for x, y in inner:
        rr = math.hypot((x - cx) / 84, (y - cy + 3) / 62)
        col = water[1]
        if rr > .84 and (x - cx) + (y - cy) < 0:
            col = water[2]                                  # rim shades the near water
        elif int(rr * 9 + noise(x // 7, y // 7, 3) * .9) % 3 == 0 and noise(x, y // 2, 4) < .4:
            col = water[0]
        if noise(x, y, 5) > .988:
            col = (246, 252, 248)
        c.put(x, y, col)
    for x, y in inner:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in inner:
                c.put(*q, OUTLINE)
    c.blob(disc(cx, cy + 2, 22, 8), STONE, cx, cy + 2, 20, 14)
    c.box(cx - 10, cy - 60, cx + 10, cy - 4, STONE)
    c.blob(disc(cx, cy - 62, 40, 15), STONE, cx, cy - 62, 38, 12)
    c.blob(disc(cx, cy - 66, 30, 8), water, cx, cy - 66, 26, 13)
    c.box(cx - 5, cy - 86, cx + 5, cy - 66, STONE)
    spray = (246, 252, 248)
    for k in range(26):                                     # jet
        c.rect(cx - 1 - (k > 18), cy - 112 + k, cx + 1 + (k > 18), cy - 111 + k, spray if k % 4 else water[0])
    for sx in (-36, -22, -8, 8, 22, 36):                    # falling streams
        drop = 12 - abs(sx) // 4
        for y in range(cy - 58 + abs(sx) // 6, cy - 6 + drop):
            c.rect(cx + sx - 1, y, cx + sx + 1, y + 1, spray if (y + sx) % 5 < 3 else water[0])
        c.rect(cx + sx - 4, cy - 6 + drop, cx + sx + 4, cy - 5 + drop, spray)


def lamp(c, x, y):
    c.box(x - 9, y - 8, x + 9, y, GREY)
    c.box(x - 3, y - 86, x + 3, y - 6, GREY)
    c.box(x - 6, y - 60, x + 6, y - 55, GREY)
    c.box(x - 13, y - 116, x + 13, y - 84, GLOW)
    c.rect(x - 7, y - 110, x + 5, y - 90, (255, 252, 226))
    c.rect(x - 1, y - 116, x + 1, y - 84, GREY[1])
    c.box(x - 16, y - 122, x + 16, y - 114, GREY)
    c.box(x - 3, y - 129, x + 3, y - 121, GREY)


def bench(c, x, y):
    for lx in (x - 38, x + 32):
        c.box(lx, y - 8, lx + 6, y + 14, GREY)
    for i in range(3):
        c.box(x - 42, y - 30 + i * 8, x + 42, y - 23 + i * 8, WOOD)
    for i in range(2):
        c.box(x - 42, y - 5 + i * 7, x + 42, y + 3 + i * 7, (WOOD[0], WOOD[0], WOOD[1]))
    for lx in (x - 45, x + 39):
        c.box(lx, y - 14, lx + 6, y - 9, GREY)


def tree(c, cx, by, pal, seed):
    rng = random.Random(seed)
    for y in range(by - 42, by):                            # trunk with root flare
        half = 7 + max(0, y - by + 8) // 2
        for x in range(cx - half, cx + half + 1):
            edge = abs(x - cx) == half
            bark = WOOD[0] if x < cx - 3 else WOOD[2] if x > cx + 3 or noise(x // 2, y // 5, seed) < .25 else WOOD[1]
            c.put(x, y, OUTLINE if edge else bark)
    c.rect(cx - 11, by, cx + 12, by + 1, OUTLINE)
    ccy = by - 72
    pts = disc(cx, ccy, 45, 39) | disc(cx - 27, by - 51, 27, 24) | disc(cx + 27, by - 51, 27, 24) | disc(cx, by - 96, 30, 24)
    for k in range(10):                                     # lumpy edge
        a = k * math.pi / 5 + rng.random() * .4
        pts |= disc(cx + int(44 * math.cos(a)), ccy + int(36 * math.sin(a)) - 4, rng.randint(9, 13), rng.randint(8, 11))
    tone = {}
    for x, y in pts:
        d, n = ((x - cx) + (y - ccy)) / 73, noise(x, y, seed)
        tone[x, y] = 1 if d < -.28 + (n - .5) * .2 else 3 if d > .3 + (n - .5) * .2 else 2
    for _ in range(70):                                     # leaf clumps
        px, py, r = cx + rng.randint(-56, 56), ccy + rng.randint(-50, 48), rng.randint(5, 8)
        if (px, py) not in pts:
            continue
        for q in disc(px, py, r, r - 1):
            if q in tone:
                s = (q[0] - px) + (q[1] - py)
                tone[q] = max(0, tone[q] - 1) if s < -r * .35 else min(4, tone[q] + 1) if s > r * .6 else tone[q]
    ramp = (mix(pal[0], (255, 250, 220), .35), pal[0], pal[1], pal[2], darker(pal[2], .8))
    for (x, y), t in tone.items():
        c.put(x, y, ramp[t])
    ring = {(x + dx, y + dy) for x, y in pts for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - pts
    ring |= {(x + dx, y + dy) for x, y in ring for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - pts
    for q in ring:
        c.put(*q, OUTLINE)


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
        hall=(mm.HALL[0] * TS, mm.HALL[1] * TS))


def draw_town(sc):
    """Return (finished map, the same map before anything was stood on it)."""
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
    c.apply_shadow()
    bare = c.im.copy()

    jobs = [(oy + 376, lambda i=i, o=(ox, oy): buildings.house(c.at(*o), i))
            for i, (ox, oy) in enumerate(sc['homes'])]
    jobs.append((sc['hall'][1] + 432, lambda: buildings.hall(c.at(*sc['hall']))))
    jobs.append((FY + 60, lambda: fountain(c.at(0, 0), FX, FY)))
    jobs += [(y, lambda x=x, y=y: lamp(c.at(0, 0), x, y)) for x, y in sc['lamps']]
    jobs += [(y + 12, lambda x=x, y=y: bench(c.at(0, 0), x, y)) for x, y in sc['benches']]
    jobs += [(by, lambda i=i, t=(cx, by, pal): tree(c.at(0, 0), *t, i))
             for i, (by, cx, pal) in enumerate(sc['trees'])]
    for _, draw in sorted(jobs, key=lambda job: job[0]):    # far things first, near things over them
        draw()
    return c.im, bare


def town_data(sc):
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
    return dict(w=W * TS, h=H * TS, cell=cell, spawn=[FX, H * TS - 150],
                solid=[''.join('1' if v else '0' for v in row) for row in solid], things=things)


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
    return out


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sc = scene()
    town, bare = draw_town(sc)
    town.save(out / 'town-1950s-hd.png', optimize=True)
    cut_out(town, bare).save(out / 'town-1950s-objects.png', optimize=True)
    (out / 'town-1950s.js').write_text('window.TOWN = ' + json.dumps(town_data(sc), separators=(',', ':')) + ';\n')
    visitor_sheet().save(out / 'visitor.png')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'maps')
