import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from tracker.engine import TrackerEngine
from tracker.state import _migrate_state, default_state


class CrasherWakeAliasRegressionTests(unittest.TestCase):
    def setUp(self):
        self.state = default_state()
        self.events = []
        self.engine = TrackerEngine(
            self.state,
            on_event=lambda ts, text, level="info": self.events.append((ts, text, level)),
            save_callback=lambda _state: None,
        )

    def feed(self, *lines):
        for line in lines:
            self.engine.process_line(line + "\n")

    def test_observed_leader_wake_log_maps_to_pastoria(self):
        # Regression from external tester evidence on 2026-08-30. PokeMMO uses
        # the shorter in-log name "Wake" even though the tracker route/catalogue
        # uses the canonical display name "Crasher Wake".
        self.feed(
            "[8/30/26 3:45:06 PM] [Battle] You are challenged by [#ff8a00]Leader[#] [#ff8a00]Wake[#]!",
            "[8/30/26 3:45:12 PM] [Battle] [#ff8a00]expducktwo[#] sent out [#ff8a00]Archeops[#] and [#ff8a00]Torkoal[#]!",
            "[8/30/26 3:47:06 PM] [Battle] Player defeated [#ff8a00]Leader[#] [#ff8a00]Wake[#]!",
            "[8/30/26 3:47:07 PM] [Battle] [#ff8a00]expducktwo[#] got $[#ff8a00]13572[#] for winning!",
        )

        char = self.state["characters"]["expducktwo"]
        self.assertNotIn("Wake", char["gyms"])
        self.assertIn("Crasher Wake", char["gyms"])
        record = char["gyms"]["Crasher Wake"]
        self.assertEqual(record["defeated_at"], "2026-08-30T15:47:06")
        self.assertEqual(record["ready_at"], "2026-08-31T09:47:06")
        self.assertEqual(record["payout"], 13572)
        self.assertEqual(char["earnings"]["events"][0]["leader"], "Crasher Wake")
        self.assertTrue(any("GYM WIN: Sinnoh / Pastoria" in text for _ts, text, _level in self.events))
        self.assertTrue(any("PAYOUT: Crasher Wake" in text for _ts, text, _level in self.events))

    def test_existing_wake_state_is_repaired_on_load_migration(self):
        state = default_state()
        state["characters"] = {
            "expducktwo": {
                "gyms": {
                    "Wake": {
                        "defeated_at": "2026-08-30T15:47:06",
                        "ready_at": "2026-08-31T09:47:06",
                        "other_trainers": 0,
                        "qualifying_events": [],
                        "manual_ready": False,
                        "payout": 13572,
                        "payout_at": "2026-08-30T15:47:07",
                    }
                },
                "earnings": {
                    "run_started_at": "2026-08-30T15:47:07",
                    "events": [
                        {
                            "id": "wake-test",
                            "ts": "2026-08-30T15:47:07",
                            "opponent": "Leader Wake",
                            "amount": 13572,
                            "is_gym": True,
                            "leader": "Wake",
                        }
                    ],
                },
            }
        }
        state["custom_routes"] = {"Test route": ["Wake", "Brock"]}

        migrated = _migrate_state(state)
        char = migrated["characters"]["expducktwo"]

        self.assertNotIn("Wake", char["gyms"])
        self.assertEqual(char["gyms"]["Crasher Wake"]["payout"], 13572)
        self.assertEqual(char["earnings"]["events"][0]["leader"], "Crasher Wake")
        self.assertEqual(migrated["custom_routes"]["Test route"], ["Crasher Wake", "Brock"])


if __name__ == "__main__":
    unittest.main()
