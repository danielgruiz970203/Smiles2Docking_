from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean, median
from typing import Any

from rdkit import Chem

from src.database.spreadsheet_source import SpreadsheetSource, SpreadsheetSourceError
from src.export.mol2_writer import Mol2ExportError, StructureExporter
from src.preprocessing.smiles_cleaner import (
    AmbiguousFragmentError,
    InvalidSmilesError,
    SmilesCleaner,
)
from src.protonation.base import ProtonationError
from src.protonation.factory import build_protonator
from src.protonation.openbabel_adapter import OpenBabelError
from src.structure_generation.builder import StructureBuilder, StructureGenerationError
from src.utils.logging_utils import resolve_log_path
from src.utils.models import MolecularRecord, RunReport, WorkflowExecutionResult
from src.utils.reporting import write_report


ProgressCallback = Callable[[int, int, str], None]
MessageCallback = Callable[[str], None]

PROGRESS_TEXT = {
    "en": {"processing": "Processing", "row": "row", "completed": "Completed"},
    "pt": {"processing": "Processando", "row": "linha", "completed": "Concluido"},
}


@dataclass(slots=True)
class _RecordOutcome:
    record: MolecularRecord
    status: str  # "ok" | "invalid" | "failure" | "ambiguous" | "skipped"
    molecule: Chem.Mol | None = None
    salts_removed: bool = False
    force_field: str = "unknown"
    error_message: str = ""
    log_level: int = logging.INFO
    elapsed_seconds: float = 0.0
    stage_seconds: dict[str, float] = field(default_factory=dict)


def run_workflow(
    settings: dict[str, Any],
    logger: logging.Logger,
    progress_callback: ProgressCallback | None = None,
    message_callback: MessageCallback | None = None,
) -> WorkflowExecutionResult:
    language = str(settings.get("ui", {}).get("language", "en")).lower()
    if language not in PROGRESS_TEXT:
        language = "en"
    report = RunReport(
        input_file=settings["input"]["file_path"],
        protonation_ph=float(settings["protonation"].get("ph", 7.4)),
        export_mode=str(settings["export"].get("mode", "separate_mol2")),
    )
    if report.export_mode in {"single_sdf", "separate_sdf"}:
        report.export_format = "sdf"
    elif report.export_mode in {"single_pdbqt", "separate_pdbqt"}:
        report.export_format = "pdbqt"
    else:
        report.export_format = "mol2"
    report.log_file_path = str(resolve_log_path(settings))
    batched_structures: list[tuple[str, Any]] = []
    report.started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    run_start = time.perf_counter()

    def emit(level: int, message: str, *args: Any) -> None:
        logger.log(level, message, *args)
        if message_callback is not None:
            rendered = message % args if args else message
            message_callback(rendered)

    try:
        source = SpreadsheetSource(settings)
        exporter = StructureExporter(settings["export"], settings["protonation"])
        records = source.load_records()
        report.total_records_retrieved = len(records)
        total_records = len(records)

        parallel_settings = settings.get("parallel", {})
        n_jobs = _resolve_n_jobs(parallel_settings, total_records)
        report.n_jobs_used = n_jobs

        if n_jobs == 1:
            outcomes_iter = _iterate_records_sequential(records, settings)
        else:
            outcomes_iter = _iterate_records_parallel(records, settings, n_jobs, parallel_settings)

        for index, outcome in enumerate(outcomes_iter, start=1):
            record = outcome.record
            if progress_callback is not None:
                target = record.access_code or f"{PROGRESS_TEXT[language]['row']} {record.source_row}"
                progress_callback(
                    index - 1, total_records, f"{PROGRESS_TEXT[language]['processing']} {target}"
                )

            _apply_outcome_to_report(
                outcome=outcome,
                report=report,
                exporter=exporter,
                batched_structures=batched_structures,
                emit=emit,
            )

            if outcome.status == "ambiguous":
                raise AmbiguousFragmentError(outcome.error_message)

            if progress_callback is not None:
                target = record.access_code or f"{PROGRESS_TEXT[language]['row']} {record.source_row}"
                progress_callback(
                    index, total_records, f"{PROGRESS_TEXT[language]['completed']} {target}"
                )

        if batched_structures:
            exported_paths = exporter.write_batch(batched_structures)
            _register_exported_paths(report, exported_paths, exporter.export_format)
            report.structure_records_exported += len(batched_structures)
            emit(
                logging.INFO,
                "Merged %s molecules into %s",
                len(batched_structures),
                ", ".join(str(path) for path in exported_paths),
            )
    except SpreadsheetSourceError as exc:
        report.status = "failed"
        report.abort_reason = str(exc)
        emit(logging.ERROR, "Input loading failed: %s", exc)
        _finalize_timings(report, run_start)
        report_path = write_report(report, settings["reporting"]["report_dir"])
        emit(logging.INFO, "Run report written to %s", report_path)
        return WorkflowExecutionResult(report=report, report_path=str(report_path))
    except AmbiguousFragmentError:
        _finalize_timings(report, run_start)
        report_path = write_report(report, settings["reporting"]["report_dir"])
        emit(logging.INFO, "Run report written to %s", report_path)
        return WorkflowExecutionResult(report=report, report_path=str(report_path))

    _finalize_timings(report, run_start)
    emit(
        logging.INFO,
        "Run finished in %.2fs (mean=%.3fs/mol, throughput=%.1f mol/min)",
        report.wall_clock_seconds,
        report.mean_seconds_per_record or 0.0,
        report.throughput_molecules_per_minute or 0.0,
    )
    report_path = write_report(report, settings["reporting"]["report_dir"])
    emit(logging.INFO, "Run report written to %s", report_path)
    return WorkflowExecutionResult(report=report, report_path=str(report_path))


