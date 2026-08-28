import tempfile
import unittest
from pathlib import Path


class DummyEngine:
    def __init__(self):
        self.lines = []
        self.events = []

    def process_line(self, line):
        self.lines.append(line)

    def emit(self, ts, text, level):
        self.events.append((ts, text, level))


class ChatLiveTailerTests(unittest.TestCase):
    def setUp(self):
        import sys
        root = Path(__file__).resolve().parents[1]
        app = root / "app"
        if str(app) not in sys.path:
            sys.path.insert(0, str(app))
        from tracker.logs import ChatLiveTailer
        self.ChatLiveTailer = ChatLiveTailer

    def test_stable_unterminated_eof_record_is_processed_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            path = folder / "chat_test.log"
            path.write_text("existing\n", encoding="utf-8")
            engine = DummyEngine()
            tailer = self.ChatLiveTailer(folder, engine)
            tailer.switch_to(path)

            payout = "[28/08/2026 13:49:34] [Battle] [#ff8a00]OhKaibaBoi[#] got $[#ff8a00]6000[#] for winning!"
            with path.open("a", encoding="utf-8", newline="") as handle:
                handle.write(payout)
                handle.flush()

            tailer.poll()
            self.assertEqual(engine.lines, [])

            tailer.poll()
            self.assertEqual(engine.lines, [payout])

            with path.open("a", encoding="utf-8", newline="") as handle:
                handle.write("\n")
                handle.flush()

            tailer.poll()
            self.assertEqual(engine.lines, [payout])

    def test_growing_partial_record_waits_for_completed_line(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            path = folder / "chat_test.log"
            path.write_text("existing\n", encoding="utf-8")
            engine = DummyEngine()
            tailer = self.ChatLiveTailer(folder, engine)
            tailer.switch_to(path)

            first = "[28/08/2026 13:49:34] [Battle] OhKaibaBoi got $60"
            rest = "00 for winning!\n"
            with path.open("a", encoding="utf-8", newline="") as handle:
                handle.write(first)
                handle.flush()

            tailer.poll()
            self.assertEqual(engine.lines, [])

            with path.open("a", encoding="utf-8", newline="") as handle:
                handle.write(rest)
                handle.flush()

            tailer.poll()
            self.assertEqual(engine.lines, [first + rest])


if __name__ == "__main__":
    unittest.main()
