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

    def test_waiting_gym_is_not_claimed_as_predictable_ready(self):
        state = {
            "characters": {
                "Tester": {
                    "gyms": {
                        "Misty": self.record("2026-08-30T14:00:00", count=3),
                        "Erika": self.record("2026-08-30T15:15:00", count=5),
                    }
                }
            }
        }
        result = next_ready_gym(state, "Tester", now=self.now)
        self.assertEqual(result["leader"], "Erika")
        self.assertFalse(result["ready_now"])
        self.assertEqual(format_next_ready_time(result), "30 Aug · 15:15")

    def test_ready_now_beats_future_ready(self):
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
        self.assertEqual(result["leader"], "Misty")
        self.assertTrue(result["ready_now"])
        self.assertEqual(format_next_ready_time(result), "READY NOW")
        self.assertEqual(format_next_ready_detail(result, "Tester"), "Misty")

    def test_earliest_future_ready_is_selected(self):
        state = {
            "characters": {
                "Tester": {
                    "gyms": {
                        "Crasher Wake": self.record("2026-08-31T09:47:06", count=5),
                        "Misty": self.record("2026-08-31T09:40:00", count=5),
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
                "Beta": {"gyms": {"Brock": self.record("2026-08-31T09:30:00", count=5)}},
            }
        }
        result = next_ready_gym(state, ALL_CHARACTERS, now=self.now)
        self.assertEqual(result["leader"], "Brock")
        self.assertEqual(result["character"], "Beta")
        self.assertEqual(format_next_ready_detail(result, ALL_CHARACTERS), "Brock · Beta")

    def test_no_five_rule_complete_gym_has_no_predicted_time(self):
        state = {
            "characters": {
                "Tester": {"gyms": {"Misty": self.record("2026-08-30T14:00:00", count=4)}}
            }
        }
        result = next_ready_gym(state, "Tester", now=self.now)
        self.assertIsNone(result)
        self.assertEqual(format_next_ready_time(result), "—")
        self.assertEqual(format_next_ready_detail(result, "Tester"), "Complete 5-rule first")

    def test_legacy_manual_ready_matches_existing_row_semantics(self):
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
        self.assertEqual(format_next_ready_time(result), "READY NOW")

    def test_header_priority_order_drops_redundant_cooldown_card(self):
        self.assertEqual(
            next_ready_header_card_order(),
            ("next_ready", "ready", "waiting", "earnings", "details"),
        )
        self.assertNotIn("cooldown", next_ready_header_card_order())

    def test_header_uses_four_equal_headlines_before_run_details(self):
        weights = next_ready_summary_column_weights()
        self.assertEqual(weights[:4], (1, 1, 1, 1))
        self.assertEqual(len(weights), 5)
        self.assertGreater(weights[4], weights[3])


if __name__ == "__main__":
    unittest.main()
