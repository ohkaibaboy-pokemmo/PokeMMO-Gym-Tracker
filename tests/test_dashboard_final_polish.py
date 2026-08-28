import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_final_polish import (
    DashboardFinalPolish,
    current_run_row_payout,
    migrate_known_only_state,
    payout_is_current,
    region_colour,
)
from tracker.earnings import GYM_BASE_PAYOUTS


class DashboardFinalPolishTests(unittest.TestCase):
    def test_historical_payout_is_muted_back_to_base_after_reset(self):
        paid = datetime(2026, 8, 27, 10, 0, 0)
        reset = paid + timedelta(minutes=5)
        record = {
            "payout": 99999,
            "payout_at": paid.isoformat(),
        }
        character = {"earnings": {"run_started_at": reset.isoformat()}}

        amount, actual = current_run_row_payout("Misty", record, character)
        self.assertEqual(amount, GYM_BASE_PAYOUTS["Misty"])
        self.assertFalse(actual)

    def test_current_run_payout_stays_empirical_and_gold(self):
        reset = datetime(2026, 8, 27, 10, 0, 0)
        paid = reset + timedelta(minutes=5)
        record = {
            "payout": 13104,
            "payout_at": paid.isoformat(),
        }
        character = {"earnings": {"run_started_at": reset.isoformat()}}

        self.assertTrue(payout_is_current(record, character))
        amount, actual = current_run_row_payout("Misty", record, character)
        self.assertEqual(amount, 13104)
        self.assertTrue(actual)

    def test_missing_or_invalid_timestamps_do_not_mark_current(self):
        self.assertFalse(payout_is_current({}, {}))
        self.assertFalse(
            payout_is_current(
                {"payout_at": "bad"},
                {"earnings": {"run_started_at": "also bad"}},
            )
        )

    def test_known_only_saved_state_migrates_to_composable_filter(self):
        state = {"display_filter": "Known only", "hide_unknown": False}
        self.assertTrue(migrate_known_only_state(state))
        self.assertEqual(state["display_filter"], "All")
        self.assertTrue(state["hide_unknown"])
        self.assertFalse(migrate_known_only_state(state))

    def test_region_colours_separate_regions_and_have_theme_variants(self):
        self.assertNotEqual(region_colour("[ Kanto ]", "Dark"), region_colour("[ Hoenn ]", "Dark"))
        self.assertNotEqual(region_colour("Kanto", "Dark"), region_colour("Kanto", "Light"))
        self.assertNotEqual(region_colour("Kanto", "Dark"), region_colour("Kanto", "PokeMMO"))
        self.assertIsNone(region_colour("Unknown Place", "Dark"))

    def test_kanto_accent_is_neutral_not_old_error_red(self):
        self.assertNotEqual(region_colour("Kanto", "Dark"), "#E06B6B")
        self.assertNotEqual(region_colour("Kanto", "Light"), "#B43D3D")

    def test_final_polish_theme_pass_runs_after_global_theme(self):
        calls = []

        class FakeApp:
            def apply_theme(self):
                calls.append("global")
                return "result"

        polish = DashboardFinalPolish.__new__(DashboardFinalPolish)
        polish.app = FakeApp()
        polish.apply_theme = lambda: calls.append("final-polish")

        polish._wrap_app_theme()
        result = polish.app.apply_theme()

        self.assertEqual(result, "result")
        self.assertEqual(calls, ["global", "final-polish"])
        self.assertTrue(
            getattr(polish.app.apply_theme, "_dashboard_final_polish_theme_wrapped", False)
        )


if __name__ == "__main__":
    unittest.main()
