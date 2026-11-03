import sys
import os
from pathlib import Path

def get_app_data_dir(app_name: str = "pacman") -> Path:
    """Returns the platform-specific writable application directory."""
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or (Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = os.getenv("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    
    path = Path(base) / app_name
    path.mkdir(parents=True, exist_ok=True)
    return path

DATA_DIR = get_app_data_dir()