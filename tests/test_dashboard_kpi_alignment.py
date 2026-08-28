import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_kpi_alignment import (
    KPI_GROUP_ROW_WEIGHTS,
    KPI_ICON_SPAN_BASE,
    KPI_ICON_SPAN_MIN,
    kpi_icon_span_size,
)


class DashboardKpiAlignmentTests(unittest.TestCase):
    def test_one_x_icon_spans_two_line_kpi_block(self):
        self.assertEqual(kpi_icon_span_size(1.0), KPI_ICON_SPAN_BASE)
        self.assertGreaterEqual(kpi_icon_span_size(1.0), 40)

    def test_icon_span_scales_with_ui(self):
        self.assertLess(kpi_icon_span_size(0.85), kpi_icon_span_size(1.0))
        self.assertGreater(kpi_icon_span_size(1.5), kpi_icon_span_size(1.0))
        self.assertGreater(kpi_icon_span_size(2.0), kpi_icon_span_size(1.5))

    def test_invalid_scale_uses_one_x_and_minimum_is_preserved(self):
        self.assertEqual(kpi_icon_span_size("bad"), KPI_ICON_SPAN_BASE)
        self.assertGreaterEqual(kpi_icon_span_size(0), KPI_ICON_SPAN_MIN)

    def test_title_and_value_rows_share_spare_height_evenly(self):
        self.assertEqual(KPI_GROUP_ROW_WEIGHTS, (1, 1))
        self.assertEqual(KPI_GROUP_ROW_WEIGHTS[0], KPI_GROUP_ROW_WEIGHTS[1])


if __name__ == "__main__":
    unittest.main()
