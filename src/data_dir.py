"""Application data directory resolver for persistent storage."""

from pathlib import Path
import sys
from platformdirs import user_data_dir, user_log_dir


def get_app_data_dir(app_name: str = "pacman") -> Path:
    """Return the platform-specific writable application directory.

    Args:
        app_name: Name of the application directory.

    Returns:
        Path: Absolute path to the directory, created if non-existent.
    """
    path = Path(user_data_dir(appname=app_name, appauthor=False))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_app_logs_dir(app_name: str = "pacman") -> Path:
    """Return the platform-specific writable application log directory.

    Args:
        app_name: Name of the application directory.

    Returns:
        Path: Absolute path to the directory, created if non-existent.
    """
    path = Path(user_log_dir(appname=app_name, appauthor=False))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_assets_dir() -> Path:

    """Resolve the assets directory for both terminal and executable."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).parent.parent

    candidate = base / "assets"
    if candidate.is_dir():
        return candidate
    return base / "assets"


ASSETS_DIR = get_assets_dir()
LOGS_DIR = get_app_logs_dir()
DATA_DIR = get_app_data_dir()
