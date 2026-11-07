"""Application data directory resolver for persistent storage."""

import os
from pathlib import Path
import sys


def get_app_data_dir(app_name: str = "pacman") -> Path:
    """Return the platform-specific writable application directory.

    Args:
        app_name: Name of the application directory.

    Returns:
        Path: Absolute path to the directory, created if non-existent.
    """
    if sys.platform == "win32":
        local_app = os.getenv("LOCALAPPDATA")
        app_data = os.getenv("APPDATA")
        default_win = Path.home() / "AppData" / "Local"
        base: str | Path = local_app or app_data or default_win
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        xdg_data = os.getenv("XDG_DATA_HOME")
        default_linux = Path.home() / ".local" / "share"
        base = xdg_data or default_linux

    path = Path(base) / app_name
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = get_app_data_dir()
