"""Application data directory resolver for persistent storage."""

from __future__ import annotations

from pathlib import Path
from platformdirs import user_data_dir


def get_app_data_dir(app_name: str = "pacman") -> Path:
    """Return the platform-specific writable application directory.

    Args:
        app_name: Name of the application directory.

    Returns:
        Path: Absolute path to the directory, created if non-existent.
    """
    path = Path(user_data_dir(appname=app_name))
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = get_app_data_dir()
