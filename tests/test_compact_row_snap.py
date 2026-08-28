import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.compact_row_snap import (
    compact_partial_row_growth,
    compact_route_snap_delta,
)


class CompactRowSnapTests(unittest.TestCase):
    def test_already_aligned_viewport_needs_no_growth(self):
        # 27px heading/data origin + six 27px rows + 2px border.
        self.assertEqual(compact_route_snap_delta(191, 27, 27), 0)

    def test_partial_bottom_row_grows_only_to_next_full_row(self):
        # 10px of a 27px row are visible, so another 17px finishes it.
        self.assertEqual(compact_route_snap_delta(201, 27, 27), 17)

    def test_actual_partial_visible_row_reports_exact_growth(self):
        # Tree bottom is 202px after border. A row at y=192 with height 27 is
        # visible by 10px and needs 17px more room.
        self.assertEqual(compact_partial_row_growth(204, 192, 27), 17)

    def test_fully_visible_actual_row_needs_no_growth(self):
        self.assertEqual(compact_partial_row_growth(204, 175, 27), 0)

    def test_row_below_viewport_does_not_force_growth(self):
        self.assertEqual(compact_partial_row_growth(204, 202, 27), 0)

    def test_invalid_geometry_fails_safe(self):
        self.assertEqual(compact_route_snap_delta(0, 27, 27), 0)
        self.assertEqual(compact_route_snap_delta(200, -1, 27), 0)
        self.assertEqual(compact_route_snap_delta(200, 27, 0), 0)
        self.assertEqual(compact_partial_row_growth(0, 20, 27), 0)


if __name__ == "__main__":
    unittest.main()
