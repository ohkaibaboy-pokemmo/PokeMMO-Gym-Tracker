import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_action_grouping import right_action_visual_order


class DashboardActionGroupingTests(unittest.TestCase):
    def test_export_sits_with_file_log_actions(self):
        order = right_action_visual_order()
        self.assertEqual(order[:3], ("Replay Log File", "Choose Log Folder", "Export"))
        self.assertLess(order.index("Export"), order.index("Calculator"))
        self.assertLess(order.index("Calculator"), order.index("Reset Run"))


if __name__ == "__main__":
    unittest.main()
