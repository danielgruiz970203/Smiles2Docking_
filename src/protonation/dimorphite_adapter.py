from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rdkit import Chem

from src.protonation.base import ProtonationError


@dataclass(slots=True)
class DimorphiteProtonator:
    """Protonation backend using Dimorphite-DL.

    Dimorphite-DL applies SMARTS-based pKa rules that account for
    multiple ionizable centers and substituent effects, addressing
    limitations of the Open Babel `-p` mode that protonates every
    ionizable group independently.
    """

    settings: dict[str, Any]
    backend_name: str = field(default="dimorphite", init=False)

    def protonate_smiles(self, smiles: str, access_code: str) -> str:
        if not self.settings.get("enabled", True):
            return smiles

        try:
            from dimorphite_dl import DimorphiteDL
        except ImportError as exc:
            raise ProtonationError(
                "dimorphite_dl is not installed. Install it via `pip install dimorphite-dl` "
                "or switch the protonation backend to 'openbabel' in settings."
            ) from exc

        ph = float(self.settings.get("ph", 7.4))
        ph_tol = float(self.settings.get("ph_tolerance", 1.0))
        max_variants = int(self.settings.get("max_variants", 1))
        keep_label = str(self.settings.get("variant_selection", "first")).lower()

        engine = DimorphiteDL(
            min_ph=ph - ph_tol,
            max_ph=ph + ph_tol,
            max_variants=max_variants,
            label_states=False,
            pka_precision=float(self.settings.get("pka_precision", 1.0)),
        )

        try:
            variants = engine.protonate(smiles)
        except Exception as exc:
            raise ProtonationError(
                f"Dimorphite-DL failed to protonate {access_code!r}: {exc}"
            ) from exc

        if not variants:
            raise ProtonationError(f"Dimorphite-DL returned no variants for {access_code!r}")

        if keep_label == "most_neutral":
            chosen = min(variants, key=lambda smi: _abs_formal_charge(smi, access_code))
        else:
            chosen = variants[0]
        return chosen


def _abs_formal_charge(smiles: str, access_code: str) -> int:
    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise ProtonationError(f"Invalid SMILES emitted for {access_code!r}: {smiles}")
    return abs(Chem.GetFormalCharge(molecule))
