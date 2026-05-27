from __future__ import annotations

from typing import Protocol


class ProtonationError(Exception):
    """Raised when a protonation backend fails."""


class Protonator(Protocol):
    backend_name: str

    def protonate_smiles(self, smiles: str, access_code: str) -> str: ...
