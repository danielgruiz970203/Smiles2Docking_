from __future__ import annotations

import pytest

from src.protonation.factory import (
    NullProtonator,
    ProtonationError,
    build_protonator,
)
from src.protonation.openbabel_adapter import OpenBabelProtonator


def test_build_returns_null_when_disabled() -> None:
    protonator = build_protonator({"enabled": False, "backend": "dimorphite"})
    assert isinstance(protonator, NullProtonator)
    assert protonator.backend_name == "none"
    assert protonator.protonate_smiles("CC(=O)O", "ACID") == "CC(=O)O"


def test_build_returns_openbabel() -> None:
    protonator = build_protonator(
        {"enabled": True, "backend": "openbabel", "ph": 7.4, "obabel_binary": "obabel"}
    )
    assert isinstance(protonator, OpenBabelProtonator)
    assert protonator.backend_name == "openbabel"


def test_build_rejects_unknown_backend() -> None:
    with pytest.raises(ProtonationError):
        build_protonator({"enabled": True, "backend": "magic-pka"})


def test_build_default_backend_is_dimorphite() -> None:
    protonator = build_protonator({"enabled": True, "ph": 7.4})
    assert protonator.backend_name == "dimorphite"


def test_null_protonator_is_identity() -> None:
    protonator = NullProtonator({})
    assert protonator.protonate_smiles("Cc1ccccc1N", "X") == "Cc1ccccc1N"
