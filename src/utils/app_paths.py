from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "smiles2docking"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def is_appimage() -> bool:
    return bool(os.environ.get("APPIMAGE")) or "/.mount_" in str(Path(__file__).resolve())


def user_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def user_cache_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME / "cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / APP_NAME
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / APP_NAME


def user_log_dir() -> Path:
    if os.name == "nt":
        return user_data_dir() / "logs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / APP_NAME
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / APP_NAME / "logs"


def ensure_user_dirs() -> dict[str, Path]:
    dirs = {
        "data": user_data_dir(),
        "cache": user_cache_dir(),
        "logs": user_log_dir(),
        "processed": user_data_dir() / "processed",
        "reports": user_data_dir() / "reports",
        "intermediate": user_cache_dir() / "intermediate",
        "protonation_tmp": user_cache_dir() / "intermediate" / "protonation",
        "export_tmp": user_cache_dir() / "intermediate" / "export",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs
