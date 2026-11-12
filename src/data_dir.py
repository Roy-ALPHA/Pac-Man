"""Application data directory resolver for persistent storage."""

from pathlib import Path
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


LOGS_DIR = get_app_logs_dir()
DATA_DIR = get_app_data_dir()