def _finalize_timings(report: RunReport, run_start: float) -> None:
    report.wall_clock_seconds = round(time.perf_counter() - run_start, 4)
    report.finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    successful = [entry["seconds"] for entry in report.per_record_timings if entry["status"] == "ok"]
    if successful:
        report.mean_seconds_per_record = round(mean(successful), 4)
        report.median_seconds_per_record = round(median(successful), 4)
        sorted_seconds = sorted(successful)
        idx = max(0, int(round(0.95 * (len(sorted_seconds) - 1))))
        report.p95_seconds_per_record = round(sorted_seconds[idx], 4)
        report.fastest_seconds = round(min(successful), 4)
        report.slowest_seconds = round(max(successful), 4)
        if report.wall_clock_seconds > 0:
            report.throughput_molecules_per_minute = round(
                (len(successful) / report.wall_clock_seconds) * 60.0, 2
            )


def _resolve_n_jobs(parallel_settings: dict[str, Any], total_records: int) -> int:
    if not parallel_settings.get("enabled", True):
        return 1
    if total_records <= 1:
        return 1
    requested = parallel_settings.get("n_jobs", 1)
    try:
        requested_int = int(requested)
    except (TypeError, ValueError):
        return 1
    if requested_int == 0:
        return 1
    return requested_int


def _iterate_records_sequential(
    records: list[MolecularRecord], settings: dict[str, Any]
):
    cleaner = SmilesCleaner(settings["processing"])
    protonator = build_protonator(settings["protonation"])
    builder = StructureBuilder(settings["structure_generation"])
    for record in records:
        yield _process_record(record, cleaner, protonator, builder)


def _iterate_records_parallel(
    records: list[MolecularRecord],
    settings: dict[str, Any],
    n_jobs: int,
    parallel_settings: dict[str, Any],
):
    try:
        from joblib import Parallel, delayed
    except ImportError:
        yield from _iterate_records_sequential(records, settings)
        return

    backend = str(parallel_settings.get("backend", "loky"))
    batch_size = parallel_settings.get("batch_size", "auto")
    parallel = Parallel(n_jobs=n_jobs, backend=backend, batch_size=batch_size, return_as="generator")
    tasks = (
        delayed(_process_record_isolated)(
            record,
            settings["processing"],
            settings["protonation"],
            settings["structure_generation"],
        )
        for record in records
    )
    yield from parallel(tasks)


def _process_record_isolated(
    record: MolecularRecord,
    processing_settings: dict[str, Any],
    protonation_settings: dict[str, Any],
    structure_settings: dict[str, Any],
) -> _RecordOutcome:
    cleaner = SmilesCleaner(processing_settings)
    protonator = build_protonator(protonation_settings)
    builder = StructureBuilder(structure_settings)
    return _process_record(record, cleaner, protonator, builder)


def _process_record(
    record: MolecularRecord,
    cleaner: SmilesCleaner,
    protonator: Any,
    builder: StructureBuilder,
) -> _RecordOutcome:
    overall_start = time.perf_counter()
    stage_seconds: dict[str, float] = {}

    if not record.access_code:
        return _RecordOutcome(
            record=record,
            status="skipped",
            error_message="Missing access code.",
            log_level=logging.WARNING,
            elapsed_seconds=time.perf_counter() - overall_start,
            stage_seconds=stage_seconds,
        )
    try:
        stage_start = time.perf_counter()
        cleaned = cleaner.clean_record(record)
        stage_seconds["clean"] = time.perf_counter() - stage_start

        stage_start = time.perf_counter()
        protonated_smiles = protonator.protonate_smiles(cleaned.cleaned_smiles, record.access_code)
        stage_seconds["protonate"] = time.perf_counter() - stage_start

        stage_start = time.perf_counter()
        molecule_3d = builder.build_3d(protonated_smiles, record.access_code)
        stage_seconds["build_3d"] = time.perf_counter() - stage_start
    except InvalidSmilesError as exc:
        return _RecordOutcome(
            record=record,
            status="invalid",
            error_message=str(exc),
            log_level=logging.WARNING,
            elapsed_seconds=time.perf_counter() - overall_start,
            stage_seconds=stage_seconds,
        )
    except AmbiguousFragmentError as exc:
        return _RecordOutcome(
            record=record,
            status="ambiguous",
            error_message=str(exc),
            log_level=logging.ERROR,
            elapsed_seconds=time.perf_counter() - overall_start,
            stage_seconds=stage_seconds,
        )
    except (
        ProtonationError,
        OpenBabelError,
        StructureGenerationError,
        Mol2ExportError,
        SpreadsheetSourceError,
    ) as exc:
        return _RecordOutcome(
            record=record,
            status="failure",
            error_message=str(exc),
            log_level=logging.ERROR,
            elapsed_seconds=time.perf_counter() - overall_start,
            stage_seconds=stage_seconds,
        )

    force_field = (
        molecule_3d.GetProp("force_field") if molecule_3d.HasProp("force_field") else "unknown"
    )
    return _RecordOutcome(
        record=record,
        status="ok",
        molecule=molecule_3d,
        salts_removed=cleaned.salts_removed,
        force_field=force_field,
        elapsed_seconds=time.perf_counter() - overall_start,
        stage_seconds=stage_seconds,
    )


