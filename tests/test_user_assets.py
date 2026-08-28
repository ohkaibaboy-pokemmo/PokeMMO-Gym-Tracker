import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.user_assets import application_directory, custom_asset_directory


class UserAssetPathTests(unittest.TestCase):
    def test_frozen_app_uses_executable_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "PokeMMO Gym Tracker.exe"
            self.assertEqual(
                application_directory(frozen=True, executable=exe),
                Path(temp).resolve(),
            )

    def test_source_run_uses_launched_script_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "app" / "main.pyw"
            self.assertEqual(
                application_directory(frozen=False, argv0=script),
                script.resolve().parent,
            )

    def test_custom_asset_directory_is_beside_app(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.assertEqual(
                custom_asset_directory("type_icons", base_directory=base),
                base / "custom" / "type_icons",
            )
            self.assertEqual(
                custom_asset_directory("leader_sprites", base_directory=base),
                base / "custom" / "leader_sprites",
            )


if __name__ == "__main__":
    unittest.main()
