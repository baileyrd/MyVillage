"""Enlarge pixel art four times with smooth corners and diagonals, and nothing blurred.

Every art pixel becomes a 4 x 4 block; where two neighbours of the same colour meet at a corner
the corner is filled in (the Scale2x rule, applied twice). Straight edges and flat colour stay
exactly as they were, and no new colours appear, so the result sits seamlessly on the original.
Needs numpy as well as Pillow: the same job in plain Python takes minutes per town.
"""
import numpy as np
from PIL import Image

K = 4                                                       # how many times larger smooth4x makes a picture


def _twice(p: np.ndarray) -> np.ndarray:
    """Scale2x on a grid of colour numbers."""
    edge = np.pad(p, 1, mode='edge')
    up, down, left, right = edge[:-2, 1:-1], edge[2:, 1:-1], edge[1:-1, :-2], edge[1:-1, 2:]
    out = np.repeat(np.repeat(p, 2, 0), 2, 1)
    out[0::2, 0::2] = np.where((left == up) & (left != down) & (up != right), up, p)
    out[0::2, 1::2] = np.where((up == right) & (up != left) & (right != down), right, p)
    out[1::2, 0::2] = np.where((down == left) & (down != right) & (left != up), left, p)
    out[1::2, 1::2] = np.where((right == down) & (right != up) & (down != left), down, p)
    return out


def smooth4x(im: Image.Image) -> Image.Image:
    """Return im (any mode) four times larger as RGBA, with see-through pixels kept see-through."""
    rgba = np.array(im.convert('RGBA'))
    rgba[rgba[..., 3] == 0] = 0                             # every see-through pixel is the same "colour"
    big = _twice(_twice(rgba.view(np.uint32)[..., 0]))
    return Image.fromarray(big.view(np.uint8).reshape(*big.shape, 4), 'RGBA')
