import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from tracker.constants import SIX_PILLOWS_ROUTE
from tracker.earnings import (
    format_yen,
    projection_rows,
    record_payout,
    reset_run,
    route_base_total,
    summarize_run,
)
from tracker.state import default_state


class EarningsTests(unittest.TestCase):
    def test_six_pillows_base_total(self):
        self.assertEqual(route_base_total(SIX_PILLOWS_ROUTE), 268632)

    def test_projection_matches_expected_no_donator_values(self):
        settings = {
            "amulet_price": 0,
            "riches_75_price": 0,
            "riches_100_price": 0,
            "donator": False,
        }
        rows = {row["name"]: row for row in projection_rows(268632, settings)}
        self.assertEqual(rows["No charm"]["gross"], 268632)
        self.assertEqual(rows["Amulet Coin"]["gross"], 402948)
        self.assertEqual(rows["Riches Charm 75%"]["gross"], 470106)
        self.assertEqual(rows["Riches Charm 100%"]["gross"], 537264)

    def test_projection_subtracts_manual_charm_cost_and_applies_donator(self):
        settings = {
            "amulet_price": 20000,
            "riches_75_price": 30000,
            "riches_100_price": 40000,
            "donator": True,
        }
        rows = {row["name"]: row for row in projection_rows(268632, settings)}
        self.assertEqual(rows["No charm"]["gross"], 282064)
        self.assertEqual(rows["Amulet Coin"]["net"], 403095)
        self.assertEqual(rows["Riches Charm 75%"]["net"], 463611)
        self.assertEqual(rows["Riches Charm 100%"]["net"], 524127)

    def test_current_run_summary_separates_route_gyms_and_other_payouts(self):
        state = default_state()
        char = state["characters"].setdefault("TestCharacter", {"gyms": {}})
        reset_run(char, datetime(2026, 8, 23, 15, 0, 0))
        record_payout(state, datetime(2026, 8, 23, 15, 8, 50), "TestCharacter", "Leader Brock", 8632)
        record_payout(state, datetime(2026, 8, 23, 15, 11, 15), "TestCharacter", "Gentleman Yan", 5400)

        summary = summarize_run(char, ["Brock", "Misty"])
        self.assertEqual(summary["total"], 14032)
        self.assertEqual(summary["route_gym_total"], 8632)
        self.assertEqual(summary["other_total"], 5400)
        self.assertEqual(summary["gym_count"], 1)
        self.assertEqual(summary["route_count"], 2)
        self.assertEqual(summary["remaining_base"], 8736)

    def test_reset_excludes_older_payouts_without_deleting_history(self):
        state = default_state()
        char = state["characters"].setdefault("TestCharacter", {"gyms": {}})
        record_payout(state, datetime(2026, 8, 23, 14, 0, 0), "TestCharacter", "Leader Brock", 8632)
        reset_run(char, datetime(2026, 8, 23, 15, 0, 0))
        record_payout(state, datetime(2026, 8, 23, 15, 30, 0), "TestCharacter", "Leader Misty", 8736)

        summary = summarize_run(char, ["Brock", "Misty"])
        self.assertEqual(summary["total"], 8736)
        self.assertEqual(len(char["earnings"]["events"]), 2)

    def test_yen_format(self):
        self.assertEqual(format_yen(268632), "¥268,632")
        self.assertEqual(format_yen(-5000), "-¥5,000")


if __name__ == "__main__":
    unittest.main()
