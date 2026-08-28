import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.state import default_state
from tracker.trainers import recalculate_5_rule_counts


class FiveRuleStateRepairTests(unittest.TestCase):
    def test_recalculation_ignores_legacy_fractional_manual_leader_events(self):
        state = default_state()
        state["characters"] = {
            "Tester": {
                "gyms": {
                    "Bugsy": {
                        "defeated_at": "2026-08-26T18:52:20",
                        "ready_at": "2026-08-27T12:52:20",
                        "other_trainers": 5,
                        "qualifying_events": [],
                        "manual_ready": False,
                    }
                }
            }
        }
        state["processed_events"] = [
            "2026-08-26T18:52:20|Tester|Leader Bugsy",
            "2026-08-26T18:59:11.102150|Tester|Leader Maylene",
            "2026-08-27T09:15:32.950932|Tester|Leader Koga",
            "2026-08-27T09:26:43.223769|Tester|Leader Misty",
            "2026-08-27T09:27:06.148106|Tester|Leader Misty",
            "2026-08-27T09:27:12.242489|Tester|Leader Brock",
            "2026-08-28T13:49:31|Tester|PI Carlos",
            "2026-08-28T14:09:19|Tester|Socialite Marian",
            "2026-08-28T14:15:10|Tester|Leader Gardenia",
            "2026-08-28T14:53:36|Tester|Leader Lt. Surge",
        ]

        recalculate_5_rule_counts(state)

        bugsy = state["characters"]["Tester"]["gyms"]["Bugsy"]
        self.assertEqual(bugsy["other_trainers"], 4)
        self.assertEqual(
            [event["opponent"] for event in bugsy["qualifying_events"]],
            ["PI Carlos", "Socialite Marian", "Leader Gardenia", "Leader Lt. Surge"],
        )


if __name__ == "__main__":
    unittest.main()
