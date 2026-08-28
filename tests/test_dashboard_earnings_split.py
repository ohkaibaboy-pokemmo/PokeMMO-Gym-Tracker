import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_earnings_split import (
    DETAILS_TITLE_BASELINE_LIFT_BASE,
    DETAILS_TITLE_COLOURS,
    DETAIL_METRIC_GROUP_HEIGHT_BASE,
    DETAIL_METRIC_LABELS,
    DETAIL_METRIC_TOP_PADDING_BASE,
    DETAIL_METRIC_VALUE_Y_BASE,
    DETAIL_WEIGHT,
    earnings_summary_column_weights,
    run_details_metric_geometry,
    run_details_metric_labels,
    run_details_metric_top_padding,
    run_details_title_baseline_lift,
    run_details_title_colour,
)


class DashboardEarningsSplitTests(unittest.TestCase):
    def test_four_headline_kpis_share_equal_weight(self):
        weights = earnings_summary_column_weights()
        self.assertEqual(weights[:4], (1, 1, 1, 1))

    def test_run_details_is_the_wider_supporting_card(self):
        weights = earnings_summary_column_weights()
        self.assertEqual(weights, (1, 1, 1, 1, DETAIL_WEIGHT))
        self.assertGreater(weights[4], weights[3])

    def test_run_details_heading_has_its_own_theme_aware_accent(self):
        self.assertEqual(run_details_title_colour("Dark"), DETAILS_TITLE_COLOURS["Dark"])
        self.assertEqual(run_details_title_colour("PokeMMO"), DETAILS_TITLE_COLOURS["PokeMMO"])
        self.assertEqual(run_details_title_colour("Light"), DETAILS_TITLE_COLOURS["Light"])
        self.assertNotEqual(run_details_title_colour("Dark"), run_details_title_colour("Light"))

    def test_unknown_theme_falls_back_to_dark_details_accent(self):
        self.assertEqual(run_details_title_colour("Other"), DETAILS_TITLE_COLOURS["Dark"])

    def test_supporting_metric_labels_are_visually_demoted_from_card_title(self):
        labels = run_details_metric_labels()
        self.assertEqual(labels, DETAIL_METRIC_LABELS)
        self.assertEqual(labels, ("Route base", "Actual run", "Route gyms", "Other payouts"))
        self.assertTrue(all(label != label.upper() for label in labels))

    def test_metric_group_keeps_top_inset_and_safe_line_separation(self):
        top_padding = run_details_metric_top_padding(1.0)
        value_y, group_height = run_details_metric_geometry(1.0)
        self.assertEqual(top_padding, DETAIL_METRIC_TOP_PADDING_BASE)
        self.assertEqual(value_y - top_padding, DETAIL_METRIC_VALUE_Y_BASE)
        self.assertEqual(group_height, DETAIL_METRIC_GROUP_HEIGHT_BASE)
        self.assertGreaterEqual(value_y - top_padding, 16)

    def test_metric_group_retains_bottom_breathing_room_after_larger_gap(self):
        value_y, group_height = run_details_metric_geometry(1.0)
        self.assertGreater(group_height, value_y)
        self.assertGreaterEqual(group_height - value_y, 4)

    def test_metric_geometry_scales_without_collapsing_line_separation(self):
        one_x_y, one_x_height = run_details_metric_geometry(1.0)
        two_x_y, two_x_height = run_details_metric_geometry(2.0)
        self.assertGreater(two_x_y, one_x_y)
        self.assertGreater(two_x_height, one_x_height)
        self.assertLessEqual(two_x_y, one_x_y * 2)

    def test_run_details_title_gets_small_scale_aware_baseline_lift(self):
        self.assertEqual(run_details_title_baseline_lift(1.0), DETAILS_TITLE_BASELINE_LIFT_BASE)
        self.assertGreater(run_details_title_baseline_lift(2.0), run_details_title_baseline_lift(1.0))


if __name__ == "__main__":
    unittest.main()
