"""The buildings of the 1950s town, one per AI agent, plus the town hall.

Each house is the 1950s small-town version of its agent's job. BUILDINGS and
YARDS are indexed like make_maps.HOUSES. All signs are pictures, never words.
A building draws in local coordinates (see kit.py); its yard is the three
tiles below the wall, with the door path running down x 192..288.
"""
import math

import make_maps as mm
from kit import (ACCENT, BRASS, BRASS3, CREAM, GLOW, GREY, MARBLE, ROOFS, SIDINGS, STONE, TH, TRIMS, TS,
                 awning, block, bricks, door, flat_roof, gable_roof, glass, pane, porch, roundel, shingles,
                 shrub, steps, wall_fill, window)
from make_maps import OUTLINE, WOOD, darker, disc, mix, noise

TAN_BRICK = ((228, 188, 132), (206, 162, 108), (168, 126, 84))
DARK_BRICK = ((180, 100, 80), (150, 76, 62), (112, 54, 50))
BROWN_BRICK = ((198, 132, 98), (168, 104, 76), (128, 76, 60))
PALE_STONE = ((246, 238, 218), (228, 216, 192), (192, 178, 156))
ROOF_GREY = ((230, 218, 200), (198, 184, 168), (160, 146, 134))
STEEL = ((214, 210, 208), (172, 166, 168), (122, 114, 122))
TIN = ((216, 206, 198), (186, 174, 168), (148, 136, 136))
COPPER = ((170, 206, 178), (118, 166, 142), (80, 124, 110))
BRONZE = ((176, 136, 92), (140, 102, 70), (98, 70, 54))
GREEN = ((150, 176, 112), (112, 142, 86), (78, 104, 64))
SMOKE = ((248, 242, 234), (228, 220, 212), (198, 188, 184))
BOARD = (56, 84, 70)
SPINES = [(198, 84, 62), (226, 180, 84), (112, 142, 86), (104, 150, 170), (150, 118, 128),
          (240, 226, 192), (176, 100, 80), (86, 64, 78)]
RED, MUSTARD, SAGE, TEAL = (206, 70, 56), (228, 182, 92), (150, 176, 112), (104, 150, 170)


# ---------- picture signs ----------

def icon_play(c, x, y):
    for dx in range(-6, 10):
        half = (9 - dx) * 10 // 15
        c.rect(x + dx, y - half, x + dx + 1, y + half + 1, CREAM[0])


def icon_envelope(c, x, y):
    c.rect(x - 11, y - 7, x + 11, y + 7, CREAM[0])
    c.frame(x - 12, y - 8, x + 12, y + 8)
    c.line(x - 11, y - 7, x, y + 1, OUTLINE)
    c.line(x + 10, y - 7, x, y + 1, OUTLINE)


def icon_lens(c, x, y):
    for p in disc(x - 2, y - 2, 8, 8):
        c.put(*p, OUTLINE)
    for p in disc(x - 2, y - 2, 6, 6):
        c.put(*p, (166, 212, 208))
    c.line(x + 4, y + 4, x + 10, y + 10, WOOD[2], 3)


def icon_gear(c, x, y):
    for k in range(8):
        gx, gy = x + round(10 * math.cos(k * math.pi / 4)), y + round(10 * math.sin(k * math.pi / 4))
        c.rect(gx - 2, gy - 2, gx + 3, gy + 3, GREY[2])
    for p in disc(x, y, 8, 8):
        c.put(*p, GREY[1])
    for p in disc(x, y, 3, 3):
        c.put(*p, CREAM[0])


