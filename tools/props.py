#!/usr/bin/env python3
"""Small props for the town, each drawn on its own so it can be placed anywhere.

Usage: python props.py OUT_DIR
Writes OUT_DIR/props-sheet.png (every prop in its own cell, see-through behind)
and OUT_DIR/props/<name>.png (one file per prop). Needs Pillow, with kit.py and
make_maps.py beside it.

A prop is drawn by draw(canvas, x, y) with (x, y) the middle of its foot on the
ground. PROPS maps each name to (width, height, depth, draw); depth is how much
ground it blocks behind its foot. The fountain is centred on its basin instead.
"""
import math
import sys
from pathlib import Path

from PIL import Image

import make_maps as mm
from kit import ACCENT, CREAM, GLOW, GREY, STONE, TH, Canvas
from make_maps import OUTLINE, WOOD, disc, mix, noise

KEY = (255, 0, 255)
LEAF = mm.OAK
DARK_LEAF = mm.DARK_OAK
SOIL = ((132, 96, 76), (106, 74, 60), (80, 54, 48))
CHROME = ((236, 232, 224), (190, 186, 184), (132, 126, 132))
POP = ((238, 122, 92), (212, 84, 66), (158, 58, 52))            # vending machine red
BOTTLE = ((126, 172, 150), (86, 132, 118), (56, 94, 90))


def panel(c, x0, y0, x1, y1, pal):
    """A lit block with a bold two-pixel outline."""
    c.box(x0, y0, x1, y1, pal)
    c.frame(x0 - 1, y0 - 1, x1 + 1, y1 + 1)


def bench(c, x, y):
    """Park bench; (x, y) is the middle of the seat, its feet are 12 below."""
    for lx in (x - 38, x + 32):
        c.box(lx, y - 8, lx + 6, y + 14, GREY)
    for i in range(3):
        c.box(x - 42, y - 30 + i * 8, x + 42, y - 23 + i * 8, WOOD)
    for i in range(2):
        c.box(x - 42, y - 5 + i * 7, x + 42, y + 3 + i * 7, (WOOD[0], WOOD[0], WOOD[1]))
    for lx in (x - 45, x + 39):
        c.box(lx, y - 14, lx + 6, y - 9, GREY)


