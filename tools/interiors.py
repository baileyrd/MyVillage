#!/usr/bin/env python3
"""Draw the inside of every house: one room per building, nobody in it.

Usage: python interiors.py OUT_DIR [DETAIL] [ROOM ...]
DETAIL 1 is the draft: 512 x 384, a standing person is 32 pixels, one twelfth of the
height. DETAIL 2 is the finished room: 1024 x 768, so the 64-pixel visitor from the town
is exactly one twelfth, plus a 4K copy (4096 x 3072) where every art pixel is a crisp
4 x 4 block. All positions below are in draft pixels whatever the detail.
The room fills the image: a thin back wall on top, thin side walls, and a thin
front wall at the bottom with one door in the middle. Every room has exactly one
desk with a chair behind it, where its owner will sit facing the door.

A room is a floor, a wall colour, things hung on the back wall, and a list of
things standing on the floor as (name, x, y, options). (x, y) is the middle of
the thing's front foot. Things are drawn far to near.
"""
import os
import sys

from PIL import Image

import kit
from kit import ACCENT, BRASS3, CREAM, GLOW, MARBLE, OUTLINE, SHADOW, block, darker, disc, mix, noise

W, H = 512, 384
WALL_H, SIDE, FRONT = 40, 6, 10                             # back wall height, side and front wall thickness
DOOR = (240, 272)
PERSON = H // 12

WALNUT = ((150, 104, 72), (118, 78, 54), (84, 54, 40))
MAHOG = ((176, 96, 68), (140, 68, 52), (98, 44, 38))
OAK = ((226, 182, 124), (200, 154, 100), (158, 116, 76))
EBONY = ((96, 82, 84), (64, 52, 58), (42, 32, 40))
STEEL = ((212, 208, 202), (170, 166, 166), (120, 114, 122))
GOLD = ((255, 230, 128), (240, 192, 72), (190, 138, 50))
PAPER = ((255, 250, 236), (240, 230, 206), (206, 192, 164))
GREEN = ((104, 142, 104), (72, 108, 80), (46, 76, 60))
OXBLOOD = ((184, 76, 66), (146, 50, 50), (100, 34, 42))
TEAL = ((96, 146, 150), (64, 112, 122), (42, 78, 94))
NAVY = ((92, 104, 142), (64, 74, 112), (44, 50, 82))
PLUM = ((150, 104, 128), (116, 76, 102), (82, 52, 76))
LEAF = ((146, 178, 92), (104, 142, 72), (66, 102, 58))
GLASS = ((236, 248, 248), (204, 230, 234), (170, 206, 214))
SPINES = (OXBLOOD, GREEN, NAVY, GOLD, PLUM, TEAL, CREAM, MAHOG)


class Canvas(kit.Canvas):
    """A room canvas. Everything is placed in draft pixels; k is how many real pixels each one is."""

    def __init__(self, k=1):
        super().__init__(W * k, H * k)
        self.k = k

    def dot(self, X, Y, col):
        """One real pixel."""
        if 0 <= X < self.w and 0 <= Y < self.h:
            self.p[X, Y] = col

    def fill(self, X0, Y0, X1, Y1, col):
        """A block of real pixels."""
        for Y in range(max(0, Y0), min(self.h, Y1)):
            for X in range(max(0, X0), min(self.w, X1)):
                self.p[X, Y] = col

    def tone(self, X, Y, col, a):
        if 0 <= X < self.w and 0 <= Y < self.h:
            self.p[X, Y] = mix(self.p[X, Y], col, a)

    def put(self, x, y, col):
        self.fill(x * self.k, y * self.k, (x + 1) * self.k, (y + 1) * self.k, col)

    def get(self, x, y):
        return self.p[min(self.w - 1, max(0, x * self.k)), min(self.h - 1, max(0, y * self.k))]

    def dim(self, x, y, a=.3):
        for Y in range(y * self.k, (y + 1) * self.k):
            for X in range(x * self.k, (x + 1) * self.k):
                self.tone(X, Y, SHADOW, a)

    def blob(self, pts, pal, cx, cy, r, seed):
        """Shaded, outlined shape lit from the upper left; the shading is worked out per real pixel."""
        L, M, D = pal
        k = self.k
        for x, y in pts:
            for Y in range(y * k, (y + 1) * k):
                for X in range(x * k, (x + 1) * k):
                    d = ((X / k - cx) + (Y / k - cy)) / (r * 1.4)
                    n = noise(X, Y, seed)
                    col = L if d < -.3 + (n - .5) * .3 else D if d > .32 + (n - .5) * .3 else M
                    self.dot(X, Y, col)
        for x, y in pts:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q not in pts:
                    self.put(*q, OUTLINE)

    def oval(self, x, y, rx, ry, pal, seed):
        """A smooth shaded ball or dish with an outline and a small glint."""
        k = self.k
        cx, cy, ax, ay = (x + .5) * k, (y + .5) * k, (rx + .9) * k, (ry + .9) * k
        for Y in range(int(cy - ay - k) - 1, int(cy + ay + k) + 2):
            for X in range(int(cx - ax - k) - 1, int(cx + ax + k) + 2):
                u, v = (X + .5 - cx), (Y + .5 - cy)
                if (u / (ax + k)) ** 2 + (v / (ay + k)) ** 2 > 1:
                    continue
                if (u / ax) ** 2 + (v / ay) ** 2 > 1:
                    self.dot(X, Y, OUTLINE)
                    continue
                d = (u / ax + v / ay) / 1.4 + (noise(X, Y, seed) - .5) * .22
                col = pal[0] if d < -.3 else pal[2] if d > .32 else pal[1]
                if rx >= 4 and ((u + ax * .4) / ax) ** 2 + ((v + ay * .45) / ay) ** 2 < .035:
                    col = mix(pal[0], (255, 255, 255), .6)
                self.dot(X, Y, col)

    def line(self, x0, y0, x1, y1, col, w=1):
        k = self.k
        n = max(abs(x1 - x0), abs(y1 - y0), 1) * k
        for i in range(n + 1):
            X, Y = round((x0 + (x1 - x0) * i / n) * k), round((y0 + (y1 - y0) * i / n) * k)
            self.fill(X, Y, X + w * k, Y + w * k, col)


# ---------- floors: each returns colour(X, Y, k) for a real pixel ----------

