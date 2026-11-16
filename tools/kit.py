"""Shared drawing kit for the detailed 1950s town: palettes, a canvas with a
movable origin, and the building parts every recipe is made from.

Everything is in map pixels at 48 pixels per tile. Buildings draw in local
coordinates: the front wall spans x 48..432 and y 226..376, the roof top is y 40.
"""
import make_maps as mm
from PIL import Image
from make_maps import OUTLINE, SHADOW, WOOD, darker, disc, mix, noise

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

    def line(self, x0, y0, x1, y1, col, w=1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
            self.rect(x, y, x + w, y + w, col)


def block(x0, y0, x1, y1):
    return {(x, y) for x in range(x0, x1) for y in range(y0, y1)}



BRASS3 = ((250, 216, 120), (226, 180, 84), (176, 132, 60))
MARBLE = ((250, 242, 222), (228, 214, 188), (192, 174, 148))


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


def glass(c, x0, y0, w, h, curtains=False, lit=False):
    for yr in range(h):
        for xr in range(w):
            col = mix((128, 170, 174), (68, 104, 118), int((xr + yr) / (w + h) * 5) / 5)
            if lit:
                col = mix(col, GLOW[1], .55)             # lamplight inside
            s = xr + yr - w // 2
            if -3 <= s < 1 or 6 <= s < 8:
                col = mix(col, mm.GLINT, .55)
            side = min(xr, w - 1 - xr)
            if curtains and yr < h * .82 and side < int(w * .34 - w * .24 * yr / h):
                col = CREAM[2] if side % 4 == 3 else CREAM[0] if side % 4 == 0 else CREAM[1]
            c.put(x0 + xr, y0 + yr, col)


def window(c, x0, y0, w, h, cols=2, rows=2, shutters=None, flowers=False, curtains=False, lit=False):
    c.rect(x0 - 4, y0 - 4, x0 + w + 4, y0 + h + 4, CREAM[1])
    c.rect(x0 - 4, y0 - 4, x0 + w + 4, y0 - 2, CREAM[0])
    c.frame(x0 - 5, y0 - 5, x0 + w + 5, y0 + h + 5)
    glass(c, x0, y0, w, h, curtains, lit)
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



# ---------- walls, roofs and doors shared by every building ----------

def wall_fill(c, style, pal, seed, x0=48, y0=226, x1=432, y1=376):
    """Front wall in siding, brick, stone or stucco, with eave shade and a foundation."""
    L, M, D = pal
    for y in range(y0, y1):
        for x in range(x0, x1):
            ry, n = y - y0, noise(x, y, seed)
            if style == 'siding':
                col = D if ry % 8 == 7 else L if ry % 8 == 0 else mix(M, D, .25) if n < .05 else M
            elif style == 'brick':
                r = ry // 6
                xx = x - x0 + (6 if r % 2 else 0)
                t = noise(xx // 12, r, seed)
                col = mix(L, (255, 244, 220), .45) if ry % 6 == 5 or xx % 12 == 0 else D if t < .28 else L if t > .8 else M
            elif style == 'stone':
                r = ry // 12
                xx = x - x0 + (12 if r % 2 else 0)
                t = noise(xx // 24, r, seed)
                col = (D if ry % 12 == 11 or xx % 24 == 0 else L if ry % 12 == 0 or xx % 24 == 1
                       else mix(M, L, .5) if t > .7 else mix(M, D, .3) if t < .2 else M)
            else:                                           # stucco
                col = L if n > .93 else mix(M, D, .5) if n < .04 else M
            if ry < 9 or (ry < 12 and n < .5) or (x1 - x < 34 and n < (x - x1 + 34) / 40):
                col = darker(col, .78)
            if y1 - y <= 10:                                # foundation blocks
                col = STONE[2] if (x - x0) % 24 == 0 or y1 - y == 10 else STONE[1]
            c.put(x, y, col)
    for bx in ((x0, x1 - 8) if style == 'siding' else ()):  # corner boards
        c.rect(bx, y0 + 6, bx + 8, y1 - 10, CREAM[1])
        c.rect(bx, y0 + 6, bx + 2, y1 - 10, CREAM[0])
        c.rect(bx + 7, y0 + 6, bx + 8, y1 - 10, CREAM[2])
    c.frame2(x0, y0, x1, y1)


def gable_roof(c, pal, seed, chim=None, x0=36, y0=40, x1=444, y1=226):
    """Shingled roof with cream trim and, if chim is given, a brick chimney at that x."""
    shingles(c, x0, y0, x1, y1, pal, seed, ridge=y0 + 44)
    for x, y in (block(chim + 14, y0 + 32, chim + 56, y0 + 100) if chim else ()):
        if x >= chim + 36 or y >= y0 + 86:
            c.dim(x, y)
    c.rect(x0, y0, x0 + 4, y1, CREAM[1])
    c.rect(x1 - 4, y0, x1, y1, CREAM[2])
    c.rect(x0, y1 - 7, x1, y1, CREAM[1])
    c.rect(x0, y1 - 7, x1, y1 - 5, CREAM[0])
    c.rect(x0, y1 - 2, x1, y1, CREAM[2])
    c.frame2(x0, y0, x1, y1)
    if chim:
        bricks(c, chim, y0 + 22, chim + 36, y0 + 86, mm.BRICK)
        c.box(chim - 5, y0 + 13, chim + 41, y0 + 23, STONE)
        for px in (chim + 5, chim + 21):
            c.box(px, y0 + 5, px + 10, y0 + 14, mm.TERRACOTTA[0])


def flat_roof(c, pal, seed, x0=36, y0=40, x1=444, y1=229):
    """Gravel roof behind a parapet."""
    L, M, D = pal
    for y in range(y0, y1):
        for x in range(x0, x1):
            e, n = min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y), noise(x, y, seed)
            if e < 12:
                col = M if (x1 - 1 - x < 12 or y1 - 1 - y < 12) else L
                col = darker(D, .9) if e == 11 else mix(col, (255, 250, 232), .5) if e == 1 else col
            else:
                col = D if n < .1 else L if n > .93 else mix(M, D, .3) if noise(x, y, seed + 1) < .2 else M
                if min(x - x0, y - y0) < 22:
                    col = darker(col, .82)                  # shade just inside the parapet
            c.put(x, y, col)
    c.frame2(x0, y0, x1, y1)


def door(c, pal, style='panel', cx=240, top=288, bottom=370, w=48):
    """Front door with frame and two steps. style: panel, double or open."""
    x0, x1 = cx - w // 2, cx + w // 2
    c.rect(x0 - 6, top - 6, x1 + 6, bottom, CREAM[1])
    c.rect(x0 - 6, top - 6, x0 - 4, bottom, CREAM[0])
    c.frame(x0 - 7, top - 7, x1 + 7, bottom + 1)
    for y in range(top, bottom):
        for x in range(x0, x1):
            c.put(x, y, pal[0] if x - x0 < 3 else pal[2] if x1 - x <= 3 else pal[1])
    c.frame(x0 - 1, top - 1, x1 + 1, bottom + 1)
    if style == 'open':                                     # warm hallway, door swung aside
        c.rect(x0 + 12, top, x1, bottom, (118, 82, 62))
        c.rect(x0 + 12, bottom - 12, x1, bottom, (150, 108, 78))
        c.rect(x0 + 16, top + 6, x1 - 4, top + 30, GLOW[1])
        c.frame(x0 + 11, top - 1, x0 + 13, bottom + 1)
    elif style == 'double':
        for lx in (x0, cx):
            glass(c, lx + 5, top + 8, w // 2 - 10, 34)
            c.frame(lx + 4, top + 7, lx + w // 2 - 4, top + 43)
            c.rect(lx + 5, top + 50, lx + w // 2 - 5, top + 74, mix(pal[1], pal[2], .4))
            c.frame(lx + 4, top + 49, lx + w // 2 - 4, top + 75)
        c.rect(cx - 1, top, cx + 1, bottom, OUTLINE)
        for hx in (cx - 6, cx + 3):
            c.rect(hx, top + 40, hx + 3, top + 54, BRASS)
    else:
        for k in range(3):                                  # three little panes
            glass(c, x0 + 7 + k * 12, top + 8, 10, 13)
            c.frame(x0 + 6 + k * 12, top + 7, x0 + 18 + k * 12, top + 22)
        for px in (x0 + 6, x0 + 26):                        # raised panels
            for py, ph in ((top + 28, 20), (top + 54, 22)):
                c.rect(px, py, px + 16, py + ph, mix(pal[1], pal[2], .35))
                c.rect(px, py, px + 16, py + 1, pal[2])
                c.rect(px, py, px + 1, py + ph, pal[2])
                c.rect(px, py + ph - 1, px + 16, py + ph, pal[0])
                c.rect(px + 15, py, px + 16, py + ph, pal[0])
        c.rect(x1 - 8, top + 48, x1 - 4, top + 52, BRASS)
        c.put(x1 - 8, top + 48, (255, 240, 180))
        c.rect(x1 - 8, top + 52, x1 - 4, top + 53, pal[2])
    steps(c, cx, bottom, (w // 2 + 12, w // 2 + 22))
    c.box(x0 - 22, top + 10, x0 - 14, top + 24, GLOW)       # porch lamp
    c.box(x0 - 23, top + 7, x0 - 13, top + 11, GREY)


def porch(c, pal, seed, cx=240, y0=258):
    """Little shingled roof over the front door."""
    for x, y in block(cx - 40, y0 + 20, cx + 48, y0 + 27):
        c.dim(x, y)
    shingles(c, cx - 44, y0, cx + 44, y0 + 20, pal, seed)
    c.rect(cx - 44, y0 + 16, cx + 44, y0 + 20, CREAM[1])
    c.rect(cx - 44, y0 + 16, cx + 44, y0 + 17, CREAM[0])
    c.frame2(cx - 44, y0, cx + 44, y0 + 20)
    for k in range(10):                                     # brackets
        c.rect(cx - 38 + k, y0 + 21 + k, cx - 35 + k, y0 + 22 + k, OUTLINE)
        c.rect(cx + 35 - k, y0 + 21 + k, cx + 38 - k, y0 + 22 + k, OUTLINE)


def awning(c, x0, x1, y, depth, a, b):
    """Striped shop awning with a scalloped edge."""
    for x, yy in block(x0 + 4, y + depth, x1 + 4, y + depth + 6):
        c.dim(x, yy)
    for x in range(x0, x1):
        k = (x - x0) % 16
        col = a if k < 8 else b
        for d in range(depth - (1 if k % 8 in (0, 7) else 0)):
            c.put(x, y + d, mix(col, (255, 250, 232), .3) if d < 3 else darker(col, .82) if d >= depth - 4 else col)
    c.frame(x0 - 1, y - 1, x1 + 1, y + depth - 1)


def roundel(c, cx, cy, r, bg, icon=None):
    """Round brass-rimmed sign showing a picture, never words."""
    c.blob(disc(cx, cy, r, r), BRASS3, cx, cy, r, 1)
    for p in disc(cx, cy, r - 3, r - 3):
        c.put(*p, bg)
    if icon:
        icon(c, cx, cy)


def pane(c, x0, y0, w, h, inside, frame=CREAM):
    """A framed opening whose contents are drawn by inside(c, x0, y0, w, h)."""
    c.box(x0 - 5, y0 - 5, x0 + w + 5, y0 + h + 5, frame)
    inside(c, x0, y0, w, h)
    c.frame(x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1)
