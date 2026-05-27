from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from src.utils import app_paths

IS_WINDOWS = os.name == "nt"
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform == "darwin"


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows-only path resolution")
def test_user_data_dir_windows_uses_appdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    result = app_paths.user_data_dir()
    assert result == tmp_path / "smiles2docking"


@pytest.mark.skipif(not IS_LINUX, reason="Linux-only path resolution")
def test_user_data_dir_linux_respects_xdg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    result = app_paths.user_data_dir()
    assert result == tmp_path / "smiles2docking"


@pytest.mark.skipif(not IS_LINUX, reason="Linux-only fallback")
def test_user_data_dir_linux_falls_back_to_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    result = app_paths.user_data_dir()
    assert result == Path.home() / ".local" / "share" / "smiles2docking"


def test_ensure_user_dirs_creates_writable_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    dirs = app_paths.ensure_user_dirs()

    for path in dirs.values():
        assert path.exists()
        assert os.access(str(path), os.W_OK)


def test_is_appimage_detects_env_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APPIMAGE", "/tmp/.mount_abc/SMILES2Docking.AppImage")
    assert app_paths.is_appimage() is True


def test_is_appimage_returns_false_when_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APPIMAGE", raising=False)
    assert isinstance(app_paths.is_appimage(), bool)
