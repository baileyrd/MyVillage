#!/usr/bin/env python3
"""Draw the My AI Village town map in five historical periods.

Usage: python make_maps.py OUT_DIR [SCALE]
SCALE (default 1) also saves a crisp "-Nx" enlargement of each map: every
art pixel becomes an N by N block, so nothing blurs when zooming.
Needs Pillow. Every map shares one layout (LAYOUT constants below), so
doors, yards and paths sit in the same place whichever period is chosen.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image

T = 16                      # pixels per tile
W, H = 80, 60               # map size in tiles
HOUSES = [(8, 5), (20, 5), (52, 5), (64, 5), (6, 21), (66, 21),
          (6, 37), (66, 37), (20, 43), (52, 43)]   # top-left tile of each
HW, HH = 8, 7               # house footprint in tiles
HALL = (33, 12, 14, 9)      # x, y, w, h in tiles
PLAZA = (28, 24, 24, 16)
OUTLINE = (58, 36, 28)
SHADOW = (60, 38, 48)
WOOD = ((158, 104, 60), (124, 78, 44), (90, 56, 36))
WATER = ((160, 210, 206), (104, 170, 178), (72, 134, 154))
GLASS, GLINT, TRIM = (92, 132, 140), (214, 226, 200), (240, 226, 190)


def noise(x, y, s=0):
    """Deterministic 0..1 hash of a point, used for all texture."""
    h = (x * 374761393 + y * 668265263 + s * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536


def darker(c, k=0.74):
    return tuple(int(v * k) for v in c)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def disc(cx, cy, rx, ry):
    return {(x, y) for y in range(cy - ry, cy + ry + 1) for x in range(cx - rx, cx + rx + 1)
            if ((x - cx) / (rx + .4)) ** 2 + ((y - cy) / (ry + .4)) ** 2 <= 1}


def layout():
    """Tile grid: G grass, P path, Q plaza, Y yard, B building."""
    g = [['G'] * W for _ in range(H)]

    def fill(x0, y0, w, h, c):
        for y in range(max(0, y0), min(H, y0 + h)):
            for x in range(max(0, x0), min(W, x0 + w)):
                g[y][x] = c

    fill(*PLAZA, 'Q')
    for road in [(11, 15, 21, 2), (48, 15, 21, 2), (30, 15, 2, 9), (48, 15, 2, 9),
                 (38, 21, 4, 3), (9, 31, 19, 2), (52, 31, 19, 2), (0, 53, 80, 2), (39, 40, 2, 20)]:
        fill(*road, 'P')
    for hx, hy in HOUSES:
        fill(hx, hy, HW, HH, 'B')
        fill(hx - 1, hy + HH, HW + 2, 3, 'Y')
        y = hy + HH
        while y < H and g[y][hx + 3] != 'P':      # door path runs down to the road
            g[y][hx + 3] = g[y][hx + 4] = 'P'
            y += 1
    fill(*HALL, 'B')
    fill(37, 10, 6, 2, 'B')                        # room for the hall tower
    return g


class Canvas:
    def __init__(self):
        self.im = Image.new('RGB', (W * T, H * T))
        self.p = self.im.load()
        self.w, self.h = self.im.size
        self.shadow = set()

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[x, y] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.put(x, y, c)

    def frame(self, x0, y0, x1, y1, c=OUTLINE):
        for x in range(x0, x1):
            self.put(x, y0, c)
            self.put(x, y1 - 1, c)
        for y in range(y0, y1):
            self.put(x0, y, c)
            self.put(x1 - 1, y, c)

    def box(self, x0, y0, x1, y1, pal):
        """Small lit block: light left edge, dark right edge, outline."""
        self.rect(x0, y0, x1, y1, pal[1])
        self.rect(x0, y0, x0 + 2, y1, pal[0])
        self.rect(x1 - 2, y0, x1, y1, pal[2])
        self.frame(x0, y0, x1, y1)

    def blob(self, pts, pal, cx, cy, r, seed):
        """Shaded, outlined shape lit from the upper left."""
        L, M, D = pal
        for x, y in pts:
            d = ((x - cx) + (y - cy)) / (r * 1.4)
            n = noise(x, y, seed)
            col = L if d < -.3 + (n - .5) * .3 else D if d > .32 + (n - .5) * .3 else M
            n2 = noise(x, y, seed + 9)
            if col == M and n2 < .07:
                col = D
            elif col == M and n2 > .95:
                col = L
            self.put(x, y, col)
        for x, y in pts:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q not in pts:
                    self.put(*q, OUTLINE)

    def apply_shadow(self):
        for x, y in self.shadow:
            if 0 <= x < self.w and 0 <= y < self.h:
                self.p[x, y] = mix(self.p[x, y], SHADOW, .32)
        self.shadow = set()


# ---------- ground ----------

def surface(style, pal, x, y):
    L, M, D, E = pal
    n = noise(x, y, 1)
    if style == 'dirt':
        return D if n < .07 else L if n > .9 else M
    if style == 'pave':
        return E if x % 32 == 0 or y % 32 == 0 else L if n > .93 else M
    bw, bh = {'stone': (16, 8), 'cobble': (6, 5), 'brick': (8, 4)}[style]
    r = y // bh
    xx = x + (bw // 2 if r % 2 else 0)
    if y % bh == 0 or xx % bw == 0:
        return E
    t = noise(xx // bw, r, 2)
    return L if t > .62 else D if t < .22 else M


def grass(pal, x, y, stripes=False):
    L, M, D, M2 = pal
    n = noise(x, y, 5)
    base = M2 if noise(x // 12, y // 12, 6) > .6 else M
    if stripes:
        base = M2 if (x // 8) % 2 else M
    return D if n < .08 else L if n > .93 else base


def draw_ground(c, g, th):
    yard = tuple(mix(col, (240, 226, 150), .22) for col in th['grass'])
    paved = 'PQB'

    def tt(x, y):
        return g[min(H - 1, max(0, y))][min(W - 1, max(0, x))]

    for ty in range(H):
        for tx in range(W):
            k = g[ty][tx]
            l, r = tt(tx - 1, ty) not in paved, tt(tx + 1, ty) not in paved
            u, d = tt(tx, ty - 1) not in paved, tt(tx, ty + 1) not in paved
            for oy in range(T):
                for ox in range(T):
                    x, y = tx * T + ox, ty * T + oy
                    if k in 'PQ':
                        fx, fy = (ox if l else T), (oy if u else T)
                        gx, gy = (T - 1 - ox if r else T), (T - 1 - oy if d else T)
                        corner = min(fx, gx) + min(fy, gy)
                        if corner < 2:
                            col = grass(th['grass'], x, y)
                        elif corner == 2 or min(fx, gx, fy, gy) == 0:
                            col = pal_edge(th, k)
                        else:
                            style, pal = th['plaza'] if k == 'Q' else th['path']
                            col = surface(style, pal, x, y)
                    elif k == 'Y':
                        col = grass(yard, x, y, th.get('stripes', False))
                    else:
                        col = grass(th['grass'], x, y)
                    c.p[x, y] = col


def pal_edge(th, k):
    return darker((th['plaza'] if k == 'Q' else th['path'])[1][3], .86)


def draw_flowers(c, g, th, rng):
    for _ in range(420):
        x, y = rng.randrange(W * T), rng.randrange(H * T)
        if g[y // T][x // T] not in 'GY':
            continue
        if rng.random() < .25:                       # pebble
            c.blob(disc(x, y, 2, 1), th['stone'], x, y, 2, 3)
            continue
        petal = rng.choice(th['flowers'])
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            c.put(x + dx, y + dy, petal)
        c.put(x, y, (250, 224, 120))


# ---------- building parts ----------

def roof(c, x0, y0, x1, y1, style, pal, seed):
    L, M, D = pal
    ridge = y0 + (y1 - y0) // 4
    for y in range(y0, y1):
        for x in range(x0, x1):
            fx, n = (x - x0) / (x1 - x0), noise(x, y, seed)
            if style == 'flat':
                e = min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y)
                far = x1 - 1 - x < 4 or y1 - 1 - y < 4
                col = (M if far else L) if e < 4 else D if e == 4 or n < .08 else M
            else:
                if style == 'thatch':
                    t = noise(x // 2, y // 5, seed + 1)
                    col = L if t > .72 else D if t < .2 else M
                else:
                    step, tick = {'tile': (5, 6), 'shingle': (4, 8), 'slate': (4, 7)}[style]
                    r = (y - y0) // step
                    xx = x + (tick // 2 if r % 2 else 0)
                    col = D if (y - y0) % step == step - 1 or xx % tick == 0 else M
                    if col == M and (y - y0) % step == 0 and fx < .6:
                        col = L
                if y < ridge:
                    col = D if col != L else M
                elif y < ridge + 2:
                    col = L
                elif col == M and fx < .3 and n < .4:
                    col = L
                elif col == M and fx > .82 and n < .5:
                    col = D
            c.put(x, y, col)
    c.frame(x0, y0, x1, y1)


def wall(c, x0, y0, x1, y1, style, pal, seed):
    L, M, D = pal
    for y in range(y0, y1):
        for x in range(x0, x1):
            n, ry = noise(x, y, seed), y - y0
            if style in ('plaster', 'timber'):
                col = L if n > .9 else D if n < .04 else M
            elif style == 'brick':
                r = ry // 4
                xx = x + (4 if r % 2 else 0)
                col = L if ry % 4 == 3 or xx % 8 == 0 else D if noise(xx // 8, r, seed) < .25 else M
            elif style == 'plank':
                col = D if (x - x0) % 6 == 5 else L if n > .92 else M
            elif style == 'siding':
                col = D if ry % 4 == 3 else L if ry % 4 == 0 else M
            elif style == 'wattle':
                t = noise(x // 3, y // 2, seed)
                col = L if t > .7 else D if t < .25 else M
            else:                                   # stone blocks
                r = ry // 6
                xx = x + (6 if r % 2 else 0)
                col = D if ry % 6 == 5 or xx % 12 == 0 else L if noise(xx // 12, r, seed) > .6 else M
            if ry < 3 or (x1 - x <= (x1 - x0) // 10 and n < .5):
                col = darker(col)                   # eave shadow, shaded right end
            if y1 - y <= 3:
                col = darker(D, .9)
            c.put(x, y, col)
    if style == 'timber':
        beam = (98, 62, 42)
        w = x1 - x0
        for bx in (x0, x0 + w // 4, x0 + w // 2 - 1, x0 + 3 * w // 4, x1 - 3):
            c.rect(bx, y0, bx + 3, y1, beam)
        c.rect(x0, y0 + 3, x1, y0 + 6, beam)
        for i in range(w // 4 - 3):                 # corner braces
            c.put(x0 + 3 + i, y1 - 4 - i, beam)
            c.put(x1 - 4 - i, y1 - 4 - i, beam)
    c.frame(x0, y0, x1, y1)


def door(c, cx, y1, w, h, arch=False, double=False):
    x0, y0 = cx - w // 2, y1 - h
    for y in range(y0, y1):
        for x in range(x0, x0 + w):
            c.put(x, y, WOOD[2] if (x - x0) % 4 == 3 else WOOD[0] if x - x0 < 2 else WOOD[1])
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y1 + 1)
    if arch:
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            c.put(x0 + dx, y0 + dy, OUTLINE)
            c.put(x0 + w - 1 - dx, y0 + dy, OUTLINE)
    if double:
        c.rect(cx, y0, cx + 1, y1, OUTLINE)
        c.put(cx - 3, y0 + h // 2, TRIM)
    c.put(cx + 3 if double else x0 + w - 4, y0 + h // 2, TRIM)
    c.box(x0 - 4, y1, x0 + w + 4, y1 + 4, ((226, 212, 190), (196, 180, 158), (160, 144, 128)))


def window(c, x0, y0, w, h, style):
    c.rect(x0, y0, x0 + w, y0 + h, GLASS)
    for i in range(min(w, h) - 2):
        if 2 <= i <= 5:
            c.put(x0 + 1 + i, y0 + h - 2 - i, GLINT)
    c.rect(x0 + w // 2, y0, x0 + w // 2 + 1, y0 + h, TRIM)
    c.rect(x0, y0 + h // 2, x0 + w, y0 + h // 2 + 1, TRIM)
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1)
    c.rect(x0 - 2, y0 + h + 1, x0 + w + 2, y0 + h + 3, TRIM)
    if style == 'shutter':
        c.box(x0 - 6, y0 - 1, x0 - 1, y0 + h + 1, WOOD)
        c.box(x0 + w + 1, y0 - 1, x0 + w + 6, y0 + h + 1, WOOD)
    if style == 'box':
        c.box(x0 - 2, y0 + h + 2, x0 + w + 2, y0 + h + 6, WOOD)
        for i in range(x0 - 1, x0 + w + 1, 3):
            c.put(i, y0 + h + 1, (214, 70, 60))
            c.put(i + 1, y0 + h, (120, 150, 66))


def chimney(c, x, y, pal):
    c.shadow |= {(i, j) for i in range(x + 12, x + 18) for j in range(y + 6, y + 22)}
    c.box(x, y + 3, x + 12, y + 20, pal)
    c.box(x - 1, y, x + 13, y + 5, tuple(mix(p, (236, 222, 196), .45) for p in pal))


def house(c, tx, ty, th, i, rng):
    x0, y0 = tx * T, ty * T
    x1, y1, cx = x0 + HW * T, y0 + HH * T, x0 + HW * T // 2
    rstyle, rpal = th['roofs'][i % len(th['roofs'])]
    wstyle, wpal = rng.choice(th['walls'])
    if th.get('hut'):
        cy = y0 + 52
        c.blob(disc(cx, cy + 12, 44, 40), wpal, cx, cy + 12, 44, i)
        pts = disc(cx, cy - 4, 52, 40)
        c.blob(pts, rpal, cx, cy - 4, 46, i + 20)
        for x, y in pts:                            # thatch rings and spokes
            rr = math.hypot((x - cx) / 52, (y - cy + 4) / 40)
            a = math.atan2(y - cy + 4, x - cx) * 16 / math.pi
            if rr < .97 and (abs(rr - .38) < .02 or abs(rr - .7) < .016
                             or (abs(a - round(a)) < .09 and rr > .12)) and noise(x, y, 4) < .7:
                c.put(x, y, rpal[2])
        c.blob(disc(cx, cy - 4, 4, 3), (WOOD[2], darker(WOOD[2]), OUTLINE), cx, cy - 4, 4, 1)
        c.rect(cx - 7, cy + 35, cx + 7, cy + 52, (52, 32, 28))
        c.box(cx - 10, cy + 32, cx - 6, cy + 53, WOOD)
        c.box(cx + 6, cy + 32, cx + 10, cy + 53, WOOD)
        c.box(cx - 11, cy + 30, cx + 11, cy + 35, WOOD)
        return
    yw = y0 + 60
    wall(c, x0, yw, x1, y1, wstyle, wpal, i + 30)
    if th.get('window'):
        for wx in (x0 + 18, x1 - 32):
            window(c, wx, yw + 13, 14, 14, th['window'])
    door(c, cx, y1 - 1, 16, 28, th.get('arch', False))
    roof(c, x0 - 4, y0, x1 + 4, yw + 1, rstyle, rpal, i + 40)
    if th.get('chimney'):
        chimney(c, x0 + (18 if i % 2 else HW * T - 32), y0 + 6, th['chimney'])
        c.apply_shadow()


def hall(c, th):
    tx, ty, tw, hh = HALL
    x0, y0 = tx * T, ty * T
    x1, y1, cx, yw = x0 + tw * T, y0 + hh * T, x0 + tw * T // 2, y0 + 76
    wstyle, wpal = th['hall_wall']
    rstyle, rpal = th['hall_roof']
    feat = th['feature']
    wall(c, x0, yw, x1, y1, wstyle, wpal, 77)
    if feat not in ('temple', 'posts'):
        for wx in (x0 + 16, x0 + 52, x1 - 68, x1 - 32):
            window(c, wx, yw + 16, 16, 24, th.get('window'))
    door(c, cx, y1 - 1, 28, 42, th.get('arch', False), double=True)
    roof(c, x0 - 4, y0, x1 + 4, yw + 1, rstyle, rpal, 78)
    marble = ((250, 242, 222), (228, 214, 188), (192, 174, 148))
    if feat == 'temple':
        for k in range(46):                         # pediment
            y, half = yw - 45 + k, int(k * 104 / 45)
            for x in range(cx - half, cx + half + 1):
                edge = abs(x - cx) >= half - 1 or k == 45
                c.put(x, y, OUTLINE if edge else marble[2] if abs(x - cx) >= half - 4 else marble[1])
        c.blob(disc(cx, yw - 15, 7, 7), th['roofs'][0][1], cx, yw - 15, 7, 2)
        c.box(x0 - 2, yw - 1, x1 + 2, yw + 5, marble)
        for px in (x0 + 8, x0 + 38, x0 + 68, x1 - 78, x1 - 48, x1 - 18):
            c.box(px, yw + 5, px + 10, y1 - 3, marble)
            c.box(px - 2, yw + 5, px + 12, yw + 9, marble)
            c.box(px - 2, y1 - 5, px + 12, y1 - 1, marble)
    elif feat in ('tower', 'clock'):
        wall(c, cx - 24, y0 + 4, cx + 24, y0 + 58, wstyle, wpal, 79)
        for k in range(27):
            y, half = y0 - 22 + k, 2 + k
            for x in range(cx - half, cx + half + 1):
                col = rpal[0] if x < cx - half // 3 else rpal[1] if x < cx + half // 3 else rpal[2]
                c.put(x, y, OUTLINE if abs(x - cx) == half or k == 26 else col)
        if feat == 'clock':
            c.blob(disc(cx, y0 + 28, 12, 12), marble, cx, y0 + 28, 30, 5)
            for dx, dy in ((0, -10), (10, 0), (0, 10), (-10, 0)):
                c.put(cx + dx, y0 + 28 + dy, OUTLINE)
            c.rect(cx, y0 + 20, cx + 1, y0 + 29, OUTLINE)
            c.rect(cx, y0 + 28, cx + 7, y0 + 29, OUTLINE)
        else:
            c.rect(cx - 2, y0 + 20, cx + 2, y0 + 36, (52, 32, 28))
            c.frame(cx - 3, y0 + 19, cx + 3, y0 + 37)
            c.rect(cx, y0 - 34, cx + 1, y0 - 22, OUTLINE)
            for k in range(6):
                c.rect(cx + 1, y0 - 34 + k, cx + 11 - 2 * k, y0 - 33 + k, (206, 70, 56))
            for bx in (cx - 40, cx + 32):           # plain banners by the door
                c.box(bx, yw + 14, bx + 9, yw + 40, ((226, 96, 72), (196, 66, 54), (150, 46, 44)))
    elif feat == 'modern':
        c.box(cx - 30, yw + 14, cx + 30, yw + 21, ((226, 110, 80), (198, 84, 62), (150, 60, 50)))
        px, py = x0 + 44, y1 + 42
        c.rect(px, py - 62, px + 2, py, (112, 100, 100))
        c.frame(px - 1, py - 63, px + 3, py + 1)
        for k, col in enumerate(((206, 70, 56), TRIM, (206, 70, 56))):
            c.rect(px + 3, py - 61 + k * 4, px + 21, py - 57 + k * 4, col)
        c.frame(px + 2, py - 62, px + 22, py - 48)
    elif feat == 'posts':
        for px in (cx - 30, cx + 22):
            c.box(px, yw + 10, px + 8, y1 + 3, WOOD)
            for k in range(3):
                c.rect(px + 1, yw + 18 + k * 12, px + 7, yw + 20 + k * 12, WOOD[2])
            flame(c, px + 4, yw + 9)


def flame(c, cx, y):
    for dx, dy, col in ((0, -6, (250, 206, 90)), (-1, -5, (240, 150, 60)), (1, -5, (240, 150, 60)),
                        (0, -5, (252, 232, 150)), (-2, -3, (232, 120, 50)), (2, -3, (232, 120, 50)),
                        (-1, -3, (250, 206, 90)), (0, -3, (252, 232, 150)), (1, -3, (250, 206, 90)),
                        (-2, -1, (220, 96, 46)), (-1, -1, (240, 150, 60)), (0, -1, (250, 206, 90)),
                        (1, -1, (240, 150, 60)), (2, -1, (220, 96, 46))):
        c.rect(cx + dx, y + dy, cx + dx + 1, y + dy + 2, col)


# ---------- square furniture ----------

def fountain(c, cx, cy, th):
    stone = th['stone']
    inner = disc(cx, cy - 1, 27, 20)
    if th['fountain'] == 'spring':
        c.blob(inner, WATER, cx, cy, 26, 11)
        for k in range(16):
            a = k * math.pi / 8
            bx, by = cx + int(31 * math.cos(a)), cy + int(23 * math.sin(a))
            c.blob(disc(bx, by, 6 + k % 2, 5), stone, bx, by, 6, k)
        c.blob(disc(cx, cy - 10, 6, 12), stone, cx, cy - 10, 10, 3)
    else:
        c.blob(disc(cx, cy, 35, 27), stone, cx, cy, 34, 10)
        c.blob(inner, WATER, cx, cy, 26, 11)
        c.box(cx - 4, cy - 20, cx + 4, cy + 3, stone)
        c.blob(disc(cx, cy - 20, 12, 5), stone, cx, cy - 20, 10, 12)
        c.blob(disc(cx, cy - 21, 8, 2), WATER, cx, cy - 21, 6, 13)
        if th['fountain'] == 'tiered':
            c.box(cx - 2, cy - 32, cx + 2, cy - 23, stone)
            c.blob(disc(cx, cy - 32, 6, 3), stone, cx, cy - 32, 5, 14)
    top = cy - (37 if th['fountain'] == 'tiered' else 27)
    spray = (244, 252, 246)
    for k in range(5):
        c.put(cx, top + k, spray)
    for k in range(16):                            # falling water
        if k % 3 != 2:
            c.put(cx - 12 - k // 4, cy - 17 + k, spray)
            c.put(cx + 12 + k // 4, cy - 17 + k, spray)


def post(c, x, y, kind, th):
    if kind == 'urn':
        c.blob(disc(x, y - 7, 6, 7), th['roofs'][0][1], x, y - 7, 6, 21)
        c.blob(disc(x, y - 17, 7, 5), th['trees'][0][1], x, y - 17, 6, 22)
        return
    pole = WOOD if kind == 'torch' else ((118, 104, 108), (86, 72, 80), (60, 48, 58))
    c.box(x - 3, y - 3, x + 3, y, pole)
    c.box(x - 2, y - 26, x + 2, y - 2, pole)
    if kind == 'torch':
        flame(c, x, y - 27)
    else:
        c.box(x - 5, y - 37, x + 5, y - 26, ((255, 244, 190), (250, 220, 130), (226, 180, 90)))
        c.box(x - 6, y - 39, x + 6, y - 36, pole)


def bench(c, x, y):
    c.box(x - 14, y - 7, x + 14, y - 2, WOOD)
    c.box(x - 14, y - 2, x + 14, y + 3, (WOOD[0], WOOD[0], WOOD[1]))
    c.rect(x - 12, y + 3, x - 10, y + 6, OUTLINE)
    c.rect(x + 10, y + 3, x + 12, y + 6, OUTLINE)


# ---------- trees ----------

def tree_shape(kind, cx, by):
    if kind == 'tall':
        return disc(cx, by - 27, 7, 20), 27
    if kind == 'pine':
        pts = set()
        for i in range(3):
            for k in range(17):
                half = 1 + (k * (7 + 3 * i)) // 16
                pts |= {(x, by - 46 + i * 11 + k) for x in range(cx - half, cx + half + 1)}
        return pts, 26
    if kind == 'small':
        return disc(cx, by - 18, 12, 10) | disc(cx - 7, by - 13, 8, 6) | disc(cx + 8, by - 14, 7, 6), 18
    return (disc(cx, by - 24, 15, 13) | disc(cx - 9, by - 17, 9, 8)
            | disc(cx + 9, by - 17, 9, 8) | disc(cx, by - 32, 10, 8)), 24


def tree(c, cx, by, kind, pal, seed):
    c.box(cx - 3, by - 12, cx + 3, by, WOOD)
    pts, up = tree_shape(kind, cx, by)
    c.blob(pts, pal, cx, by - up, 17, seed)


def place_trees(g, th, rng):
    def free(tx, ty):
        return all(0 <= x < W and 0 <= y < H and g[y][x] == 'G'
                   for y in range(ty - 3, ty + 1) for x in range(tx - 1, tx + 2))

    out, taken = [], set()
    for _ in range(2600):
        tx, ty = rng.randrange(1, W - 1), rng.randrange(3, H)
        edge = min(tx, W - 1 - tx, ty - 2, H - 1 - ty)
        if not free(tx, ty) or rng.random() > (.9 if edge < 3 else .2):
            continue
        if any((tx + dx, ty + dy) in taken for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        taken.add((tx, ty))
        kind, pal = rng.choice(th['trees'])
        out.append((ty * T + 14 + rng.randrange(-2, 2), tx * T + 8 + rng.randrange(-3, 4), kind, pal))
    return sorted(out)


# ---------- themes ----------

OAK = ((154, 182, 76), (110, 148, 60), (72, 110, 54))
DARK_OAK = ((128, 162, 72), (90, 130, 58), (60, 96, 52))
PINE = ((108, 144, 84), (72, 110, 68), (48, 80, 58))
CYPRESS = ((114, 144, 74), (78, 112, 62), (52, 82, 54))
OLIVE = ((180, 184, 124), (142, 152, 100), (106, 118, 82))
MAPLE = ((244, 176, 76), (216, 128, 50), (170, 86, 42))
RUSSET = ((228, 124, 72), (194, 86, 54), (146, 60, 46))
BLOSSOM = ((250, 200, 190), (230, 156, 156), (188, 114, 124))
THATCH = [((234, 200, 118), (206, 166, 88), (160, 120, 62)),
          ((224, 186, 122), (192, 152, 92), (146, 110, 66)),
          ((216, 182, 100), (186, 148, 74), (140, 106, 52))]
TERRACOTTA = [((228, 136, 84), (198, 102, 62), (150, 70, 46)),
              ((234, 152, 92), (206, 118, 68), (158, 82, 50)),
              ((216, 122, 82), (184, 92, 62), (138, 62, 46))]
BROWN_ROOF = ((178, 118, 80), (148, 92, 62), (108, 64, 46))
RED_ROOF = ((198, 106, 74), (166, 80, 58), (122, 54, 44))
SLATE = ((152, 120, 130), (120, 92, 106), (86, 64, 78))
CREAM = ((250, 238, 206), (234, 216, 178), (200, 178, 140))
SAND = ((248, 226, 190), (230, 200, 160), (196, 164, 126))
BRICK = ((208, 122, 86), (180, 94, 66), (138, 66, 50))
GREY_STONE = ((206, 194, 178), (170, 158, 144), (126, 114, 108))
DIRT = ((206, 170, 118), (184, 146, 96), (150, 114, 74), (126, 92, 60))

THEMES = [
    dict(file='1-iron-age', name='Iron Age roundhouse village, about 500 BC', hut=True,
         grass=((158, 176, 84), (128, 152, 66), (98, 124, 54), (138, 158, 70)),
         path=('dirt', DIRT),
         plaza=('dirt', ((224, 192, 140), (206, 170, 118), (174, 138, 94), (140, 104, 68))),
         roofs=[('thatch', p) for p in THATCH],
         walls=[('wattle', ((206, 168, 124), (178, 136, 96), (138, 100, 70)))],
         hall_roof=('thatch', THATCH[0]), hall_wall=('wattle', ((206, 168, 124), (178, 136, 96), (138, 100, 70))),
         feature='posts', stone=GREY_STONE, fountain='spring', post='torch', bench=False,
         trees=[('round', OAK)] * 3 + [('pine', PINE)] * 2 + [('round', DARK_OAK)] * 2,
         flowers=[(250, 244, 220), (236, 196, 80)]),
    dict(file='2-roman', name='Roman town, about 100 AD',
         grass=((170, 180, 90), (142, 156, 70), (110, 128, 58), (152, 162, 74)),
         path=('stone', ((228, 214, 186), (206, 190, 160), (182, 164, 136), (148, 128, 104))),
         plaza=('stone', ((242, 230, 202), (224, 210, 180), (202, 186, 156), (164, 144, 118))),
         roofs=[('tile', p) for p in TERRACOTTA],
         walls=[('plaster', CREAM), ('plaster', SAND),
                ('plaster', ((246, 216, 152), (228, 190, 122), (192, 152, 94)))],
         window='shutter', hall_roof=('tile', TERRACOTTA[0]),
         hall_wall=('plaster', ((252, 244, 222), (238, 226, 198), (204, 190, 160))),
         feature='temple', stone=((244, 234, 212), (214, 200, 176), (170, 154, 134)),
         fountain='tiered', post='urn', bench=True,
         trees=[('tall', CYPRESS)] * 3 + [('small', OLIVE)] * 3 + [('round', OAK)],
         flowers=[(226, 96, 86), (250, 244, 220), (190, 130, 190)]),
    dict(file='3-medieval', name='Medieval market village, about 1300', arch=True,
         grass=((150, 178, 84), (116, 150, 66), (86, 120, 54), (126, 158, 70)),
         path=('dirt', ((200, 166, 122), (176, 140, 100), (144, 110, 78), (118, 88, 62))),
         plaza=('cobble', ((206, 192, 172), (182, 166, 146), (156, 140, 124), (118, 102, 90))),
         roofs=[('thatch', THATCH[0]), ('shingle', BROWN_ROOF), ('thatch', THATCH[2]), ('shingle', RED_ROOF)],
         walls=[('timber', CREAM), ('timber', ((240, 220, 176), (222, 196, 150), (188, 160, 120)))],
         window='box', chimney=GREY_STONE, hall_roof=('shingle', RED_ROOF), hall_wall=('stone', GREY_STONE),
         feature='tower', stone=GREY_STONE, fountain='basin', post='torch', bench=False,
         trees=[('round', OAK)] * 4 + [('round', DARK_OAK)] * 2 + [('pine', PINE)],
         flowers=[(226, 96, 86), (250, 244, 220), (236, 196, 80)]),
    dict(file='4-victorian', name='Victorian town, about 1880', arch=True,
         grass=((146, 170, 86), (112, 142, 68), (84, 114, 56), (122, 150, 72)),
         path=('cobble', ((200, 186, 172), (174, 160, 148), (148, 134, 126), (112, 98, 94))),
         plaza=('brick', ((224, 162, 122), (202, 136, 100), (174, 110, 82), (150, 96, 74))),
         roofs=[('slate', SLATE), ('slate', ((142, 106, 98), (112, 80, 76), (80, 56, 56))), ('shingle', RED_ROOF)],
         walls=[('brick', BRICK), ('brick', ((216, 152, 106), (190, 124, 84), (148, 92, 62))), ('plaster', CREAM)],
         window='plain', chimney=BRICK, hall_roof=('slate', SLATE), hall_wall=('brick', BRICK),
         feature='clock', stone=GREY_STONE, fountain='tiered', post='lamp', bench=True,
         trees=[('round', OAK)] * 3 + [('round', MAPLE)] * 2 + [('round', RUSSET)],
         flowers=[(250, 244, 220), (236, 196, 80), (226, 130, 110)]),
    dict(file='5-nineteen-fifties', name='1950s small town', stripes=True,
         grass=((160, 186, 92), (128, 160, 72), (98, 130, 60), (138, 168, 78)),
         path=('pave', ((234, 224, 206), (216, 206, 188), (192, 182, 166), (172, 160, 146))),
         plaza=('pave', ((242, 226, 202), (228, 210, 184), (202, 184, 160), (180, 160, 138))),
         roofs=[('shingle', RED_ROOF), ('shingle', BROWN_ROOF),
                ('shingle', ((228, 182, 92), (200, 150, 66), (154, 110, 48))),
                ('shingle', ((222, 142, 132), (192, 110, 104), (146, 78, 78)))],
         walls=[('siding', ((252, 242, 214), (236, 222, 188), (204, 188, 154))),
                ('siding', ((250, 228, 152), (232, 204, 122), (196, 166, 94))),
                ('siding', ((250, 206, 172), (232, 180, 144), (196, 142, 112))),
                ('siding', ((216, 224, 172), (192, 202, 146), (154, 166, 116)))],
         window='box', chimney=BRICK,
         hall_roof=('flat', ((230, 218, 200), (198, 184, 168), (160, 146, 134))),
         hall_wall=('plaster', CREAM), feature='modern', stone=((236, 226, 208), (204, 192, 174), (160, 148, 136)),
         fountain='basin', post='lamp', bench=True,
         trees=[('round', OAK)] * 3 + [('round', BLOSSOM)] * 2 + [('round', MAPLE)],
         flowers=[(250, 244, 220), (236, 196, 80), (240, 150, 160)]),
]


def draw_map(th, seed):
    rng = random.Random(seed)
    g, c = layout(), Canvas()
    draw_ground(c, g, th)
    draw_flowers(c, g, th, rng)
    trees = place_trees(g, th, rng)
    px, py, pw, ph = (v * T for v in PLAZA)
    fx, fy = px + pw // 2, py + ph // 2
    posts = [(px + 24, py + 40), (px + pw - 24, py + 40), (px + 24, py + ph - 12), (px + pw - 24, py + ph - 12)]
    benches = [(fx - 76, fy + 4), (fx + 76, fy + 4)] if th['bench'] else []

    for tx, ty in HOUSES:                           # every shadow first, so nothing shades twice
        x0, y0 = tx * T, ty * T
        if th.get('hut'):
            c.shadow |= disc(x0 + 72, y0 + 72, 50, 40)
        else:
            c.shadow |= {(x, y) for x in range(x0 + 8, x0 + 138) for y in range(y0 + 24, y0 + 119)}
    hx, hy = HALL[0] * T, HALL[1] * T
    c.shadow |= {(x, y) for x in range(hx + 10, hx + 236) for y in range(hy + 30, hy + 153)}
    c.shadow |= disc(fx + 8, fy + 6, 35, 27)
    for by, cx, kind, _ in trees:
        c.shadow |= disc(cx + 5, by - 1, 7 if kind in ('tall', 'pine') else 13, 5)
    for x, y in posts + benches:
        c.shadow |= disc(x + 3, y, 6, 2)
    c.apply_shadow()

    for i, (tx, ty) in enumerate(HOUSES):
        house(c, tx, ty, th, i, rng)
    hall(c, th)
    fountain(c, fx, fy, th)
    for x, y in posts:
        post(c, x, y, th['post'], th)
    for x, y in benches:
        bench(c, x, y)
    for i, (by, cx, kind, pal) in enumerate(trees):
        tree(c, cx, by, kind, pal, i)
    return c.im


def main(out_dir, scale=1):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i, th in enumerate(THEMES):
        im = draw_map(th, 100 + i)
        im.save(out / f"town-{th['file']}.png")
        if scale > 1:
            big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            big.save(out / f"town-{th['file']}-{scale}x.png", optimize=True)
        print(th['file'], '-', th['name'])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'maps',
         int(sys.argv[2]) if len(sys.argv) > 2 else 1)
