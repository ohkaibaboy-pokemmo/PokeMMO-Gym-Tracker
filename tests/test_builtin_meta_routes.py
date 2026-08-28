import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.constants import (
    BUILTIN_ROUTES,
    DISPLAY_MODES,
    PREHISTORIC_5_MAIN_ROUTE,
    PREHISTORIC_5_MAIN_ROUTE_NAME,
)


class BuiltinMetaRouteTests(unittest.TestCase):
    def test_prehistoric_main_is_exact_28_gym_preset(self):
        self.assertEqual(len(PREHISTORIC_5_MAIN_ROUTE), 28)
        self.assertEqual(PREHISTORIC_5_MAIN_ROUTE[:5], [
            "Flannery", "Wattson", "Winona", "Brawly", "Norman"
        ])
        self.assertEqual(PREHISTORIC_5_MAIN_ROUTE[-4:], [
            "Lt. Surge", "Brock", "Misty", "Erika"
        ])
        self.assertEqual(BUILTIN_ROUTES[PREHISTORIC_5_MAIN_ROUTE_NAME], PREHISTORIC_5_MAIN_ROUTE)

    def test_known_only_is_not_a_duplicate_display_mode(self):
        self.assertNotIn("Known only", DISPLAY_MODES)


if __name__ == "__main__":
    unittest.main()