def icon_chart(c, x, y):
    pts = [(-11, 7), (-5, 0), (0, 5), (9, -7)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        c.line(x + ax, y + ay, x + bx, y + by, GREEN[2], 2)
    c.line(x + 4, y - 8, x + 10, y - 8, GREEN[2], 2)
    c.line(x + 10, y - 8, x + 10, y - 2, GREEN[2], 2)


def icon_bolt(c, x, y):
    for ax, ay, bx, by in ((3, -11, -4, 0), (-4, 0, 3, 0), (3, 0, -3, 11)):
        c.line(x + ax, y + ay, x + bx, y + by, (250, 214, 110), 3)


def icon_horn(c, x, y):
    for dx in range(-9, 8):
        half = 2 + (dx + 9) * 7 // 16
        c.rect(x + dx, y - half, x + dx + 1, y + half + 1, ACCENT[1])
    c.rect(x + 8, y - 10, x + 11, y + 11, OUTLINE)
    c.rect(x - 7, y + 3, x - 4, y + 10, OUTLINE)


def heart(c, x, y, col):
    for dx, dy, w in ((-2, -2, 2), (1, -2, 2), (-3, -1, 7), (-2, 0, 5), (-1, 1, 3), (0, 2, 1)):
        c.rect(x + dx, y + dy, x + dx + w, y + dy + 1, col)


# ---------- what shows through a window ----------

def in_poster(kind):
    def inside(c, x0, y0, w, h):
        for yr in range(h):
            band = min(3, yr * 4 // h)
            col = ((250, 206, 120), (240, 150, 90), (206, 90, 80), (110, 70, 96))[band] if kind == 0 else \
                mix((70, 96, 120), (36, 50, 80), yr / h)
            c.rect(x0, y0 + yr, x0 + w, y0 + yr + 1, col)
        cx, cy = x0 + w // 2, y0 + h // 2
        if kind == 0:                                       # sunset
            for p in disc(cx, cy + 6, 10, 10):
                c.put(*p, CREAM[0])
        else:                                               # starry night
            for dx, dy in ((0, 0), (-14, -18), (12, -24), (16, 14), (-16, 20), (4, 26)):
                c.rect(cx + dx - 3, cy + dy, cx + dx + 4, cy + dy + 1, GLOW[0])
                c.rect(cx + dx, cy + dy - 3, cx + dx + 1, cy + dy + 4, GLOW[0])
    return inside


def in_books(c, x0, y0, w, h):
    c.rect(x0, y0, x0 + w, y0 + h, (70, 48, 40))
    for r, sy in enumerate(range(y0, y0 + h - 4, 14)):
        for k, x in enumerate(range(x0 + 1, x0 + w - 2, 3)):
            col = SPINES[int(noise(k, r, 5) * len(SPINES))]
            top = sy + 1 + int(noise(k, r, 6) * 4)
            c.rect(x, top, x + 2, sy + 12, col)
            c.rect(x + 2, top, x + 3, sy + 12, darker(col, .7))
        c.rect(x0, sy + 12, x0 + w, sy + 14, WOOD[0])


def in_vault(c, x0, y0, w, h):
    c.rect(x0, y0, x0 + w, y0 + h, (62, 54, 62))
    cx, cy, r = x0 + w // 2, y0 + h // 2, min(w, h) // 2 - 3
    c.blob(disc(cx, cy, r, r), STEEL, cx, cy, r, 4)
    for p in disc(cx, cy, r - 5, r - 5) - disc(cx, cy, r - 6, r - 6):
        c.put(*p, STEEL[2])
    for k in range(3):
        a = k * math.pi / 3
        c.line(cx - round(12 * math.cos(a)), cy - round(12 * math.sin(a)),
               cx + round(12 * math.cos(a)), cy + round(12 * math.sin(a)), GREY[2], 2)
    c.blob(disc(cx, cy, 4, 4), BRASS3, cx, cy, 4, 5)


def in_goods(c, x0, y0, w, h):
    c.rect(x0, y0, x0 + w, y0 + h, (252, 238, 204))
    for r, sy in enumerate(range(y0 + 2, y0 + h - 10, 20)):
        for k, x in enumerate(range(x0 + 4, x0 + w - 10, 12)):
            col, n = SPINES[int(noise(k, r, 7) * 5)], noise(k, r, 8)
            if n < .35:                                     # bottle
                c.box(x + 2, sy + 4, x + 7, sy + 17, (col, col, darker(col, .7)))
                c.rect(x + 3, sy + 1, x + 6, sy + 5, col)
            else:                                           # boxed product
                c.box(x, sy + 6 + int(n * 4), x + 10, sy + 17, (mix(col, CREAM[0], .4), col, darker(col, .7)))
        c.rect(x0, sy + 17, x0 + w, sy + 19, WOOD[0])


def in_board(c, x0, y0, w, h):
    c.rect(x0, y0, x0 + w, y0 + h, BOARD)
    pts = [(4, h - 12), (14, h - 24), (22, h - 16), (32, h - 34), (40, h - 26), (w - 6, 8)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        c.line(x0 + ax, y0 + ay, x0 + bx, y0 + by, (250, 236, 170), 2)
    for k, (tx, up) in enumerate(((8, True), (22, False), (36, True), (50, True))):
        for d in range(4):
            yy = y0 + h - 5 - d if up else y0 + h - 8 + d
            c.rect(x0 + tx - 3 + d, yy, x0 + tx + 4 - d, yy + 1, (132, 204, 122) if up else (232, 100, 84))


def in_ticker(c, x0, y0, w, h):
    c.rect(x0, y0, x0 + w, y0 + h, (92, 64, 54))
    cx, base = x0 + w // 2, y0 + h - 6
    c.box(cx - 14, base - 6, cx + 14, base, WOOD)
    c.box(cx - 8, base - 20, cx + 8, base - 6, BRASS3)
    for x, y in disc(cx, base - 16, 17, 20) - disc(cx, base - 16, 16, 19):
        if y < base - 6:
            c.put(x, y, (226, 240, 232))                    # glass dome
    tape = [(cx + 8, base - 14), (cx + 16, base - 22), (cx + 20, base - 10), (cx + 24, base - 2)]
    for (ax, ay), (bx, by) in zip(tape, tape[1:]):
        c.line(ax, ay, bx, by, CREAM[0], 2)


def in_press(c, x0, y0, w, h):
    c.rect(x0, y0, x0 + w, y0 + h, (74, 60, 58))
    c.box(x0 + 5, y0 + 22, x0 + w - 12, y0 + h - 4, GREY)
    for rx in (x0 + 15, x0 + 33):
        c.blob(disc(rx, y0 + 18, 8, 8), STEEL, rx, y0 + 18, 8, rx)
    c.rect(x0 + w - 20, y0 + 26, x0 + w - 2, y0 + 44, CREAM[0])
    for k in range(4):
        c.rect(x0 + w - 18, y0 + 29 + k * 4, x0 + w - 5, y0 + 30 + k * 4, GREY[0])
    c.frame(x0 + w - 21, y0 + 25, x0 + w - 1, y0 + 45)


def in_switchboard(c, x0, y0, w, h):
    c.rect(x0, y0, x0 + w, y0 + h, (98, 68, 50))
    for r in range(5):
        for k in range(7):
            n = noise(k, r, 9)
            c.rect(x0 + 5 + k * 7, y0 + 5 + r * 7, x0 + 8 + k * 7, y0 + 8 + r * 7,
                   GLOW[1] if n > .6 else (232, 100, 84) if n > .4 else (58, 40, 36))
    for k, col in enumerate((RED, MUSTARD, CREAM[0], TEAL)):
        c.line(x0 + 8 + k * 13, y0 + h - 3, x0 + 12 + (k * 23) % 40, y0 + 12 + (k * 11) % 24, col)


# ---------- things on a roof ----------

def mast(c, x, base, top, bolt=False):
    """Red-and-cream radio tower with broadcast rings at the top."""
    for y in range(top, base):
        t = (y - top) / (base - top)
        half = 2 + round(8 * t)
        col = ACCENT[1] if ((y - top) // 24) % 2 == 0 else CREAM[0]
        for lx in (x - half, x + half - 1):
            c.rect(lx, y, lx + 2, y + 1, col)
            c.put(lx - 1 if lx < x else lx + 2, y, OUTLINE)
        k = (y - top) % 12
        cross = x - half + round(2 * half * k / 12) if ((y - top) // 12) % 2 == 0 else x + half - round(2 * half * k / 12)
        c.put(cross, y, GREY[2])
    c.box(x - 12, base - 4, x + 12, base, GREY)
    for k, (rx, ry) in enumerate(((9, 4), (16, 7), (23, 10))):
        for px, py in disc(x, top + 2, rx, ry) - disc(x, top + 2, rx - 1, ry - 1):
            if py <= top + 2:
                c.put(px, py, GLOW[1] if k % 2 == 0 else CREAM[0])
    c.blob(disc(x, top, 3, 3), ACCENT, x, top, 3, 2)
    if bolt:
        icon_bolt(c, x + 22, top + 26)


def dome(c, cx, cy, r):
    """Copper observatory dome with a telescope looking out of the slit."""
    c.box(cx - r - 3, cy + r // 2, cx + r + 3, cy + r // 2 + 12, STONE)
    c.blob(disc(cx, cy, r, int(r * .8)), COPPER, cx, cy, r, 6)
    c.rect(cx + 2, cy - int(r * .8) + 3, cx + 14, cy + 6, (52, 48, 60))
    c.frame(cx + 1, cy - int(r * .8) + 2, cx + 15, cy + 7)
    for k in range(7):
        c.line(cx + 8 - k, cy - 8, cx - 20 - k, cy - r - 12, BRASS3[1 if k < 4 else 2])
    for k in (-1, 7):
        c.line(cx + 8 - k, cy - 8, cx - 20 - k, cy - r - 12, OUTLINE)
    c.line(cx - 21, cy - r - 13, cx - 27, cy - r - 12, OUTLINE)


def smoke(c, x, y):
    for dx, dy, rx, ry in ((6, -14, 9, 7), (17, -32, 12, 9), (32, -52, 15, 11)):
        c.blob(disc(x + dx, y + dy, rx, ry), SMOKE, x + dx, y + dy, rx, x)


def smokestack(c, x, base, top):
    bricks(c, x - 13, top, x + 13, base, mm.BRICK)
    c.box(x - 15, top - 4, x + 15, top + 6, DARK_BRICK)


def sawtooth_roof(c, x0=36, y0=40, x1=444, y1=229):
    """Factory roof: three bays, each a strip of north-light glass over ribbed tin."""
    L, M, D = TIN
    bay = (y1 - y0) // 3
    for b in range(3):
        top = y0 + b * bay
        for y in range(top, top + bay):
            for x in range(x0, x1):
                t = (y - top - 16) / (bay - 16)
                col = D if (x - x0) % 8 == 0 else L if t < .25 else M if t < .7 else mix(M, D, .5)
                if x1 - x < 60 and noise(x, y, 3) < (60 - x1 + x) / 90:
                    col = darker(col, .85)
                c.put(x, y, col)
        for gx in range(x0 + 6, x1 - 24, 26):
            glass(c, gx, top + 3, 22, 11)
            c.frame(gx - 1, top + 2, gx + 23, top + 15)
        c.rect(x0, top + bay - 2, x1, top + bay, D)
        c.rect(x0, top, x1, top + 1, OUTLINE)
    c.frame2(x0, y0, x1, y1)


def bell(c, x, y):
    c.box(x - 16, y - 34, x - 12, y, WOOD)
    c.box(x + 12, y - 34, x + 16, y, WOOD)
    c.box(x - 20, y - 40, x + 20, y - 33, ACCENT)
    c.blob(disc(x, y - 18, 9, 10), BRASS3, x, y - 18, 9, 3)
    c.box(x - 11, y - 10, x + 11, y - 6, BRASS3)
    c.rect(x - 1, y - 6, x + 2, y - 2, OUTLINE)


def pigeon_loft(c, x, y):
    c.box(x - 20, y - 20, x + 20, y, CREAM)
    for hx in (x - 12, x, x + 12):
        c.blob(disc(hx, y - 9, 3, 4), ((52, 36, 32),) * 3, hx, y - 9, 3, 1)
    shingles(c, x - 24, y - 30, x + 24, y - 20, mm.BROWN_ROOF, 61)
    c.frame(x - 24, y - 30, x + 24, y - 20)
    for bx in (x - 14, x + 9):                              # pigeons
        c.blob(disc(bx, y - 35, 5, 4), STEEL, bx, y - 35, 5, bx)
        c.blob(disc(bx + 5, y - 39, 3, 3), STEEL, bx + 5, y - 39, 3, bx)
        c.put(bx + 9, y - 39, MUSTARD)


def horn(c, x, y):
    """Rooftop loudspeaker."""
    c.box(x - 2, y - 30, x + 2, y, GREY)
    for dx in range(0, 22):
        half = 3 + dx * 9 // 21
        c.rect(x + dx, y - 34 - half, x + dx + 1, y - 34 + half + 1, STEEL[0] if dx < 16 else STEEL[1])
        c.put(x + dx, y - 35 - half, OUTLINE)
        c.put(x + dx, y - 33 + half, OUTLINE)
    c.rect(x + 22, y - 47, x + 24, y - 21, OUTLINE)
    c.box(x - 6, y - 38, x + 1, y - 30, GREY)


def wire_rack(c, x, y, sides=(-1, 1)):
    """Pole with crossarms and telephone wires fanning away."""
    for arm, half in ((y - 40, 22), (y - 28, 16)):
        for s in sides:
            for k in range(3):
                ix = x + s * (half - k * 6)
                c.line(ix, arm - 3, x + s * 190, arm + 18 + k * 13 + (arm - y + 40), (74, 56, 56))
    c.box(x - 3, y - 48, x + 3, y, WOOD)
    for arm, half in ((y - 40, 22), (y - 28, 16)):
        c.box(x - half - 2, arm, x + half + 2, arm + 4, WOOD)
        for ix in range(x - half, x + half + 1, 6):
            c.rect(ix - 1, arm - 4, ix + 2, arm, TEAL)
            c.put(ix, arm - 5, OUTLINE)


def reel(c, x, y):
    c.blob(disc(x, y, 16, 16), GREY, x, y, 16, 5)
    for k in range(5):
        hx, hy = x + round(9 * math.cos(k * 1.257)), y + round(9 * math.sin(k * 1.257))
        c.blob(disc(hx, hy, 3, 3), ((60, 48, 58),) * 3, hx, hy, 3, k)
    c.blob(disc(x, y, 2, 2), BRASS3, x, y, 2, 1)


def scales(c, x, y):
    c.box(x - 8, y - 4, x + 8, y, BRASS3)
    c.box(x - 2, y - 44, x + 2, y - 3, BRASS3)
    c.box(x - 26, y - 46, x + 26, y - 42, BRASS3)
    for px in (x - 24, x + 24):
        c.line(px, y - 42, px - 7, y - 24, OUTLINE)
        c.line(px, y - 42, px + 7, y - 24, OUTLINE)
        c.box(px - 9, y - 24, px + 10, y - 20, BRASS3)


def vane(c, x, y, robot=False):
    c.rect(x, y - 38, x + 2, y, OUTLINE)
    c.rect(x - 14, y - 30, x + 16, y - 28, OUTLINE)
    for k in range(5):
        c.rect(x + 16 + k, y - 33 + k, x + 17 + k, y - 24 - k, OUTLINE)
    if robot:                                               # little tin robot
        c.box(x - 6, y - 52, x + 8, y - 38, STEEL)
        c.box(x - 4, y - 62, x + 6, y - 52, STEEL)
        c.rect(x - 2, y - 59, x, y - 57, GLOW[1])
        c.rect(x + 2, y - 59, x + 4, y - 57, GLOW[1])
        c.rect(x, y - 67, x + 2, y - 62, OUTLINE)
        c.rect(x - 1, y - 69, x + 3, y - 67, ACCENT[1])
        c.rect(x - 2, y - 48, x + 4, y - 44, ACCENT[1])


def bunting(c, x0, x1, y):
    for k, x in enumerate(range(x0, x1 - 11, 13)):
        sag = round(5 * math.sin((x - x0) / (x1 - x0) * math.pi))
        col = (RED, MUSTARD, CREAM[0], SAGE)[k % 4]
        for d in range(8):
            c.rect(x + d // 2 + 1, y + sag + d, x + 12 - d // 2 - (d % 2), y + sag + d + 1, col)
        c.rect(x, y + sag - 1, x + 13, y + sag, OUTLINE)


# ---------- things standing in a yard: name -> (width, height, depth, draw) ----------

def p_dropbox(c, x, y):
    c.box(x - 12, y - 4, x + 12, y, GREY)
    c.box(x - 10, y - 34, x + 10, y - 3, ACCENT)
    c.blob(disc(x, y - 34, 10, 6), ACCENT, x, y - 34, 10, 3)
    c.rect(x - 7, y - 30, x + 7, y - 27, OUTLINE)
    c.rect(x - 6, y - 22, x + 6, y - 12, CREAM[0])
    c.frame(x - 7, y - 23, x + 7, y - 11)
    icon_envelope_small(c, x, y - 17)


def icon_envelope_small(c, x, y):
    c.line(x - 5, y - 4, x, y, OUTLINE)
    c.line(x + 5, y - 4, x, y, OUTLINE)


def p_bike(c, x, y):
    for wx in (x - 17, x + 17):
        for p in disc(wx, y - 11, 11, 11) - disc(wx, y - 11, 9, 9):
            c.put(*p, OUTLINE)
        c.line(wx - 8, y - 11, wx + 8, y - 11, GREY[0])
        c.line(wx, y - 19, wx, y - 3, GREY[0])
    for ax, ay, bx, by in ((-17, -11, -4, -26), (-4, -26, 12, -26), (12, -26, 17, -11), (-4, -26, 2, -11),
                           (-17, -11, 2, -11)):
        c.line(x + ax, y + ay, x + bx, y + by, ACCENT[1], 2)
    c.rect(x - 9, y - 30, x + 1, y - 27, OUTLINE)
    c.line(x + 12, y - 26, x + 10, y - 34, OUTLINE, 2)
    c.rect(x + 6, y - 36, x + 16, y - 34, OUTLINE)


def p_globe(c, x, y):
    c.box(x - 9, y - 4, x + 9, y, WOOD)
    c.box(x - 2, y - 18, x + 2, y - 3, BRASS3)
    c.blob(disc(x, y - 30, 13, 13), mm.WATER, x, y - 30, 13, 7)
    for dx, dy, rx, ry in ((-4, -4, 5, 4), (5, 3, 4, 5), (-6, 6, 3, 2)):
        for p in disc(x + dx, y - 30 + dy, rx, ry):
            c.put(*p, GREEN[1])
    for p in disc(x, y - 30, 15, 15) - disc(x, y - 30, 14, 14):
        if p[0] > x:
            c.put(*p, BRASS3[2])


def p_weather(c, x, y):
    for lx in (x - 9, x + 7):
        c.box(lx, y - 26, lx + 3, y, WOOD)
    c.box(x - 12, y - 44, x + 12, y - 24, CREAM)
    for k in range(4):
        c.rect(x - 9, y - 40 + k * 4, x + 9, y - 39 + k * 4, CREAM[2])
    c.rect(x, y - 58, x + 1, y - 44, OUTLINE)
    c.rect(x - 9, y - 58, x + 10, y - 57, OUTLINE)
    for dx in (-10, 9):
        c.blob(disc(x + dx, y - 58, 2, 2), ACCENT, x + dx, y - 58, 2, 1)


def crate(c, x0, y0, w, h):
    c.box(x0, y0, x0 + w, y0 + h, WOOD)
    for k in range(6, w - 2, 7):
        c.rect(x0 + k, y0 + 1, x0 + k + 1, y0 + h - 1, WOOD[2])
    c.rect(x0 + 1, y0 + 4, x0 + w - 1, y0 + 6, WOOD[0])
    c.rect(x0 + 1, y0 + h - 6, x0 + w - 1, y0 + h - 4, WOOD[0])


def p_crates(c, x, y):
    crate(c, x - 24, y - 22, 24, 22)
    crate(c, x + 1, y - 20, 22, 20)
    crate(c, x - 12, y - 40, 22, 19)


def p_handtruck(c, x, y):
    for p in disc(x - 8, y - 5, 5, 5):
        c.put(*p, OUTLINE)
    c.put(x - 8, y - 5, GREY[0])
    c.box(x - 12, y - 46, x - 8, y - 4, ACCENT)
    c.box(x - 12, y - 6, x + 12, y - 2, GREY)
    crate(c, x - 7, y - 24, 18, 18)
    c.box(x - 5, y - 38, x + 9, y - 24, (mix(MUSTARD, CREAM[0], .4), MUSTARD, darker(MUSTARD, .7)))


def p_sandbox(c, x, y):
    c.box(x - 30, y - 26, x + 30, y, WOOD)
    for py in range(y - 22, y - 4):
        for px in range(x - 26, x + 26):
            c.put(px, py, (226, 196, 140) if noise(px, py, 2) < .12 else (246, 222, 170))
    c.box(x + 8, y - 20, x + 18, y - 10, ACCENT)
    c.rect(x - 16, y - 14, x - 6, y - 12, TEAL)
    c.rect(x - 8, y - 18, x - 6, y - 12, TEAL)


def p_doghouse(c, x, y):
    c.box(x - 17, y - 24, x + 17, y, WOOD)
    c.blob(disc(x, y - 6, 7, 9), ((52, 36, 32),) * 3, x, y - 6, 7, 1)
    c.rect(x - 8, y - 3, x + 9, y, (52, 36, 32))
    for k in range(13):
        c.rect(x - 21 + k, y - 25 - k, x + 22 - k, y - 24 - k, ACCENT[0] if k % 4 == 0 else ACCENT[1])
        c.put(x - 22 + k, y - 25 - k, OUTLINE)
        c.put(x + 22 - k, y - 25 - k, OUTLINE)
    c.rect(x - 9, y - 38, x + 10, y - 37, OUTLINE)
    c.rect(x - 22, y - 24, x + 23, y - 23, OUTLINE)


def p_laundry(c, x, y):
    for px in (x - 62, x + 58):
        c.box(px, y - 54, px + 4, y, WOOD)
    c.rect(x - 58, y - 50, x + 58, y - 49, OUTLINE)
    for x0, w, h, col in ((-48, 16, 20, CREAM[0]), (-24, 14, 18, RED), (-2, 22, 26, CREAM[0]), (28, 13, 17, TEAL)):
        c.box(x + x0, y - 49, x + x0 + w, y - 49 + h, (mix(col, CREAM[0], .4), col, darker(col, .8)))
        c.rect(x + x0 + 2, y - 51, x + x0 + 4, y - 47, WOOD[2])


def p_fence(c, x, y):
    c.rect(x - 88, y - 16, x + 88, y - 13, CREAM[2])
    c.rect(x - 88, y - 7, x + 88, y - 4, CREAM[2])
    for px in range(x - 88, x + 84, 8):
        c.box(px, y - 21, px + 5, y, CREAM)
        c.rect(px + 1, y - 23, px + 4, y - 21, CREAM[0])
        c.rect(px + 2, y - 24, px + 3, y - 23, OUTLINE)


def statue(horns):
    def draw(c, x, y):
        f = 1 if horns else -1                              # bull faces right, bear faces left
        c.box(x - 15, y - 14, x + 15, y, STONE)
        for lx in (x - 10, x - 4, x + 3, x + 8):
            c.box(lx, y - 22, lx + 4, y - 13, BRONZE)
        c.blob(disc(x, y - 27, 13, 7), BRONZE, x, y - 27, 13, 2)
        c.blob(disc(x + f * 13, y - 31, 6, 6), BRONZE, x + f * 13, y - 31, 6, 3)
        if horns:
            c.line(x + 11, y - 37, x + 8, y - 43, CREAM[0], 2)
            c.line(x + 17, y - 37, x + 20, y - 43, CREAM[0], 2)
            c.line(x - 13, y - 29, x - 17, y - 22, BRONZE[2], 2)
        else:
            for ex in (x - 17, x - 9):
                c.blob(disc(ex, y - 37, 2, 2), BRONZE, ex, y - 37, 2, 1)
    return draw


def p_newsstand(c, x, y):
    c.box(x - 18, y - 36, x + 18, y, WOOD)
    for r in range(3):
        for k in range(3):
            c.box(x - 15 + k * 11, y - 33 + r * 11, x - 6 + k * 11, y - 25 + r * 11, CREAM)
            c.rect(x - 13 + k * 11, y - 30 + r * 11, x - 8 + k * 11, y - 29 + r * 11, GREY[1])
    c.box(x - 20, y - 40, x + 20, y - 35, ACCENT)


def p_booth(c, x, y):
    c.box(x - 15, y - 66, x + 15, y, ACCENT)
    for k in range(3):
        glass(c, x - 10, y - 60 + k * 18, 20, 14)
        c.frame(x - 11, y - 61 + k * 18, x + 11, y - 45 + k * 18)
    c.box(x - 4, y - 40, x + 4, y - 28, ((70, 56, 60),) * 3)
    c.box(x - 17, y - 74, x + 17, y - 65, CREAM)
    c.box(x - 12, y - 78, x + 12, y - 73, ACCENT)


def p_bench(c, x, y):
    for lx in (x - 30, x + 24):
        c.box(lx, y - 8, lx + 6, y, GREY)
    for k in range(3):
        c.box(x - 34, y - 30 + k * 7, x + 34, y - 24 + k * 7, WOOD)
    c.box(x - 34, y - 10, x + 34, y - 4, (WOOD[0], WOOD[0], WOOD[1]))


def p_topiary(c, x, y):
    c.box(x - 10, y - 14, x + 10, y, STONE)
    c.box(x - 2, y - 24, x + 2, y - 13, WOOD)
    c.blob(disc(x, y - 36, 13, 13), mm.DARK_OAK, x, y - 36, 13, x)


def p_spot(c, x, y):
    """Studio searchlight pointing at the sky."""
    c.box(x - 10, y - 5, x + 10, y, GREY)
    c.box(x - 3, y - 18, x + 3, y - 4, GREY)
    c.blob(disc(x, y - 26, 12, 10), STEEL, x, y - 26, 12, 4)
    c.blob(disc(x - 2, y - 28, 7, 6), GLOW, x - 2, y - 28, 7, 5)


PROPS = {
    'dropbox': (26, 42, 12, p_dropbox), 'bike': (58, 38, 10, p_bike), 'globe': (32, 46, 10, p_globe),
    'weather': (28, 60, 10, p_weather), 'crates': (50, 42, 14, p_crates), 'handtruck': (28, 48, 10, p_handtruck),
    'sandbox': (62, 28, 26, p_sandbox), 'doghouse': (48, 40, 16, p_doghouse), 'laundry': (128, 56, 6, p_laundry),
    'fence': (178, 26, 8, p_fence), 'bull': (40, 46, 14, statue(True)), 'bear': (40, 42, 14, statue(False)),
    'newsstand': (42, 42, 12, p_newsstand), 'booth': (36, 80, 14, p_booth), 'bench': (70, 32, 12, p_bench),
    'topiary': (28, 50, 12, p_topiary), 'spot': (26, 38, 10, p_spot),
}
MAILBOX = (164, 376 + 3 * TS - 16)
YARDS = [                                                   # per house: (prop, x, y) with y on the ground
    [('dropbox', 132, 446), ('bike', 362, 452)],                                        # post office
    [('bench', 118, 444), ('booth', 384, 458)],                                         # telephone exchange
    [('spot', 108, 440), ('spot', 372, 440)],                                           # television studio
    [('newsstand', 132, 446), ('bike', 364, 456)],                                      # newspaper office
    [('topiary', 166, 408), ('topiary', 314, 408)],                                     # bank
    [('bull', 152, 414), ('bear', 328, 414)],                                           # stock exchange
    [('sandbox', 104, 462), ('laundry', 368, 432), ('doghouse', 404, 486),
     ('fence', 92, 518), ('fence', 388, 518)],                                          # family home
    [],                                                                                 # spare house
    [('globe', 130, 442), ('weather', 364, 452)],                                       # library
    [('handtruck', 134, 448), ('crates', 366, 446)],                                    # workshop
]


BODY = (34, -80, 426, 474)                                  # x, y, w, h: walls, roof, ordinary rooftop things
REACH = {                                                   # per house: boxes for parts that stick out further
    1: [(460, 60, 34, 66)],                                 # telephone wires
    5: [(460, 108, 126, 76)],                               # telegraph wires
    9: [(104, -100, 48, 20)],                               # top of the smoke
}


def cover(i):
    """Local boxes inside which house i is redrawn over a walker standing behind it."""
    return [BODY] + REACH.get(i, [])


def mailbox(c):
    mx, my = MAILBOX
    c.box(mx - 2, my - 26, mx + 2, my, WOOD)
    c.box(mx - 10, my - 38, mx + 10, my - 25, ((232, 228, 220), (196, 192, 188), (146, 140, 142)))
    c.rect(mx + 10, my - 40, mx + 13, my - 30, ACCENT[1])
    c.frame(mx + 9, my - 41, mx + 14, my - 29)


# ---------- the ten houses ----------

def post_office(c, i):
    wall_fill(c, 'brick', mm.BRICK, 30 + i)
    window(c, 84, 262, 54, 54)
    c.rect(316, 256, 414, 322, BRASS3[2])                   # wall of brass mailbox doors
    c.frame(315, 255, 415, 323)
    for r in range(4):
        for k in range(6):
            bx, by = 318 + k * 16, 258 + r * 16
            c.box(bx, by, bx + 15, by + 15, BRASS3)
            c.rect(bx + 4, by + 3, bx + 11, by + 5, BRASS3[2])
            c.put(bx + 7, by + 10, OUTLINE)
    door(c, TRIMS[0])
    c.box(206, 244, 274, 278, CREAM)
    icon_envelope(c, 240, 261)
    crate(c, 166, 356, 22, 20)                              # parcels and a mail sack on the step
    c.rect(176, 356, 178, 376, RED)
    c.blob(disc(302, 364, 10, 12), TAN_BRICK, 302, 364, 10, 4)
    c.rect(298, 351, 307, 354, WOOD[2])
    gable_roof(c, mm.SLATE, 40 + i, chim=336)
    pigeon_loft(c, 130, 96)
    shrub(c, 78, 372, mm.DARK_OAK)


def phone_exchange(c, i):
    wall_fill(c, 'siding', SIDINGS[3], 30 + i)
    pane(c, 82, 262, 58, 54, in_switchboard)
    window(c, 342, 262, 54, 54, shutters=TRIMS[3], curtains=True)
    door(c, TRIMS[3], 'open')
    roundel(c, 240, 258, 20, CREAM[0], icon_horn)
    bunting(c, 54, 214, 236)
    bunting(c, 266, 426, 236)
    gable_roof(c, ROOFS[3], 40 + i, chim=108)
    wire_rack(c, 300, 92)
    for bx in (78, 402):
        shrub(c, bx, 372, mm.DARK_OAK, CREAM[0])


def tv_studio(c, i):
    for y in range(388, 376 + 3 * TS):                      # red carpet down the path
        for x in range(214, 266):
            edge = x < 217 or x >= 263
            c.put(x, y, BRASS3[1] if edge else ACCENT[2] if noise(x, y, 3) < .15 else ACCENT[1])
    wall_fill(c, 'stucco', CREAM, 30 + i)
    c.rect(48, 344, 432, 350, ACCENT[1])
    pane(c, 84, 256, 54, 76, in_poster(0), BRASS3)
    pane(c, 342, 256, 54, 76, in_poster(1), BRASS3)
    door(c, TRIMS[0], 'double')
    c.rect(222, 370, 258, 388, ACCENT[1])
    for x, y in block(164, 284, 324, 291):                  # marquee and its shadow
        c.dim(x, y)
    c.rect(160, 250, 320, 284, ACCENT[1])
    c.rect(160, 250, 320, 262, ACCENT[0])
    c.frame2(160, 250, 320, 284)
    for bx in range(165, 316, 9):                           # marquee bulbs
        for by in (254, 277):
            c.rect(bx, by, bx + 4, by + 4, GLOW[0])
            c.put(bx + 3, by + 3, GLOW[2])
    c.rect(170, 264, 310, 274, CREAM[0])
    c.frame(169, 263, 311, 275)
    flat_roof(c, ROOF_GREY, 60 + i)
    roundel(c, 240, 222, 27, ACCENT[1], icon_play)
    for k in range(12):                                     # bulbs round the sign
        a = k * math.pi / 6
        bx, by = 240 + round(24 * math.cos(a)), 222 + round(24 * math.sin(a))
        c.rect(bx - 1, by - 1, bx + 2, by + 2, GLOW[0])
    reel(c, 112, 124)
    mast(c, 378, 160, -44)


def newspaper(c, i):
    wall_fill(c, 'brick', TAN_BRICK, 30 + i)
    pane(c, 82, 262, 58, 54, in_press)
    window(c, 342, 262, 54, 54, shutters=TRIMS[2])
    door(c, TRIMS[2])
    roundel(c, 240, 258, 20, (74, 60, 78), icon_bolt)
    for k in range(3):                                      # bundles of papers tied with string
        c.box(294, 366 - k * 9, 322, 376 - k * 9, CREAM)
        c.rect(307, 366 - k * 9, 309, 376 - k * 9, WOOD[2])
    gable_roof(c, mm.BROWN_ROOF, 40 + i, chim=336)
    mast(c, 110, 150, -36, bolt=True)
    horn(c, 256, 120)
    vane(c, 200, 86, robot=True)
    shrub(c, 78, 372, mm.DARK_OAK)


def bank(c, i):
    wall_fill(c, 'stone', PALE_STONE, 30 + i)
    window(c, 84, 272, 54, 48)
    for bx in range(91, 138, 9):                            # window bars
        c.rect(bx, 272, bx + 2, 320, GREY[2])
    pane(c, 342, 266, 54, 58, in_vault)
    for ax in (76, 334):
        awning(c, ax, ax + 70, 248, 15, GREEN[1], CREAM[0])
    for px in (56, 156, 312, 412):                          # pilasters
        c.box(px, 238, px + 12, 366, MARBLE)
        c.box(px - 3, 234, px + 15, 240, MARBLE)
        c.box(px - 3, 360, px + 15, 366, MARBLE)
    door(c, BRASS3, 'double')
    c.blob(disc(240, 256, 21, 21), BRASS3, 240, 256, 21, 8)  # big gold coin
    for p in disc(240, 256, 16, 16) - disc(240, 256, 15, 15):
        c.put(*p, BRASS3[2])
    c.line(233, 248, 238, 243, (255, 248, 210), 2)
    c.box(288, 324, 310, 336, BRASS3)                       # night-deposit slot
    c.rect(291, 329, 307, 331, OUTLINE)
    flat_roof(c, ((242, 234, 216), (216, 206, 188), (178, 166, 152)), 60 + i)
    c.box(36, 222, 444, 232, MARBLE)
    for dx in range(42, 440, 12):
        c.rect(dx, 228, dx + 6, 231, MARBLE[2])
    scales(c, 240, 150)


def stock_exchange(c, i):
    wall_fill(c, 'brick', DARK_BRICK, 30 + i)
    for k in range(0, 126, 24):                             # stone corners
        for qx in (48, 414):
            c.box(qx, 238 + k, qx + 18, 250 + k, PALE_STONE)
    pane(c, 82, 262, 58, 56, in_board)
    pane(c, 340, 262, 58, 56, in_ticker)
    awning(c, 74, 148, 242, 14, GREEN[1], CREAM[0])
    awning(c, 332, 406, 242, 14, ACCENT[1], CREAM[0])
    door(c, TRIMS[1])
    roundel(c, 240, 258, 20, CREAM[0], icon_chart)
    flat_roof(c, ROOF_GREY, 60 + i)
    bell(c, 240, 110)
    wire_rack(c, 392, 150, sides=(1,))


def family_home(c, i):
    wall_fill(c, 'siding', SIDINGS[1], 30 + i)
    for wx in (84, 342):
        window(c, wx, 262, 54, 54, shutters=TRIMS[0], flowers=True, curtains=True, lit=True)
        for sx in (wx - 13, wx + 67):
            heart(c, sx, 288, CREAM[0])
    door(c, TRIMS[0])
    for p in disc(240, 322, 8, 8) - disc(240, 322, 4, 4):   # wreath
        c.put(*p, GREEN[1] if noise(p[0], p[1], 2) > .3 else GREEN[2])
    c.rect(238, 312, 243, 316, RED)
    porch(c, ROOFS[0], 50 + i)
    gable_roof(c, ROOFS[0], 40 + i, chim=336)
    for bx in (78, 402):
        shrub(c, bx, 372, mm.DARK_OAK, (244, 160, 170))


def spare_house(c, i):
    wall_fill(c, 'siding', SIDINGS[0], 30 + i)
    for wx in (84, 342):
        window(c, wx, 262, 54, 54, shutters=TRIMS[2])
    door(c, TRIMS[2])
    porch(c, mm.BROWN_ROOF, 50 + i)
    gable_roof(c, mm.BROWN_ROOF, 40 + i, chim=108)
    for bx in (78, 402):
        shrub(c, bx, 372, mm.DARK_OAK)


def library(c, i):
    wall_fill(c, 'brick', BROWN_BRICK, 30 + i)
    for wx in (82, 340):                                    # tall arched windows full of books
        pane(c, wx, 250, 58, 86, in_books)
        for k in range(7):
            c.rect(wx - 1, 249 + k, wx + 7 - k, 250 + k, CREAM[1])
            c.rect(wx + 51 + k, 249 + k, wx + 59, 250 + k, CREAM[1])
            c.put(wx + 7 - k, 249 + k, OUTLINE)
            c.put(wx + 50 + k, 249 + k, OUTLINE)
    door(c, TRIMS[2])
    roundel(c, 240, 258, 20, CREAM[0], icon_lens)
    for k, col in enumerate((RED, TEAL, MUSTARD, SAGE, (150, 118, 128))):   # stacks of books
        c.box(166 + (k % 2) * 2, 370 - k * 6, 192 + (k % 2) * 2, 376 - k * 6, (col, col, darker(col, .7)))
    for k, col in enumerate((TEAL, RED, MUSTARD)):
        c.box(292, 370 - k * 6, 316, 376 - k * 6, (col, col, darker(col, .7)))
    gable_roof(c, mm.SLATE, 40 + i, chim=108)
    dome(c, 336, 128, 46)
    vane(c, 196, 86)


def workshop(c, i):
    wall_fill(c, 'brick', mm.BRICK, 30 + i)
    pane(c, 66, 264, 116, 62, in_goods)
    awning(c, 58, 190, 244, 16, (240, 160, 80), CREAM[0])
    for y in range(272, 366):                               # roller loading door
        c.rect(318, y, 414, y + 1, STEEL[2] if y % 6 == 5 else STEEL[0] if y % 6 == 0 else STEEL[1])
    c.frame2(318, 272, 414, 367)
    c.box(312, 366, 420, 377, STONE)
    door(c, TRIMS[2])
    roundel(c, 240, 258, 20, CREAM[0], icon_gear)
    sawtooth_roof(c)
    smokestack(c, 96, 150, -30)


BUILDINGS = [post_office, phone_exchange, tv_studio, newspaper, bank, stock_exchange,
             family_home, spare_house, library, workshop]


def house(c, i):
    """Draw house i with its mailbox and everything standing in its yard."""
    BUILDINGS[i](c, i)
    mailbox(c)
    for name, x, y in sorted(YARDS[i], key=lambda p: p[2]):
        PROPS[name][3](c, x, y)


def house_shadow(c, i):
    c.cast({p for p in block(60, 120, 458, 394) if p[0] >= 432 or p[1] >= 376})
    c.cast(disc(MAILBOX[0] + 6, MAILBOX[1] + 1, 10, 3))
    for name, x, y in YARDS[i]:
        c.cast(disc(x + 6, y, PROPS[name][0] // 2, 4))


# ---------- town hall (local origin: top-left of its 672 x 432 footprint) ----------

HALL_FLAG = (132, 432 + 126)                                # flagpole foot on the lawn
FLAG = (4, -198, 66, 39)                                    # the cloth, from the pole's foot: x, y, w, h

# Where the page animates things, in each building's local pixels (index = house).
CHIMNEYS = {0: (354, 42), 1: (126, 42), 3: (354, 42), 6: (354, 42), 7: (126, 42), 8: (126, 42), 9: (96, -36)}
BULBS = {2: [(bx, by, 4) for by in (254, 277) for bx in range(165, 316, 9)]}                 # the studio marquee
LIGHTS = {1: [(87 + k * 7, 267 + r * 7, 3) for r in range(5) for k in range(7)]}            # the switchboard
BLINK = {5: [(82 + 52, 262 + 8)]}                                                           # end of the price line


def hall(c):
    wd, ht, rh, cx = 672, 432, 228, 336
    wall_fill(c, 'stucco', CREAM, 77, 0, rh, wd, ht)
    c.rect(0, rh + 16, wd, rh + 21, ACCENT[1])
    c.rect(0, rh + 21, wd, rh + 22, ACCENT[2])
    for wx in (42, 150, 462, 570):
        window(c, wx, rh + 46, 60, 84, cols=2, rows=3)
    bunting(c, 30, 236, rh + 26)
    bunting(c, 436, 642, rh + 26)
    c.box(222, rh + 70, 270, rh + 124, WOOD)                # notice board with pinned papers
    c.rect(226, rh + 74, 266, rh + 120, (204, 160, 112))
    for px, py, w, h in ((229, 78, 14, 18), (247, 80, 16, 12), (231, 100, 18, 14), (252, 96, 11, 20)):
        c.rect(px, rh + py, px + w, rh + py + h, CREAM[0])
        c.frame(px - 1, rh + py - 1, px + w + 1, rh + py + h + 1)
        c.rect(px + w // 2, rh + py, px + w // 2 + 2, rh + py + 2, RED)

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

    for x, y in block(cx - 96, rh + 48, cx + 104, rh + 58):  # balcony over the entrance
        c.dim(x, y)
    c.rect(cx - 100, rh + 26, cx + 100, rh + 48, ACCENT[1])
    c.rect(cx - 100, rh + 26, cx + 100, rh + 38, ACCENT[0])
    c.rect(cx - 100, rh + 45, cx + 100, rh + 48, ACCENT[2])
    c.frame2(cx - 100, rh + 26, cx + 100, rh + 48)
    for bx in range(cx - 96, cx + 94, 8):                   # balusters
        c.box(bx, rh + 9, bx + 4, rh + 26, MARBLE)
    c.box(cx - 100, rh + 5, cx + 100, rh + 11, MARBLE)
    for px in (cx - 96, cx - 70, cx + 60, cx + 86):         # columns
        c.box(px, rh + 49, px + 10, ht + 1, MARBLE)
        c.box(px - 2, rh + 49, px + 12, rh + 54, MARBLE)
        c.box(px - 2, ht - 5, px + 12, ht + 1, MARBLE)
    steps(c, cx, ht, (66, 78, 90))
    for bx in (cx - 132, cx + 132):                         # planters
        c.box(bx - 17, ht - 8, bx + 17, ht + 12, mm.TERRACOTTA[0])
        shrub(c, bx, ht - 14, mm.OAK, (244, 160, 170))

    flat_roof(c, TH['hall_roof'][1], 78, -12, 0, wd + 12, rh + 3)
    for x, y in block(306, 76, 318, 162) | block(156, 150, 318, 162):
        c.dim(x, y)
    c.rect(150, 70, 306, 150, CREAM[1])                     # skylight
    for k in range(3):
        for j in range(2):
            glass(c, 156 + k * 50, 76 + j * 37, 44, 31)
            c.frame(155 + k * 50, 75 + j * 37, 201 + k * 50, 108 + j * 37)
    c.frame2(150, 70, 306, 150)
    for vx, vy, vw, vh in ((478, 60, 50, 42), (552, 112, 62, 50)):   # roof vents
        for x, y in block(vx + vw, vy + 8, vx + vw + 10, vy + vh + 10) | block(vx + 8, vy + vh, vx + vw + 10, vy + vh + 10):
            c.dim(x, y)
        c.box(vx, vy, vx + vw, vy + vh, GREY)
        c.rect(vx + 2, vy + 2, vx + vw - 2, vy + 10, GREY[0])
        for yy in range(vy + 16, vy + vh - 4, 5):
            c.rect(vx + 6, yy, vx + vw - 6, yy + 2, GREY[2])

    for x, y in block(cx + 58, rh - 60, cx + 74, rh + 3):   # clock tower over the entrance
        c.dim(x, y)
    wall_fill(c, 'stucco', CREAM, 79, cx - 58, rh - 76, cx + 58, rh + 3)
    c.box(cx - 62, rh - 82, cx + 62, rh - 74, MARBLE)
    c.blob(disc(cx, rh - 36, 27, 27), MARBLE, cx, rh - 36, 60, 5)
    for k in range(12):
        a = k * math.pi / 6
        c.rect(cx + round(22 * math.sin(a)) - 1, rh - 36 - round(22 * math.cos(a)) - 1,
               cx + round(22 * math.sin(a)) + 1, rh - 36 - round(22 * math.cos(a)) + 1, OUTLINE)
    c.line(cx, rh - 37, cx, rh - 54, OUTLINE, 2)
    c.line(cx, rh - 37, cx + 12, rh - 30, OUTLINE, 2)
    for px in (cx - 24, cx + 20):                           # bell cupola
        c.box(px, rh - 122, px + 4, rh - 81, MARBLE)
    c.blob(disc(cx, rh - 102, 10, 11), BRASS3, cx, rh - 102, 10, 3)
    c.box(cx - 12, rh - 93, cx + 12, rh - 89, BRASS3)
    for k in range(26):
        half = 4 + k * 30 // 25
        for x in range(cx - half, cx + half + 1):
            edge = abs(x - cx) == half or k == 25
            c.put(x, rh - 148 + k, OUTLINE if edge else ACCENT[0] if x < cx - half // 3 else
                  ACCENT[1] if x < cx + half // 3 else ACCENT[2])

    px, py = HALL_FLAG                                      # tall flagpole on the lawn
    c.box(px - 9, py - 8, px + 9, py, STONE)
    c.box(px - 3, py - 202, px + 3, py - 6, GREY)
    c.blob(disc(px, py - 205, 4, 4), BRASS3, px, py - 205, 4, 1)
    # The cloth itself is drawn by the page, waving: see FLAG and index.html.


def hall_shadow(c):
    c.cast({p for p in block(30, 90, 708, 464) if p[0] >= 672 or p[1] >= 432})
    c.cast(disc(HALL_FLAG[0] + 8, HALL_FLAG[1], 14, 4))
