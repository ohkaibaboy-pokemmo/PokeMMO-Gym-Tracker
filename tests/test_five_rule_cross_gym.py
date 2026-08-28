import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.engine import TrackerEngine
from tracker.state import default_state


class CrossGymFiveRuleTests(unittest.TestCase):
    def setUp(self):
        self.state = default_state()
        self.engine = TrackerEngine(self.state, save_callback=lambda _state: None)

    def feed(self, *lines):
        for line in lines:
            self.engine.process_line(line + "\n")

    def test_different_gym_leader_counts_for_existing_gym_but_new_gym_starts_at_zero(self):
        self.feed(
            "[23/08/2026 15:00:00] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:00:05] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:02:00] [Battle] Player defeated Leader Brock!",
            "[23/08/2026 15:02:05] [Battle] TestCharacter got $8632 for winning!",
            "[23/08/2026 15:10:00] [Battle] You are challenged by Leader Misty!",
            "[23/08/2026 15:10:05] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:12:00] [Battle] Player defeated Leader Misty!",
            "[23/08/2026 15:12:05] [Battle] TestCharacter got $8736 for winning!",
        )

        gyms = self.state["characters"]["TestCharacter"]["gyms"]
        self.assertEqual(gyms["Brock"]["other_trainers"], 1)
        self.assertEqual(gyms["Brock"]["qualifying_events"][0]["opponent"], "Leader Misty")
        self.assertEqual(gyms["Misty"]["other_trainers"], 0)
        self.assertEqual(gyms["Misty"]["qualifying_events"], [])


if __name__ == "__main__":
    unittest.main()
