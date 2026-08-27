"""
Path resolution utilities for AetherClean.
Ensures seamless resource resolution in development and PyInstaller frozen executable modes.
"""

import sys
import os


def get_base_dir() -> str:
    """
    Returns the root directory of the application.
    Supports development mode, standard pip packages, and PyInstaller frozen .exe bundles.
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # 2 levels up from core/
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_path(relative_path: str = "config") -> str:
    """
    Returns the absolute path to a configuration file or directory.
    Checks bundled resources (_MEIPASS) and executable-local overrides.
    """
    base = get_base_dir()
    primary = os.path.join(base, relative_path)
    if os.path.exists(primary):
        return primary

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        secondary = os.path.join(exe_dir, relative_path)
        if os.path.exists(secondary):
            return secondary

    return primary
