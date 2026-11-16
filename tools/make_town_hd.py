#!/usr/bin/env python3
"""Draw the 1950s town at three times the detail (48-pixel tiles, 3840 x 2880).

Usage: python make_town_hd.py OUT_DIR
Needs Pillow and make_maps.py beside it. The layout (houses, hall, square,
paths, yards, tree positions) comes from make_maps.py unchanged, so one tile
here is exactly one tile there, three times larger. Writes into OUT_DIR:
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

import make_maps as mm
from make_maps import OUTLINE, SHADOW, WOOD, H, W, darker, disc, mix, noise

S = 3
TS = mm.T * S
TH = mm.THEMES[4]
GRASS = TH['grass']
YARD = tuple(mix(col, (240, 226, 150), .22) for col in GRASS)
CREAM = ((255, 246, 222), (240, 226, 192), (204, 186, 152))
STONE = ((236, 226, 208), (208, 196, 178), (164, 152, 140))
GREY = ((150, 138, 138), (112, 100, 104), (78, 66, 74))
PATH = ((234, 224, 206), (216, 206, 188), (192, 182, 166), (166, 152, 138))
SQUARE = ((244, 230, 206), (230, 212, 186), (206, 188, 164), (176, 156, 134))
PAVER = ((226, 152, 114), (202, 124, 94), (172, 98, 78), (140, 78, 64))
ACCENT = ((226, 110, 80), (198, 84, 62), (150, 60, 50))
GLOW = ((255, 246, 196), (250, 222, 132), (226, 180, 90))
BRASS = (238, 198, 98)
ROOFS = [p for _, p in TH['roofs']]
SIDINGS = [p for _, p in TH['walls']]
WALL_OF_HOUSE = [2, 0, 3, 2, 0, 2, 1, 0, 1, 0]
TRIMS = [((198, 98, 74), (166, 70, 56), (122, 48, 44)),       # shutter and door colours
         ((150, 164, 104), (116, 132, 80), (80, 96, 60)),
         ((182, 128, 88), (146, 96, 64), (104, 66, 46)),
         ((150, 118, 128), (120, 92, 106), (86, 64, 78))]
PX0, PY0 = mm.PLAZA[0] * TS, mm.PLAZA[1] * TS
PX1, PY1 = PX0 + mm.PLAZA[2] * TS, PY0 + mm.PLAZA[3] * TS
FX, FY = (PX0 + PX1) // 2, (PY0 + PY1) // 2


class Canvas(mm.Canvas):
    """A canvas with a movable origin, so each object draws in local coordinates."""

    def __init__(self, w, h):
        self.im = Image.new('RGB', (w, h))
        self.p, self.w, self.h = self.im.load(), w, h
        self.shadow, self.ox, self.oy = set(), 0, 0

    def at(self, ox, oy):
        self.ox, self.oy = ox, oy
        return self

    def put(self, x, y, c):
        x, y = x + self.ox, y + self.oy
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[x, y] = c

    def get(self, x, y):
        return self.p[min(self.w - 1, max(0, x + self.ox)), min(self.h - 1, max(0, y + self.oy))]

    def dim(self, x, y, a=.3):
        self.put(x, y, mix(self.get(x, y), SHADOW, a))

    def cast(self, pts):
        self.shadow |= {(x + self.ox, y + self.oy) for x, y in pts}

    def frame2(self, x0, y0, x1, y1):
        self.frame(x0, y0, x1, y1)
        self.frame(x0 - 1, y0 - 1, x1 + 1, y1 + 1)


def block(x0, y0, x1, y1):
    return {(x, y) for x in range(x0, x1) for y in range(y0, y1)}


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


# ---------- shared building parts ----------

def shingles(c, x0, y0, x1, y1, pal, seed, ridge=None):
    L, M, D = pal
    for y in range(y0, y1):
        for x in range(x0, x1):
            fx, ry, n = (x - x0) / (x1 - x0), y - y0, noise(x, y, seed)
            r = ry // 6
            xx = x + (5 if r % 2 else 0)
            t = noise(xx // 10, r, seed + 1)
            base = mix(M, L, .35) if t > .75 else mix(M, D, .3) if t < .2 else M
            col = D if ry % 6 == 5 or xx % 10 == 0 else mix(base, L, .6) if ry % 6 == 0 else base
            if ridge and y < ridge:
                col = mix(col, darker(D, .8), .45)          # far slope
            elif ridge and y < ridge + 4:
                col = M if y == ridge + 3 else L            # ridge cap
            elif fx < .35 and n < (.35 - fx) * 1.6:
                col = mix(col, L, .5)
            elif fx > .7 and n < (fx - .7) * 2:
                col = mix(col, D, .6)
            c.put(x, y, col)


def bricks(c, x0, y0, x1, y1, pal):
    L, M, D = pal
    for y in range(y0, y1):
        for x in range(x0, x1):
            r = (y - y0) // 5
            xx = x - x0 + (5 if r % 2 else 0)
            col = L if (y - y0) % 5 == 4 or xx % 10 == 0 else D if noise(xx // 10, r, 9) < .3 else M
            if x - x0 < 4:
                col = mix(col, L, .4)
            if x1 - x <= 6:
                col = darker(col, .8)
            c.put(x, y, col)
    c.frame2(x0, y0, x1, y1)


def glass(c, x0, y0, w, h, curtains=False):
    for yr in range(h):
        for xr in range(w):
            col = mix((128, 170, 174), (68, 104, 118), int((xr + yr) / (w + h) * 5) / 5)
            s = xr + yr - w // 2
            if -3 <= s < 1 or 6 <= s < 8:
                col = mix(col, mm.GLINT, .55)
            side = min(xr, w - 1 - xr)
            if curtains and yr < h * .82 and side < int(w * .34 - w * .24 * yr / h):
                col = CREAM[2] if side % 4 == 3 else CREAM[0] if side % 4 == 0 else CREAM[1]
            c.put(x0 + xr, y0 + yr, col)


def window(c, x0, y0, w, h, cols=2, rows=2, shutters=None, flowers=False, curtains=False):
    c.rect(x0 - 4, y0 - 4, x0 + w + 4, y0 + h + 4, CREAM[1])
    c.rect(x0 - 4, y0 - 4, x0 + w + 4, y0 - 2, CREAM[0])
    c.frame(x0 - 5, y0 - 5, x0 + w + 5, y0 + h + 5)
    glass(c, x0, y0, w, h, curtains)
    for i in range(1, cols):
        c.rect(x0 + w * i // cols - 1, y0, x0 + w * i // cols + 1, y0 + h, CREAM[0])
    for j in range(1, rows):
        yy = y0 + h * j // rows
        c.rect(x0, yy - 1, x0 + w, yy + 2, CREAM[0])
        c.rect(x0, yy + 2, x0 + w, yy + 3, (60, 92, 104))
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1)
    for sx in ((x0 - 20, x0 + w + 6) if shutters else ()):  # louvred shutters
        for y in range(y0 - 4, y0 + h + 4):
            k = (y - y0) % 4
            c.rect(sx, y, sx + 14, y + 1, shutters[2] if k == 3 else shutters[0] if k == 0 else shutters[1])
        c.frame(sx - 1, y0 - 5, sx + 15, y0 + h + 5)
    c.box(x0 - 8, y0 + h + 5, x0 + w + 8, y0 + h + 10, CREAM)
    if flowers:
        c.box(x0 - 5, y0 + h + 13, x0 + w + 5, y0 + h + 23, WOOD)
        for i, k in enumerate(range(x0 - 2, x0 + w + 2, 7)):
            c.blob(disc(k + 2, y0 + h + 11, 4, 4), mm.OAK, k + 2, y0 + h + 11, 4, i)
            c.rect(k + 1, y0 + h + 7, k + 4, y0 + h + 10,
                   ((226, 80, 70), (250, 214, 110), (244, 160, 170))[i % 3])
            c.put(k + 2, y0 + h + 8, (255, 244, 200))


def steps(c, cx, y, widths, rise=9):
    for i, half in enumerate(widths):
        sy = y + i * rise
        c.rect(cx - half, sy, cx + half, sy + rise, STONE[0])
        c.rect(cx - half, sy + rise - 3, cx + half, sy + rise, STONE[2])
        c.rect(cx + half - 4, sy, cx + half, sy + rise, STONE[2])
        c.frame(cx - half - 1, sy - 1, cx + half + 1, sy + rise + 1)


def shrub(c, bx, by, pal, flower=None):
    pts = disc(bx, by - 6, 20, 13) | disc(bx - 15, by, 11, 9) | disc(bx + 15, by, 11, 9)
    c.blob(pts, pal, bx, by - 6, 22, bx)
    for i in range(7 if flower else 0):
        fx, fy = bx - 18 + i * 6, by - 12 + (i * 5) % 11
        c.rect(fx, fy, fx + 2, fy + 2, flower)


# ---------- house (local origin: wall spans x 48..432, roof top at y 40) ----------

def house(c, i):
    roof_pal, side_pal = ROOFS[i % 4], SIDINGS[WALL_OF_HOUSE[i]]
    trim, door_pal = TRIMS[(i + i // 4) % 4], TRIMS[(i * 3 + 1) % 4]
    chim = 336 if i % 2 == 0 else 108
    L, M, D = side_pal
    for y in range(226, 376):                               # siding
        for x in range(48, 432):
            ry, n = y - 226, noise(x, y, 30 + i)
            col = D if ry % 8 == 7 else L if ry % 8 == 0 else mix(M, D, .25) if n < .05 else M
            if ry < 9 or (ry < 12 and n < .5) or (432 - x < 34 and n < (x - 398) / 40):
                col = darker(col, .78)
            if y >= 366:                                    # foundation blocks
                col = STONE[2] if (x - 48) % 24 == 0 or y == 366 else STONE[1]
            c.put(x, y, col)
    for x0 in (48, 424):                                    # corner boards
        c.rect(x0, 232, x0 + 8, 366, CREAM[1])
        c.rect(x0, 232, x0 + 2, 366, CREAM[0])
        c.rect(x0 + 7, 232, x0 + 8, 366, CREAM[2])
    c.frame2(48, 226, 432, 376)
    for wx in (84, 342):
        window(c, wx, 262, 54, 54, shutters=trim, flowers=True, curtains=True)

    x0, x1, y0, y1 = 216, 264, 288, 370                     # front door
    c.rect(x0 - 6, y0 - 6, x1 + 6, y1, CREAM[1])
    c.rect(x0 - 6, y0 - 6, x0 - 4, y1, CREAM[0])
    c.frame(x0 - 7, y0 - 7, x1 + 7, y1 + 1)
    for y in range(y0, y1):
        for x in range(x0, x1):
            c.put(x, y, door_pal[0] if x - x0 < 3 else door_pal[2] if x1 - x <= 3 else door_pal[1])
    c.frame(x0 - 1, y0 - 1, x1 + 1, y1 + 1)
    for k in range(3):                                      # three little panes
        glass(c, x0 + 7 + k * 12, y0 + 8, 10, 13)
        c.frame(x0 + 6 + k * 12, y0 + 7, x0 + 18 + k * 12, y0 + 22)
    for px in (x0 + 6, x0 + 26):                            # raised panels
        for py, ph in ((y0 + 28, 20), (y0 + 54, 22)):
            c.rect(px, py, px + 16, py + ph, mix(door_pal[1], door_pal[2], .35))
            c.rect(px, py, px + 16, py + 1, door_pal[2])
            c.rect(px, py, px + 1, py + ph, door_pal[2])
            c.rect(px, py + ph - 1, px + 16, py + ph, door_pal[0])
            c.rect(px + 15, py, px + 16, py + ph, door_pal[0])
    c.rect(x1 - 8, y0 + 48, x1 - 4, y0 + 52, BRASS)
    c.put(x1 - 8, y0 + 48, (255, 240, 180))
    c.rect(x1 - 8, y0 + 52, x1 - 4, y0 + 53, door_pal[2])
    steps(c, 240, y1, (36, 46))
    c.box(x0 - 22, y0 + 10, x0 - 14, y0 + 24, GLOW)         # porch lamp
    c.box(x0 - 23, y0 + 7, x0 - 13, y0 + 11, GREY)

    for y in range(278, 285):                               # porch roof and its shadow
        for x in range(200, 288):
            c.dim(x, y)
    shingles(c, 196, 258, 284, 278, roof_pal, 50 + i)
    c.rect(196, 274, 284, 278, CREAM[1])
    c.rect(196, 274, 284, 275, CREAM[0])
    c.frame2(196, 258, 284, 278)
    for k in range(10):                                     # brackets
        c.rect(202 + k, 279 + k, 205 + k, 280 + k, OUTLINE)
        c.rect(275 - k, 279 + k, 278 - k, 280 + k, OUTLINE)

    shingles(c, 36, 40, 444, 226, roof_pal, 40 + i, ridge=84)
    for y in range(72, 140):                                # chimney shadow on the roof
        for x in range(chim + 14, chim + 56):
            if x >= chim + 36 or y >= 126:
                c.dim(x, y)
    c.rect(36, 40, 40, 226, CREAM[1])
    c.rect(440, 40, 444, 226, CREAM[2])
    c.rect(36, 219, 444, 226, CREAM[1])
    c.rect(36, 219, 444, 221, CREAM[0])
    c.rect(36, 224, 444, 226, CREAM[2])
    c.frame2(36, 40, 444, 226)
    bricks(c, chim, 62, chim + 36, 126, mm.BRICK)
    c.box(chim - 5, 53, chim + 41, 63, STONE)
    for px in (chim + 5, chim + 21):
        c.box(px, 45, px + 10, 54, mm.TERRACOTTA[0])
    if i % 3 != 1:                                          # television aerial
        ax = 480 - chim - 18
        c.box(ax - 2, 12, ax + 2, 66, GREY)
        c.box(ax - 6, 62, ax + 6, 68, GREY)
        for y, half in ((16, 15), (25, 11), (34, 7)):
            c.rect(ax - half, y, ax + half, y + 2, GREY[2])
    for bx in (78, 402):
        shrub(c, bx, 372, mm.DARK_OAK, ((244, 160, 170), (250, 244, 220), (250, 214, 110))[i % 3])

    mx, my = 164, 376 + 3 * TS - 16                         # mailbox by the path
    c.box(mx - 2, my - 26, mx + 2, my, WOOD)
    c.box(mx - 10, my - 38, mx + 10, my - 25, ((232, 228, 220), (196, 192, 188), (146, 140, 142)))
    c.rect(mx + 10, my - 40, mx + 13, my - 30, ACCENT[1])
    c.frame(mx + 9, my - 41, mx + 14, my - 29)


def house_shadow(c):
    c.cast({p for p in block(60, 120, 458, 394) if p[0] >= 432 or p[1] >= 376})
    c.cast(disc(86, 380, 26, 8) | disc(410, 380, 26, 8) | disc(170, 376 + 3 * TS - 15, 10, 3))


# ---------- town hall (local origin: top-left of its 672 x 432 footprint) ----------

def hall(c):
    wd, ht, rh, cx = 672, 432, 228, 336
    L, M, D = CREAM
    for y in range(rh, ht):                                 # stucco wall
        for x in range(wd):
            n = noise(x, y, 77)
            col = L if n > .93 else mix(M, D, .5) if n < .04 else M
            if rh + 16 <= y < rh + 22:
                col = ACCENT[1] if y < rh + 21 else ACCENT[2]
            if y - rh < 12 or (y - rh < 15 and n < .5) or (wd - x < 50 and n < (x - wd + 50) / 60):
                col = darker(col, .78)
            if ht - y <= 16:
                col = STONE[2] if x % 32 == 0 or ht - y == 16 else STONE[1]
            c.put(x, y, col)
    c.frame2(0, rh, wd, ht)
    for wx in (42, 150, 462, 570):
        window(c, wx, rh + 46, 60, 84, cols=2, rows=3)

    x0, x1, y0 = cx - 45, cx + 45, ht - 128                 # glass double doors
    c.rect(x0 - 7, y0 - 24, x1 + 7, ht, CREAM[1])
    c.rect(x0 - 7, y0 - 24, x0 - 5, ht, CREAM[0])
    c.frame(x0 - 8, y0 - 25, x1 + 8, ht + 1)
    for k in range(3):                                      # transom
        glass(c, x0 + 1 + k * 30, y0 - 19, 28, 13)
        c.frame(x0 + k * 30, y0 - 20, x0 + 30 + k * 30, y0 - 5)
    for lx in (x0, cx + 1):
        c.rect(lx, y0, lx + 44, ht, WOOD[1])
        c.rect(lx, y0, lx + 2, ht, WOOD[0])
        c.rect(lx + 42, y0, lx + 44, ht, WOOD[2])
        glass(c, lx + 7, y0 + 7, 30, 96)
        c.frame(lx + 6, y0 + 6, lx + 38, y0 + 104)
        c.rect(lx + 2, ht - 14, lx + 42, ht - 3, BRASS)
        c.rect(lx + 2, ht - 5, lx + 42, ht - 3, (190, 150, 70))
        c.frame(lx - 1, y0 - 1, lx + 45, ht + 1)
    for hx in (cx - 8, cx + 5):
        c.rect(hx, y0 + 52, hx + 3, y0 + 74, BRASS)
        c.frame(hx - 1, y0 + 51, hx + 4, y0 + 75)

    for y in range(rh + 48, rh + 58):                       # canopy and its shadow
        for x in range(cx - 92, cx + 100):
            c.dim(x, y)
    c.rect(cx - 96, rh + 26, cx + 96, rh + 48, ACCENT[1])
    c.rect(cx - 96, rh + 26, cx + 96, rh + 38, ACCENT[0])
    c.rect(cx - 96, rh + 45, cx + 96, rh + 48, ACCENT[2])
    c.frame2(cx - 96, rh + 26, cx + 96, rh + 48)
    for px in (cx - 90, cx + 84):
        c.box(px, rh + 49, px + 6, ht + 1, GREY)
    steps(c, cx, ht, (66, 78, 90))
    for bx in (cx - 132, cx + 132):                         # planters
        c.box(bx - 17, ht - 8, bx + 17, ht + 12, mm.TERRACOTTA[0])
        shrub(c, bx, ht - 14, mm.OAK, (244, 160, 170))

    rx0, rx1, ry1 = -12, wd + 12, rh + 3                    # flat gravel roof with parapet
    RL, RM, RD = TH['hall_roof'][1]
    for y in range(0, ry1):
        for x in range(rx0, rx1):
            e, n = min(x - rx0, rx1 - 1 - x, y, ry1 - 1 - y), noise(x, y, 78)
            near = min(x - rx0, y)
            if e < 12:
                col = RM if (rx1 - 1 - x < 12 or ry1 - 1 - y < 12) else RL
                col = darker(RD, .9) if e == 11 else mix(col, (255, 250, 232), .5) if e == 1 else col
            else:
                col = RD if n < .1 else RL if n > .93 else mix(RM, RD, .3) if noise(x, y, 79) < .2 else RM
                if near < 22:
                    col = darker(col, .82)                  # shade just inside the parapet
            c.put(x, y, col)
    c.frame2(rx0, 0, rx1, ry1)
    for x, y in block(306, 76, 318, 162) | block(156, 150, 318, 162):
        c.dim(x, y)
    c.rect(150, 70, 306, 150, CREAM[1])                     # skylight
    for k in range(3):
        for j in range(2):
            glass(c, 156 + k * 50, 76 + j * 37, 44, 31)
            c.frame(155 + k * 50, 75 + j * 37, 201 + k * 50, 108 + j * 37)
    c.frame2(150, 70, 306, 150)
    for vx, vy, vw, vh in ((430, 60, 50, 42), (524, 112, 62, 50)):   # roof vents
        for x, y in block(vx + vw, vy + 8, vx + vw + 10, vy + vh + 10) | block(vx + 8, vy + vh, vx + vw + 10, vy + vh + 10):
            c.dim(x, y)
        c.box(vx, vy, vx + vw, vy + vh, GREY)
        c.rect(vx + 2, vy + 2, vx + vw - 2, vy + 10, GREY[0])
        for yy in range(vy + 16, vy + vh - 4, 5):
            c.rect(vx + 6, yy, vx + vw - 6, yy + 2, GREY[2])

    px, py = 132, ht + 126                                  # flagpole on the lawn
    c.box(px - 9, py - 8, px + 9, py, STONE)
    c.box(px - 3, py - 190, px + 3, py - 6, GREY)
    c.blob(disc(px, py - 193, 4, 4), (BRASS, (214, 170, 80), (170, 128, 60)), px, py - 193, 4, 1)
    for u in range(60):
        dy = round(2.5 * math.sin(u / 8))
        for v in range(39):
            c.put(px + 4 + u, py - 186 + v + dy, CREAM[0] if 13 <= v < 26 else
                  ACCENT[0] if u < 20 and v % 13 < 4 else ACCENT[1])
        c.put(px + 4 + u, py - 187 + dy, OUTLINE)
        c.put(px + 4 + u, py - 147 + dy, OUTLINE)
    for v in range(-1, 40):
        c.put(px + 64, py - 186 + v + round(2.5 * math.sin(7.5)), OUTLINE)


def hall_shadow(c):
    c.cast({p for p in block(30, 90, 708, 464) if p[0] >= 672 or p[1] >= 432})
    c.cast(disc(140, 432 + 126, 14, 4))


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
    for origin in sc['homes']:                              # every ground shadow first
        house_shadow(c.at(*origin))
    hall_shadow(c.at(*sc['hall']))
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

    for i, origin in enumerate(sc['homes']):
        house(c.at(*origin), i)
    hall(c.at(*sc['hall']))
    c.at(0, 0)
    fountain(c, FX, FY)
    for x, y in sc['lamps']:
        lamp(c, x, y)
    for x, y in sc['benches']:
        bench(c, x, y)
    for i, (by, cx, pal) in enumerate(sc['trees']):
        tree(c, cx, by, pal, i)
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

    for ox, oy in sc['homes']:
        things.append((ox + 34, oy + 10, 412, 384, oy + 376))
        mx, my = ox + 164, oy + 376 + 3 * TS - 16
        things.append((mx - 12, my - 42, 28, 43, my))
        block_px(mx - 8, my - 10, mx + 8, my)
    hx, hy = sc['hall']
    things.append((hx - 14, hy - 2, 700, 448, hy + 432))
    things.append((hx + 120, hy + 362, 80, 198, hy + 558))  # flagpole
    block_px(hx + 124, hy + 548, hx + 140, hy + 558)
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
