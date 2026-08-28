import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_scrollbar import DashboardScrollbar, scrollbar_thumb_geometry


class DashboardScrollbarGeometryTests(unittest.TestCase):
    def test_full_content_uses_full_track(self):
        top, bottom = scrollbar_thumb_geometry(120, 0.0, 1.0, 1.0)
        self.assertEqual(top, 2)
        self.assertEqual(bottom, 118)

    def test_thumb_moves_down_with_scroll_position(self):
        top_start, bottom_start = scrollbar_thumb_geometry(200, 0.0, 0.25, 1.0)
        top_middle, bottom_middle = scrollbar_thumb_geometry(200, 0.5, 0.75, 1.0)
        self.assertGreater(top_middle, top_start)
        self.assertGreater(bottom_middle, bottom_start)
        self.assertEqual(bottom_start - top_start, bottom_middle - top_middle)

    def test_thumb_keeps_a_usable_minimum_size(self):
        top, bottom = scrollbar_thumb_geometry(300, 0.4, 0.41, 1.0)
        self.assertGreaterEqual(bottom - top, 22)

    def test_geometry_scales_with_ui_factor(self):
        small = scrollbar_thumb_geometry(300, 0.4, 0.41, 0.85)
        large = scrollbar_thumb_geometry(300, 0.4, 0.41, 1.5)
        self.assertGreaterEqual((large[1] - large[0]), (small[1] - small[0]))

    def test_pointer_leave_does_not_cancel_active_thumb_drag(self):
        scrollbar = Mock()
        scrollbar._hovered = True
        scrollbar._drag_offset = 7

        DashboardScrollbar._leave(scrollbar)

        self.assertFalse(scrollbar._hovered)
        self.assertEqual(scrollbar._drag_offset, 7)
        scrollbar._draw.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
