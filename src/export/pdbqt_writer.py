from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rdkit import Chem
from rdkit.Chem import AllChem


class PDBQTExportError(Exception):
    """Raised when PDBQT export fails."""


@dataclass(slots=True)
class PDBQTWriter:
    """Writes RDKit molecules to AutoDock-compatible PDBQT.

    Uses Meeko (Scripps Research) which is the maintained reference
    implementation for AutoDock Vina / AutoDock-GPU ligand preparation.
    Meeko preserves molecular topology (no fragmentation) and assigns
    Gasteiger charges and atom types in a single pass.
    """

    settings: dict[str, Any]

    def __post_init__(self) -> None:
        try:
            from meeko import MoleculePreparation  # noqa: F401
        except ImportError as exc:
            raise PDBQTExportError(
                "meeko is not installed. Install it via `pip install meeko>=0.5` "
                "to enable PDBQT export."
            ) from exc

    def write_one(self, molecule: Chem.Mol, output_path: Path, access_code: str) -> Path:
        pdbqt_string = self._to_pdbqt_string(molecule, access_code)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(pdbqt_string, encoding="utf-8")
        return output_path

    def write_batch(self, molecules: list[tuple[str, Chem.Mol]], output_path: Path) -> Path:
        chunks: list[str] = []
        for access_code, molecule in molecules:
            pdbqt_string = self._to_pdbqt_string(molecule, access_code)
            chunks.append(pdbqt_string.rstrip())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(chunks) + "\n", encoding="utf-8")
        return output_path

    def _to_pdbqt_string(self, molecule: Chem.Mol, access_code: str) -> str:
        from meeko import MoleculePreparation, PDBQTWriterLegacy

        prepared = self._prepare_molecule(molecule, access_code)

        prep_kwargs: dict[str, Any] = {
            "charge_model": str(self.settings.get("charge_model", "gasteiger")),
        }
        if self.settings.get("rigid", False):
            prep_kwargs["rigid_macrocycles"] = True
        if self.settings.get("keep_nonpolar_hydrogens", False):
            prep_kwargs["merge_these_atom_types"] = ()
        else:
            prep_kwargs["merge_these_atom_types"] = ("H",)

        try:
            preparator = MoleculePreparation(**prep_kwargs)
            mol_setups = preparator.prepare(prepared)
        except Exception as exc:
            raise PDBQTExportError(
                f"Meeko preparation failed for {access_code!r}: {exc}"
            ) from exc

        if not mol_setups:
            raise PDBQTExportError(f"Meeko returned no setups for {access_code!r}")

        pdbqt_string, is_ok, error_msg = PDBQTWriterLegacy.write_string(mol_setups[0])
        if not is_ok or not pdbqt_string:
            raise PDBQTExportError(
                f"Meeko could not write PDBQT for {access_code!r}: {error_msg or 'unknown error'}"
            )
        return _stamp_name(pdbqt_string, access_code)

    def _prepare_molecule(self, molecule: Chem.Mol, access_code: str) -> Chem.Mol:
        working = Chem.Mol(molecule)

        fragments = Chem.GetMolFrags(working, asMols=True, sanitizeFrags=True)
        if not fragments:
            raise PDBQTExportError(f"No fragments left for {access_code!r}")
        if len(fragments) > 1:
            working = max(fragments, key=lambda frag: frag.GetNumHeavyAtoms())

        if self.settings.get("add_hydrogens", True):
            if not any(atom.GetAtomicNum() == 1 for atom in working.GetAtoms()):
                working = Chem.AddHs(working, addCoords=True)

        if working.GetNumConformers() == 0:
            params = AllChem.ETKDGv3()
            params.randomSeed = 61453
            if AllChem.EmbedMolecule(working, params) != 0:
                raise PDBQTExportError(
                    f"3D embedding required for PDBQT but failed for {access_code!r}"
                )
            AllChem.MMFFOptimizeMolecule(working, maxIters=200)

        try:
            Chem.SanitizeMol(working)
        except Exception as exc:
            raise PDBQTExportError(
                f"Could not sanitize molecule for PDBQT export ({access_code!r}): {exc}"
            ) from exc

        return working


def _stamp_name(pdbqt_string: str, access_code: str) -> str:
    if pdbqt_string.startswith("REMARK  Name"):
        return pdbqt_string
    return f"REMARK  Name = {access_code}\n{pdbqt_string}"