def parquet(pal):
    L, M, D = pal

    def at(X, Y, k):
        u, pw = 12 * k, 4 * k
        if (X // u + Y // u) % 2:
            seam, plank, along, across = Y % pw == 0 or X % u == 0, (X // u, Y // pw), X, Y
        else:
            seam, plank, along, across = X % pw == 0 or Y % u == 0, (X // pw, Y // u), Y, X
        if seam:
            return D
        t = noise(plank[0], plank[1], 3)
        col = L if t > .7 else mix(M, D, .35) if t < .2 else M
        if k > 1 and noise(along // (5 * k), across, 17) < .2:
            col = mix(col, D, .22)                          # grain
        return col
    return at


def planks(pal):
    L, M, D = pal

    def at(X, Y, k):
        r = Y // (8 * k)
        xx = X + (23 * k if r % 2 else 0)
        if Y % (8 * k) == 0 or xx % (46 * k) == 0:
            return D
        t = noise(xx // (46 * k), r, 5)
        col = L if t > .7 else mix(M, D, .3) if t < .2 else M
        if k > 1 and noise(xx // (6 * k), Y, 19) < .22:
            col = mix(col, D, .2)
        if k > 1 and Y % (8 * k) == 1:
            col = mix(col, L, .35)                          # polish along the top of each board
        return col
    return at


def checker(a, b):
    def at(X, Y, k):
        t = 16 * k
        pal = a if (X // t + Y // t) % 2 else b
        if X % t == 0 or Y % t == 0:
            return pal[2]
        if k > 1 and (X % t == 1 or Y % t == 1):
            return pal[0]                                   # bevelled edge
        if noise(X // (k + 1), (X + Y) // (3 * k), 8) > (.93 if k == 1 else .9) and noise(X // (5 * k), Y // (5 * k), 9) > .45:
            return pal[0]                                   # veins
        return pal[0] if noise(X, Y, 7) > .93 else pal[1]
    return at


def carpet(pal):
    def at(X, Y, k):
        n = noise(X, Y, 11)
        col = pal[0] if n > .88 else pal[2] if n < .1 else pal[1]
        return mix(col, pal[2], .18) if k > 1 and (X + Y) % 4 == 0 else col
    return at


# ---------- the shell ----------

def shell(c, floor, wall, trim=WALNUT):
    k = c.k
    for Y in range(H * k):
        for X in range(W * k):
            c.dot(X, Y, floor(X, Y, k))
    for y in range(WALL_H, WALL_H + 4):                     # soft shadow under the back wall
        for x in range(SIDE, W - SIDE):
            c.dim(x, y, .34 - .07 * (y - WALL_H))
    for Y in range(4 * k, (WALL_H - 9) * k):                # wallpaper: fine stripes and a small diamond
        for X in range(W * k):
            sx, sy = X % (12 * k), Y % (10 * k)
            col = wall[0] if sx < max(1, k // 2) else wall[1]
            if abs(sx - 6 * k) + abs(sy - 5 * k) < 1.5 * k:
                col = wall[2] if k == 1 or abs(sx - 6 * k) + abs(sy - 5 * k) >= .5 * k else wall[0]
            c.dot(X, Y, col)
    c.rect(0, 4, W, 6, mix(wall[1], OUTLINE, .25))
    c.rect(0, WALL_H - 10, W, WALL_H - 9, GOLD[1])           # picture rail above the panelling
    for Y in range((WALL_H - 9) * k, WALL_H * k):           # panelling, with a recessed field in each panel
        for X in range(W * k):
            px, py = X % (24 * k), Y - (WALL_H - 9) * k
            col = trim[2] if px < k or py >= 8 * k else trim[0] if py < k else trim[1]
            if k > 1 and 4 * k <= px < 21 * k and 3 * k <= py < 7 * k:
                col = trim[2] if px == 4 * k or py == 3 * k else trim[0] if px == 21 * k - 1 or py == 7 * k - 1 else mix(trim[1], trim[2], .3)
            c.dot(X, Y, col)
    cap = darker(trim[2], .8)
    c.rect(0, 0, W, 4, cap)
    c.rect(0, 0, SIDE, H, cap)
    c.rect(W - SIDE, 0, W, H, cap)
    c.rect(0, H - FRONT, W, H, cap)
    c.rect(0, 0, W, 1, trim[1])
    c.rect(1, 1, 2, H - 1, trim[1])
    c.frame(SIDE - 1, 3, W - SIDE + 1, H - FRONT + 1)
    c.frame(0, 0, W, H)
    c.rect(0, WALL_H, SIDE - 1, WALL_H + 1, OUTLINE)
    x0, x1 = DOOR                                           # the door: polished leaves set in the front wall
    c.rect(x0, H - FRONT, x1, H, OAK[1])
    c.rect(x0, H - FRONT, x1, H - FRONT + 2, OAK[0])
    c.rect(x0 + 15, H - FRONT, x0 + 17, H, OAK[2])
    c.frame(x0 - 1, H - FRONT - 1, x1 + 1, H + 1)
    for kx in (x0 + 12, x0 + 18):
        c.rect(kx, H - 6, kx + 2, H - 4, GOLD[0])
    rug(c, (x0 + x1) // 2, H - FRONT - 2, 40, 10, OXBLOOD)   # door mat


# ---------- building blocks ----------

def slab(c, x, y, w, d, h, top, side=None, shadow=True):
    """A box seen three-quarter: w wide, d deep, h tall, front foot centred on (x, y)."""
    side = side or top
    x0, y0 = x - w // 2, y - h - d
    if shadow:
        for px, py in block(x0 + 3, y, x0 + w + 3, y + 3) | block(x0 + w, y0 + 5, x0 + w + 3, y + 3):
            c.dim(px, py, .3)
    c.rect(x0, y0, x0 + w, y - h, top[1])
    c.rect(x0, y0, x0 + w, y0 + 1, top[0])
    c.rect(x0, y0, x0 + 1, y - h, top[0])
    c.rect(x0, y - h, x0 + w, y, side[2])
    c.rect(x0, y - h, x0 + w, y - h + 1, side[1])
    c.rect(x0, y - h, x0 + 1, y, side[1])
    k = c.k
    if k > 1:                                               # grain and polish, in real pixels
        seed = x0 * 7 + y * 13
        for Y in range(y0 * k, (y - h) * k):
            for X in range(x0 * k, (x0 + w) * k):
                if Y == y0 * k or X == x0 * k:
                    c.tone(X, Y, (255, 250, 236), .3)
                elif noise(X // (4 * k), Y, seed) < .16:
                    c.tone(X, Y, top[2], .3)
        for Y in range((y - h) * k + k, y * k):
            a = .16 * (Y - (y - h) * k) / max(1, h * k)
            for X in range(x0 * k + k, (x0 + w) * k):
                c.tone(X, Y, OUTLINE, a + (.2 if Y == y * k - 1 else 0))
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y + 1)
    return x0, y0


def ball(c, x, y, r, pal, seed=1, ry=None):
    if c.k == 1:
        c.blob(disc(x, y, r, ry or r), pal, x, y, r, seed)
    else:
        c.oval(x, y, r, ry or r, pal, seed)


def rug(c, x, y, w, d, pal, border=GOLD, name=None):
    k = c.k
    x0, y0 = x - w // 2, y - d
    for Y in range(d * k):
        for X in range(w * k):
            edge = min(X, w * k - 1 - X, Y, d * k - 1 - Y) / k
            n = noise(X, Y, 13)
            col = pal[0] if n > .9 else pal[2] if n < .1 else pal[1]
            if w > 30 and 2 <= edge < 4:
                col = border[1] if k == 1 or 2.5 <= edge < 3.5 else border[2]
            elif k > 1 and w > 30 and 5 <= edge < 5.5:
                col = border[1]
            elif edge >= 7 and w > 60:
                lat = abs((X / k) % 14 - 7) + abs((Y / k) % 14 - 7)
                if 6 <= lat < 7 or lat < (1 if k > 1 else 0):
                    col = mix(col, border[1], .55)
            c.dot(x0 * k + X, y0 * k + Y, col)
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y + 1)


def chair(c, x, y, pal=OXBLOOD, wood=WALNUT, back=True):
    """A side chair. back=True shows its back rest above the seat (it faces the door)."""
    if back:
        slab(c, x, y - 6, 12, 0, 13, pal, pal, shadow=False)
        c.rect(x - 4, y - 16, x + 4, y - 15, pal[0])
    slab(c, x, y, 12, 6, 4, pal, wood)


def armchair(c, x, y, pal=OXBLOOD):
    slab(c, x, y - 7, 20, 0, 13, pal, pal, shadow=False)
    slab(c, x, y, 20, 8, 5, pal, pal)
    for ax in (x - 9, x + 9):
        slab(c, ax, y, 4, 9, 8, pal, pal, shadow=False)
    c.rect(x - 5, y - 17, x + 5, y - 16, pal[0])


def sofa(c, x, y, pal=GREEN, w=44):
    slab(c, x, y - 7, w, 0, 14, pal, pal, shadow=False)
    slab(c, x, y, w, 8, 5, pal, pal)
    for ax in (x - w // 2 + 2, x + w // 2 - 2):
        slab(c, ax, y, 5, 9, 9, pal, pal, shadow=False)
    for bx in range(x - w // 2 + 8, x + w // 2 - 6, 9):
        c.put(bx, y - 15, pal[2])
        c.rect(bx + 4, y - 12, bx + 5, y - 5, pal[2])


def table(c, x, y, w=30, d=14, pal=WALNUT, h=7, on=()):
    x0, y0 = slab(c, x, y, w, d, h, pal)
    c.rect(x0 + 2, y - h + 2, x0 + w - 2, y, darker(pal[2], .7))    # open underneath
    for lx in (x0, x0 + w - 3):
        c.rect(lx, y - h, lx + 3, y, pal[1])
    put_on(c, x0, y0, w, d, on)
    return x0, y0


def round_table(c, x, y, r=11, pal=WALNUT):
    for px, py in disc(x + 3, y - 1, r, r * 2 // 3):
        c.dim(px, py, .3)
    c.rect(x - 2, y - 8, x + 2, y, pal[2])
    ball(c, x, y - 10, r, pal, 4, r * 2 // 3)


def plant(c, x, y, tall=True):
    slab(c, x, y, 9, 3, 6, BRASS3)
    top = y - (24 if tall else 15)
    for i, (dx, dy, r) in enumerate(((0, 0, 6), (-5, 5, 5), (5, 6, 5), (0, 9, 6)) if tall else ((0, 0, 5), (-3, 4, 4), (4, 4, 4))):
        ball(c, x + dx, top + dy, r, LEAF, 20 + i)


def floor_lamp(c, x, y):
    for px, py in disc(x + 3, y, 5, 2):
        c.dim(px, py, .3)
    c.rect(x - 1, y - 26, x + 1, y, BRASS3[1])
    c.rect(x - 4, y - 1, x + 4, y + 1, BRASS3[2])
    c.frame(x - 5, y - 2, x + 5, y + 2)
    c.blob({(px, py) for py in range(y - 36, y - 25) for px in range(x - 4 - (py - y + 36) // 3, x + 5 + (py - y + 36) // 3)},
           GLOW, x, y - 30, 8, 2)


def rope(c, x, y, n=3, gap=22):
    """Brass posts joined by a velvet rope."""
    for i in range(n):
        px = x + i * gap
        if i:
            for t in range(gap):
                c.put(px - gap + t, y - 12 + round(4 * (1 - (2 * t / gap - 1) ** 2)), OXBLOOD[1])
        c.rect(px - 1, y - 14, px + 1, y, BRASS3[1])
        c.frame(px - 2, y - 15, px + 2, y + 1)
        ball(c, px, y - 16, 2, GOLD, 3)


# ---------- small things that sit on a desk or table ----------

def on_lamp(c, x, y):
    c.rect(x + 2, y - 5, x + 3, y, BRASS3[1])
    c.rect(x, y - 7, x + 6, y - 4, GREEN[0])
    c.rect(x, y - 4, x + 6, y - 3, GLOW[0])
    c.frame(x - 1, y - 8, x + 7, y - 3)


def on_papers(c, x, y):
    c.rect(x, y - 4, x + 6, y, PAPER[0])
    c.rect(x + 1, y - 2, x + 5, y - 1, PAPER[2])
    c.frame(x - 1, y - 5, x + 7, y + 1)


def on_phone(c, x, y):
    c.rect(x, y - 3, x + 6, y, EBONY[1])
    c.rect(x - 1, y - 5, x + 7, y - 3, EBONY[0])
    c.frame(x - 2, y - 6, x + 8, y + 1)
    c.put(x + 3, y - 2, GOLD[0])


def on_typewriter(c, x, y):
    c.rect(x, y - 4, x + 9, y, EBONY[1])
    c.rect(x + 1, y - 7, x + 8, y - 4, PAPER[0])
    c.rect(x + 1, y - 2, x + 8, y - 1, STEEL[0])
    c.frame(x - 1, y - 8, x + 10, y + 1)


def on_screen(c, x, y):
    c.rect(x, y - 9, x + 10, y, EBONY[1])
    c.rect(x + 1, y - 8, x + 9, y - 2, TEAL[0])
    c.rect(x + 2, y - 7, x + 5, y - 6, PAPER[0])
    c.frame(x - 1, y - 10, x + 11, y + 1)


def on_globe(c, x, y):
    c.rect(x + 2, y - 2, x + 5, y, BRASS3[2])
    ball(c, x + 3, y - 5, 3, TEAL, 6)
    c.put(x + 2, y - 6, LEAF[0])
    c.put(x + 4, y - 4, LEAF[1])


def on_gold(c, x, y):
    for i, (dx, dy) in enumerate(((0, 0), (5, 0), (2, -3))):
        c.rect(x + dx, y - 3 + dy, x + dx + 5, y + dy, GOLD[1])
        c.rect(x + dx, y - 3 + dy, x + dx + 5, y - 2 + dy, GOLD[0])
        c.frame(x + dx - 1, y - 4 + dy, x + dx + 6, y + dy + 1)


def on_mic(c, x, y):
    c.rect(x + 2, y - 6, x + 3, y, STEEL[2])
    c.rect(x, y - 10, x + 5, y - 5, STEEL[1])
    c.rect(x + 1, y - 9, x + 2, y - 6, STEEL[0])
    c.frame(x - 1, y - 11, x + 6, y - 4)
    c.rect(x, y - 1, x + 5, y, STEEL[2])


def on_tools(c, x, y):
    c.rect(x, y - 2, x + 8, y - 1, STEEL[0])
    c.rect(x + 8, y - 3, x + 11, y, ACCENT[1])
    c.rect(x + 2, y - 6, x + 3, y - 3, WALNUT[0])
    c.rect(x, y - 8, x + 5, y - 6, STEEL[1])


def on_tray(c, x, y):
    c.rect(x, y - 3, x + 9, y, WALNUT[2])
    c.rect(x + 1, y - 5, x + 8, y - 2, PAPER[0])
    c.rect(x + 1, y - 3, x + 8, y - 2, PAPER[2])
    c.frame(x - 1, y - 6, x + 10, y + 1)


def on_plan(c, x, y):
    c.rect(x, y - 6, x + 12, y, (120, 150, 186))
    c.line(x + 2, y - 2, x + 9, y - 5, PAPER[0])
    c.rect(x + 2, y - 5, x + 5, y - 4, PAPER[0])
    c.frame(x - 1, y - 7, x + 13, y + 1)


ON = dict(lamp=on_lamp, papers=on_papers, phone=on_phone, typewriter=on_typewriter, screen=on_screen,
          globe=on_globe, gold=on_gold, mic=on_mic, tools=on_tools, tray=on_tray, plan=on_plan)


def put_on(c, x0, y0, w, d, names):
    """Spread small things along a table top."""
    for i, name in enumerate(names):
        ON[name](c, x0 + 3 + i * (w - 12) // max(1, len(names) - 1 or 1) if len(names) > 1 else x0 + w // 2 - 4,
                 y0 + d - 3)


def desk(c, x, y, w=48, pal=MAHOG, seat=OXBLOOD, on=('lamp', 'papers', 'phone')):
    """The owner's desk: a high-backed chair behind it, facing the door."""
    slab(c, x, y - 26, 16, 0, 18, seat, seat, shadow=False)           # chair back
    c.rect(x - 6, y - 42, x + 6, y - 41, seat[0])
    for bx in (x - 4, x, x + 4):
        c.put(bx, y - 37, seat[2])
        c.put(bx, y - 32, seat[2])
    x0, y0 = slab(c, x, y, w, 15, 10, pal)
    c.rect(x0 + 1, y0 + 1, x0 + w - 1, y0 + 2, GOLD[1])                # inlay line
    for px in (x0 + 2, x0 + w - 13):                                   # drawer pedestals
        c.rect(px, y - 8, px + 11, y - 1, pal[1])
        c.rect(px + 4, y - 6, px + 7, y - 5, GOLD[0])
        c.rect(px + 4, y - 3, px + 7, y - 2, GOLD[0])
    put_on(c, x0, y0, w, 15, on)


# ---------- things against the back wall (their foot is just in front of it) ----------

def shelves(c, x, y, w=36, h=38, pal=WALNUT, kind='books', seed=1):
    """A tall case: books, boxes, files, slots, reels, goods, drawers or empty."""
    x0, y0 = slab(c, x, y, w, 4, h, pal)
    rows = max(2, h // 9)
    for r in range(rows):
        ry0, ry1 = y - h + 2 + r * (h - 3) // rows, y - h + 1 + (r + 1) * (h - 3) // rows
        c.rect(x0 + 2, ry0, x0 + w - 2, ry1, darker(pal[2], .62))
        xx = x0 + 2
        while xx < x0 + w - 3:
            n = noise(xx, r, seed)
            if kind == 'books':
                k = c.k
                X, X1 = xx * k, (x0 + w - 2) * k
                while X < X1:
                    n = noise(X, r, seed)
                    bw = k + int(n * 2 * k)
                    top = ry0 * k + int(noise(X, r, seed + 1) * 3 * k)
                    sp = SPINES[int(noise(X, r, seed + 2) * len(SPINES))]
                    c.fill(X, top, min(X + bw, X1), ry1 * k, sp[1])
                    c.fill(X, top, X + max(1, k // 2), ry1 * k, sp[0])
                    if k > 1 and n > .5:
                        c.fill(X, top + 2 * k, min(X + bw, X1), top + 2 * k + 1, GOLD[0])
                    X += bw
                xx = x0 + w
            elif kind == 'slots':                                       # pigeonholes with letters
                c.rect(xx, ry0, xx + 5, ry1, darker(pal[2], .62))
                if n > .3:
                    c.rect(xx + 1, ry1 - 2 - int(n * 3), xx + 4, ry1, PAPER[0 if n > .6 else 1])
                c.rect(xx + 5, ry0, xx + 6, ry1, pal[1])
                xx += 6
            elif kind in ('boxes', 'drawers'):                          # brass deposit boxes, card drawers
                face = BRASS3 if kind == 'boxes' else OAK
                c.rect(xx, ry0, xx + 6, ry1 - 1, face[1])
                c.rect(xx, ry0, xx + 6, ry0 + 1, face[0])
                c.put(xx + 3, (ry0 + ry1) // 2, OUTLINE if kind == 'boxes' else GOLD[0])
                c.rect(xx + 6, ry0, xx + 7, ry1, pal[2])
                xx += 7
            elif kind == 'reels':
                if n > .25:
                    ball(c, xx + 4, ry1 - 4, 3, STEEL, int(n * 9))
                    c.put(xx + 4, ry1 - 4, EBONY[2])
                xx += 9
            elif kind == 'goods':
                if n > .2:
                    sp, gh = SPINES[int(noise(xx, r, seed + 2) * len(SPINES))], 3 + int(n * 4)
                    c.rect(xx + 1, ry1 - gh, xx + 5, ry1, sp[1])
                    c.rect(xx + 1, ry1 - gh, xx + 2, ry1, sp[0])
                    c.rect(xx + 2, ry1 - gh - 1, xx + 4, ry1 - gh, GOLD[0])
                xx += 7
            elif kind == 'files':
                c.rect(xx, ry0 + 1, xx + 3, ry1, (PAPER, OAK, GREEN)[int(n * 3)][1])
                c.rect(xx + 1, ry0 + 3, xx + 2, ry0 + 5, PAPER[0])
                xx += 4
            else:
                xx += w
        c.rect(x0 + 1, ry1, x0 + w - 1, ry1 + 1, pal[0])
    c.rect(x0, y - 2, x0 + w, y, pal[2])


def sideboard(c, x, y, w=40, pal=WALNUT, on=()):
    x0, y0 = slab(c, x, y, w, 8, 12, pal)
    for dx in range(x0 + 2, x0 + w - 8, 10):
        c.rect(dx, y - 10, dx + 8, y - 2, pal[1])
        c.put(dx + 6, y - 6, GOLD[0])
    put_on(c, x0, y0, w, 8, on)


def filing(c, x, y, n=2, pal=GREEN):
    for i in range(n):
        fx = x + i * 13 - (n - 1) * 6
        slab(c, fx, y, 12, 6, 24, pal)
        for dy in (20, 13, 6):
            c.rect(fx - 4, y - dy, fx + 4, y - dy + 5, pal[1])
            c.rect(fx - 1, y - dy + 2, fx + 2, y - dy + 3, GOLD[0])


def fireplace(c, x, y):
    x0, _ = slab(c, x, y, 54, 6, 30, MARBLE)
    c.rect(x0 + 12, y - 20, x0 + 42, y, EBONY[2])
    c.frame(x0 + 11, y - 21, x0 + 43, y + 1)
    for i, fx in enumerate((x - 8, x - 2, x + 5)):
        ball(c, fx, y - 6 - i % 2 * 2, 4, (GLOW[0], GOLD[1], ACCENT[1]), 30 + i, 6)
    c.rect(x0 + 14, y - 3, x0 + 40, y - 1, WALNUT[2])
    c.rect(x - 22, y - 37, x - 14, y - 36, GOLD[1])                    # things on the mantel
    ball(c, x + 16, y - 39, 3, TEAL, 5)
    for fx in (x - 6, x + 3):
        c.rect(fx, y - 41, fx + 6, y - 36, PAPER[1])
        c.frame(fx - 1, y - 42, fx + 7, y - 35, GOLD[2])


# wall pieces: (x, y) is the centre of the piece on the back wall

def window(c, x, w=30, drape=OXBLOOD):
    y0, y1 = 8, WALL_H - 11
    for yy in range(y0, y1):
        for xx in range(x - w // 2, x + w // 2):
            c.put(xx, yy, mix((176, 214, 220), (255, 240, 200), (xx - x + w / 2 + yy) / (w + 30)))
    c.rect(x - 1, y0, x + 1, y1, CREAM[0])
    c.rect(x - w // 2, (y0 + y1) // 2, x + w // 2, (y0 + y1) // 2 + 1, CREAM[0])
    c.frame(x - w // 2 - 1, y0 - 1, x + w // 2 + 1, y1 + 1)
    for sx in (x - w // 2 - 6, x + w // 2 + 1):
        c.rect(sx, y0 - 2, sx + 5, y1 + 4, drape[1])
        c.rect(sx, y0 - 2, sx + 1, y1 + 4, drape[0])
        c.rect(sx + 3, y0 - 2, sx + 4, y1 + 4, drape[2])
        c.frame(sx - 1, y0 - 3, sx + 6, y1 + 5)
    c.rect(x - w // 2 - 8, y0 - 4, x + w // 2 + 8, y0 - 2, GOLD[1])
    for yy in range(WALL_H + 2, WALL_H + 22):                           # daylight on the floor
        for xx in range(x - w // 2 + (yy - WALL_H) // 2, x + w // 2 + (yy - WALL_H) // 2):
            c.put(xx, yy, mix(c.get(xx, yy), (255, 244, 204), .16))


def painting(c, x, w=22, h=16, seed=1):
    """A gilt-framed landscape: sky, hills, a sun or a lake. No figures."""
    x0, y0 = x - w // 2, 8
    for yy in range(h):
        for xx in range(w):
            hill = h * .55 + 3 * noise(xx // 5, seed, 40) - 2 * abs(xx - w * noise(seed, 1, 41)) / w
            col = mix((250, 214, 160), (150, 190, 204), yy / h) if yy < hill else mix(LEAF[1], GREEN[1], (yy - hill) / h)
            if seed % 2 and yy > h * .75:
                col = TEAL[0]
            c.put(x0 + xx, y0 + yy, col)
    ball(c, x0 + int(w * (.25 + .5 * noise(seed, 2, 42))), y0 + 4, 2, (GLOW[0], GLOW[0], GLOW[1]), 1)
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1, GOLD[1])
    c.frame(x0 - 2, y0 - 2, x0 + w + 2, y0 + h + 2, GOLD[2])
    c.frame(x0 - 3, y0 - 3, x0 + w + 3, y0 + h + 3)


def clock(c, x, y=16, r=6):
    ball(c, x, y, r, BRASS3, 3)
    ball(c, x, y, r - 2, PAPER, 4)
    c.line(x, y, x, y - r + 3, OUTLINE)
    c.line(x, y, x + r - 4, y + 1, OUTLINE)


def sconce(c, x):
    c.rect(x - 1, 14, x + 1, 22, BRASS3[1])
    ball(c, x, 12, 3, GLOW, 2)
    for px, py in disc(x, 13, 9, 8):
        c.put(px, py, mix(c.get(px, py), GLOW[0], .18))


def board(c, x, w=120, kind='quotes'):
    """A big wall board: chalk price lines, a pin map, a chalk diagram or a cork board."""
    x0, y0, y1 = x - w // 2, 7, WALL_H - 11
    face = dict(quotes=(52, 84, 74), map=(214, 200, 160), chalk=(58, 78, 72), cork=(196, 150, 104))[kind]
    c.rect(x0, y0, x0 + w, y1, face)
    for xx in range(x0 + 2, x0 + w - 2):
        t = (xx - x0) / w
        if kind == 'quotes':
            if (xx - x0) % 20 == 0:
                c.rect(xx, y0, xx + 1, y1, mix(face, PAPER[0], .25))
            c.put(xx, y1 - 4 - int(6 * t + 5 * noise(xx // 4, 1, 50)), GLOW[0])
            c.put(xx, y0 + 5 + int(7 * t * noise(xx // 6, 2, 51) + 3 * noise(xx // 3, 3, 52)), ACCENT[0])
            if (xx - x0) % 5 == 2 and noise(xx, 4, 53) > .4:
                c.rect(xx, y1 - 2 - int(noise(xx, 5, 54) * 4), xx + 2, y1 - 1, LEAF[0] if noise(xx, 6, 55) > .4 else ACCENT[0])
        elif kind == 'map':
            for yy in range(y0 + 2, y1 - 2):
                if noise(xx // 9, yy // 5, 60) > .45 and noise(xx // 3, yy // 3, 61) > .2:
                    c.put(xx, yy, LEAF[1] if noise(xx // 4, yy // 4, 62) > .4 else (224, 190, 120))
                else:
                    c.put(xx, yy, (150, 192, 200))
            if noise(xx, 0, 63) > .9:
                py = y0 + 4 + int(noise(xx, 1, 64) * (y1 - y0 - 8))
                c.rect(xx, py, xx + 2, py + 2, ACCENT[0])
        elif kind == 'chalk':
            c.put(xx, y0 + 10 + int(6 * __import__('math').sin(t * 12)), PAPER[0])
            if (xx - x0) % 30 == 14:
                ring = disc(xx, y0 + 9, 5, 5) - disc(xx, y0 + 9, 4, 4)
                for px, py in ring:
                    c.put(px, py, GLOW[0])
        else:
            if (xx - x0) % 13 == 3:
                py = y0 + 3 + int(noise(xx, 2, 70) * 8)
                c.rect(xx, py, xx + 8, py + 7, (PAPER[0], PAPER[1], GLOW[0], (190, 214, 220))[int(noise(xx, 3, 71) * 4)])
                c.put(xx + 4, py, ACCENT[0])
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y1 + 1, WALNUT[0])
    c.frame(x0 - 2, y0 - 2, x0 + w + 2, y1 + 2)


def pegboard(c, x, w=110):
    x0, y0, y1 = x - w // 2, 7, WALL_H - 11
    c.rect(x0, y0, x0 + w, y1, OAK[0])
    for xx in range(x0 + 6, x0 + w - 6, 9):
        k = int(noise(xx, 0, 80) * 4)
        top = y0 + 3 + int(noise(xx, 1, 81) * 4)
        c.rect(xx, top, xx + 2, top + 9 + k, (STEEL[1], WALNUT[1], ACCENT[1], STEEL[2])[k])
        c.rect(xx - 1 - k % 2, top, xx + 3 + k % 2, top + 3, STEEL[0] if k % 2 else STEEL[2])
        c.frame(xx - 2 - k % 2, top - 1, xx + 4 + k % 2, top + 4)
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y1 + 1)


def vault(c, x):
    """A round bank vault door set in the back wall."""
    c.rect(x - 28, 4, x + 28, WALL_H, STEEL[2])
    c.frame(x - 29, 3, x + 29, WALL_H + 1)
    ball(c, x, 21, 16, STEEL, 7)
    ball(c, x, 21, 11, (STEEL[0], STEEL[0], STEEL[1]), 8)
    for i in range(8):
        a = i * 3.14159 / 4
        c.rect(x + round(14 * __import__('math').cos(a)), 21 + round(14 * __import__('math').sin(a)),
               x + round(14 * __import__('math').cos(a)) + 2, 23 + round(14 * __import__('math').sin(a)), GOLD[1])
    c.line(x - 6, 21, x + 6, 21, GOLD[2], 2)
    c.line(x, 15, x, 27, GOLD[2], 2)
    ball(c, x, 21, 3, GOLD, 9)


def flag(c, x, y, pal=ACCENT):
    for px, py in disc(x + 3, y, 5, 2):
        c.dim(px, py, .3)
    c.rect(x - 1, y - 44, x + 1, y, BRASS3[1])
    c.frame(x - 2, y - 45, x + 2, y + 1)
    ball(c, x, y - 46, 2, GOLD, 2)
    for yy in range(y - 42, y - 16):
        for xx in range(x + 2, x + 12 - max(0, yy - y + 22) // 2 * 2):
            c.put(xx, yy, GOLD[1] if xx in (x + 3, x + 9) else pal[0] if xx < x + 5 else pal[1])
    c.rect(x - 4, y - 1, x + 4, y + 1, BRASS3[2])


# ---------- one-of-a-kind pieces ----------

def counter(c, x, y, w=120, pal=WALNUT, grille=False, top=MARBLE):
    x0, y0 = slab(c, x, y, w, 9, 15, top, pal)
    for dx in range(x0 + 3, x0 + w - 10, 14):
        c.rect(dx, y - 12, dx + 11, y - 2, pal[1])
        c.frame(dx, y - 12, dx + 11, y - 2, pal[0])
    if grille:                                                          # brass teller bars
        for dx in range(x0 + 2, x0 + w - 1, 4):
            c.rect(dx, y0 - 14, dx + 1, y0 + 1, GOLD[1])
        c.rect(x0, y0 - 15, x0 + w, y0 - 13, GOLD[0])
        c.frame(x0 - 1, y0 - 16, x0 + w + 1, y0 - 12)
        for gx in range(x0 + 16, x0 + w - 10, 34):
            c.rect(gx, y0 - 7, gx + 12, y0 + 1, top[1])                 # wickets
            c.frame(gx - 1, y0 - 8, gx + 13, y0 + 2, GOLD[2])


def gold_stack(c, x, y):
    slab(c, x, y, 34, 12, 4, WALNUT)
    for row, n in enumerate((5, 4, 3)):
        for i in range(n):
            bx, by = x - n * 3 + i * 6, y - 5 - row * 4
            c.rect(bx, by - 6, bx + 6, by, GOLD[1])
            c.rect(bx, by - 6, bx + 6, by - 4, GOLD[0])
            c.frame(bx - 1, by - 7, bx + 7, by + 1)


def scale(c, x, y):
    slab(c, x, y, 12, 5, 3, BRASS3)
    c.rect(x - 1, y - 24, x + 1, y - 8, BRASS3[1])
    c.rect(x - 10, y - 24, x + 10, y - 23, GOLD[0])
    for sx in (x - 10, x + 9):
        c.line(sx, y - 23, sx, y - 15, GOLD[2])
        c.rect(sx - 3, y - 15, sx + 4, y - 13, GOLD[1])
        c.frame(sx - 4, y - 16, sx + 5, y - 12)


def trunk(c, x, y, pal=WALNUT, w=22):
    x0, y0 = slab(c, x, y, w, 9, 10, pal)
    for bx in (x0 + 4, x0 + w - 6):
        c.rect(bx, y0, bx + 2, y, GOLD[1])
    c.rect(x - 1, y - 9, x + 2, y - 6, GOLD[0])


def parcels(c, x, y):
    for i, (dx, dy, w) in enumerate(((-8, 0, 16), (9, 0, 14), (0, -11, 14))):
        x0, y0 = slab(c, x + dx, y + dy, w, 6, 9, OAK, shadow=dy == 0)
        c.rect(x + dx - 1, y0, x + dx + 1, y + dy, ACCENT[1])
        c.rect(x0, y + dy - 5, x0 + w, y + dy - 4, ACCENT[1])


def tube(c, x, y):
    """Pneumatic message tube rising up the back wall."""
    c.rect(x - 2, 4, x + 2, y - 14, GOLD[1])
    c.rect(x - 2, 4, x - 1, y - 14, GOLD[0])
    c.frame(x - 3, 3, x + 3, y - 13)
    slab(c, x, y, 14, 5, 14, BRASS3)
    c.rect(x - 4, y - 11, x + 4, y - 4, (150, 190, 200))
    c.frame(x - 5, y - 12, x + 5, y - 3)


def switchboard(c, x, y, w=96):
    x0, _ = slab(c, x, y, w, 5, 40, WALNUT)
    c.rect(x0 + 3, y - 37, x0 + w - 3, y - 15, EBONY[1])
    for yy in range(y - 35, y - 17, 3):
        for xx in range(x0 + 5, x0 + w - 5, 3):
            n = noise(xx, yy, 90)
            c.put(xx, yy, GLOW[0] if n > .85 else ACCENT[0] if n > .78 else BRASS3[2])
    c.rect(x0 + 2, y - 14, x0 + w - 2, y - 10, OAK[1])                 # key shelf
    for xx in range(x0 + 6, x0 + w - 6, 7):                             # patch cords
        n = noise(xx, 0, 91)
        col = (ACCENT[1], GOLD[1], TEAL[0], GREEN[0])[int(n * 4)]
        c.line(xx, y - 12, xx + int((n - .5) * 14), y - 17 - int(n * 14), col)
        c.put(xx, y - 12, STEEL[0])
    for xx in range(x0 + 14, x0 + w, 30):                               # operators' stools stay empty
        ball(c, xx, y + 6, 5, OXBLOOD, 4, 3)
        c.rect(xx - 1, y + 9, xx + 1, y + 13, STEEL[2])


def booth(c, x, y):
    x0, _ = slab(c, x, y, 26, 8, 38, MAHOG)
    c.rect(x0 + 4, y - 34, x0 + 22, y - 4, (150, 196, 204))
    c.rect(x0 + 4, y - 34, x0 + 22, y - 31, GLOW[1])
    c.rect(x0 + 12, y - 34, x0 + 14, y - 4, MAHOG[1])
    c.frame(x0 + 3, y - 35, x0 + 23, y - 3)
    c.rect(x0 + 6, y - 24, x0 + 10, y - 16, EBONY[1])
    c.put(x0 + 15, y - 18, GOLD[0])


def camera(c, x, y):
    """A studio television camera on a wheeled pedestal."""
    for px, py in disc(x + 3, y, 11, 4):
        c.dim(px, py, .3)
    for lx in (x - 9, x + 8, x):
        c.line(x, y - 12, lx, y, STEEL[2], 2)
        ball(c, lx, y, 2, EBONY, 3)
    c.rect(x - 2, y - 22, x + 2, y - 10, STEEL[1])
    c.frame(x - 3, y - 23, x + 3, y - 9)
    slab(c, x, y - 20, 22, 8, 12, STEEL, EBONY, shadow=False)
    ball(c, x - 5, y - 26, 4, EBONY, 6)
    ball(c, x - 5, y - 26, 2, (150, 196, 220), 7)
    ball(c, x + 5, y - 27, 2, EBONY, 8)
    c.rect(x + 7, y - 42, x + 13, y - 36, EBONY[1])                    # viewfinder
    c.frame(x + 6, y - 43, x + 14, y - 35)
    c.put(x + 9, y - 30, ACCENT[0])


def light_stand(c, x, y, left=True):
    for px, py in disc(x + 3, y, 7, 2):
        c.dim(px, py, .3)
    for lx in (x - 7, x + 6):
        c.line(x, y - 8, lx, y, EBONY[1])
    c.rect(x - 1, y - 40, x + 1, y - 6, STEEL[1])
    slab(c, x + (3 if left else -3), y - 38, 14, 4, 12, EBONY, shadow=False)
    c.rect(x + (-2 if left else -8), y - 49, x + (8 if left else 2), y - 40, GLOW[0])
    for i in range(1, 9):                                               # a soft cone of light
        for xx in range(-i, i + 1):
            px, py = x + (3 + i if left else -3 - i) + xx, y - 36 + i * 2
            c.put(px, py, mix(c.get(px, py), GLOW[0], .1))


def stage(c, x, y, w=150):
    """The set the camera points at: a curtain, a low stage, a host sofa and a little table."""
    x0 = x - w // 2
    for xx in range(x0, x0 + w):
        col = OXBLOOD[0] if xx % 8 < 2 else OXBLOOD[2] if xx % 8 > 5 else OXBLOOD[1]
        c.rect(xx, 4, xx + 1, WALL_H + 6, col)
    c.rect(x0, 4, x0 + w, 7, GOLD[1])
    c.frame(x0 - 1, 3, x0 + w + 1, WALL_H + 7)
    slab(c, x, y, w + 16, y - WALL_H - 10, 4, OAK)
    rug(c, x, y - 8, w - 30, y - WALL_H - 28, NAVY)
    for i in range(9):                                                  # footlights
        ball(c, x0 + 6 + i * (w - 12) // 8, y - 6, 2, GLOW, i)


def reels(c, x, y):
    slab(c, x, y, 26, 10, 12, EBONY)
    for dx in (-7, 7):
        ball(c, x + dx, y - 26, 6, STEEL, 5)
        ball(c, x + dx, y - 26, 2, EBONY, 6)
    c.rect(x - 4, y - 9, x + 4, y - 4, GLOW[1])


def press(c, x, y):
    """A printing press with a ribbon of paper running through it."""
    x0, _ = slab(c, x, y, 70, 16, 18, STEEL, EBONY)
    for i, dx in enumerate((-22, 0, 22)):
        ball(c, x + dx, y - 28, 8, STEEL, 10 + i, 6)
        ball(c, x + dx, y - 28, 3, EBONY, 13 + i, 2)
    c.rect(x0 - 12, y - 30, x0 + 82, y - 27, PAPER[0])
    c.frame(x0 - 13, y - 31, x0 + 83, y - 26)
    for dx in (x0 + 8, x0 + 30, x0 + 52):
        c.rect(dx, y - 14, dx + 10, y - 4, EBONY[1])
        c.put(dx + 5, y - 9, GOLD[0])
    ball(c, x0 - 16, y - 12, 9, PAPER, 16)                              # the paper roll
    ball(c, x0 - 16, y - 12, 2, WALNUT, 17)
    for i in range(3):                                                  # finished bundles
        slab(c, x0 + 90 + i % 2 * 4, y - i * 5, 14, 8, 4, PAPER, shadow=i == 0)
        c.rect(x0 + 89 + i % 2 * 4, y - i * 5 - 9, x0 + 91 + i % 2 * 4, y - i * 5 - 4, ACCENT[1])


def radio_booth(c, x, y, w=90):
    """A glass-walled radio corner: microphone table, dials, a red lamp."""
    x0, _ = slab(c, x, y, w, 0, 30, GLASS, (GLASS[1], GLASS[1], GLASS[1]), shadow=False)
    for xx in range(x0 + 4, x0 + w, 9):
        c.line(xx, y - 28, xx + 6, y - 2, (224, 240, 240))
    c.rect(x0, y - 30, x0 + w, y - 28, WALNUT[1])
    c.rect(x0, y - 2, x0 + w, y, WALNUT[2])
    for xx in (x0, x0 + w // 2, x0 + w - 2):
        c.rect(xx, y - 30, xx + 2, y, WALNUT[1])
    ball(c, x0 + w - 8, y - 35, 3, (255, 150, 120), 3)


def console(c, x, y, pal=EBONY):
    """A bank of dials and little screens."""
    x0, y0 = slab(c, x, y, 60, 10, 14, pal)
    for i, dx in enumerate(range(x0 + 3, x0 + 54, 11)):
        if i % 2:
            c.rect(dx, y0 + 2, dx + 8, y0 + 8, TEAL[0])
            c.line(dx + 1, y0 + 6, dx + 6, y0 + 3, GLOW[0])
        else:
            ball(c, dx + 4, y0 + 5, 3, STEEL, i)
            c.put(dx + 4, y0 + 4, ACCENT[0])
    for dx in range(x0 + 4, x0 + 56, 5):
        c.put(dx, y - 8, (GLOW[0], ACCENT[0], LEAF[0])[dx % 3])


def teletype(c, x, y):
    slab(c, x, y, 20, 9, 16, STEEL, EBONY)
    c.rect(x - 6, y - 36, x + 6, y - 22, PAPER[0])
    c.rect(x - 4, y - 32, x + 4, y - 31, PAPER[2])
    c.rect(x - 4, y - 28, x + 2, y - 27, PAPER[2])
    c.frame(x - 7, y - 37, x + 7, y - 21)
    for yy in range(y + 2, y + 10, 2):                                  # paper tape curling onto the floor
        c.rect(x + 11 + yy % 4, yy, x + 15 + yy % 4, yy + 1, PAPER[0])


def ticker(c, x, y):
    """A brass ticker under a glass dome, on a marble pedestal."""
    slab(c, x, y, 16, 6, 16, MARBLE)
    ball(c, x, y - 26, 7, GLASS, 3, 8)
    ball(c, x, y - 24, 3, GOLD, 4)
    for i in range(10):
        c.put(x + 7 + i // 2, y - 20 + i, PAPER[0])
        c.put(x + 8 + i // 2, y - 20 + i, PAPER[0])


def post(c, x, y):
    """A trading post: a round counter with a column of quote cards."""
    for px, py in disc(x + 4, y - 4, 30, 14):
        c.dim(px, py, .3)
    ball(c, x, y - 12, 28, WALNUT, 3, 13)
    c.rect(x - 28, y - 12, x + 29, y - 4, WALNUT[2])
    ball(c, x, y - 4, 28, WALNUT, 3, 13)
    ball(c, x, y - 16, 28, MAHOG, 5, 13)
    ball(c, x, y - 16, 20, EBONY, 6, 9)
    slab(c, x, y - 12, 10, 6, 30, BRASS3, shadow=False)
    for yy in range(y - 40, y - 14, 5):
        c.rect(x - 3, yy, x + 3, yy + 3, PAPER[0])
    for a, dx in enumerate((-22, -8, 8, 22)):
        on_phone(c, x + dx - 3, y - 6 - abs(dx) // 6)


def bronze(c, x, y, bull=True):
    slab(c, x, y, 20, 7, 10, MARBLE)
    pal = BRASS3 if bull else ((176, 128, 96), (140, 96, 72), (98, 64, 52))
    ball(c, x, y - 22, 8, pal, 3, 5)
    ball(c, x - 8 if bull else x + 8, y - 26, 4, pal, 4)
    if bull:
        c.line(x - 11, y - 30, x - 9, y - 32, PAPER[0])
        c.line(x - 6, y - 30, x - 7, y - 32, PAPER[0])
    else:
        c.put(x + 6, y - 30, pal[2])
        c.put(x + 10, y - 30, pal[2])


def piano(c, x, y):
    for px, py in disc(x + 4, y - 4, 26, 14):
        c.dim(px, py, .3)
    body = disc(x - 6, y - 20, 18, 12) | block(x - 24, y - 20, x + 24, y - 8) | disc(x + 12, y - 16, 12, 8)
    c.blob(body, EBONY, x, y - 18, 26, 3)
    c.rect(x - 22, y - 8, x + 24, y - 4, PAPER[0])
    for kx in range(x - 21, x + 23, 3):
        c.rect(kx, y - 8, kx + 1, y - 6, EBONY[2])
    c.frame(x - 23, y - 9, x + 25, y - 3)
    c.line(x - 14, y - 26, x + 14, y - 20, GOLD[1])
    slab(c, x, y + 8, 22, 5, 4, OXBLOOD, EBONY)                         # stool


def dining(c, x, y):
    for cx in (x - 22, x, x + 22):
        chair(c, cx, y - 22, GREEN)
    x0, y0 = table(c, x, y, 70, 18, MAHOG)
    c.rect(x0 + 6, y0 + 4, x0 + 64, y0 + 13, CREAM[0])                  # table runner
    for px in (x0 + 12, x0 + 32, x0 + 52):
        ball(c, px + 2, y0 + 8, 3, PAPER, 3, 2)
    ball(c, x, y0 + 5, 3, ACCENT, 8)
    ball(c, x - 2, y0 + 2, 2, LEAF, 9)
    for cx in (x - 22, x, x + 22):
        chair(c, cx, y + 9, GREEN, back=False)


def tv(c, x, y):
    slab(c, x, y, 30, 8, 22, WALNUT)
    c.rect(x - 11, y - 20, x + 5, y - 7, (120, 160, 160))
    c.line(x - 9, y - 10, x - 1, y - 18, (190, 220, 216))
    c.frame(x - 12, y - 21, x + 6, y - 6)
    for dy in (18, 13):
        ball(c, x + 10, y - dy, 2, GOLD, dy)
    c.rect(x - 11, y - 4, x + 12, y - 2, OAK[1])


def toys(c, x, y):
    trunk(c, x, y, (ACCENT[0], ACCENT[1], ACCENT[2]), 24)
    ball(c, x + 20, y - 2, 4, (GLOW[0], GOLD[1], ACCENT[1]), 4)
    for i, col in enumerate((NAVY, GOLD, GREEN)):
        slab(c, x - 20 + i * 3, y + 2 - i * 5, 6, 3, 4, col, shadow=i == 0)


def telescope(c, x, y):
    for px, py in disc(x + 3, y, 12, 4):
        c.dim(px, py, .3)
    for lx in (x - 10, x + 10, x):
        c.line(x, y - 20, lx, y, WALNUT[1], 2)
    ball(c, x, y - 21, 3, GOLD, 2)
    for i in range(34):                                                 # the brass tube, pointing up and right
        px, py = x - 12 + i, y - 12 - i * 2 // 3
        r = 2 if i < 8 else 3 if i < 26 else 4
        c.rect(px, py - r, px + 2, py + r, BRASS3[0] if i % 9 == 0 else BRASS3[1])
        c.put(px, py - r - 1, OUTLINE)
        c.put(px, py + r, OUTLINE)
    c.rect(x + 22, y - 39, x + 24, y - 30, OUTLINE)
    c.rect(x - 14, y - 15, x - 12, y - 9, OUTLINE)


def globe(c, x, y):
    for px, py in disc(x + 3, y, 8, 3):
        c.dim(px, py, .3)
    c.rect(x - 6, y - 3, x + 6, y, WALNUT[1])
    c.frame(x - 7, y - 4, x + 7, y + 1)
    c.rect(x - 1, y - 8, x + 1, y - 3, GOLD[1])
    ball(c, x, y - 16, 9, TEAL, 5)
    for px, py in disc(x, y - 16, 8, 8):
        if noise(px // 3, py // 3, 77) > .58:
            c.put(px, py, LEAF[1] if noise(px, py, 78) > .3 else LEAF[0])
    ring = disc(x, y - 16, 11, 11) - disc(x, y - 16, 10, 10)
    for px, py in ring:
        if px < x - 2 or py > y - 14:
            c.put(px, py, GOLD[1])


def orrery(c, x, y):
    round_table(c, x, y, 13, MAHOG)
    for r in (10, 6):
        for px, py in disc(x, y - 16, r, r * 2 // 3) - disc(x, y - 16, r - 1, r * 2 // 3 - 1):
            c.put(px, py, GOLD[1])
    ball(c, x, y - 17, 3, (GLOW[0], GOLD[0], GOLD[1]), 3)
    ball(c, x + 9, y - 18, 2, TEAL, 4)
    ball(c, x - 5, y - 13, 1, ACCENT, 5)


def case(c, x, y, w=40):
    """A glass display case of specimens on velvet."""
    x0, y0 = slab(c, x, y, w, 12, 12, GLASS, WALNUT)
    c.rect(x0 + 2, y0 + 2, x0 + w - 2, y0 + 10, PLUM[1])
    for i, dx in enumerate(range(x0 + 5, x0 + w - 4, 7)):
        ball(c, dx, y0 + 6, 2, (GOLD, TEAL, PAPER, ACCENT, LEAF)[i % 5], i)
    c.line(x0 + 3, y0 + 9, x0 + 10, y0 + 2, (240, 250, 250))


def ladder(c, x, y):
    for sx in (x - 4, x + 4):
        c.line(sx + 3, y - 40, sx, y, OAK[1], 2)
    for i in range(1, 8):
        c.rect(x - 3 + (40 - i * 5) * 3 // 40, y - i * 5, x + 5 + (40 - i * 5) * 3 // 40, y - i * 5 + 1, OAK[2])


def reading_table(c, x, y):
    chair(c, x - 14, y - 16, GREEN)
    chair(c, x + 14, y - 16, GREEN)
    table(c, x, y, 60, 14, OAK, on=('lamp', 'papers', 'lamp'))


def workbench(c, x, y, w=72, on=('tools', 'plan', 'tools')):
    x0, y0 = table(c, x, y, w, 14, OAK, 9, on)
    c.rect(x0 + w - 12, y0 - 6, x0 + w - 4, y0 + 2, STEEL[1])           # vice
    c.frame(x0 + w - 13, y0 - 7, x0 + w - 3, y0 + 3)
    c.rect(x0 + 6, y - 5, x0 + w - 6, y - 3, OAK[2])


def drafting(c, x, y):
    for lx in (x - 14, x + 13):
        c.line(lx, y - 20, lx, y, STEEL[2], 2)
    c.rect(x - 14, y - 4, x + 15, y - 2, STEEL[2])
    pts = {(px, py) for py in range(y - 34, y - 12) for px in range(x - 20 + (py - y + 34) // 6, x + 20 + (py - y + 34) // 6)}
    c.blob(pts, PAPER, x, y - 24, 22, 3)
    c.line(x - 12, y - 28, x + 10, y - 18, (120, 150, 186))
    c.rect(x - 8, y - 24, x + 4, y - 23, (120, 150, 186))
    c.rect(x - 16, y - 30, x + 20, y - 29, WALNUT[0])                   # T-square


def drill(c, x, y):
    slab(c, x, y, 18, 10, 6, STEEL, EBONY)
    c.rect(x + 3, y - 40, x + 7, y - 12, STEEL[1])
    c.frame(x + 2, y - 41, x + 8, y - 11)
    slab(c, x - 2, y - 30, 16, 6, 8, GREEN, shadow=False)
    c.rect(x - 5, y - 30, x - 3, y - 22, STEEL[0])
    ball(c, x + 9, y - 38, 3, EBONY, 4)


def plinth(c, x, y, kind=0):
    """A lit display stand with one finished product on it."""
    for px, py in disc(x, y - 22, 12, 9):
        c.put(px, py, mix(c.get(px, py), GLOW[0], .22))
    slab(c, x, y, 14, 8, 14, MARBLE)
    if kind == 0:                                                       # a radio
        slab(c, x, y - 18, 10, 3, 6, MAHOG, shadow=False)
        c.put(x - 2, y - 21, GOLD[0])
        c.put(x + 2, y - 21, GOLD[0])
    elif kind == 1:                                                     # a toy rocket
        c.rect(x - 2, y - 30, x + 2, y - 18, ACCENT[1])
        c.frame(x - 3, y - 31, x + 3, y - 17)
        c.rect(x - 1, y - 33, x + 1, y - 30, PAPER[0])
        c.rect(x - 4, y - 21, x + 4, y - 18, NAVY[1])
    else:                                                               # a desk fan
        ball(c, x, y - 25, 5, STEEL, 3)
        ball(c, x, y - 25, 1, TEAL, 4)
        c.rect(x - 2, y - 20, x + 2, y - 18, TEAL[1])


def rolls(c, x, y):
    slab(c, x, y, 24, 8, 16, WALNUT)
    for i, dx in enumerate(range(x - 9, x + 9, 5)):
        c.rect(dx, y - 34 + i % 2 * 3, dx + 4, y - 22, (PAPER[0], (150, 180, 210))[i % 2])
        c.frame(dx - 1, y - 35 + i % 2 * 3, dx + 5, y - 21)


def meeting(c, x, y, n=4):
    """A long polished table with empty chairs down both sides."""
    w = n * 20 + 14
    for i in range(n):
        chair(c, x - w // 2 + 17 + i * 20, y - 24, NAVY)
    x0, y0 = table(c, x, y, w, 20, MAHOG)
    c.rect(x0 + 2, y0 + 2, x0 + w - 2, y0 + 3, GOLD[1])
    for i in range(n):
        on_papers(c, x0 + 14 + i * 20, y0 + 9)
        on_papers(c, x0 + 14 + i * 20, y0 + 18)
    ball(c, x, y0 + 10, 3, LEAF, 4)
    for i in range(n):
        chair(c, x - w // 2 + 17 + i * 20, y + 9, NAVY, back=False)


def side_chair(c, x, y, pal, left):
    """A chair seen from the side, its back to the outside of the table."""
    slab(c, x, y, 11, 7, 4, pal, WALNUT)
    slab(c, x - 6 if left else x + 6, y, 3, 7, 15, pal, pal, shadow=not left)


def council(c, x, y, seats=5, pal=NAVY):
    """One big table: a grand chair at the head, `seats` down each side and one at the foot."""
    w, d, h = 66, seats * 30 + 14, 9
    top = y - h - d
    slab(c, x, top + 3, 20, 0, 24, OXBLOOD, OXBLOOD, shadow=False)     # the head chair, taller than the rest
    c.frame(x - 9, top - 20, x + 9, top + 2, GOLD[1])
    for bx in (x - 5, x, x + 5):
        for by in (top - 15, top - 9, top - 3):
            c.put(bx, by, GOLD[0])
    for fx in (x - 10, x + 10):
        ball(c, fx, top - 23, 2, GOLD, 3)
    x0, y0 = slab(c, x, y, w, d, h, MAHOG)
    c.frame(x0 + 3, y0 + 3, x0 + w - 3, y0 + d - 3, GOLD[1])           # inlay
    rug(c, x, y - h - 12, 18, d - 24, GREEN, border=GOLD)              # leather runner
    for px in (x - 5, x + 4):                                          # the head's place setting
        on_papers(c, px - 3, y0 + 11)
    on_lamp(c, x - 3, y0 + 24)
    for i in range(seats):
        sy = y0 + 34 + i * 30
        on_papers(c, x0 + 6, sy)
        on_papers(c, x0 + w - 13, sy)
        side_chair(c, x0 - 9, sy + 6, pal, True)
        side_chair(c, x0 + w + 8, sy + 6, pal, False)
    for px in (x - 6, x + 6):                                          # flowers along the middle
        ball(c, px, y - h - d // 2, 3, LEAF, px)
    ball(c, x, y - h - d // 2 - 2, 3, ACCENT, 5)
    on_papers(c, x - 3, y - h - 5)
    slab(c, x, y + 12, 12, 6, 4, pal, WALNUT)                          # the foot chair, seen from behind
    slab(c, x, y + 13, 12, 0, 13, pal, pal, shadow=False)


def cubbies(c, x, y):
    """Ten brass message boxes, one for each house in the village."""
    x0, _ = slab(c, x, y, 64, 5, 30, MAHOG)
    for i in range(10):
        bx, by = x0 + 3 + (i % 5) * 12, y - 27 + (i // 5) * 13
        c.rect(bx, by, bx + 10, by + 10, BRASS3[1])
        c.rect(bx, by, bx + 10, by + 1, BRASS3[0])
        c.rect(bx + 2, by + 3, bx + 8, by + 5, OUTLINE)
        if noise(i, 0, 99) > .4:
            c.rect(bx + 3, by + 2, bx + 7, by + 4, PAPER[0])
        c.frame(bx - 1, by - 1, bx + 11, by + 11)


def bell_rope(c, x):
    c.rect(x - 1, 4, x + 1, WALL_H + 8, GOLD[1])
    c.rect(x - 2, WALL_H + 8, x + 2, WALL_H + 16, OXBLOOD[1])
    c.frame(x - 3, WALL_H + 7, x + 3, WALL_H + 17)


THINGS = dict(
    desk=desk, chair=chair, armchair=armchair, sofa=sofa, table=table, round_table=round_table, rug=rug,
    plant=plant, floor_lamp=floor_lamp, rope=rope, shelves=shelves, sideboard=sideboard, filing=filing,
    fireplace=fireplace, flag=flag, counter=counter, gold_stack=gold_stack, scale=scale, trunk=trunk,
    parcels=parcels, tube=tube, switchboard=switchboard, booth=booth, camera=camera, light_stand=light_stand,
    stage=stage, reels=reels, press=press, radio_booth=radio_booth, console=console, teletype=teletype,
    ticker=ticker, post=post, bronze=bronze, piano=piano, dining=dining, tv=tv, toys=toys, telescope=telescope,
    globe=globe, orrery=orrery, case=case, ladder=ladder, reading_table=reading_table, workbench=workbench,
    drafting=drafting, drill=drill, plinth=plinth, rolls=rolls, meeting=meeting, cubbies=cubbies, council=council)
WALLS = dict(window=window, painting=painting, clock=clock, sconce=sconce, board=board, pegboard=pegboard,
             vault=vault, bell_rope=bell_rope)
BACK = WALL_H + 14                                          # foot of a tall thing standing against the back wall


def T(name, x, y, **kw):
    return name, x, y, kw


def Wl(name, x, **kw):
    return name, x, kw


# ---------- the rooms (index = make_maps.HOUSES index; the last is the town hall) ----------

ROOMS = [
    dict(name='post-office', floor=planks(OAK), wall=CREAM, hang=[
        Wl('clock', 256), Wl('window', 60), Wl('window', 452), Wl('sconce', 216), Wl('sconce', 296)], things=[
        T('shelves', 142, BACK, w=96, kind='slots'), T('shelves', 370, BACK, w=96, kind='boxes'),
        T('tube', 256, BACK), T('rug', 256, 366, w=56, d=250, pal=OXBLOOD),
        T('counter', 110, 150, w=150), T('scale', 60, 132), T('parcels', 150, 132),
        T('desk', 256, 140, on=('lamp', 'tray', 'typewriter')),
        T('table', 400, 160, w=80, d=16, on=('tray', 'papers', 'tray')), T('chair', 380, 138), T('chair', 420, 138),
        T('trunk', 60, 250), T('trunk', 92, 262, pal=OXBLOOD), T('parcels', 76, 310),
        T('sofa', 430, 270, pal=OXBLOOD), T('round_table', 430, 300), T('plant', 484, 240),
        T('plant', 28, 356), T('plant', 484, 356), T('floor_lamp', 388, 258)]),
    dict(name='telephone-exchange', floor=carpet(TEAL), wall=CREAM, hang=[
        Wl('board', 400, w=150, kind='map'), Wl('clock', 264), Wl('clock', 284), Wl('clock', 304), Wl('window', 232, w=20)],
        things=[
        T('switchboard', 110, BACK, w=180), T('rug', 256, 366, w=56, d=200, pal=GOLD, border=OXBLOOD),
        T('desk', 256, 170, on=('phone', 'papers', 'phone')),
        T('booth', 440, 150), T('booth', 474, 150), T('sideboard', 400, 86, w=60, on=('phone', 'globe', 'phone')),
        T('sofa', 90, 250, pal=OXBLOOD), T('sofa', 90, 320, pal=OXBLOOD), T('round_table', 90, 284),
        T('table', 420, 280, w=70, d=14, on=('phone', 'phone', 'phone')), T('chair', 400, 262), T('chair', 440, 262),
        T('filing', 470, 340, n=2, pal=OXBLOOD), T('plant', 28, 356), T('plant', 28, 190), T('floor_lamp', 150, 240)]),
    dict(name='television-studio', floor=planks(EBONY), wall=NAVY, trim=EBONY, hang=[
        Wl('sconce', 300), Wl('painting', 340, seed=3), Wl('window', 440)], things=[
        T('stage', 130, 150, w=170), T('sofa', 110, 120, pal=GOLD), T('round_table', 170, 124, r=8),
        T('plant', 60, 110), T('light_stand', 40, 210), T('light_stand', 230, 210, left=False),
        T('camera', 100, 230), T('camera', 170, 250),
        T('shelves', 340, BACK + 2, w=50, kind='reels'), T('reels', 480, 110),
        T('console', 420, 180), T('desk', 420, 250, pal=EBONY, on=('screen', 'mic', 'screen')),
        T('rug', 256, 366, w=56, d=110, pal=OXBLOOD),
        T('armchair', 60, 330, pal=GOLD), T('armchair', 100, 330, pal=GOLD), T('round_table', 140, 334, r=8),
        T('trunk', 470, 330, pal=EBONY), T('trunk', 440, 344, pal=STEEL), T('plant', 484, 290)]),
    dict(name='newspaper-office', floor=parquet(WALNUT), wall=CREAM, hang=[
        Wl('board', 330, w=110, kind='cork'), Wl('clock', 416), Wl('clock', 436), Wl('clock', 456), Wl('window', 484, w=18)],
        things=[
        T('radio_booth', 100, 150, w=150), T('console', 60, 96), T('table', 130, 130, w=44, on=('mic', 'papers')),
        T('chair', 130, 112), T('shelves', 232, BACK, w=40, kind='files'),
        T('press', 110, 250), T('teletype', 30, 320), T('teletype', 62, 320),
        T('desk', 380, 170, w=56, on=('lamp', 'typewriter', 'papers')),
        T('table', 410, 270, w=90, d=16, on=('typewriter', 'papers', 'typewriter')),
        T('chair', 385, 250), T('chair', 435, 250), T('filing', 470, 100, n=3),
        T('rug', 256, 366, w=56, d=150, pal=GREEN),
        T('armchair', 330, 340, pal=GREEN), T('round_table', 365, 344, r=8), T('plant', 484, 356), T('floor_lamp', 300, 330)]),
    dict(name='bank', floor=checker(MARBLE, ((226, 190, 170), (206, 168, 150), (170, 134, 122))), wall=GREEN, hang=[
        Wl('vault', 256), Wl('sconce', 200), Wl('sconce', 312), Wl('painting', 150, w=30, seed=2), Wl('painting', 362, w=30, seed=5)],
        things=[
        T('shelves', 60, BACK, w=84, kind='boxes'), T('shelves', 452, BACK, w=84, kind='boxes'),
        T('gold_stack', 200, 96), T('gold_stack', 312, 96), T('rope', 212, 120, n=5),
        T('counter', 100, 190, w=170, grille=True), T('rug', 256, 366, w=60, d=220, pal=OXBLOOD),
        T('desk', 410, 190, w=56, on=('lamp', 'gold', 'papers')), T('scale', 470, 170),
        T('armchair', 390, 240, pal=GREEN), T('armchair', 430, 240, pal=GREEN),
        T('sofa', 80, 290, pal=GREEN), T('round_table', 80, 320), T('plant', 28, 356), T('plant', 484, 356),
        T('plant', 150, 300), T('trunk', 440, 320, pal=EBONY), T('floor_lamp', 30, 270)]),
    dict(name='stock-exchange', floor=parquet(MAHOG), wall=CREAM, hang=[
        Wl('board', 256, w=300), Wl('clock', 60), Wl('clock', 84), Wl('clock', 428), Wl('clock', 452)], things=[
        T('post', 256, 220), T('ticker', 180, 120), T('ticker', 332, 120),
        T('desk', 256, 110, w=60, on=('phone', 'screen', 'phone')),
        T('bronze', 60, 110), T('bronze', 452, 110, bull=False),
        T('table', 80, 220, w=90, d=14, on=('phone', 'papers', 'phone')), T('chair', 60, 202), T('chair', 100, 202),
        T('table', 432, 220, w=90, d=14, on=('phone', 'papers', 'phone')), T('chair', 412, 202), T('chair', 452, 202),
        T('rug', 256, 366, w=56, d=110, pal=NAVY),
        T('armchair', 70, 330, pal=OXBLOOD), T('armchair', 110, 330, pal=OXBLOOD), T('round_table', 150, 334, r=8),
        T('filing', 450, 330, n=3, pal=NAVY), T('plant', 28, 280), T('plant', 484, 280), T('floor_lamp', 400, 320)]),
    dict(name='family-home', floor=planks(WALNUT), wall=((250, 226, 170), (238, 208, 146), (206, 174, 118)), hang=[
        Wl('window', 80), Wl('window', 432), Wl('painting', 190, seed=4), Wl('painting', 322, seed=7), Wl('sconce', 222), Wl('sconce', 290)],
        things=[
        T('fireplace', 256, BACK), T('shelves', 150, BACK, w=40), T('shelves', 362, BACK, w=40),
        T('rug', 256, 190, w=150, d=90, pal=OXBLOOD),
        T('sofa', 256, 190, pal=CREAM, w=56), T('armchair', 190, 150, pal=GREEN), T('armchair', 322, 150, pal=GREEN),
        T('round_table', 256, 140), T('tv', 60, 120), T('piano', 440, 140),
        T('dining', 110, 290), T('toys', 60, 200),
        T('desk', 420, 280, w=44, pal=WALNUT, seat=GREEN, on=('lamp', 'papers')),
        T('sideboard', 440, 356, w=60, on=('globe',)), T('rug', 256, 366, w=44, d=60, pal=GREEN),
        T('plant', 28, 356), T('plant', 484, 220), T('floor_lamp', 380, 130)]),
    dict(name='spare-house', floor=parquet(OAK), wall=CREAM, hang=[
        Wl('window', 110), Wl('window', 402), Wl('painting', 256, w=34, seed=6), Wl('sconce', 200), Wl('sconce', 312)],
        things=[
        T('shelves', 40, BACK, w=44, kind='none'), T('shelves', 472, BACK, w=44, kind='none'),
        T('sideboard', 256, 74, w=70), T('rug', 256, 240, w=180, d=120, pal=TEAL),
        T('desk', 256, 190, on=('lamp',)),
        T('armchair', 220, 250, pal=CREAM), T('armchair', 292, 250, pal=CREAM),
        T('sofa', 90, 300, pal=CREAM), T('round_table', 90, 330), T('trunk', 440, 300), T('trunk', 440, 322, pal=OXBLOOD),
        T('plant', 28, 356), T('plant', 484, 356), T('plant', 28, 110), T('plant', 484, 110), T('floor_lamp', 150, 290)]),
    dict(name='library', floor=parquet(WALNUT), wall=PLUM, hang=[
        Wl('board', 256, w=90, kind='chalk'), Wl('window', 484, w=18), Wl('sconce', 200), Wl('sconce', 312)], things=[
        T('shelves', 60, BACK, w=100, seed=1), T('shelves', 160, BACK, w=70, seed=2), T('ladder', 120, BACK + 6),
        T('shelves', 352, BACK, w=70, seed=3), T('shelves', 440, BACK, w=70, kind='drawers'),
        T('rug', 256, 250, w=130, d=110, pal=NAVY),
        T('desk', 256, 130, on=('lamp', 'papers', 'globe')),
        T('telescope', 440, 190), T('orrery', 256, 220), T('globe', 180, 200),
        T('reading_table', 90, 200), T('reading_table', 90, 290), T('shelves', 30, 340, w=40, h=30, seed=5),
        T('case', 420, 280), T('case', 420, 330), T('armchair', 330, 320, pal=GREEN), T('floor_lamp', 356, 310),
        T('plant', 484, 356), T('plant', 484, 120)]),
    dict(name='workshop', floor=planks(OAK), wall=CREAM, trim=OAK, hang=[
        Wl('pegboard', 110, w=170), Wl('window', 256)], things=[
        T('workbench', 110, BACK + 12, w=170, on=('tools', 'tools', 'plan', 'tools')),
        T('shelves', 330, BACK, w=40, kind='goods'), T('shelves', 400, BACK, w=70, kind='goods', seed=4),
        T('rolls', 470, BACK + 6), T('drill', 40, 170), T('workbench', 120, 190, w=90),
        T('drafting', 200, 260), T('chair', 200, 280, back=False),
        T('desk', 400, 150, pal=OAK, seat=GREEN, on=('lamp', 'plan', 'tools')),
        T('rug', 256, 366, w=56, d=120, pal=OXBLOOD),
        T('plinth', 340, 250, kind=0), T('plinth', 400, 250, kind=1), T('plinth', 460, 250, kind=2),
        T('rope', 330, 270, n=7), T('parcels', 60, 300), T('trunk', 100, 330, pal=OAK),
        T('armchair', 440, 340, pal=GREEN), T('plant', 484, 356), T('plant', 28, 356)]),
    dict(name='town-hall', floor=checker(MARBLE, ((236, 214, 170), (220, 194, 148), (184, 156, 118))), wall=OXBLOOD, hang=[
        Wl('board', 256, w=110, kind='map'), Wl('window', 110), Wl('window', 402), Wl('sconce', 180), Wl('sconce', 332),
        Wl('bell_rope', 492)], things=[
        T('flag', 176, BACK), T('flag', 322, BACK, pal=NAVY), T('cubbies', 50, BACK), T('filing', 450, BACK, n=3, pal=NAVY),
        T('rug', 256, 344, w=190, d=250, pal=OXBLOOD), T('council', 256, 308),
        T('desk', 420, 180, w=52, on=('lamp', 'papers', 'phone')),
        T('sideboard', 60, 200, w=60, on=('globe', 'papers')), T('armchair', 50, 300, pal=NAVY), T('armchair', 90, 300, pal=NAVY),
        T('round_table', 70, 330, r=9), T('armchair', 430, 300, pal=NAVY), T('armchair', 470, 300, pal=NAVY),
        T('round_table', 450, 330, r=9),
        T('plant', 28, 356), T('plant', 484, 356), T('plant', 28, 130), T('plant', 484, 130),
        T('floor_lamp', 120, 160), T('floor_lamp', 392, 280)]),
]


def room(spec, k=1):
    """Draw one room at detail k and return its image."""
    c = Canvas(k)
    shell(c, spec['floor'], spec['wall'], spec.get('trim', WALNUT))
    for name, x, kw in spec['hang']:
        WALLS[name](c, x, **kw)
    flat = sorted((t for t in spec['things'] if t[0] in ('rug', 'stage')), key=lambda t: t[0] != 'stage')
    for name, x, y, kw in flat + sorted((t for t in spec['things'] if t[0] not in ('rug', 'stage')), key=lambda t: t[2]):
        THINGS[name](c, x, y, **kw)
    return c.im


def main(out_dir, k=1, names=()):
    os.makedirs(out_dir, exist_ok=True)
    for i, spec in enumerate(ROOMS):
        if names and spec['name'] not in names:
            continue
        im = room(spec, k)
        stem = os.path.join(out_dir, f'room-{i:02d}-{spec["name"]}')
        if k == 1:
            im.save(stem + '-draft.png')
        else:
            im.save(stem + '.png')
            im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(stem + '-4k.png', optimize=True)
        print('wrote', spec['name'])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.', int(sys.argv[2]) if len(sys.argv) > 2 else 1, sys.argv[3:])
