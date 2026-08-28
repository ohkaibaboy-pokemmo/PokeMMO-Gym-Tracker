import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.compact_type_icons import (
    compact_type_icon_gap,
    compact_type_icon_size,
    compact_type_icon_x,
    compact_type_max_text_width,
    compact_type_prepare_tree_values,
    compact_type_row_fully_visible,
    compact_type_visible_height,
)
from tracker.compact_ui import _as_dollar, compact_progress_values


class CompactDashboardTests(unittest.TestCase):
    def test_progress_summary_parses_shared_tracker_text(self):
        values = compact_progress_values(
            "Ready 14/41  •  Waiting 0  •  Cooldown 3  •  Unknown 24"
        )
        self.assertEqual(
            values,
            {
                "ready": "14",
                "total": "41",
                "waiting": "0",
                "cooldown": "3",
                "unknown": "24",
            },
        )

    def test_progress_summary_fails_safe(self):
        values = compact_progress_values("")
        self.assertEqual(values["ready"], "0")
        self.assertEqual(values["total"], "0")

    def test_compact_run_money_uses_normal_dollar_text(self):
        self.assertEqual(_as_dollar("¥77,400"), "$77,400")
        self.assertEqual(_as_dollar("$5,400"), "$5,400")
        self.assertEqual(_as_dollar("—"), "—")

    def test_compact_type_icon_dimensions_stay_subtle(self):
        self.assertEqual(compact_type_icon_size(1.0), 15)
        self.assertEqual(compact_type_icon_gap(1.0), 5)
        self.assertLess(compact_type_icon_size(1.0), 20)
        self.assertLess(compact_type_icon_gap(1.0), 10)

    def test_compact_type_icon_dimensions_scale_with_ui(self):
        self.assertGreater(compact_type_icon_size(1.5), compact_type_icon_size(1.0))
        self.assertGreater(compact_type_icon_gap(1.5), compact_type_icon_gap(1.0))
        self.assertGreaterEqual(compact_type_icon_size(0.85), 13)
        self.assertGreaterEqual(compact_type_icon_gap(0.85), 4)

    def test_compact_type_icon_rail_is_centred_and_shared(self):
        first = compact_type_icon_x(100, 180, 72, 1.0)
        second = compact_type_icon_x(100, 180, 72, 1.0)
        self.assertEqual(first, second)
        content_width = compact_type_icon_size(1.0) + compact_type_icon_gap(1.0) + 72
        self.assertAlmostEqual(first, 100 + (180 - content_width) / 2.0, delta=1.0)

    def test_compact_type_group_cannot_overflow_gym_cell(self):
        cell_width = 120
        max_text = compact_type_max_text_width(cell_width, 1.0)
        content_width = (
            compact_type_icon_size(1.0)
            + compact_type_icon_gap(1.0)
            + max_text
        )
        self.assertLessEqual(content_width, cell_width - 4)
        # Even an extremely long measured name is clamped before centring.
        x = compact_type_icon_x(50, cell_width, 999, 1.0)
        self.assertGreaterEqual(x, 52)
        self.assertLessEqual(x + content_width, 50 + cell_width - 2)

    def test_compact_refresh_blanks_native_gym_before_tree_insert(self):
        prepared, gym = compact_type_prepare_tree_values(
            ("7", "Celadon", "00:00:00", "5/5")
        )
        self.assertEqual(gym, "Celadon")
        self.assertEqual(prepared, ("7", "", "00:00:00", "5/5"))

    def test_compact_overlay_reports_full_and_partial_visible_height(self):
        self.assertEqual(compact_type_visible_height(40, 27, 200), 27)
        self.assertEqual(compact_type_visible_height(185, 27, 200), 13)
        self.assertEqual(compact_type_visible_height(198, 27, 200), 0)
        self.assertEqual(compact_type_visible_height(-1, 27, 200), 0)
        self.assertTrue(compact_type_row_fully_visible(170, 27, 200))
        self.assertFalse(compact_type_row_fully_visible(185, 27, 200))


if __name__ == "__main__":
    unittest.main()
