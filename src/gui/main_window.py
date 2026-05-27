from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from src.app_metadata import (
    APP_NAME,
    APP_VERSION,
    AUTHOR_AFFILIATION,
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    PROJECT_LICENSE,
)
from src.utils.config import load_settings, merge_settings, resolve_project_path, resolve_settings_paths
from src.utils.logging_utils import setup_logging
from src.workflow.pipeline import run_workflow


LANGUAGE_TEXT = {
    "en": {
        "about": "About",
        "title": "Ligand preparation for docking",
        "subtitle": "Load a spreadsheet, adjust protonation pH, export MOL2 or SDF files, and run the workflow without blocking the desktop.",
        "input": "Input",
        "processing": "Processing",
        "output": "Output",
        "execution": "Execution",
        "language": "Language",
        "file": "Input file",
        "sheet": "Excel sheet",
        "smiles": "SMILES column",
        "id": "ID column",
        "ph": "Target pH",
        "output_dir": "Output directory",
        "export_mode": "Export mode",
        "bundle_name": "Output name / prefix",
        "bundle_hint_single": "Used as the name of the single exported file.",
        "bundle_hint_separate": "Optional prefix for separate files. Leave blank to keep only the compound IDs.",
        "browse": "Browse...",
        "browse_input_title": "Select spreadsheet",
        "browse_output_title": "Select output directory",
        "spreadsheet_filter": "Spreadsheets (*.csv *.xls *.xlsx)",
        "run": "Run workflow",
        "clear_log": "Clear log",
        "sheet_placeholder": "Optional for Excel",
        "log_placeholder": "Execution log will appear here.",
        "status_idle": "Waiting to start.",
        "status_initializing": "Initializing workflow...",
        "status_completed": "Execution completed.",
        "status_failed": "Execution failed.",
        "warning_input": "Select a CSV/XLS/XLSX input file.",
        "summary_author": f"Author: {AUTHOR_NAME} | {AUTHOR_AFFILIATION} | {AUTHOR_EMAIL}",
        "mode_separate_mol2": "Separate MOL2 files",
        "mode_separate_sdf": "Separate SDF files",
        "mode_single_mol2": "Single MOL2 file",
        "mode_single_sdf": "Single SDF file",
        "background": "Run in background and minimize the window",
        "failure_summary": "Execution failed: {message}",
        "author_label": "Author",
        "license_label": "Project license",
        "summary_status": "Status",
        "summary_ph": "pH",
        "summary_export": "Export",
        "summary_records": "Structures exported",
        "summary_files": "Files generated",
        "summary_failures": "Failures/skipped",
        "summary_report": "Report",
        "summary_log": "Final log",
        "about_title": f"About {APP_NAME}",
        "about_notice": "Open distribution with third-party notices in docs/THIRD_PARTY_NOTICES.md.",
        "bundle_placeholder_enabled": "Example: prepared_ligands",
        "bundle_placeholder_disabled": "Optional prefix for separate-file export",
    },
    "pt": {
        "about": "Sobre",
        "title": "Preparação de ligantes para docking",
        "subtitle": "Carregue uma planilha, ajuste o pH de protonação, exporte arquivos MOL2 ou SDF e rode o workflow sem bloquear o desktop.",
        "input": "Entrada",
        "processing": "Processamento",
        "output": "Saída",
        "execution": "Execução",
        "language": "Idioma",
        "file": "Arquivo de entrada",
        "sheet": "Aba Excel",
        "smiles": "Coluna SMILES",
        "id": "Coluna ID",
        "ph": "pH alvo",
        "output_dir": "Diretório de saída",
        "export_mode": "Modo de exportação",
        "bundle_name": "Nome de saída / prefixo",
        "bundle_hint_single": "Usado como nome do arquivo único exportado.",
        "bundle_hint_separate": "Prefixo opcional para arquivos separados. Deixe em branco para usar apenas os IDs.",
        "browse": "Selecionar...",
        "browse_input_title": "Selecionar planilha",
        "browse_output_title": "Selecionar diretório de saída",
        "spreadsheet_filter": "Planilhas (*.csv *.xls *.xlsx)",
        "run": "Executar workflow",
        "clear_log": "Limpar log",
        "sheet_placeholder": "Opcional para Excel",
        "log_placeholder": "O log de execução aparecerá aqui.",
        "status_idle": "Aguardando execução.",
        "status_initializing": "Inicializando workflow...",
        "status_completed": "Execução concluída.",
        "status_failed": "Execução falhou.",
        "warning_input": "Selecione um arquivo CSV/XLS/XLSX.",
        "summary_author": f"Autoria: {AUTHOR_NAME} | {AUTHOR_AFFILIATION} | {AUTHOR_EMAIL}",
        "mode_separate_mol2": "Arquivos MOL2 separados",
        "mode_separate_sdf": "Arquivos SDF separados",
        "mode_single_mol2": "Um único arquivo MOL2",
        "mode_single_sdf": "Um único arquivo SDF",
        "background": "Executar em segundo plano e minimizar a janela",
        "failure_summary": "Execução falhou: {message}",
        "author_label": "Autoria",
        "license_label": "Licença do projeto",
        "summary_status": "Status",
        "summary_ph": "pH",
        "summary_export": "Exportação",
        "summary_records": "Estruturas exportadas",
        "summary_files": "Arquivos gerados",
        "summary_failures": "Falhas/ignorados",
        "summary_report": "Relatório",
        "summary_log": "Log final",
        "about_title": f"Sobre {APP_NAME}",
        "about_notice": "Distribuição aberta com notices de terceiros em docs/THIRD_PARTY_NOTICES.md.",
        "bundle_placeholder_enabled": "Ex.: prepared_ligands",
        "bundle_placeholder_disabled": "Prefixo opcional para exportação em arquivos separados",
    },
}


