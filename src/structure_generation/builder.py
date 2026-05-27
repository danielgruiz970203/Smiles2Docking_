from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rdkit import Chem
from rdkit.Chem import AllChem


class StructureGenerationError(Exception):
    """Raised when 3D coordinate generation fails."""


def _mopac_settings(settings: dict[str, Any]) -> dict[str, Any] | None:
    raw = settings.get("mopac")
    if not isinstance(raw, dict):
        return None
    if not raw.get("enabled", False):
        return None
    return raw


@dataclass(slots=True)
class StructureBuilder:
    settings: dict[str, Any]

    def build_3d(self, smiles: str, access_code: str) -> Chem.Mol:
        molecule = Chem.MolFromSmiles(smiles, sanitize=True)
        if molecule is None:
            raise StructureGenerationError(f"Unable to parse protonated SMILES for {access_code!r}")

        molecule = Chem.AddHs(molecule)
        params = AllChem.ETKDGv3()
        params.randomSeed = int(self.settings.get("embed_seed", 61453))

        max_attempts = int(self.settings.get("max_attempts", 3))
        for _ in range(max_attempts):
            working_copy = Chem.Mol(molecule)
            if AllChem.EmbedMolecule(working_copy, params) == 0:
                self._optimize_geometry(working_copy, access_code)
                working_copy = self._refine_with_mopac(working_copy, access_code)
                working_copy.SetProp("_Name", access_code)
                return working_copy

        raise StructureGenerationError(f"3D embedding failed for {access_code!r}")

    def _refine_with_mopac(self, molecule: Chem.Mol, access_code: str) -> Chem.Mol:
        mopac_settings = _mopac_settings(self.settings)
        if mopac_settings is None:
            return molecule
        try:
            from src.quantum.mopac_adapter import MopacError, MopacOptimizer
        except ImportError:
            molecule.SetProp("mopac_status", "module_unavailable")
            return molecule
        try:
            result = MopacOptimizer(mopac_settings).optimize(molecule, access_code)
        except MopacError as exc:
            if mopac_settings.get("fail_on_error", False):
                raise StructureGenerationError(
                    f"MOPAC refinement failed for {access_code!r}: {exc}"
                ) from exc
            molecule.SetProp("mopac_status", "failed")
            molecule.SetProp("mopac_error", str(exc))
            return molecule
        refined = result.molecule
        refined.SetProp("mopac_status", "completed")
        return refined

    def _optimize_geometry(self, molecule: Chem.Mol, access_code: str) -> None:
        if not self.settings.get("optimize_geometry", True):
            molecule.SetProp("force_field", "none")
            return

        preferences = self.settings.get("force_field_preference", ["mmff94", "mmff94s", "uff"])
        max_iterations = int(self.settings.get("max_optimization_iterations", 1000))
        allow_unoptimized = self.settings.get("allow_unoptimized_output", False)

        optimization_errors: list[str] = []
        for force_field_name in preferences:
            try:
                result = self._run_force_field(molecule, force_field_name, max_iterations)
            except Exception as exc:
                optimization_errors.append(f"{force_field_name}: {exc}")
                continue

            if result is None:
                optimization_errors.append(f"{force_field_name}: not parameterizable for this molecule")
                continue

            if result != 0:
                optimization_errors.append(
                    f"{force_field_name}: optimization did not converge within {max_iterations} iterations"
                )
                continue

            molecule.SetProp("force_field", force_field_name)
            return

        molecule.SetProp("force_field", "unoptimized")
        if allow_unoptimized:
            return

        details = "; ".join(optimization_errors) if optimization_errors else "no force field was applicable"
        raise StructureGenerationError(
            f"Geometry optimization failed for {access_code!r}. Attempts: {details}"
        )

    def _run_force_field(self, molecule: Chem.Mol, force_field_name: str, max_iterations: int) -> int | None:
        normalized_name = force_field_name.strip().lower()
        if normalized_name in {"mmff94", "mmff94s"}:
            properties = AllChem.MMFFGetMoleculeProperties(molecule, mmffVariant=normalized_name)
            if properties is None:
                return None
            return AllChem.MMFFOptimizeMolecule(
                molecule,
                mmffVariant=normalized_name,
                maxIters=max_iterations,
            )

        if normalized_name == "uff":
            if not AllChem.UFFHasAllMoleculeParams(molecule):
                return None
            return AllChem.UFFOptimizeMolecule(molecule, maxIters=max_iterations)

        raise StructureGenerationError(
            f"Unsupported force field '{force_field_name}'. Supported values: mmff94, mmff94s, uff."
        )
