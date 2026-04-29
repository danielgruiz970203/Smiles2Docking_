from __future__ import annotations

import os
import sys
from pathlib import Path


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))


plugin_root = _bundle_root() / "PySide6" / "plugins"
platforms_dir = plugin_root / "platforms"

if platforms_dir.exists():
    os.environ.setdefault("QT_PLUGIN_PATH", str(plugin_root))
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platforms_dir))
    os.environ.setdefault("QT_QPA_PLATFORM", "windows")
