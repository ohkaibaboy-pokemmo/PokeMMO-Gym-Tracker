import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.constants import BUILTIN_ROUTES, GYMS
from tracker.core import canonical_leader
from tracker.earnings import GYM_BASE_PAYOUTS


class ReleaseContractTests(unittest.TestCase):
    def test_every_supported_gym_has_a_positive_base_payout(self):
        leaders = {canonical_leader(leader) for _region, _gym, leader in GYMS}
        self.assertEqual(leaders, set(GYM_BASE_PAYOUTS))
        for leader in leaders:
            self.assertGreater(GYM_BASE_PAYOUTS[leader], 0, leader)

    def test_builtin_routes_only_reference_supported_unique_leaders(self):
        supported = {canonical_leader(leader) for _region, _gym, leader in GYMS}
        for route_name, route in BUILTIN_ROUTES.items():
            canonical = [canonical_leader(leader) for leader in route]
            self.assertTrue(canonical, route_name)
            self.assertEqual(len(canonical), len(set(canonical)), f"duplicate gym in {route_name}")
            self.assertTrue(set(canonical).issubset(supported), route_name)

    def test_builtin_route_entries_all_have_payouts(self):
        for route_name, route in BUILTIN_ROUTES.items():
            for leader in route:
                canonical = canonical_leader(leader)
                self.assertIn(canonical, GYM_BASE_PAYOUTS, f"{route_name}: {leader}")

    def test_v060_startup_exposes_no_manual_state_mutation_feature(self):
        main_source = (APP / "main.pyw").read_text(encoding="utf-8")
        center_source = (APP / "tracker" / "dashboard_center_chrome.py").read_text(encoding="utf-8")
        manual_module = APP / "tracker" / "manual_correction_safety.py"

        self.assertFalse(manual_module.exists())
        self.assertNotIn("manual_correction_safety", main_source)
        self.assertNotIn("install_manual_correction", main_source)
        for label in ("Mark defeated", "Mark ready", "Forget"):
            self.assertNotIn(label, center_source)


if __name__ == "__main__":
    unittest.main()
