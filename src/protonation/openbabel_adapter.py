from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.utils.runtime import bundled_obabel_binary, openbabel_runtime_env


class OpenBabelError(Exception):
    """Raised when Open Babel execution fails."""


def _subprocess_kwargs() -> dict[str, Any]:
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


@dataclass(slots=True)
class OpenBabelProtonator:
    settings: dict[str, Any]
    backend_name: str = field(default="openbabel", init=False)

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        if not self.settings.get("enabled", True):
            return smiles

        ph = str(self.settings.get("ph", 7.4))
        obabel_binary = bundled_obabel_binary(self.settings.get("obabel_binary", "obabel"))
        temp_root = self.settings.get("temp_dir")
        if temp_root:
            base_dir = Path(temp_root)
            base_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = base_dir / f"job_{uuid.uuid4().hex}"
        else:
            tmp_path = Path.cwd() / f"obabel_tmp_{uuid.uuid4().hex}"
        tmp_path.mkdir(parents=True, exist_ok=True)

        try:
            input_path = tmp_path / "input.smi"
            output_path = tmp_path / "output.smi"
            input_path.write_text(f"{smiles}\t{access_code}\n", encoding="utf-8")

            command = [
                obabel_binary,
                str(input_path),
                "-O",
                str(output_path),
                "-p",
                ph,
            ]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                env=openbabel_runtime_env(),
                **_subprocess_kwargs(),
            )
            if result.returncode != 0:
                raise OpenBabelError(result.stderr.strip() or result.stdout.strip() or "Unknown Open Babel error.")

            lines = [line.strip() for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                raise OpenBabelError(f"Open Babel returned no protonated SMILES for {access_code!r}")
            return lines[0].split()[0]
        finally:
            shutil.rmtree(tmp_path, ignore_errors=True)


@dataclass(slots=True)
class OpenBabelConverter:
    settings: dict[str, Any]

    def sdf_to_mol2(self, input_sdf: Path, output_mol2: Path) -> None:
        obabel_binary = bundled_obabel_binary(self.settings.get("obabel_binary", "obabel"))
        command = [obabel_binary, str(input_sdf), "-O", str(output_mol2)]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=openbabel_runtime_env(),
            **_subprocess_kwargs(),
        )
        if result.returncode != 0:
            raise OpenBabelError(result.stderr.strip() or result.stdout.strip() or "Unknown Open Babel error.")
