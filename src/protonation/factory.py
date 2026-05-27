from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.protonation.base import ProtonationError, Protonator
from src.protonation.dimorphite_adapter import DimorphiteProtonator
from src.protonation.openbabel_adapter import OpenBabelError, OpenBabelProtonator


@dataclass(slots=True)
class NullProtonator:
    """Pass-through backend used when protonation is disabled."""

    settings: dict[str, Any]
    backend_name: str = field(default="none", init=False)

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        return smiles


def build_protonator(settings: dict[str, Any]) -> Protonator:
    backend = str(settings.get("backend", "dimorphite")).strip().lower()
    if not settings.get("enabled", True):
        return NullProtonator(settings)
    if backend in {"dimorphite", "dimorphite_dl", "dimorphite-dl"}:
        return DimorphiteProtonator(settings)
    if backend in {"openbabel", "obabel", "ob"}:
        return OpenBabelProtonator(settings)
    if backend in {"none", "off"}:
        return NullProtonator(settings)
    raise ProtonationError(
        f"Unknown protonation backend '{backend}'. "
        "Supported backends: dimorphite, openbabel, none."
    )


__all__ = [
    "NullProtonator",
    "ProtonationError",
    "OpenBabelError",
    "build_protonator",
]
