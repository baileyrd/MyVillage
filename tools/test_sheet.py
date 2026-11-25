"""Checks for sheet.py on a drawn stand-in for a generated sheet: python -m unittest tools/test_sheet.py"""
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import sheet  # noqa: E402

CELL_W, CELL_H, PX = 120, 200, 3          # stand-in cell and art-pixel size


def stand_in(white_inside: bool = True) -> Image.Image:
    """A cream sheet of twelve figures: dark outline, white middle, wider in row 2 to tell it apart."""
    a = np.full((CELL_H * 4, CELL_W * 3, 3), (250, 247, 240), np.uint8)
    for r in range(4):
        for c in range(3):
            w = 30 if r == 1 else 20
            top, left = r * CELL_H + 10, c * CELL_W + 40
            a[top:top + 174, left:left + w * PX // 2] = (40, 20, 20)
            if white_inside:
                a[top + 6:top + 168, left + 6:left + w * PX // 2 - 6] = (255, 255, 255)
    return Image.fromarray(a)


class SheetTest(unittest.TestCase):
    def test_size_and_feet(self) -> None:
        out = np.array(sheet.convert(stand_in()))
        self.assertEqual(out.shape, (256, 144, 4))
        for r in range(4):
            for c in range(3):
                alpha = out[r * 64:(r + 1) * 64, c * 48:(c + 1) * 48, 3]
                ys = np.nonzero(alpha)[0]
                self.assertEqual(ys.max(), sheet.FEET)
                self.assertEqual(ys.max() - ys.min() + 1, sheet.HEIGHT)

    def test_white_inside_outline_is_kept(self) -> None:
        out = np.array(sheet.convert(stand_in()))
        self.assertEqual(out[30, 24, 3], 255)
        self.assertTrue((out[30, 24, :3] > 240).all())

    def test_right_from_left_mirrors_row_three(self) -> None:
        out = np.array(sheet.convert(stand_in(), right_from_left=True))
        for c in range(3):
            cols = slice(c * 48, (c + 1) * 48)
            np.testing.assert_array_equal(out[64:128, cols], out[128:192, cols][:, ::-1])

    def test_empty_cell_is_an_error(self) -> None:
        img = np.array(stand_in())
        img[:CELL_H, :CELL_W] = (250, 247, 240)
        with self.assertRaises(ValueError):
            sheet.convert(Image.fromarray(img))


if __name__ == '__main__':
    unittest.main()
