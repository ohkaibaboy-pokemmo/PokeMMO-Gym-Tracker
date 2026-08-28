import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_gym_list import DashboardGymList, GymRow, dashboard_column_layout
from tracker.dashboard_resize_smoothing import (
    FULL_WINDOW_RESIZABLE,
    dashboard_minimum_size,
    full_route_bottom_gap,
    gym_viewport_height,
)


class DashboardResizeSmoothingTests(unittest.TestCase):
    def test_full_dashboard_is_resizable_again(self):
        self.assertEqual(FULL_WINDOW_RESIZABLE, (True, True))

    def test_full_gym_route_uses_canvas_renderer(self):
        self.assertEqual(DashboardGymList.ROW_RENDERER, "canvas")

    def test_full_minimum_keeps_lower_dashboard_sections_available_at_1x(self):
        self.assertEqual(dashboard_minimum_size(1.0, 1920, 1080), (1280, 800))
        self.assertEqual(dashboard_minimum_size(0.85, 1920, 1080), (1280, 800))

    def test_full_minimum_scales_up_but_is_screen_capped(self):
        self.assertEqual(dashboard_minimum_size(2.0, 1920, 1080), (1880, 1000))
        self.assertEqual(dashboard_minimum_size(1.5, 1366, 768), (1326, 688))

    def test_gym_route_requested_height_yields_space_to_detector_at_minimum(self):
        self.assertEqual(gym_viewport_height(1.0), 190)
        self.assertEqual(gym_viewport_height(0.85), 162)
        self.assertEqual(gym_viewport_height(1.5), 285)

    def test_full_route_bottom_gap_hides_fractional_last_row(self):
        self.assertEqual(full_route_bottom_gap(58 * 14, 58), 0)
        self.assertEqual(full_route_bottom_gap((58 * 14) + 12, 58), 12)
        self.assertEqual(full_route_bottom_gap((58 * 14) + 57, 58), 57)

    def test_full_route_bottom_gap_keeps_tiny_viewport_usable(self):
        self.assertEqual(full_route_bottom_gap(40, 58), 0)
        self.assertEqual(full_route_bottom_gap("bad", 58), 0)

    def test_canvas_columns_fill_exact_available_width(self):
        bounds = dashboard_column_layout(1220, 1.0)
        self.assertEqual(len(bounds), 10)
        self.assertEqual(bounds[0][0], 0)
        self.assertEqual(bounds[-1][1], 1220)
        self.assertTrue(all(right > left for left, right in bounds))

    def test_timer_tick_changes_only_row_state_not_semantics(self):
        row = GymRow("Brock")
        portrait = object()
        initial = (
            "01",
            "[ Kanto ]",
            "Pewter",
            "Brock",
            "00:00:01",
            "5/5",
            "26/08 15:00:00",
            "READY",
        )
        row.update(initial, (), portrait, "$8,632", False)
        changed = row.update(
            initial[:4] + ("00:00:00",) + initial[5:],
            (),
            portrait,
            "$8,632",
            False,
        )
        self.assertEqual(changed, {"cooldown"})
        self.assertEqual(row.status_code, "READY")

    def test_semantic_row_change_is_reported(self):
        row = GymRow("Brock")
        portrait = object()
        row.update(
            ("01", "[ Kanto ]", "Pewter", "Brock", "00:00:00", "5/5", "26/08 15:00:00", "READY"),
            (),
            portrait,
            "$8,632",
            False,
        )
        changed = row.update(
            ("01", "[ Kanto ]", "Pewter", "Brock", "Need 2 battles", "3/5", "26/08 15:00:00", "WAITING"),
            (),
            portrait,
            "$8,632",
            False,
        )
        self.assertIn("semantic", changed)
        self.assertEqual(row.status_code, "WAITING")


if __name__ == "__main__":
    unittest.main()
