import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.async_replay import AsyncReplayController


class FakeVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeTailer:
    def __init__(self):
        self.paused = False
        self.current_path = Path("chat_live.log")


class ClosableIterator:
    def __init__(self, count):
        self.remaining = count
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining <= 0:
            raise StopIteration
        self.remaining -= 1
        return self.remaining

    def close(self):
        self.closed = True


class FakeEngine:
    def __init__(self, iterator):
        self.iterator = iterator
        self.paths = []

    def replay_iter(self, path):
        self.paths.append(Path(path))
        return self.iterator


class FakeApp:
    def __init__(self, iterator):
        self.engine = FakeEngine(iterator)
        self.tailer = FakeTailer()
        self.status_var = FakeVar("● Live — chat_live.log")
        self.state_data = {"log_folder": ""}
        self._replay_in_progress = False
        self.scheduled = []
        self.cancelled = []
        self.refresh_characters_calls = 0
        self.refresh_table_calls = 0

    def after(self, delay, callback):
        token = f"after-{len(self.scheduled) + 1}"
        self.scheduled.append((token, delay, callback))
        return token

    def after_cancel(self, token):
        self.cancelled.append(token)

    def refresh_characters(self):
        self.refresh_characters_calls += 1

    def refresh_table(self):
        self.refresh_table_calls += 1


class AsyncReplayControllerTests(unittest.TestCase):
    def test_replay_runs_in_bounded_batches_and_restores_live_state(self):
        iterator = ClosableIterator(AsyncReplayController.BATCH_LINES + 1)
        app = FakeApp(iterator)
        controller = AsyncReplayController(app)

        with patch("tracker.async_replay.messagebox.showinfo") as showinfo:
            self.assertTrue(controller.start(Path("chat_history.log")))
            self.assertTrue(controller.running)
            self.assertTrue(app._replay_in_progress)
            self.assertTrue(app.tailer.paused)
            self.assertEqual(app.status_var.get(), "Replaying — chat_history.log")
            self.assertEqual(app.scheduled[0][1], 0)

            # First callback consumes exactly one bounded batch and yields back to Tk.
            _token, _delay, callback = app.scheduled.pop(0)
            callback()
            self.assertTrue(controller.running)
            self.assertTrue(app.tailer.paused)
            self.assertEqual(iterator.remaining, 1)
            self.assertEqual(app.scheduled[0][1], AsyncReplayController.BATCH_DELAY_MS)

            # Second callback reaches EOF and performs the normal completion path.
            _token, _delay, callback = app.scheduled.pop(0)
            callback()

        self.assertFalse(controller.running)
        self.assertFalse(app._replay_in_progress)
        self.assertFalse(app.tailer.paused)
        self.assertEqual(app.status_var.get(), "● Live — chat_live.log")
        self.assertEqual(app.refresh_characters_calls, 1)
        self.assertEqual(app.refresh_table_calls, 1)
        showinfo.assert_called_once()

    def test_replay_failure_resumes_live_tailer_and_reports_error(self):
        class FailingIterator:
            def __iter__(self):
                return self

            def __next__(self):
                raise RuntimeError("boom")

            def close(self):
                pass

        app = FakeApp(FailingIterator())
        controller = AsyncReplayController(app)
        controller.start(Path("chat_bad.log"))
        _token, _delay, callback = app.scheduled.pop(0)

        with patch("tracker.async_replay.messagebox.showerror") as showerror:
            callback()

        self.assertFalse(controller.running)
        self.assertFalse(app._replay_in_progress)
        self.assertFalse(app.tailer.paused)
        self.assertEqual(app.status_var.get(), "● Live — chat_live.log")
        self.assertEqual(app.refresh_characters_calls, 1)
        self.assertEqual(app.refresh_table_calls, 1)
        self.assertIn("boom", showerror.call_args.args[1])

    def test_close_cancels_pending_batch_and_closes_iterator(self):
        iterator = ClosableIterator(500)
        app = FakeApp(iterator)
        controller = AsyncReplayController(app)
        controller.start(Path("chat_long.log"))
        scheduled_token = controller._after_id

        controller.close()

        self.assertFalse(controller.running)
        self.assertFalse(app._replay_in_progress)
        self.assertFalse(app.tailer.paused)
        self.assertTrue(iterator.closed)
        self.assertIn(scheduled_token, app.cancelled)

    def test_second_start_is_rejected_while_replay_is_running(self):
        iterator = ClosableIterator(500)
        app = FakeApp(iterator)
        controller = AsyncReplayController(app)

        self.assertTrue(controller.start(Path("first.log")))
        self.assertFalse(controller.start(Path("second.log")))
        self.assertEqual(app.engine.paths, [Path("first.log")])


if __name__ == "__main__":
    unittest.main()
