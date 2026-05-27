from __future__ import annotations

from src.workflow.pipeline import _resolve_n_jobs


def test_resolve_n_jobs_disabled_returns_one() -> None:
    assert _resolve_n_jobs({"enabled": False, "n_jobs": 8}, 100) == 1


def test_resolve_n_jobs_single_record_returns_one() -> None:
    assert _resolve_n_jobs({"enabled": True, "n_jobs": 8}, 1) == 1


def test_resolve_n_jobs_passthrough_positive() -> None:
    assert _resolve_n_jobs({"enabled": True, "n_jobs": 4}, 100) == 4


def test_resolve_n_jobs_passthrough_all_cores() -> None:
    assert _resolve_n_jobs({"enabled": True, "n_jobs": -1}, 100) == -1


def test_resolve_n_jobs_zero_treated_as_one() -> None:
    assert _resolve_n_jobs({"enabled": True, "n_jobs": 0}, 100) == 1


def test_resolve_n_jobs_invalid_returns_one() -> None:
    assert _resolve_n_jobs({"enabled": True, "n_jobs": "lots"}, 100) == 1
