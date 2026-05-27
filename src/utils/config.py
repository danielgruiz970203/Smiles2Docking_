from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from src.utils.app_paths import is_appimage, is_frozen, user_data_dir


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"

WRITABLE_PATH_KEYS: tuple[tuple[str, str, str], ...] = (
    ("export", "output_dir", "processed"),
    ("export", "temp_dir", "intermediate/export"),
    ("reporting", "report_dir", "reports"),
    ("figures", "output_dir", "figures"),
    ("logging", "log_dir", "logs"),
    ("protonation", "temp_dir", "intermediate/protonation"),
)


def load_settings(config_path: str | None = None) -> dict[str, Any]:
    target = Path(config_path) if config_path else DEFAULT_SETTINGS_PATH
    with target.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def merge_settings(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged


def _is_writable_location(path: Path) -> bool:
    candidate = path if path.exists() else path.parent
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return os.access(str(candidate), os.W_OK)


def resolve_project_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        return str(path)

    if is_frozen() or is_appimage():
        return str(user_data_dir() / path)

    candidate = PROJECT_ROOT / path
    if _is_writable_location(candidate):
        return str(candidate)
    return str(user_data_dir() / path)


def resolve_settings_paths(settings: dict[str, Any]) -> dict[str, Any]:
    input_path = settings.get("input", {}).get("file_path")
    if input_path:
        input_obj = Path(input_path)
        if not input_obj.is_absolute():
            settings.setdefault("input", {})["file_path"] = str(PROJECT_ROOT / input_obj)

    for section, key, fallback_subdir in WRITABLE_PATH_KEYS:
        section_dict = settings.setdefault(section, {})
        value = section_dict.get(key)
        if value:
            resolved = resolve_project_path(value)
        else:
            resolved = str(user_data_dir() / fallback_subdir)
        section_dict[key] = resolved
        try:
            Path(resolved).mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback = user_data_dir() / fallback_subdir
            fallback.mkdir(parents=True, exist_ok=True)
            section_dict[key] = str(fallback)

    export_output_dir = settings.get("export", {}).get("output_dir")
    if export_output_dir:
        if settings.get("reporting", {}).get("use_output_dir", False):
            settings.setdefault("reporting", {})["report_dir"] = export_output_dir
        if settings.get("logging", {}).get("use_output_dir", False):
            settings.setdefault("logging", {})["log_dir"] = export_output_dir
    return settings
