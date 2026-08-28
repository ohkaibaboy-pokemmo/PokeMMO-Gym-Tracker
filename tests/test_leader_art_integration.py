import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.leader_art_integration import LeaderArtController


class LeaderArtIntegrationTests(unittest.TestCase):
    def test_presentation_theme_rebuild_hook_delegates_to_adopted_portraits(self):
        presentation = Mock()
        presentation._build_leader_images = Mock(name="legacy_fallback_builder")
        app = Mock()
        app._presentation = presentation

        with patch.object(LeaderArtController, "rebuild", autospec=True) as rebuild:
            controller = LeaderArtController(app)

            # Initial install builds the adopted art once.
            rebuild.assert_called_once_with(controller)

            # FullViewPresentation._after_theme_change() calls this hook. It must
            # now target LeaderArtController.rebuild rather than the old generic
            # theme-coloured fallback badge builder.
            presentation._build_leader_images()
            self.assertEqual(rebuild.call_count, 2)
            rebuild.assert_called_with(controller)


if __name__ == "__main__":
    unittest.main()
