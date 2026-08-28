import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_header_responsive import summary_layout_mode


class DashboardHeaderResponsiveTests(unittest.TestCase):
    def test_wide_summary_keeps_details_inline(self):
        self.assertEqual(summary_layout_mode(1200, 1.0), "inline")

    def test_half_monitor_summary_stacks_details(self):
        self.assertEqual(summary_layout_mode(850, 1.0), "stacked")

    def test_threshold_scales_with_ui(self):
        self.assertEqual(summary_layout_mode(1300, 1.5), "stacked")
        self.assertEqual(summary_layout_mode(1500, 1.5), "inline")


if __name__ == "__main__":
    unittest.main()
