from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "SMILES2Docking_workflow_for_publication.docx"


PARAGRAPHS = [
    "SMILES2Docking Workflow for Publication",
    "This document describes the operational workflow implemented in SMILES2Docking for ligand preparation from spreadsheet input to structure export. The text is intended for direct reuse and adaptation in a manuscript, supplementary methods section, or software note.",
    "1. General workflow overview",
    "SMILES2Docking is a desktop and command-line workflow designed to convert 2D ligand representations encoded as SMILES strings into protonation-adjusted and geometry-optimized 3D structures suitable for downstream docking studies. The software accepts CSV, XLS, and XLSX tables containing at least two columns: one identifier column and one SMILES column. For each valid record, the workflow reads the molecular entry, applies preprocessing and fragment selection when needed, adjusts the protonation state at a user-defined pH using Open Babel, generates a 3D conformation with RDKit, optimizes the geometry through a force-field cascade, and exports the resulting structures in SDF or MOL2 format. A machine-readable JSON report and a final execution log are written at the end of each run.",
    "2. User input and configuration",
    "The user provides an input spreadsheet and specifies the columns containing the compound identifier and the SMILES representation. When the input is an Excel workbook, an optional sheet name can also be provided. The protonation pH is user-defined and defaults to 7.4. The user selects one of four export modes: separate MOL2 files, separate SDF files, one combined MOL2 file, or one combined SDF file. An optional output basename can be supplied; in single-file modes it defines the name of the exported bundle, whereas in separate-file modes it acts as an optional filename prefix. The output directory is also user-defined and is used to store the exported structures, the JSON run report, and the final log file.",
    "3. Step-by-step workflow execution",
    "Step 1: Spreadsheet loading. The workflow first validates the presence of the input file and detects its format from the file extension. CSV files are read as comma-separated tables, whereas XLS and XLSX files are read as Excel tables. The software then resolves the identifier and SMILES columns using case-insensitive matching against the user-provided column names. Each row is converted into an internal molecular record containing the compound identifier, the SMILES string, the spreadsheet row number, and any remaining metadata columns.",
    "Step 2: Record validation. Before chemical processing begins, each record is checked for the presence of an identifier. Records without an identifier are skipped and registered in the failure section of the final report. Empty SMILES values are treated as invalid entries and are also reported.",
    "Step 3: Fragment inspection and salt removal. The raw SMILES string is split at disconnected-fragment separators. If the entry contains a single fragment, that fragment is used directly. If multiple disconnected fragments are present, the software attempts to select the principal molecular fragment automatically. Fragment ranking is based on a deterministic score that favors organic fragments, then larger heavy-atom count, then larger carbon count, and finally lower absolute formal charge. This step removes salts, counterions, and disconnected minor fragments when a main fragment can be identified safely.",
    "Step 4: Ambiguity control during fragment selection. If more than one fragment receives the same best score and strict fragment disambiguation is enabled, the workflow stops and requests clarification instead of making a potentially unsafe choice. This behavior is important because it prevents silent processing of ambiguous multi-component entries. If all fragments are invalid, the record is rejected as an invalid SMILES entry.",
    "Step 5: SMILES parsing and canonicalization. The selected principal fragment is parsed with RDKit under sanitization. If parsing fails, the entry is rejected. For valid molecules, the workflow serializes the cleaned structure back to SMILES. When possible, a Kekule representation is preserved in the exported SMILES; otherwise, a canonical sanitized SMILES representation is used. Notes about salt removal and Kekule preservation are retained internally for reporting purposes.",
    "Step 6: Protonation-state adjustment. The cleaned SMILES is passed to Open Babel using the user-defined pH. Internally, the software writes the SMILES and identifier to a temporary input file and calls Open Babel with the protonation option corresponding to the selected pH. The protonated SMILES returned by Open Babel is then used as the input for 3D structure generation. Temporary files created for this step are removed automatically after execution.",
    "Step 7: 3D coordinate generation. The protonated SMILES is parsed again with RDKit. Explicit hydrogens are added, and a 3D conformation is generated using the ETKDGv3 embedding method. The embedding stage uses a fixed random seed for reproducibility and attempts structure generation up to three times by default. If no valid 3D embedding is produced within the configured number of attempts, the record is marked as failed.",
    "Step 8: Geometry optimization. After successful embedding, the generated structure is optimized through a force-field cascade. By default, the workflow attempts MMFF94 first, then MMFF94s, and finally UFF. The first force field that is both applicable and converges within the configured iteration limit is retained and recorded as metadata. If all supported force fields fail to parameterize or optimize the molecule, the workflow raises a structure-generation error unless unoptimized output has been explicitly allowed in the settings.",
    "Step 9: Structure naming and tracking. For every successfully generated molecule, the identifier is assigned as the molecular name. The software also records the force field used during optimization, which is later written into the structure object and summarized in the execution log.",
    "Step 10: Export to SDF or MOL2. Structure export depends on the mode chosen by the user. In separate-file modes, each molecule is written independently. In SDF mode, RDKit writes the output directly. In MOL2 mode, the workflow first writes a temporary SDF file and then converts it to MOL2 using Open Babel. In single-file modes, all successful structures are accumulated in memory and written at the end of the run as one combined SDF file or one combined MOL2 file. For MOL2 bundle export, the same intermediate SDF-to-MOL2 conversion strategy is used.",
    "Step 11: Reporting and logging. Once all records have been processed, the software writes a JSON run report summarizing the execution. The report includes the input file, protonation pH, export mode, total number of retrieved records, number of evaluated SMILES entries, number of invalid entries, number of molecules successfully cleaned, number of cases in which salts were removed, number of molecules converted to 3D, number of exported structure records, number of generated files, and a detailed list of failures or skipped entries. A final execution log is also written to the output directory.",
    "4. Graphical user interface workflow",
    "In the graphical user interface, the user selects the spreadsheet file, optionally provides the Excel sheet name, sets the SMILES and identifier column names, chooses the target protonation pH, defines the output directory, and selects the export mode. The interface also allows the user to provide an output basename and to run the workflow in the background while the window is minimized. During execution, the interface displays progress messages, a progress bar, and a live log. At the end of the run, the interface summarizes the execution status, pH, export mode, number of exported structures, number of generated files, number of failed or skipped entries, and the paths to the JSON report and final log.",
    "5. Command-line workflow",
    "The same processing logic is available from the command line. In this mode, the user passes the input path, optional sheet name, optional column overrides, protonation pH, export mode, output basename, and output directory as command-line arguments. These runtime options are merged with the default settings file before execution. This design ensures that both the desktop and command-line interfaces call the same validated internal pipeline.",
    "6. Error handling and conservative decisions",
    "SMILES2Docking adopts a conservative strategy for problematic entries. Invalid SMILES strings are skipped and registered. Records without identifiers are skipped. Ambiguous multi-fragment molecules can abort the run for clarification rather than being processed with an arbitrary fragment choice. Failures in protonation, 3D embedding, force-field optimization, or format conversion are captured and reported in the JSON output. This behavior is intended to maximize traceability and minimize silent corruption of chemical records.",
    "7. Main software dependencies",
    "The workflow relies primarily on pandas for spreadsheet parsing, RDKit for molecular parsing and 3D structure generation, and Open Babel for pH-dependent protonation and SDF-to-MOL2 conversion. In practical terms, the chemistry-processing sequence can be summarized as: spreadsheet import with pandas, molecular validation and embedding with RDKit, protonation and MOL2 conversion with Open Babel, and structured audit reporting in JSON format.",
    "8. Recommended wording for a manuscript",
    "A concise manuscript description may state that SMILES2Docking reads ligand tables in CSV or Excel format, identifies the user-defined compound identifier and SMILES columns, removes disconnected salts and counterions when a principal fragment can be assigned unambiguously, adjusts the protonation state at a user-selected pH with Open Babel, generates hydrogen-complete 3D coordinates with RDKit ETKDGv3, optimizes the geometry through a MMFF94 to MMFF94s to UFF cascade, exports the resulting structures in SDF or MOL2 format, and writes a JSON audit report and execution log for traceability.",
    "9. Practical output generated by one run",
    "A standard run produces the prepared ligand structure files, a JSON report describing the run outcome and failures, and a text log that records the execution progress and final status. Depending on the selected export mode, the structure output consists either of one file per compound or one combined file containing all successful structures.",
    "10. Conclusion",
    "From the user perspective, the software workflow consists of selecting a spreadsheet, defining the key columns and protonation pH, choosing the desired structure format, and running the preparation job. From the internal perspective, the workflow consists of deterministic record loading, conservative chemical cleaning, pH-aware protonation, reproducible 3D embedding, force-field-based optimization, controlled export, and auditable reporting. This combination is appropriate for publications that aim to present the software as a robust and accessible ligand-preparation tool for docking-oriented computational workflows.",
]


