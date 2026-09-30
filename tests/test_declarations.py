# ============================================================
# tests/test_declarations.py
# ============================================================

"""Tests for normalized Reactive Research declaration export."""

from pathlib import Path

from reactive_research.declarations import (
    declaration_document,
)
from reactive_research.extract import extract_repository


def test_declaration_document_normalizes_extracted_declarations(
    tmp_path: Path,
) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "# RR.DEFINES: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )

    result = extract_repository(tmp_path)

    document = declaration_document(
        result,
        extractor_version="0.1.0",
    )

    assert document["format"] == ("reactive-research-declarations")
    assert document["format_version"] == 1
    assert document["extractor_version"] == "0.1.0"

    declarations = document["declarations"]
    assert len(declarations) == 1

    declaration = declarations[0]

    assert declaration["identifier"] == ("SE-210.Definition.4.3")
    assert declaration["relation"] == "DEFINES"
    assert declaration["repository"] == tmp_path.name
    assert declaration["source_path"] == "example.py"
    assert declaration["source_line"] == 1
    assert declaration["source_kind"] == "py"
    assert declaration["extractor_version"] == "0.1.0"
