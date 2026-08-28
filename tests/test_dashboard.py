import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_detector import (
    classify_event,
    detector_content_height,
    detector_row_gap,
    detector_row_height,
    detector_viewport_height,
)
from tracker.dashboard_earnings_window import format_dashboard_currency
from tracker.dashboard_full_refresh import FullViewRefresh
from tracker.dashboard_gym_list import (
    DashboardGymList,
    format_dashboard_money,
    payout_for_record,
    status_from_text,
)
from tracker.dashboard_table_alignment import full_leader_group_geometry
from tracker.dashboard_ui import DashboardShell
from tracker.money_style import amount_only
from tracker.themes import THEMES


class DashboardThemeTests(unittest.TestCase):
    def test_core_theme_names_are_preserved(self):
        self.assertEqual(set(THEMES), {"Dark", "PokeMMO", "Light"})

    def test_dashboard_tokens_exist_in_every_theme(self):
        required = {
            "card_bg",
            "card_border",
            "control_bg",
            "control_border",
            "ready_bg",
            "waiting_bg",
            "cooldown",
            "cooldown_bg",
            "unknown_bg",
            "selection_bg",
            "selection_border",
            "money",
            "money_shadow",
            "live",
            "detector_info",
            "detector_pay",
            "detector_battle",
            "detector_success",
            "detector_warn",
        }
        for name, theme in THEMES.items():
            self.assertTrue(required.issubset(theme), f"missing dashboard tokens in {name}")

    def test_dashboard_money_presentation_uses_normal_dollar_text(self):
        self.assertEqual(DashboardShell._as_dollar("¥338,589"), "$338,589")
        self.assertEqual(DashboardShell._as_dollar("$5,400"), "$5,400")
        self.assertEqual(DashboardShell._as_dollar("0"), "$0")
        self.assertEqual(DashboardShell._as_dollar("—"), "—")

    def test_dashboard_calculator_currency_formatter(self):
        self.assertEqual(format_dashboard_currency(338589), "$338,589")
        self.assertEqual(format_dashboard_currency(0), "$0")
        self.assertEqual(format_dashboard_currency("5400"), "$5,400")
        self.assertEqual(format_dashboard_currency("bad"), "—")

    def test_amount_only_remains_available_for_money_components(self):
        self.assertEqual(amount_only("¥338,589"), "338,589")
        self.assertEqual(amount_only("$68,112"), "68,112")
        self.assertEqual(amount_only("0"), "0")

    def test_full_refresh_theme_pass_runs_after_global_theme(self):
        calls = []

        class FakeApp:
            def apply_theme(self):
                calls.append("global")
                return "result"

        refresh = FullViewRefresh.__new__(FullViewRefresh)
        refresh.app = FakeApp()
        refresh.apply_theme = lambda: calls.append("full-refresh")

        refresh._wrap_app_theme()
        result = refresh.app.apply_theme()

        self.assertEqual(result, "result")
        self.assertEqual(calls, ["global", "full-refresh"])
        self.assertTrue(
            getattr(refresh.app.apply_theme, "_full_view_refresh_theme_wrapped", False)
        )


class DashboardGymRowTests(unittest.TestCase):
    def test_status_parser_preserves_core_codes(self):
        self.assertEqual(status_from_text("READY"), "READY")
        self.assertEqual(status_from_text("READY (Alt)"), "READY")
        self.assertEqual(status_from_text("WAITING"), "WAITING")
        self.assertEqual(status_from_text("COOLDOWN"), "COOLDOWN")
        self.assertEqual(status_from_text("anything else"), "UNKNOWN")

    def test_observed_payout_beats_base_value(self):
        amount, actual = payout_for_record("Brock", {"payout": 12948})
        self.assertEqual(amount, 12948)
        self.assertTrue(actual)

    def test_base_payout_fills_unobserved_rows_offline(self):
        amount, actual = payout_for_record("Brock", None)
        self.assertEqual(amount, 8632)
        self.assertFalse(actual)
        self.assertEqual(format_dashboard_money(amount), "$8,632")

    def test_full_leader_group_fits_inside_base_leader_column(self):
        group, icon, gap, text = full_leader_group_geometry(1.0)
        leader_column = next(spec for spec in DashboardGymList.COLUMN_SPECS if spec[0] == 2)
        self.assertEqual(group, 120)
        self.assertEqual(icon, 22)
        self.assertEqual(gap, 6)
        self.assertEqual(text, 92)
        # The Leader cell currently has 5px horizontal grid padding on each side.
        self.assertLessEqual(group, leader_column[2] - 10)

    def test_full_leader_group_scales_with_ui(self):
        base = full_leader_group_geometry(1.0)
        large = full_leader_group_geometry(1.5)
        small = full_leader_group_geometry(0.85)
        self.assertGreater(large[0], base[0])
        self.assertGreater(large[1], base[1])
        self.assertLess(small[0], base[0])
        self.assertGreaterEqual(small[1], 18)


class DashboardDetectorTests(unittest.TestCase):
    def test_detector_classifies_payouts(self):
        self.assertEqual(classify_event("PAYOUT: Brock — $8,632"), ("pay", "PAY"))

    def test_detector_classifies_gym_wins(self):
        self.assertEqual(
            classify_event("GYM WIN: Erika — 18h cooldown started", "success"),
            ("success", "GYM"),
        )

    def test_detector_respects_warning_level(self):
        self.assertEqual(classify_event("Unknown trainer not counted", "warn"), ("warn", "WARN"))

    def test_detector_viewport_has_four_row_breathing_room(self):
        self.assertEqual(detector_viewport_height(1.0), 124)
        self.assertEqual(detector_viewport_height(1.5), 186)
        self.assertGreater(detector_viewport_height(0.85), 98)

    def test_detector_single_canvas_rows_have_stable_scroll_geometry(self):
        self.assertEqual(detector_row_height(1.0), 28)
        self.assertEqual(detector_row_gap(1.0), 3)
        self.assertEqual(detector_content_height(0, 1.0), 124)
        self.assertEqual(detector_content_height(1, 1.0), 28)
        self.assertEqual(detector_content_height(4, 1.0), 121)
        self.assertEqual(detector_content_height(5, 1.0), 152)

    def test_detector_row_geometry_scales_without_collapsing(self):
        self.assertGreater(detector_row_height(1.5), detector_row_height(1.0))
        self.assertGreater(detector_row_gap(1.5), detector_row_gap(1.0))
        self.assertGreater(detector_content_height(10, 1.5), detector_content_height(10, 1.0))
        self.assertGreaterEqual(detector_row_height(0.85), 24)
        self.assertGreaterEqual(detector_row_gap(0.85), 2)


if __name__ == "__main__":
    unittest.main()
