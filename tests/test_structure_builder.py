import pytest

from src.structure_generation.builder import StructureBuilder, StructureGenerationError


def test_prefers_mmff_when_available() -> None:
    builder = StructureBuilder(
        {
            "embed_seed": 61453,
            "max_attempts": 2,
            "optimize_geometry": True,
            "force_field_preference": ["mmff94", "uff"],
            "max_optimization_iterations": 500,
            "allow_unoptimized_output": False,
        }
    )

    molecule = builder.build_3d("CCO", "CMPD_001")

    assert molecule.GetNumConformers() == 1
    assert molecule.GetProp("force_field") == "mmff94"


def test_uses_uff_as_fallback_when_mmff_is_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
    builder = StructureBuilder(
        {
            "embed_seed": 61453,
            "max_attempts": 2,
            "optimize_geometry": True,
            "force_field_preference": ["mmff94", "uff"],
            "max_optimization_iterations": 500,
            "allow_unoptimized_output": False,
        }
    )

    original = StructureBuilder._run_force_field

    def fake_run_force_field(self, molecule, force_field_name, max_iterations):
        if force_field_name == "mmff94":
            return None
        return original(self, molecule, force_field_name, max_iterations)

    monkeypatch.setattr(StructureBuilder, "_run_force_field", fake_run_force_field)

    molecule = builder.build_3d("CCO", "CMPD_NA")

    assert molecule.GetNumConformers() == 1
    assert molecule.GetProp("force_field") == "uff"


def test_raises_for_unknown_force_field_name() -> None:
    builder = StructureBuilder(
        {
            "embed_seed": 61453,
            "max_attempts": 1,
            "optimize_geometry": True,
            "force_field_preference": ["bogus_ff"],
            "max_optimization_iterations": 10,
            "allow_unoptimized_output": False,
        }
    )

    with pytest.raises(StructureGenerationError):
        builder.build_3d("CCO", "CMPD_BAD")