def lamp(c, x, y):
    c.box(x - 9, y - 8, x + 9, y, GREY)
    c.box(x - 3, y - 86, x + 3, y - 6, GREY)
    c.box(x - 6, y - 60, x + 6, y - 55, GREY)
    c.box(x - 13, y - 116, x + 13, y - 84, GLOW)
    c.rect(x - 7, y - 110, x + 5, y - 90, (255, 252, 226))
    c.rect(x - 1, y - 116, x + 1, y - 84, GREY[1])
    c.box(x - 16, y - 122, x + 16, y - 114, GREY)
    c.box(x - 3, y - 129, x + 3, y - 121, GREY)


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
        elif int(rr * 9 + noise(x // 7, y // 7, 3) * .9) % 3 == 0 and noise(x // 2, y // 2, 4) < .4:
            col = water[0]
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


def barrel(c, x, y):
    for row in range(36):                                   # bulging staves
        yy = y - 2 - row
        half = 11 + round(3 * math.sin(math.pi * (row + 4) / 44))
        for xx in range(x - half, x + half + 1):
            stave = (xx - x + 20) % 6 == 0
            col = WOOD[2] if stave or xx > x + 6 else WOOD[0] if xx < x - 6 else WOOD[1]
            if row in (5, 6, 7, 27, 28, 29):
                col = GREY[0] if xx < x - 4 else GREY[2] if row in (7, 29) else GREY[1]   # iron hoops
            c.put(xx, yy, col)
        for ex in (x - half - 1, x - half - 2, x + half + 1, x + half + 2):
            c.put(ex, yy, OUTLINE)
    c.rect(x - 12, y - 2, x + 13, y, OUTLINE)
    c.ball(x, y - 38, 12, 5, (mix(WOOD[0], CREAM[0], .3), WOOD[0], WOOD[1]))
    c.rect(x - 2, y - 40, x + 2, y - 37, WOOD[2])           # bung


def crate(c, x, y):
    panel(c, x - 17, y - 36, x + 17, y - 24, (mix(WOOD[0], CREAM[0], .35), WOOD[0], WOOD[1]))   # lid
    panel(c, x - 17, y - 24, x + 17, y, WOOD)
    for px in (x - 6, x + 5):
        c.rect(px, y - 35, px + 1, y - 25, WOOD[1])
        c.rect(px, y - 23, px + 1, y - 1, WOOD[2])
    c.line(x - 14, y - 4, x + 12, y - 21, WOOD[2], 2)       # brace
    for px, py in ((x - 15, y - 22), (x + 13, y - 22), (x - 15, y - 4), (x + 13, y - 4)):
        c.rect(px, py, px + 2, py + 2, GREY[0])             # nails


def flower_bed(c, x, y):
    panel(c, x - 46, y - 16, x + 46, y, STONE)              # stone edging
    for bx in range(x - 46, x + 46, 12):
        c.rect(bx, y - 16, bx + 2, y, STONE[2])
    c.rect(x - 42, y - 14, x + 42, y - 4, SOIL[1])
    c.rect(x - 42, y - 14, x + 42, y - 12, SOIL[2])
    for i, bx in enumerate(range(x - 36, x + 40, 12)):
        c.ball(bx, y - 15, 6, 5, LEAF)
        petal = TH['flowers'][i % len(TH['flowers'])]
        for dx, dy in ((0, -3), (-3, 0), (3, 0), (0, 3)):
            c.rect(bx - 1 + dx, y - 21 + dy, bx + 2 + dx, y - 18 + dy, petal)
        c.rect(bx - 1, y - 21, bx + 2, y - 18, (250, 214, 110))


def bush(c, x, y, pal=DARK_LEAF):
    for dx, dy, rx, ry in ((-15, -10, 12, 9), (15, -10, 12, 9), (0, -16, 17, 13)):
        c.ball(x + dx, y + dy, rx, ry, pal)
    c.rect(x - 22, y - 1, x + 23, y + 1, OUTLINE)


def flower_bush(c, x, y):
    bush(c, x, y, LEAF)
    for i, (dx, dy) in enumerate(((-16, -12), (-4, -22), (8, -12), (18, -16), (-8, -8))):
        c.rect(x + dx, y + dy, x + dx + 3, y + dy + 3, TH['flowers'][i % len(TH['flowers'])])


def fence(c, x, y):
    for ry in (y - 16, y - 7):                              # rails
        c.rect(x - 46, ry, x + 46, ry + 3, CREAM[2])
    for px in range(x - 46, x + 42, 8):                     # pickets
        c.box(px, y - 21, px + 5, y, CREAM)
        c.rect(px + 1, y - 23, px + 4, y - 21, CREAM[0])
        c.rect(px + 2, y - 24, px + 3, y - 23, OUTLINE)
    for px in (x - 50, x + 44):                             # posts
        panel(c, px, y - 26, px + 6, y, CREAM)


def vending(c, x, y):
    """A 1950s pop machine: rounded red cabinet, chrome trim, a bottle picture and no writing."""
    c.ball(x, y - 74, 19, 9, POP)                           # domed top
    panel(c, x - 20, y - 74, x + 20, y - 4, POP)
    c.rect(x - 18, y - 76, x + 18, y - 72, POP[1])
    c.rect(x - 18, y - 76, x - 16, y - 72, POP[0])
    c.rect(x - 20, y - 60, x + 20, y - 57, CHROME[0])       # chrome bands
    c.rect(x - 20, y - 57, x + 20, y - 56, CHROME[2])
    c.rect(x - 20, y - 22, x + 20, y - 19, CHROME[0])
    c.rect(x - 20, y - 19, x + 20, y - 18, CHROME[2])
    c.ball(x - 5, y - 40, 11, 12, CREAM)                    # round picture of a bottle
    c.rect(x - 8, y - 42, x - 2, y - 30, BOTTLE[1])
    c.rect(x - 8, y - 42, x - 6, y - 30, BOTTLE[0])
    c.rect(x - 6, y - 50, x - 4, y - 42, BOTTLE[1])
    c.rect(x - 7, y - 52, x - 3, y - 50, CHROME[0])
    c.rect(x - 8, y - 38, x - 2, y - 35, POP[1])
    c.frame(x - 9, y - 43, x - 1, y - 29)
    panel(c, x + 10, y - 50, x + 16, y - 32, CHROME)        # coin box
    c.rect(x + 12, y - 46, x + 14, y - 44, OUTLINE)
    c.rect(x + 11, y - 38, x + 15, y - 35, GREY[2])
    panel(c, x - 14, y - 16, x + 14, y - 8, (GREY[2], (52, 40, 46), (40, 30, 38)))   # where the bottle drops
    c.rect(x - 10, y - 13, x - 4, y - 10, BOTTLE[0])
    for fx in (x - 18, x + 12):
        c.box(fx, y - 4, fx + 6, y, GREY)                   # feet


PROPS = {
    'bench': (92, 46, 24, lambda c, x, y: bench(c, x, y - 12)), 'lamp': (34, 131, 10, lamp),
    'barrel': (32, 46, 12, barrel), 'crate': (38, 38, 14, crate), 'flower_bed': (96, 28, 16, flower_bed),
    'bush': (58, 32, 10, bush), 'flower_bush': (58, 32, 10, flower_bush), 'fence': (102, 28, 6, fence),
    'vending': (44, 86, 14, vending),
}
SHEET = list(PROPS) + ['fountain']


def sprite(name):
    """One prop on its own, cropped, with a see-through background."""
    c = Canvas(360, 320)
    c.rect(0, 0, c.w, c.h, KEY)
    if name == 'fountain':
        fountain(c, 180, 200)
    else:
        PROPS[name][3](c, 180, 300)
    im = c.im.convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][:3] == KEY:
                px[x, y] = (0, 0, 0, 0)
    return im.crop(im.getbbox())


def sheet(sprites, pad=24):
    """Every prop side by side, feet on one line, each in its own cell."""
    width = sum(s.width + pad for s in sprites) + pad
    height = max(s.height for s in sprites) + 2 * pad
    out = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    x = pad
    for s in sprites:
        out.alpha_composite(s, (x, height - pad - s.height))
        x += s.width + pad
    return out


def main(out_dir):
    out = Path(out_dir)
    (out / 'props').mkdir(parents=True, exist_ok=True)
    sprites = []
    for name in SHEET:
        sprites.append(sprite(name))
        sprites[-1].save(out / 'props' / f'{name}.png')
    sheet(sprites).save(out / 'props-sheet.png')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'maps')
