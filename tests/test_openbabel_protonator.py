from __future__ import annotations

from rdkit import Chem

from src.protonation.openbabel_adapter import OpenBabelProtonator


def _formal_charge(smiles: str) -> int:
    molecule = Chem.MolFromSmiles(smiles)
    assert molecule is not None
    return sum(atom.GetFormalCharge() for atom in molecule.GetAtoms())


def test_protonator_changes_charge_state_with_ph() -> None:
    low_ph = OpenBabelProtonator({"enabled": True, "ph": 2.0, "obabel_binary": "obabel"})
    high_ph = OpenBabelProtonator({"enabled": True, "ph": 12.0, "obabel_binary": "obabel"})

    acetic_low = low_ph.protonate_smiles("CC(=O)O", "ACID")
    acetic_high = high_ph.protonate_smiles("CC(=O)O", "ACID")
    methylamine_low = low_ph.protonate_smiles("CN", "BASE")
    methylamine_high = high_ph.protonate_smiles("CN", "BASE")

    assert _formal_charge(acetic_low) == 0
    assert _formal_charge(acetic_high) == -1
    assert _formal_charge(methylamine_low) == 1
    assert _formal_charge(methylamine_high) == 0
