import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from tracker.constants import COOLDOWN_HOURS
from tracker.engine import TrackerEngine
from tracker.state import default_state
from tracker.trainers import recalculate_5_rule_counts


class ParserRegressionTests(unittest.TestCase):
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

    def test_vanilla_gym_win_with_colour_tags(self):
        self.feed(
            "[23/08/2026 15:06:31] [Battle] You are challenged by [#ff8a00]Leader[#] [#ff8a00]Brock[#]!",
            "[23/08/2026 15:06:38] [Battle] [#ff8a00]TestCharacter[#] sent out [#ff8a00]Typhlosion[#]!",
            "[23/08/2026 15:08:44] [Battle] Player defeated [#ff8a00]Leader[#] [#ff8a00]Brock[#]!",
            "[23/08/2026 15:08:50] [Battle] [#ff8a00]TestCharacter[#] got $[#ff8a00]8632[#] for winning!",
        )
        char = self.state["characters"]["TestCharacter"]
        record = char["gyms"]["Brock"]
        defeated = datetime.fromisoformat(record["defeated_at"])
        ready = datetime.fromisoformat(record["ready_at"])
        self.assertEqual((ready - defeated).total_seconds(), COOLDOWN_HOURS * 3600)
        self.assertEqual(record["other_trainers"], 0)
        self.assertEqual(record["payout"], 8632)
        self.assertEqual(len(char["earnings"]["events"]), 1)
        self.assertEqual(char["earnings"]["events"][0]["leader"], "Brock")
        self.assertEqual(char["earnings"]["events"][0]["amount"], 8632)

    def test_us_windows_gym_win_with_12_hour_timestamp(self):
        # Sanitised regression based on external Windows evidence from 2026-08-29:
        # PokeMMO emitted M/D/YY timestamps with AM/PM rather than the previously
        # validated DD/MM/YYYY 24-hour format.
        self.feed(
            "[8/29/26 4:04:30 PM] [Battle] You are challenged by [#ff8a00]Leader[#] [#ff8a00]Flannery[#]!",
            "[8/29/26 4:04:37 PM] [Battle] [#ff8a00]ExternalTester[#] sent out [#ff8a00]Archeops[#] and [#ff8a00]Blastoise[#]!",
            "[8/29/26 4:05:52 PM] [Battle] Player defeated [#ff8a00]Leader[#] [#ff8a00]Flannery[#]!",
            "[8/29/26 4:05:54 PM] [Battle] [#ff8a00]ExternalTester[#] got $[#ff8a00]14086[#] for winning!",
        )
        char = self.state["characters"]["ExternalTester"]
        record = char["gyms"]["Flannery"]
        self.assertEqual(record["defeated_at"], "2026-08-29T16:05:52")
        self.assertEqual(record["ready_at"], "2026-08-30T10:05:52")
        self.assertEqual(record["payout"], 14086)
        self.assertEqual(char["earnings"]["events"][0]["amount"], 14086)
        self.assertTrue(any("GYM WIN: Hoenn / Lavaridge" in text for _ts, text, _level in self.events))

    def test_normal_trainer_counts_after_gym_by_default(self):
        self.feed(
            "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:06:38] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
            "[23/08/2026 15:08:50] [Battle] TestCharacter got $8632 for winning!",
            "[23/08/2026 15:09:57] [Battle] You are challenged by Youngster Warren!",
            "[23/08/2026 15:10:04] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:11:12] [Battle] Player defeated Youngster Warren!",
            "[23/08/2026 15:11:15] [Battle] TestCharacter got $656 for winning!",
        )
        char = self.state["characters"]["TestCharacter"]
        record = char["gyms"]["Brock"]
        self.assertEqual(record["other_trainers"], 1)
        self.assertEqual(record["qualifying_events"][0]["opponent"], "Youngster Warren")
        self.assertTrue(any("counted toward 1 active gym requirement" in text for _ts, text, _level in self.events))

    def test_legacy_verified_trainer_still_counts(self):
        self.feed(
            "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:06:38] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
            "[23/08/2026 15:08:50] [Battle] TestCharacter got $8632 for winning!",
            "[23/08/2026 15:09:57] [Battle] You are challenged by Gentleman Yan!",
            "[23/08/2026 15:10:04] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:11:12] [Battle] Player defeated Gentleman Yan!",
            "[23/08/2026 15:11:15] [Battle] TestCharacter got $5400 for winning!",
        )
        char = self.state["characters"]["TestCharacter"]
        record = char["gyms"]["Brock"]
        self.assertEqual(record["other_trainers"], 1)
        self.assertEqual(record["qualifying_events"][0]["opponent"], "Gentleman Yan")
        self.assertEqual(len(char["earnings"]["events"]), 2)
        self.assertEqual(char["earnings"]["events"][1]["opponent"], "Gentleman Yan")
        self.assertEqual(char["earnings"]["events"][1]["amount"], 5400)
        self.assertFalse(char["earnings"]["events"][1]["is_gym"])

    def test_explicitly_excluded_trainer_does_not_count(self):
        self.state["excluded_5_rule_trainers"] = ["Youngster Warren"]
        self.feed(
            "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:06:38] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
            "[23/08/2026 15:09:57] [Battle] You are challenged by Youngster Warren!",
            "[23/08/2026 15:10:04] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:11:12] [Battle] Player defeated Youngster Warren!",
        )
        record = self.state["characters"]["TestCharacter"]["gyms"]["Brock"]
        self.assertEqual(record["other_trainers"], 0)
        self.assertTrue(any("explicitly excluded" in text for _ts, text, _level in self.events))

    def test_recalculation_backfills_previously_detected_ordinary_trainers(self):
        self.state["processed_events"] = [
            "2026-08-23T15:08:44|TestCharacter|Leader Brock",
            "2026-08-23T15:11:12|TestCharacter|Youngster Warren",
        ]
        self.state["characters"] = {
            "TestCharacter": {
                "gyms": {
                    "Brock": {
                        "defeated_at": "2026-08-23T15:08:44",
                        "ready_at": "2026-08-24T09:08:44",
                        "other_trainers": 0,
                        "qualifying_events": [],
                        "manual_ready": False,
                    }
                }
            }
        }
        recalculate_5_rule_counts(self.state)
        record = self.state["characters"]["TestCharacter"]["gyms"]["Brock"]
        self.assertEqual(record["other_trainers"], 1)
        self.assertEqual(record["qualifying_events"][0]["opponent"], "Youngster Warren")

    def test_five_battle_block_message_is_detected(self):
        self.feed("[23/08/2026 15:05:52] [System Messages] You must battle other trainers before you may rematch this trainer.")
        self.assertTrue(any("5-other-trainer requirement" in text for _ts, text, _level in self.events))

    def test_duplicate_victory_and_payout_are_ignored(self):
        lines = (
            "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:06:38] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
            "[23/08/2026 15:08:50] [Battle] TestCharacter got $8632 for winning!",
        )
        self.feed(*lines)
        first_events = list(self.state["processed_events"])
        first_payouts = list(self.state["characters"]["TestCharacter"]["earnings"]["events"])
        self.feed(*lines)
        self.assertEqual(self.state["processed_events"], first_events)
        self.assertEqual(self.state["characters"]["TestCharacter"]["earnings"]["events"], first_payouts)

    def test_payout_can_backfill_after_victory_was_already_processed(self):
        self.feed(
            "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:06:38] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
        )
        self.assertEqual(self.state["characters"]["TestCharacter"].get("earnings", {}).get("events", []), [])

        # Simulate replaying the same battle later after upgrading to an earnings-aware build.
        self.feed(
            "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:06:38] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
            "[23/08/2026 15:08:50] [Battle] TestCharacter got $8632 for winning!",
        )
        payouts = self.state["characters"]["TestCharacter"]["earnings"]["events"]
        self.assertEqual(len(payouts), 1)
        self.assertEqual(payouts[0]["amount"], 8632)


if __name__ == "__main__":
    unittest.main()
