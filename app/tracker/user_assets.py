import sys
from pathlib import Path


CUSTOM_DIRNAME = "custom"


def application_directory(*, frozen=None, executable=None, argv0=None):
    """Return the directory that owns the running app/EXE.

    Frozen Windows builds use ``sys.executable`` so user-facing custom assets can
    live beside ``PokeMMO Gym Tracker.exe``. Source runs use the launched script's
    directory, which keeps development behaviour predictable without touching
    LocalAppData.
    """
    if frozen is None:
        frozen = bool(getattr(sys, "frozen", False))

    if frozen:
        candidate = executable or sys.executable
    else:
        candidate = argv0 or (sys.argv[0] if sys.argv else "")

    try:
        path = Path(candidate).expanduser().resolve()
    except (OSError, RuntimeError, TypeError, ValueError):
        return Path.cwd().resolve()

    if path.name:
        return path.parent
    return Path.cwd().resolve()


def custom_asset_directory(name, *, base_directory=None):
    """Return one user-facing custom asset folder beside the app/EXE."""
    base = Path(base_directory) if base_directory is not None else application_directory()
    return base / CUSTOM_DIRNAME / str(name)
