from .dashboard_detector import (
    detector_content_height,
    detector_row_gap,
    detector_row_height,
)


_REPLAY_STARTED_PREFIX = "Replay started: "
_REPLAY_COMPLETE_PREFIX = "Replay complete: "
_REPLAY_FAILED_PREFIX = "Replay failed: "

# Keep Canvas scrolling pixel-addressable. Using the row height itself as Tk's
# yscrollincrement makes yview_moveto()/thumb dragging snap the viewport origin to
# row-sized multiples. After a UI-scale change the viewport/content sizes rarely
# divide evenly by that increment, so the snapped bottom can overshoot the real
# scrollregion and expose a blank strip below the newest Detector event.
DETECTOR_PIXEL_SCROLL_INCREMENT = 1


def detector_scroll_step(factor=1.0):
    """Return one visual Detector row step for mouse-wheel scrolling."""
    return detector_row_height(factor) + detector_row_gap(factor)


def replay_started_filename(text):
    """Return the replay filename from a Detector lifecycle message, if present."""
    text = str(text or "")
    if not text.startswith(_REPLAY_STARTED_PREFIX):
        return None
    filename = text[len(_REPLAY_STARTED_PREFIX) :].strip()
    return filename or None


def _is_replay_end(text, filename):
    text = str(text or "")
    if text == f"{_REPLAY_COMPLETE_PREFIX}{filename}":
        return True
    return text.startswith(f"{_REPLAY_FAILED_PREFIX}{filename}")


def without_completed_replay_sessions(events, filename):
    """Remove older completed/failed presentation sessions for one replay file.

    Persistent tracker state is already de-duplicated by TrackerEngine. Detector is
    presentation history, so replaying the same file again should replace its old
    replay block rather than append an identical second copy. Incomplete sessions
    are deliberately retained because there is no safe end boundary to remove.
    """
    filename = str(filename or "").strip()
    if not filename:
        return list(events or ())

    source = list(events or ())
    remove = set()
    index = 0
    start_text = f"{_REPLAY_STARTED_PREFIX}{filename}"

    while index < len(source):
        text = str(source[index].get("text", ""))
        if text != start_text:
            index += 1
            continue

        end = None
        for candidate in range(index + 1, len(source)):
            if _is_replay_end(source[candidate].get("text", ""), filename):
                end = candidate
                break
        if end is None:
            index += 1
            continue

        remove.update(range(index, end + 1))
        index = end + 1

    return [event for pos, event in enumerate(source) if pos not in remove]


def detector_bottom_offset(event_count, viewport_height, factor=1.0):
    """Bottom-anchor a short Detector history inside its fixed viewport."""
    try:
        viewport = max(1, int(viewport_height))
    except (TypeError, ValueError):
        viewport = 1
    if not event_count:
        return 0
    content = detector_content_height(event_count, factor)
    return max(0, viewport - content)


def install_dashboard_detector_polish(app):
    """Polish replay presentation, short histories and Detector scrolling."""
    detector = getattr(app, "_dashboard_detector", None)
    if detector is None or getattr(detector, "_replay_polish_installed", False):
        return detector

    original_render = detector._render

    def polished_render(scroll_latest=False):
        canvas = detector.body_canvas
        try:
            old_view = canvas.yview()
            was_at_bottom = bool(old_view and old_view[1] >= 0.999)
        except Exception:
            was_at_bottom = False

        result = original_render(scroll_latest=scroll_latest)
        if not detector.events:
            try:
                canvas.configure(yscrollincrement=DETECTOR_PIXEL_SCROLL_INCREMENT)
            except Exception:
                pass
            return result

        try:
            viewport = max(1, int(canvas.winfo_height()))
            width = max(1, int(canvas.winfo_width()))
        except Exception:
            return result

        # Pixel-addressable scrolling prevents Tk from snapping the bottom edge to
        # a scale-dependent row multiple and exposing blank Canvas below history.
        try:
            canvas.configure(yscrollincrement=DETECTOR_PIXEL_SCROLL_INCREMENT)
        except Exception:
            pass

        offset = detector_bottom_offset(len(detector.events), viewport, detector.factor)
        if offset:
            # A short recent-history list should end at the bottom of the Detector,
            # like a normal activity/chat timeline. This removes the misleading blank
            # slot below the newest event without inventing fake log entries.
            try:
                canvas.move("all", 0, offset)
                detector._content_height = viewport
                canvas.configure(scrollregion=(0, 0, width, viewport))
                canvas.yview_moveto(0.0)
            except Exception:
                pass
            return result

        # Scaling rebuilds the row geometry. If the user was already following the
        # newest event, keep that semantic position rather than preserving the old
        # fractional top edge against a differently-sized scrollregion. Schedule it
        # after the original renderer's own view-restoration callback so bottom wins.
        if was_at_bottom or scroll_latest:
            try:
                detector.app.after_idle(lambda: canvas.yview_moveto(1.0))
            except Exception:
                pass
        return result

    detector._render = polished_render

    # The original Detector wheel callback scrolls one Tk "unit" and relied on a
    # row-sized yscrollincrement. We now keep the Canvas increment at one pixel, so
    # explicitly scroll one rendered row+gap per wheel notch instead.
    def polished_mousewheel(event):
        try:
            units = int(-1 * (event.delta / 120))
            if units:
                detector.body_canvas.yview_scroll(
                    units * detector_scroll_step(detector.factor),
                    "units",
                )
        except Exception:
            pass
        return "break"

    try:
        detector.body_canvas.bind("<MouseWheel>", polished_mousewheel)
    except Exception:
        pass

    original_add_event = detector.add_event

    def add_event_with_replay_replacement(ts, text, level="info"):
        filename = replay_started_filename(text)
        if filename:
            detector.events = without_completed_replay_sessions(detector.events, filename)
        return original_add_event(ts, text, level)

    detector.add_event = add_event_with_replay_replacement
    detector._replay_polish_installed = True
    detector._render()
    return detector