@dataclass(slots=True)
class WorkflowOverrides:
    input_file: str
    sheet_name: str
    smiles_column: str
    access_code_column: str
    output_dir: str
    export_mode: str
    bundle_basename: str
    ph: float
    run_in_background: bool


class WorkflowWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)
    log_message = Signal(str)
    progress_changed = Signal(int, int, str)

    def __init__(self, settings: dict) -> None:
        super().__init__()
        self.settings = settings

    def run(self) -> None:
        try:
            logger = setup_logging(self.settings)
            result = run_workflow(
                self.settings,
                logger=logger,
                progress_callback=self.progress_changed.emit,
                message_callback=self.log_message.emit,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.finished.emit(
            {
                "status": result.report.status,
                "report_path": result.report_path,
                "structure_files_written": result.report.structure_files_written,
                "structure_records_exported": result.report.structure_records_exported,
                "export_mode": result.report.export_mode,
                "export_format": result.report.export_format,
                "failures": result.report.failures_or_skipped_entries,
                "ph": result.report.protonation_ph,
                "log_file_path": result.report.log_file_path or "",
            }
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.base_settings = load_settings()
        self.current_language = self.base_settings.get("ui", {}).get("language", "en")
        if self.current_language not in LANGUAGE_TEXT:
            self.current_language = "en"
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1180, 760)
        self._thread: QThread | None = None
        self._worker: WorkflowWorker | None = None
        self._last_payload: dict | None = None

        self._build_menu()
        self._build_ui()
        self._apply_style()
        self._apply_language()

    def _text(self, key: str) -> str:
        return LANGUAGE_TEXT[self.current_language][key]

    def _apply_language(self) -> None:
        self.language_label.setText(self._text("language"))
        self.about_button.setText(self._text("about"))
        self.header.setText(self._text("title"))
        self.subtitle.setText(self._text("subtitle"))
        self.input_group.setTitle(self._text("input"))
        self.processing_group.setTitle(self._text("processing"))
        self.output_group.setTitle(self._text("output"))
        self.execution_group.setTitle(self._text("execution"))
        self.input_file_label.setText(self._text("file"))
        self.sheet_label.setText(self._text("sheet"))
        self.smiles_label.setText(self._text("smiles"))
        self.id_label.setText(self._text("id"))
        self.ph_label.setText(self._text("ph"))
        self.output_dir_label.setText(self._text("output_dir"))
        self.export_mode_label.setText(self._text("export_mode"))
        self.bundle_name_label.setText(self._text("bundle_name"))
        self.bundle_name_hint_label.setText(self._bundle_name_hint_text())
        self.browse_input_button.setText(self._text("browse"))
        self.browse_output_button.setText(self._text("browse"))
        self.run_button.setText(self._text("run"))
        self.clear_log_button.setText(self._text("clear_log"))
        self.run_in_background_checkbox.setText(self._text("background"))
        self.sheet_edit.setPlaceholderText(self._text("sheet_placeholder"))
        self.log_box.setPlaceholderText(self._text("log_placeholder"))
        self.progress_label.setText(self._text("status_idle"))
        self.summary_label.setText(self._text("summary_author"))
        self._refresh_export_mode_labels()
        self._toggle_bundle_name_state()
        if self._last_payload is not None:
            self._set_summary(self._last_payload)

    def _refresh_export_mode_labels(self) -> None:
        label_map = {
            "separate_mol2": self._text("mode_separate_mol2"),
            "separate_sdf": self._text("mode_separate_sdf"),
            "single_mol2": self._text("mode_single_mol2"),
            "single_sdf": self._text("mode_single_sdf"),
        }
        for index in range(self.export_mode_combo.count()):
            export_mode = str(self.export_mode_combo.itemData(index))
            self.export_mode_combo.setItemText(index, label_map.get(export_mode, export_mode))

    def _change_language(self) -> None:
        selected = str(self.language_combo.currentData())
        if selected in LANGUAGE_TEXT and selected != self.current_language:
            self.current_language = selected
            self._apply_language()

    def _build_menu(self) -> None:
        menu_container = QWidget(self)
        menu_layout = QHBoxLayout(menu_container)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(12)

        app_badge = QLabel(APP_NAME, menu_container)
        app_badge.setObjectName("menuBadge")
        self.menu_badge = app_badge

        self.language_label = QLabel(self._text("language"), menu_container)
        self.language_label.setObjectName("toolbarLabel")
        self.language_combo = QComboBox(menu_container)
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Português", "pt")
        self.language_combo.setCurrentIndex(max(self.language_combo.findData(self.current_language), 0))
        self.language_combo.currentIndexChanged.connect(self._change_language)

        about_button = QPushButton("Sobre", menu_container)
        about_button.setObjectName("menuButton")
        about_button.clicked.connect(self._show_about_dialog)
        self.about_button = about_button

        menu_layout.addWidget(app_badge)
        menu_layout.addStretch(1)
        menu_layout.addWidget(self.language_label, 0, Qt.AlignVCenter)
        menu_layout.addWidget(self.language_combo, 0, Qt.AlignVCenter)
        menu_layout.addWidget(about_button, 0, Qt.AlignVCenter)

        self.top_bar = menu_container

    def _build_ui(self) -> None:
        central = QWidget(self)
        central.setObjectName("centralSurface")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(16)
        main_layout.addLayout(controls_layout, 4)

        side_layout = QVBoxLayout()
        side_layout.setSpacing(16)
        main_layout.addLayout(side_layout, 5)

        controls_layout.addWidget(self.top_bar)

        header = QLabel(self._text("title"))
        self.header = header
        header.setObjectName("heroTitle")
        subtitle = QLabel(self._text("subtitle"))
        self.subtitle = subtitle
        subtitle.setWordWrap(True)
        subtitle.setObjectName("heroSubtitle")

        controls_layout.addWidget(header)
        controls_layout.addWidget(subtitle)

        controls_layout.addWidget(self._build_input_group())
        controls_layout.addWidget(self._build_processing_group())
        controls_layout.addWidget(self._build_output_group())
        controls_layout.addStretch(1)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText(self._text("log_placeholder"))

        self.progress_label = QLabel(self._text("status_idle"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.summary_label = QLabel(self._text("summary_author"))
        self.summary_label.setWordWrap(True)
        self.summary_label.setObjectName("summaryLabel")

        side_layout.addWidget(self._build_actions_group())
        side_layout.addWidget(self.progress_label)
        side_layout.addWidget(self.progress_bar)
        side_layout.addWidget(self.log_box, 1)
        side_layout.addWidget(self.summary_label)

    def _build_input_group(self) -> QGroupBox:
        group = QGroupBox(self._text("input"))
        self.input_group = group
        layout = QFormLayout(group)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignTop)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(14)

        input_defaults = self.base_settings["input"]
        default_input = input_defaults.get("file_path") or str(resolve_project_path("data/raw/sample_molecules.csv"))
        self.input_file_edit = QLineEdit(str(resolve_project_path(default_input)))
        browse_input = QPushButton(self._text("browse"))
        browse_input.clicked.connect(self._browse_input_file)
        self.browse_input_button = browse_input
        input_row = QHBoxLayout()
        input_row.addWidget(self.input_file_edit, 1)
        input_row.addWidget(browse_input)

        self.sheet_edit = QLineEdit()
        self.sheet_edit.setPlaceholderText(self._text("sheet_placeholder"))
        self.smiles_column_edit = QLineEdit(input_defaults.get("smiles_column", "smiles"))
        self.access_code_column_edit = QLineEdit(input_defaults.get("access_code_column", "access_code"))
        self.input_file_label = QLabel(self._text("file"))
        self.sheet_label = QLabel(self._text("sheet"))
        self.smiles_label = QLabel(self._text("smiles"))
        self.id_label = QLabel(self._text("id"))

        layout.addRow(self.input_file_label, self._wrap_layout(input_row))
        layout.addRow(self.sheet_label, self.sheet_edit)
        layout.addRow(self.smiles_label, self.smiles_column_edit)
        layout.addRow(self.id_label, self.access_code_column_edit)
        return group

    def _build_processing_group(self) -> QGroupBox:
        group = QGroupBox(self._text("processing"))
        self.processing_group = group
        layout = QFormLayout(group)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignTop)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(14)

        self.ph_spin = QDoubleSpinBox()
        self.ph_spin.setRange(0.0, 14.0)
        self.ph_spin.setDecimals(2)
        self.ph_spin.setSingleStep(0.1)
        self.ph_spin.setValue(float(self.base_settings["protonation"].get("ph", 7.4)))
        self.ph_label = QLabel(self._text("ph"))
        layout.addRow(self.ph_label, self.ph_spin)
        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox(self._text("output"))
        self.output_group = group
        layout = QFormLayout(group)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignTop)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(14)

        self.output_dir_edit = QLineEdit(str(resolve_project_path(self.base_settings["export"]["output_dir"])))
        browse_output = QPushButton(self._text("browse"))
        browse_output.clicked.connect(self._browse_output_dir)
        self.browse_output_button = browse_output
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_dir_edit, 1)
        output_row.addWidget(browse_output)

        self.export_mode_combo = QComboBox()
        self.export_mode_combo.addItem(self._text("mode_separate_mol2"), "separate_mol2")
        self.export_mode_combo.addItem(self._text("mode_separate_sdf"), "separate_sdf")
        self.export_mode_combo.addItem(self._text("mode_single_mol2"), "single_mol2")
        self.export_mode_combo.addItem(self._text("mode_single_sdf"), "single_sdf")
        configured_export_mode = self.base_settings["export"].get("mode", "separate_mol2")
        configured_index = max(self.export_mode_combo.findData(configured_export_mode), 0)
        self.export_mode_combo.setCurrentIndex(configured_index)
        self.export_mode_combo.currentIndexChanged.connect(self._toggle_bundle_name_state)

        self.bundle_name_edit = QLineEdit(self.base_settings["export"].get("bundle_basename", "prepared_ligands"))
        self.output_dir_label = QLabel(self._text("output_dir"))
        self.export_mode_label = QLabel(self._text("export_mode"))
        self.bundle_name_label = QLabel(self._text("bundle_name"))
        self.bundle_name_hint_label = QLabel(self._bundle_name_hint_text())
        self.bundle_name_hint_label.setObjectName("fieldHintLabel")
        self.bundle_name_hint_label.setWordWrap(True)

        layout.addRow(self.output_dir_label, self._wrap_layout(output_row))
        layout.addRow(self.export_mode_label, self.export_mode_combo)
        layout.addRow(self.bundle_name_label, self.bundle_name_edit)
        layout.addRow(QLabel(""), self.bundle_name_hint_label)
        self._toggle_bundle_name_state()
        return group

    def _build_actions_group(self) -> QGroupBox:
        group = QGroupBox(self._text("execution"))
        self.execution_group = group
        layout = QVBoxLayout(group)

        self.run_in_background_checkbox = QCheckBox(self._text("background"))
        self.run_in_background_checkbox.setChecked(True)
        self.run_button = QPushButton(self._text("run"))
        self.run_button.clicked.connect(self._start_workflow)
        self.clear_log_button = QPushButton(self._text("clear_log"))
        self.clear_log_button.clicked.connect(self.log_box.clear)

        layout.addWidget(self.run_in_background_checkbox)
        layout.addWidget(self.run_button)
        layout.addWidget(self.clear_log_button)
        return group

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #ece7de;
                color: #16212f;
                font-size: 12px;
            }
            QWidget#centralSurface {
                background: #ece7de;
            }
            QMenuBar {
                background: #16324f;
                color: #f4f7fb;
                border-bottom: 1px solid #0f2438;
            }
            QLabel#toolbarLabel {
                color: #20354d;
                font-weight: 700;
            }
            QLabel#menuBadge {
                background: #dcb15d;
                color: #13263a;
                border-radius: 12px;
                padding: 7px 14px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.4px;
            }
            QPushButton#menuButton {
                min-width: 132px;
                background: #f4f0e7;
                color: #20354d;
                border: 1px solid #7f91a3;
                border-radius: 12px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 700;
                text-align: center;
            }
            QPushButton#menuButton:hover {
                background: #e7dfd1;
                border-color: #5d7388;
            }
            QPushButton#menuButton:pressed {
                background: #d8cfbf;
            }
            QGroupBox {
                border: 1px solid #b5c1cf;
                border-radius: 14px;
                margin-top: 14px;
                padding: 14px;
                background: #fffdfa;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #20354d;
            }
            QLineEdit, QPlainTextEdit, QDoubleSpinBox, QSpinBox {
                border: 1px solid #8798aa;
                border-radius: 10px;
                padding: 9px 10px;
                background: #ffffff;
                color: #172230;
                selection-background-color: #204a72;
                selection-color: #ffffff;
            }
            QLineEdit:focus, QPlainTextEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
                border: 2px solid #1f5e8a;
            }
            QPlainTextEdit {
                background: #f7f9fc;
                border: 1px solid #7e8ea0;
                color: #172230;
            }
            QCheckBox {
                color: #1a2738;
                spacing: 8px;
                font-weight: 600;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #6f8296;
                border-radius: 5px;
                background: #ffffff;
            }
            QCheckBox::indicator:checked {
                background: #1f5f8b;
                border-color: #184b6d;
            }
            QPushButton {
                border: none;
                border-radius: 11px;
                background: #1f5f8b;
                color: white;
                padding: 10px 16px;
                font-weight: 700;
                text-align: center;
            }
            QPushButton:hover {
                background: #174766;
            }
            QPushButton:pressed {
                background: #13384f;
            }
            QProgressBar {
                border: 1px solid #8998a8;
                border-radius: 9px;
                text-align: center;
                background: #ffffff;
                color: #142030;
                min-height: 22px;
            }
            QProgressBar::chunk {
                background: #d68216;
                border-radius: 7px;
            }
            QLabel#heroTitle {
                font-size: 28px;
                font-weight: 800;
                color: #102235;
            }
            QLabel#heroSubtitle, QLabel#summaryLabel {
                color: #33465a;
                line-height: 1.35;
            }
            QLabel#fieldHintLabel {
                color: #53687e;
                font-size: 11px;
            }
            QLabel {
                background: transparent;
            }
            """
        )
        font = QFont("Segoe UI", 10)
        QApplication.instance().setFont(font)

    def _wrap_layout(self, layout: QHBoxLayout) -> QWidget:
        wrapper = QWidget()
        wrapper.setLayout(layout)
        return wrapper

    def _browse_input_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._text("browse_input_title"),
            str(Path(self.input_file_edit.text()).parent),
            self._text("spreadsheet_filter"),
        )
        if path:
            self.input_file_edit.setText(path)

    def _browse_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            self._text("browse_output_title"),
            self.output_dir_edit.text(),
        )
        if path:
            self.output_dir_edit.setText(path)

    def _toggle_bundle_name_state(self) -> None:
        single_file_mode = self.export_mode_combo.currentData() in {"single_mol2", "single_sdf"}
        self.bundle_name_edit.setEnabled(True)
        if single_file_mode:
            self.bundle_name_edit.setPlaceholderText(self._text("bundle_placeholder_enabled"))
        else:
            self.bundle_name_edit.setPlaceholderText(self._text("bundle_placeholder_disabled"))
        self.bundle_name_hint_label.setText(self._bundle_name_hint_text())

    def _bundle_name_hint_text(self) -> str:
        if self.export_mode_combo.currentData() in {"single_mol2", "single_sdf"}:
            return self._text("bundle_hint_single")
        return self._text("bundle_hint_separate")

    def _build_overrides(self) -> WorkflowOverrides:
        return WorkflowOverrides(
            input_file=self.input_file_edit.text().strip(),
            sheet_name=self.sheet_edit.text().strip(),
            smiles_column=self.smiles_column_edit.text().strip(),
            access_code_column=self.access_code_column_edit.text().strip(),
            output_dir=self.output_dir_edit.text().strip(),
            export_mode=str(self.export_mode_combo.currentData()),
            bundle_basename=self.bundle_name_edit.text().strip(),
            ph=float(self.ph_spin.value()),
            run_in_background=self.run_in_background_checkbox.isChecked(),
        )

    def _start_workflow(self) -> None:
        overrides = self._build_overrides()
        if not overrides.input_file:
            QMessageBox.warning(self, APP_NAME, self._text("warning_input"))
            return

        runtime_overrides = {
            "input": {
                "file_path": overrides.input_file,
                "sheet_name": overrides.sheet_name or None,
                "smiles_column": overrides.smiles_column or "smiles",
                "access_code_column": overrides.access_code_column or "access_code",
            },
            "export": {
                "output_dir": overrides.output_dir or str(resolve_project_path("data/processed")),
                "mode": overrides.export_mode,
                "bundle_basename": overrides.bundle_basename,
            },
            "protonation": {"ph": overrides.ph},
            "ui": {"language": self.current_language},
        }
        settings = resolve_settings_paths(merge_settings(self.base_settings, runtime_overrides))

        self.run_button.setEnabled(False)
        self.log_box.clear()
        self.progress_label.setText(self._text("status_initializing"))
        self.progress_bar.setValue(0)
        self._last_payload = None

        self._thread = QThread(self)
        self._worker = WorkflowWorker(settings)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_message.connect(self.log_box.appendPlainText)
        self._worker.progress_changed.connect(self._update_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()
        if overrides.run_in_background:
            self.showMinimized()

    def _update_progress(self, current: int, total: int, message: str) -> None:
        self.progress_label.setText(message)
        percentage = 0 if total == 0 else int((current / total) * 100)
        self.progress_bar.setValue(min(percentage, 100))

    def _set_summary(self, payload: dict) -> None:
        summary_lines = [
            f"{self._text('summary_status')}: {payload['status']}",
            f"{self._text('summary_ph')}: {payload['ph']:.2f}",
            f"{self._text('summary_export')}: {self._describe_export_mode(payload['export_mode'])}",
            f"{self._text('summary_records')}: {payload['structure_records_exported']}",
            f"{self._text('summary_files')}: {payload['structure_files_written']}",
            f"{self._text('summary_failures')}: {payload['failures']}",
            f"{self._text('summary_report')}: {payload['report_path']}",
        ]
        if payload["log_file_path"]:
            summary_lines.append(f"{self._text('summary_log')}: {payload['log_file_path']}")
        self.summary_label.setText("\n".join(summary_lines))

    def _on_finished(self, payload: dict) -> None:
        self._last_payload = payload
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText(self._text("status_completed"))
        self._set_summary(payload)

    def _on_failed(self, message: str) -> None:
        self._last_payload = None
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(self._text("status_failed"))
        self.summary_label.setText(self._text("failure_summary").format(message=message))
        self.log_box.appendPlainText(message)

    def _cleanup_thread(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            self._text("about_title"),
            "\n".join(
                [
                    f"{APP_NAME} {APP_VERSION}",
                    f"{self._text('author_label')}: {AUTHOR_NAME}",
                    AUTHOR_AFFILIATION,
                    AUTHOR_EMAIL,
                    f"{self._text('license_label')}: {PROJECT_LICENSE}",
                    self._text("about_notice"),
                ]
            ),
        )

    def _describe_export_mode(self, export_mode: str) -> str:
        descriptions = {
            "separate_mol2": self._text("mode_separate_mol2"),
            "separate_sdf": self._text("mode_separate_sdf"),
            "single_mol2": self._text("mode_single_mol2"),
            "single_sdf": self._text("mode_single_sdf"),
        }
        return descriptions.get(export_mode, export_mode)