def _apply_outcome_to_report(
    *,
    outcome: _RecordOutcome,
    report: RunReport,
    exporter: StructureExporter,
    batched_structures: list[tuple[str, Any]],
    emit: Callable[..., None],
) -> None:
    record = outcome.record
    export_start = time.perf_counter()

    def _record_timing(extra_seconds: float = 0.0) -> None:
        report.per_record_timings.append(
            {
                "access_code": record.access_code,
                "row": record.source_row,
                "status": outcome.status,
                "seconds": round(outcome.elapsed_seconds + extra_seconds, 4),
                "stage_seconds": {k: round(v, 4) for k, v in outcome.stage_seconds.items()},
            }
        )

    if outcome.status == "skipped":
        report.failures_or_skipped_entries += 1
        report.failure_details.append(
            {"access_code": record.access_code, "row": record.source_row, "reason": outcome.error_message}
        )
        emit(outcome.log_level, "Skipping row %s: %s", record.source_row, outcome.error_message)
        _record_timing()
        return

    report.total_smiles_evaluated += 1

    if outcome.status == "invalid":
        report.invalid_smiles += 1
        report.failures_or_skipped_entries += 1
        report.failure_details.append(
            {"access_code": record.access_code, "row": record.source_row, "reason": outcome.error_message}
        )
        emit(outcome.log_level, "Skipping invalid SMILES for %s: %s", record.access_code, outcome.error_message)
        _record_timing()
        return

    if outcome.status == "failure":
        report.failures_or_skipped_entries += 1
        report.failure_details.append(
            {"access_code": record.access_code, "row": record.source_row, "reason": outcome.error_message}
        )
        emit(outcome.log_level, "Processing failed for %s: %s", record.access_code, outcome.error_message)
        _record_timing()
        return

    if outcome.status == "ambiguous":
        report.failures_or_skipped_entries += 1
        report.status = "aborted_for_clarification"
        report.abort_reason = outcome.error_message
        report.failure_details.append(
            {"access_code": record.access_code, "row": record.source_row, "reason": outcome.error_message}
        )
        emit(outcome.log_level, "Execution stopped: %s", outcome.error_message)
        _record_timing()
        return

    # status == "ok"
    report.molecules_successfully_cleaned += 1
    if outcome.salts_removed:
        report.molecules_with_salts_removed += 1
    report.molecules_converted_to_3d += 1

    molecule = outcome.molecule
    assert molecule is not None
    if exporter.uses_batch_export:
        batched_structures.append((record.access_code, molecule))
    else:
        try:
            exported_paths = exporter.write(molecule, record.access_code)
        except Mol2ExportError as exc:
            report.failures_or_skipped_entries += 1
            report.failure_details.append(
                {"access_code": record.access_code, "row": record.source_row, "reason": str(exc)}
            )
            emit(logging.ERROR, "Export failed for %s: %s", record.access_code, exc)
            outcome.stage_seconds["export"] = time.perf_counter() - export_start
            _record_timing(extra_seconds=outcome.stage_seconds["export"])
            return
        _register_exported_paths(report, exported_paths, exporter.export_format)
        report.structure_records_exported += 1

    export_elapsed = time.perf_counter() - export_start
    outcome.stage_seconds["export"] = export_elapsed
    _record_timing(extra_seconds=export_elapsed)
    emit(
        logging.INFO,
        "Processed %s with force field %s in %.3fs",
        record.access_code,
        outcome.force_field,
        outcome.elapsed_seconds + export_elapsed,
    )


def _register_exported_paths(report: RunReport, exported_paths: list[Any], export_format: str) -> None:
    report.structure_files_written += len(exported_paths)
    report.generated_structure_files.extend(str(path) for path in exported_paths)
    if export_format == "mol2":
        report.mol2_files_written += len(exported_paths)
        report.generated_mol2_files.extend(str(path) for path in exported_paths)
    elif export_format == "pdbqt":
        report.pdbqt_files_written += len(exported_paths)
        report.generated_pdbqt_files.extend(str(path) for path in exported_paths)