def _paragraph_xml(text: str) -> str:
    escaped = escape(text)
    return (
        "<w:p>"
        "<w:r><w:t xml:space=\"preserve\">"
        f"{escaped}"
        "</w:t></w:r>"
        "</w:p>"
    )


def build_document_xml() -> str:
    body = "".join(_paragraph_xml(paragraph) for paragraph in PARAGRAPHS)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document "
        "xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" "
        "xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" "
        "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" "
        "xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" "
        "xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" "
        "xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" "
        "xmlns:wne=\"http://schemas.microsoft.com/office/word/2006/wordml\" "
        "xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" "
        "mc:Ignorable=\"w14 wp14\">"
        "<w:body>"
        f"{body}"
        "<w:sectPr>"
        "<w:pgSz w:w=\"12240\" w:h=\"15840\"/>"
        "<w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" "
        "w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/>"
        "<w:cols w:space=\"708\"/>"
        "<w:docGrid w:linePitch=\"360\"/>"
        "</w:sectPr>"
        "</w:body>"
        "</w:document>"
    )


def write_docx(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
    core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>SMILES2Docking Workflow for Publication</dc:title>
  <dc:creator>OpenAI Codex</dc:creator>
  <cp:lastModifiedBy>OpenAI Codex</cp:lastModifiedBy>
  <dc:description>Step-by-step workflow description for manuscript preparation.</dc:description>
</cp:coreProperties>
"""
    app = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application>
</Properties>
"""

    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("docProps/core.xml", core)
        docx.writestr("docProps/app.xml", app)
        docx.writestr("word/document.xml", build_document_xml())


if __name__ == "__main__":
    write_docx(OUTPUT_PATH)
    print(OUTPUT_PATH)
