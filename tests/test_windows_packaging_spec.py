from __future__ import annotations

from pathlib import Path


def test_windows_spec_keeps_qt_runtime_files_next_to_exe() -> None:
    spec = Path("packaging/windows/smiles2docking.spec").read_text(encoding="utf-8")

    assert "pyinstaller_qt_runtime.py" in spec
    assert "packaging\" / \"qt.conf" in spec
    assert "qt_platforms_dir" in spec
    assert 'contents_directory="."' in spec
    assert '"vendor" / "mopac"' in spec


def test_windows_installer_places_mopac_in_default_path() -> None:
    installer = Path("installer/smiles2docking_setup.iss").read_text(encoding="utf-8")

    assert "PrivilegesRequired=admin" in installer
    assert 'Source: "..\\vendor\\mopac\\*"; DestDir: "{autopf}\\MOPAC\\bin"' in installer
    assert "C:\\Program Files\\MOPAC\\bin" in installer
