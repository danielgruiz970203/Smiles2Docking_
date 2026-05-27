from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.models import MolecularRecord


class SpreadsheetSourceError(Exception):
    """Raised when the spreadsheet input is invalid."""


@dataclass(slots=True)
class SpreadsheetSource:
    settings: dict[str, Any]

    def load_records(self) -> list[MolecularRecord]:
        input_settings = self.settings["input"]
        file_path = Path(input_settings["file_path"])
        if not file_path.exists():
            raise SpreadsheetSourceError(f"Input file not found: {file_path}")

        frame = self._read_table(file_path, input_settings.get("sheet_name"))
        smiles_column = self._resolve_column(frame, input_settings["smiles_column"])
        access_code_column = self._resolve_column(frame, input_settings["access_code_column"])

        records: list[MolecularRecord] = []
        for index, row in frame.iterrows():
            raw_access_code = row.get(access_code_column, "")
            raw_smiles = row.get(smiles_column, "")
            access_code = "" if pd.isna(raw_access_code) else str(raw_access_code).strip()
            smiles = "" if pd.isna(raw_smiles) else str(raw_smiles).strip()
            extra = {
                key: value
                for key, value in row.to_dict().items()
                if key not in {access_code_column, smiles_column}
            }
            records.append(
                MolecularRecord(
                    access_code=access_code,
                    smiles=smiles,
                    source_row=int(index) + 2,
                    metadata=extra,
                )
            )

        return records

    def _read_table(self, file_path: Path, sheet_name: str | None) -> pd.DataFrame:
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(file_path)
        if suffix in {".xls", ".xlsx"}:
            return pd.read_excel(file_path, sheet_name=sheet_name if sheet_name else 0)
        raise SpreadsheetSourceError(
            f"Unsupported input format '{suffix}'. Supported formats: .csv, .xls, .xlsx."
        )

    def _resolve_column(self, frame: pd.DataFrame, desired_name: str) -> str:
        normalized = {str(column).strip().lower(): column for column in frame.columns}
        key = desired_name.strip().lower()
        if key not in normalized:
            available = ", ".join(map(str, frame.columns))
            raise SpreadsheetSourceError(
                f"Column '{desired_name}' not found. Available columns: {available}"
            )
        return str(normalized[key])
