import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.constants import GYMS
from tracker.dashboard_gym_list import GYM_TYPES, TYPE_MARKERS, gym_type_for_leader
from tracker.type_icon_overrides import type_icon_filename, type_icon_path


class GymTypeMarkerTests(unittest.TestCase):
    def test_every_supported_gym_leader_has_a_type_marker(self):
        leaders = {leader for _region, _gym, leader in GYMS}
        self.assertEqual(leaders, set(GYM_TYPES))
        for leader in leaders:
            gym_type = gym_type_for_leader(leader)
            self.assertTrue(gym_type, leader)
            self.assertIn(gym_type, TYPE_MARKERS)

    def test_representative_gym_types_are_correct(self):
        self.assertEqual(gym_type_for_leader("Brock"), "Rock")
        self.assertEqual(gym_type_for_leader("Misty"), "Water")
        self.assertEqual(gym_type_for_leader("Lt. Surge"), "Electric")
        self.assertEqual(gym_type_for_leader("Tate & Liza"), "Psychic")
        self.assertEqual(gym_type_for_leader("Clay"), "Ground")
        self.assertEqual(gym_type_for_leader("Iris"), "Dragon")

    def test_unknown_leader_returns_no_marker(self):
        self.assertEqual(gym_type_for_leader("Missing"), "")
        self.assertEqual(gym_type_for_leader(None), "")

    def test_type_icon_override_filenames_are_stable_and_type_scoped(self):
        self.assertEqual(type_icon_filename("Rock"), "rock.png")
        self.assertEqual(type_icon_filename("Water"), "water.png")
        self.assertEqual(type_icon_filename("Electric"), "electric.png")
        self.assertEqual(type_icon_filename("Psychic"), "psychic.png")
        self.assertEqual(type_icon_filename(""), "")

    def test_type_icon_path_uses_supplied_override_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            self.assertEqual(type_icon_path(directory, "Dragon"), directory / "dragon.png")
            self.assertIsNone(type_icon_path(directory, ""))


if __name__ == "__main__":
    unittest.main()
