import sys
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.character_export import (
    ALL_CHARACTERS,
    build_character_export,
    build_html_report,
    default_export_filename,
    default_report_filename,
    selected_character_names,
)


class CharacterExportTests(unittest.TestCase):
    def setUp(self):
        self.state = {
            "characters": {
                "Alpha": {
                    "gyms": {
                        "Brock": {
                            "defeated_at": "2026-08-25T08:00:00",
                            "ready_at": "2026-08-26T02:00:00",
                            "other_trainers": 2,
                            "payout": 8632,
                        }
                    },
                    "earnings": {
                        "run_started_at": "2026-08-25T09:00:00",
                        "events": [
                            {
                                "ts": "2026-08-25T09:05:00",
                                "amount": 8632,
                                "is_gym": True,
                            }
                        ],
                    },
                },
                "Beta & Co": {
                    "gyms": {
                        "Misty": {
                            "defeated_at": "2026-08-24T09:00:00",
                            "ready_at": "2026-08-25T03:00:00",
                            "other_trainers": 5,
                        }
                    },
                    "earnings": {"run_started_at": None, "events": []},
                },
            },
            "processed_events": [
                "2026-08-25T09:01:00|Alpha|Leader Brock",
                "2026-08-25T09:02:00|Beta & Co|Leader Misty",
                "malformed",
            ],
            "custom_routes": {"Private route": ["Brock", "Misty"]},
            "log_folder": "C:/private/log/path",
            "theme": "Dark",
        }
        self.when = datetime(2026, 8, 25, 10, 15, 0)

    def test_specific_character_exports_only_that_character(self):
        payload = build_character_export(self.state, "Alpha", self.when)
        self.assertEqual(payload["scope"], "character")
        self.assertEqual(list(payload["characters"]), ["Alpha"])
        self.assertEqual(
            payload["processed_events"],
            ["2026-08-25T09:01:00|Alpha|Leader Brock"],
        )
        self.assertNotIn("custom_routes", payload)
        self.assertNotIn("log_folder", payload)
        self.assertNotIn("theme", payload)

    def test_all_characters_exports_every_character(self):
        payload = build_character_export(self.state, ALL_CHARACTERS, self.when)
        self.assertEqual(payload["scope"], "all")
        self.assertEqual(set(payload["characters"]), {"Alpha", "Beta & Co"})
        self.assertEqual(len(payload["processed_events"]), 2)

    def test_selection_helpers_follow_character_selector(self):
        self.assertEqual(selected_character_names(self.state, "Alpha"), ["Alpha"])
        self.assertEqual(
            selected_character_names(self.state, ALL_CHARACTERS),
            ["Alpha", "Beta & Co"],
        )
        self.assertEqual(selected_character_names(self.state, "Missing"), [])

    def test_export_filename_reflects_scope(self):
        self.assertEqual(
            default_export_filename("Alpha", self.when),
            "PokeMMO-Gym-Tracker-Alpha-2026-08-25.json",
        )
        self.assertEqual(
            default_export_filename(ALL_CHARACTERS, self.when),
            "PokeMMO-Gym-Tracker-All-Characters-2026-08-25.json",
        )
        self.assertEqual(
            default_report_filename("Alpha", self.when),
            "PokeMMO-Gym-Tracker-Alpha-2026-08-25.html",
        )

    def test_html_report_is_human_readable_and_character_scoped(self):
        report = build_html_report(self.state, "Alpha", self.when)
        self.assertIn("Alpha Report", report)
        self.assertNotIn("Beta &amp; Co", report)
        self.assertIn("Brock", report)
        self.assertIn("COOLDOWN", report)
        self.assertIn("15:45:00", report)
        self.assertIn("$8,632", report)
        self.assertIn("RUN EARNINGS", report)

    def test_all_character_html_report_contains_separate_sections_and_escapes_names(self):
        report = build_html_report(self.state, ALL_CHARACTERS, self.when)
        self.assertIn("All Characters Report", report)
        self.assertIn("Alpha", report)
        self.assertIn("Beta &amp; Co", report)
        self.assertGreaterEqual(report.count('class="character"'), 2)
        self.assertIn("READY", report)


if __name__ == "__main__":
    unittest.main()
