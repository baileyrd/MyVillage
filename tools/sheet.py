"""Turn a generated walking sheet into a village sprite sheet the same size and grid as nano.png.

The image model returns a big picture (about 1536 x 2730) on a light background, twelve figures in
4 rows and 3 columns. Each figure is cut out, shrunk so the front standing frame is as tall as
Nano's, and put in a 48 x 64 frame with its feet on the same line (y = 61) and centred across.

    python tools/sheet.py SOURCE.jpg characters/NAME.png [--right-from-left]

--right-from-left rebuilds row 2 (walking right) as a mirror of row 3 (walking left), for a sheet
whose right-walking row came out facing the wrong way.
Needs numpy as well as Pillow.
"""
import argparse
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

FRAME_W, FRAME_H = 48, 64
ROWS, COLS = 4, 3
FEET = 61                     # lowest row of pixels a figure stands on, as in nano.png
HEIGHT = 58                   # nano.png's front standing frame, head (y = 4) to feet (y = 61)
BACKGROUND_GAP = 48           # how far (largest channel difference) a pixel must be from the background
COVER = 0.5                   # share of a block that must be figure for the shrunk pixel to show


@dataclass(frozen=True)
class Box:
    """A figure's bounding box in the source picture."""
    top: int
    left: int
    bottom: int               # exclusive
    right: int                # exclusive


def figure_mask(rgb: np.ndarray) -> np.ndarray:
    """True where a pixel belongs to a figure.

    Background is whatever is close to the border colour AND reachable from the corner, so white
    hair or a cream shirt inside a figure's dark outline is kept.
    """
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    background = np.median(border, axis=0)
    near = np.abs(rgb.astype(int) - background).max(axis=2) <= BACKGROUND_GAP
    padded = Image.fromarray(np.pad(near, 1, constant_values=True).astype(np.uint8) * 255).copy()   # copy: floodfill skips a read-only array view
    ImageDraw.floodfill(padded, (0, 0), 128)
    return (np.array(padded) != 128)[1:-1, 1:-1]


def cell_box(mask: np.ndarray, row: int, col: int) -> Box:
    """Bounding box of the figure in one grid cell, in whole-picture coordinates."""
    h, w = mask.shape
    top, left = row * h // ROWS, col * w // COLS
    cell = mask[top:(row + 1) * h // ROWS, left:(col + 1) * w // COLS]
    ys, xs = np.nonzero(cell)
    if ys.size == 0:
        raise ValueError(f'cell row {row + 1}, column {col + 1} is empty')
    return Box(top + ys.min(), left + xs.min(), top + ys.max() + 1, left + xs.max() + 1)


def shrink(rgb: np.ndarray, mask: np.ndarray, box: Box, scale: float) -> np.ndarray:
    """The figure in box as RGBA art pixels: each output pixel is the median colour of its block."""
    out_h = max(1, round((box.bottom - box.top) / scale))
    out_w = max(1, round((box.right - box.left) / scale))
    art = np.zeros((out_h, out_w, 4), np.uint8)
    for y in range(out_h):
        y0 = box.bottom - round((out_h - y) * scale)
        y1 = box.bottom - round((out_h - y - 1) * scale)
        for x in range(out_w):
            x0 = box.left + round(x * scale)
            x1 = box.left + round((x + 1) * scale)
            inside = mask[y0:y1, x0:x1]
            if inside.size == 0 or inside.mean() < COVER:
                continue
            art[y, x, :3] = np.median(rgb[y0:y1, x0:x1][inside], axis=0)
            art[y, x, 3] = 255
    return art


def place(art: np.ndarray) -> np.ndarray:
    """Put a figure in an empty frame, feet on FEET, centred across."""
    h, w = art.shape[:2]
    if h > FEET + 1 or w > FRAME_W:
        raise ValueError(f'figure {w} x {h} does not fit a {FRAME_W} x {FRAME_H} frame')
    frame = np.zeros((FRAME_H, FRAME_W, 4), np.uint8)
    top, left = FEET + 1 - h, (FRAME_W - w) // 2
    frame[top:top + h, left:left + w] = art
    return frame


def convert(source: Image.Image, right_from_left: bool = False) -> Image.Image:
    """The finished 144 x 256 RGBA sheet for one generated picture."""
    rgb = np.array(source.convert('RGB'))
    mask = figure_mask(rgb)
    boxes = [[cell_box(mask, r, c) for c in range(COLS)] for r in range(ROWS)]
    standing = boxes[0][1]
    scale = (standing.bottom - standing.top) / HEIGHT
    frames = [[place(shrink(rgb, mask, b, scale)) for b in row] for row in boxes]
    if right_from_left:
        frames[1] = [f[:, ::-1] for f in frames[2]]
    sheet = np.concatenate([np.concatenate(row, axis=1) for row in frames], axis=0)
    return Image.fromarray(sheet, 'RGBA')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('source')
    parser.add_argument('target')
    parser.add_argument('--right-from-left', action='store_true')
    args = parser.parse_args()
    convert(Image.open(args.source), args.right_from_left).save(args.target)


if __name__ == '__main__':
    main()
