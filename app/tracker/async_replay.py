from pathlib import Path
from tkinter import filedialog, messagebox

from .constants import APP_NAME


class AsyncReplayController:
    """Replay large chat logs in short Tk batches instead of blocking the UI.

    ``TrackerEngine.replay_iter`` owns the actual replay semantics. This controller
    only advances that iterator a little at a time with ``after`` so Windows keeps
    servicing paint/focus/mouse messages and does not label the app Not Responding.
    """

    BATCH_LINES = 120
    BATCH_DELAY_MS = 1

    def __init__(self, app):
        self.app = app
        self.iterator = None
        self.path = None
        self.previous_status = None
        self._after_id = None

    @property
    def running(self):
        return self.iterator is not None

    def replay_log(self):
        if self.running:
            messagebox.showinfo(APP_NAME, "A log replay is already in progress.", parent=self.app)
            return

        initial = self.app.state_data.get("log_folder") or str(Path.home())
        path = filedialog.askopenfilename(
            title="Replay a PokeMMO chat log",
            initialdir=initial,
            filetypes=[
                ("PokeMMO chat logs", "chat*.log"),
                ("PokeMMO logs", "*.log"),
                ("All files", "*.*"),
            ],
            parent=self.app,
        )
        if not path:
            return
        self.start(Path(path))

    def start(self, path):
        if self.running:
            return False

        self.path = Path(path)
        self.previous_status = str(self.app.status_var.get() or "")
        self.iterator = self.app.engine.replay_iter(self.path)
        self.app._replay_in_progress = True
        if self.app.tailer is not None:
            self.app.tailer.paused = True
        self.app.status_var.set(f"Replaying — {self.path.name}")
        self._schedule_step(0)
        return True

    def _schedule_step(self, delay=None):
        if delay is None:
            delay = self.BATCH_DELAY_MS
        try:
            self._after_id = self.app.after(delay, self._step)
        except Exception:
            self._after_id = None

    def _step(self):
        self._after_id = None
        iterator = self.iterator
        if iterator is None:
            return

        try:
            for _unused in range(self.BATCH_LINES):
                next(iterator)
        except StopIteration:
            self._finish(success=True)
            return
        except Exception as exc:
            self._finish(success=False, error=exc)
            return

        # Give Tk/Windows a chance to paint, process focus changes and accept user
        # input before parsing the next batch.
        self._schedule_step()

    def _restore_live_status(self):
        tailer = self.app.tailer
        if tailer is not None and tailer.current_path is not None:
            self.app.status_var.set(f"● Live — {tailer.current_path.name}")
        else:
            self.app.status_var.set(self.previous_status or "Not connected")

    def _finish(self, success, error=None):
        self.iterator = None
        self.path = None
        self.app._replay_in_progress = False
        if self.app.tailer is not None:
            self.app.tailer.paused = False
        self._restore_live_status()

        # One final model refresh is sufficient after the incremental parser has
        # completed. Existing engine callbacks still update state during replay.
        try:
            self.app.refresh_characters()
            self.app.refresh_table()
        except Exception:
            pass

        if success:
            messagebox.showinfo(
                APP_NAME,
                "Replay complete. Previously processed victories are automatically de-duplicated.",
                parent=self.app,
            )
        else:
            messagebox.showerror(
                APP_NAME,
                f"Could not replay log:\n{error}",
                parent=self.app,
            )

        self.previous_status = None

    def close(self):
        if self._after_id is not None:
            try:
                self.app.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        iterator = self.iterator
        self.iterator = None
        if iterator is not None:
            try:
                iterator.close()
            except Exception:
                pass
        self.app._replay_in_progress = False
        if self.app.tailer is not None:
            self.app.tailer.paused = False


def install_async_replay(app):
    existing = getattr(app, "_async_replay", None)
    if existing is not None:
        return existing

    controller = AsyncReplayController(app)
    app._async_replay = controller

    # Dashboard controls are created after this installer runs, so they bind to
    # the responsive replay method rather than App.replay_log's synchronous legacy
    # implementation. The old method remains available on the class for rollback.
    app.replay_log = controller.replay_log

    # Make closing during a replay deterministic: cancel the pending batch and
    # close the generator so TrackerEngine restores its replaying flag in finally.
    original_close = app.on_close

    def close_with_replay_cleanup():
        controller.close()
        return original_close()

    app.on_close = close_with_replay_cleanup
    try:
        app.protocol("WM_DELETE_WINDOW", app.on_close)
    except Exception:
        pass

    return controller
