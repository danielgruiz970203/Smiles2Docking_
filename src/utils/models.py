from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MolecularRecord:
    access_code: str
    smiles: str
    source_row: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RunReport:
    input_file: str
    protonation_ph: float | None = None
    export_mode: str = "separate_mol2"
    export_format: str = "mol2"
    total_records_retrieved: int = 0
    total_smiles_evaluated: int = 0
    invalid_smiles: int = 0
    molecules_successfully_cleaned: int = 0
    molecules_with_salts_removed: int = 0
    molecules_converted_to_3d: int = 0
    structure_records_exported: int = 0
    structure_files_written: int = 0
    generated_structure_files: list[str] = field(default_factory=list)
    mol2_files_written: int = 0
    generated_mol2_files: list[str] = field(default_factory=list)
    pdbqt_files_written: int = 0
    generated_pdbqt_files: list[str] = field(default_factory=list)
    figure_panels_generated: int = 0
    figure_pages_written: int = 0
    figure_report_path: str | None = None
    log_file_path: str | None = None
    failures_or_skipped_entries: int = 0
    status: str = "completed"
    abort_reason: str | None = None
    failure_details: list[dict[str, Any]] = field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None
    wall_clock_seconds: float = 0.0
    per_record_timings: list[dict[str, Any]] = field(default_factory=list)
    mean_seconds_per_record: float | None = None
    median_seconds_per_record: float | None = None
    p95_seconds_per_record: float | None = None
    fastest_seconds: float | None = None
    slowest_seconds: float | None = None
    throughput_molecules_per_minute: float | None = None
    n_jobs_used: int = 1


@dataclass(slots=True)
class ProtonatedLigandRecord:
    access_code: str
    protonated_smiles: str


@dataclass(slots=True)
class WorkflowExecutionResult:
    report: RunReport
    report_path: str


@dataclass(slots=True)
class MopacOptimizationResult:
    molecule: Any
    charge: int
    keywords: str
    heat_of_formation_kcal_mol: float | None = None
    preserved_files: list[str] = field(default_factory=list)
