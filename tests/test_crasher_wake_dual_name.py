import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from tracker.engine import TrackerEngine
from tracker.state import default_state


class CrasherWakeDualNameTests(unittest.TestCase):
    def run_sequence(self, leader_text):
        state = default_state()
        events = []
        engine = TrackerEngine(
            state,
            on_event=lambda ts, text, level="info": events.append((ts, text, level)),
            save_callback=lambda _state: None,
        )
        lines = (
            f"[8/30/26 3:45:06 PM] [Battle] You are challenged by Leader {leader_text}!",
            "[8/30/26 3:45:12 PM] [Battle] ExternalTester sent out Archeops and Torkoal!",
            f"[8/30/26 3:47:06 PM] [Battle] Player defeated Leader {leader_text}!",
            "[8/30/26 3:47:07 PM] [Battle] ExternalTester got $13572 for winning!",
        )
        for line in lines:
            engine.process_line(line + "\n")
        return state, events

    def assert_canonical_pastoria_result(self, state, events):
        char = state["characters"]["ExternalTester"]
        self.assertEqual(set(char["gyms"]), {"Crasher Wake"})
        record = char["gyms"]["Crasher Wake"]
        self.assertEqual(record["payout"], 13572)
        self.assertEqual(char["earnings"]["events"][0]["leader"], "Crasher Wake")
        self.assertTrue(any("GYM WIN: Sinnoh / Pastoria" in text for _ts, text, _level in events))
        self.assertTrue(any("PAYOUT: Crasher Wake" in text for _ts, text, _level in events))

    def test_short_string_mod_name_wake_is_accepted(self):
        state, events = self.run_sequence("Wake")
        self.assert_canonical_pastoria_result(state, events)

    def test_full_name_crasher_wake_is_also_accepted(self):
        state, events = self.run_sequence("Crasher Wake")
        self.assert_canonical_pastoria_result(state, events)


if __name__ == "__main__":
    unittest.main()
