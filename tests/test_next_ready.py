import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from tracker.dashboard_next_ready import (
    next_ready_header_card_order,
    next_ready_summary_column_weights,
)
from tracker.next_ready import (
    ALL_CHARACTERS,
    format_next_ready_detail,
    format_next_ready_time,
    next_ready_gym,
)


class NextReadyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 30, 14, 30, 0)

    @staticmethod
    def record(ready_at, count=5, manual_ready=False):
        return {
            "defeated_at": "2026-08-29T20:00:00",
            "ready_at": ready_at,
            "other_trainers": count,
            "qualifying_events": [],
            "manual_ready": manual_ready,
        }

    def test_incomplete_five_rule_does_not_hide_active_cooldown_end(self):
        state = {
            "characters": {
                "Tester": {
                    "gyms": {
                        "Erika": self.record("2026-08-30T15:15:00", count=2),
                    }
                }
            }
        }
        result = next_ready_gym(state, "Tester", now=self.now)
        self.assertEqual(result["leader"], "Erika")
        self.assertFalse(result["ready_now"])
        self.assertEqual(format_next_ready_time(result), "30 Aug · 15:15")
        self.assertEqual(format_next_ready_detail(result, "Tester"), "Erika")

    def test_earliest_active_cooldown_is_selected_even_if_another_gym_is_ready(self):
        state = {
            "characters": {
                "Tester": {
                    "gyms": {
                        "Misty": self.record("2026-08-30T14:10:00", count=5),
                        "Erika": self.record("2026-08-30T15:15:00", count=5),
                    }
                }
            }
        }
        result = next_ready_gym(state, "Tester", now=self.now)
        self.assertEqual(result["leader"], "Erika")
        self.assertFalse(result["ready_now"])
        self.assertEqual(format_next_ready_time(result), "30 Aug · 15:15")

    def test_earliest_future_cooldown_end_is_selected(self):
        state = {
            "characters": {
                "Tester": {
                    "gyms": {
                        "Crasher Wake": self.record("2026-08-31T09:47:06", count=5),
                        "Misty": self.record("2026-08-31T09:40:00", count=1),
                    }
                }
            }
        }
        result = next_ready_gym(state, "Tester", now=self.now)
        self.assertEqual(result["leader"], "Misty")
        self.assertEqual(format_next_ready_time(result), "31 Aug · 09:40")

    def test_all_characters_searches_globally_and_identifies_character(self):
        state = {
            "characters": {
                "Alpha": {"gyms": {"Misty": self.record("2026-08-31T10:00:00", count=5)}},
                "Beta": {"gyms": {"Brock": self.record("2026-08-31T09:30:00", count=0)}},
            }
        }
        result = next_ready_gym(state, ALL_CHARACTERS, now=self.now)
        self.assertEqual(result["leader"], "Brock")
        self.assertEqual(result["character"], "Beta")
        self.assertEqual(format_next_ready_detail(result, ALL_CHARACTERS), "Brock · Beta")

    def test_no_active_cooldown_shows_ready_even_when_five_rule_is_incomplete(self):
        state = {
            "characters": {
                "Tester": {"gyms": {"Misty": self.record("2026-08-30T14:00:00", count=3)}}
            }
        }
        result = next_ready_gym(state, "Tester", now=self.now)
        self.assertTrue(result["ready_now"])
        self.assertEqual(format_next_ready_time(result), "READY")
        self.assertEqual(format_next_ready_detail(result, "Tester"), "No active cooldowns")

    def test_no_gym_history_shows_ready(self):
        state = {"characters": {"Tester": {"gyms": {}}}}
        result = next_ready_gym(state, "Tester", now=self.now)
        self.assertTrue(result["ready_now"])
        self.assertEqual(format_next_ready_time(result), "READY")

    def test_legacy_manual_ready_is_not_treated_as_active_cooldown(self):
        state = {
            "characters": {
                "Tester": {
                    "gyms": {
                        "Misty": self.record("2026-08-31T10:00:00", count=0, manual_ready=True)
                    }
                }
            }
        }
        result = next_ready_gym(state, "Tester", now=self.now)
        self.assertTrue(result["ready_now"])
        self.assertEqual(format_next_ready_time(result), "READY")

    def test_header_keeps_cooldown_and_puts_next_ready_first(self):
        order = next_ready_header_card_order()
        self.assertEqual(
            order,
            ("next_ready", "ready", "waiting", "cooldown", "earnings", "details"),
        )
        self.assertEqual(order[3], "cooldown")

    def test_header_uses_five_equal_headlines_before_run_details(self):
        weights = next_ready_summary_column_weights()
        self.assertEqual(weights[:5], (1, 1, 1, 1, 1))
        self.assertEqual(len(weights), 6)
        self.assertGreater(weights[5], weights[4])


if __name__ == "__main__":
    unittest.main()
