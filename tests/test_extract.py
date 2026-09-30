# ============================================================
# tests/test_extract.py
# ============================================================

"""Tests for Reactive Research extraction."""

from pathlib import Path

from reactive_research.extract import extract_repository
from reactive_research.models import ResearchRelation


def test_extract_repository_finds_defines_and_implements(
    tmp_path: Path,
) -> None:
    """Source annotations become typed research declarations."""
    source = tmp_path / "example.py"
    source.write_text(
        '"""Example."""\n\n# RR.DEFINES: SE-210.Definition.4.3\n# RR.IMPLEMENTS: SE-210.Theorem.5.2',
        encoding="utf-8",
    )

    result = extract_repository(tmp_path)

    assert result.valid
    assert len(result.declarations) == 2

    assert result.declarations[0].relation is ResearchRelation.DEFINES
    assert str(result.declarations[0].identifier) == ("SE-210.Definition.4.3")
    assert result.declarations[0].source.path == Path("example.py")
    assert result.declarations[0].source.line == 3

    assert result.declarations[1].relation is ResearchRelation.IMPLEMENTS
    assert str(result.declarations[1].identifier) == ("SE-210.Theorem.5.2")


def test_extract_repository_reports_duplicate_local_definition(
    tmp_path: Path,
) -> None:
    """One research identifier cannot be defined twice locally."""
    first = tmp_path / "first.py"
    second = tmp_path / "second.py"

    first.write_text(
        "# RR.DEFINES: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )
    second.write_text(
        "# RR.DEFINES: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )

    result = extract_repository(tmp_path)

    assert not result.valid
    assert {diagnostic.code for diagnostic in result.diagnostics} == {
        "RR.DUPLICATE_LOCAL_DEFINITION"
    }


def test_extract_repository_ignores_generated_directories(
    tmp_path: Path,
) -> None:
    """Generated and environment directories are not scanned."""
    source = tmp_path / ".venv" / "example.py"
    source.parent.mkdir()
    source.write_text(
        "# RR.DEFINES: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )

    result = extract_repository(tmp_path)

    assert result.declarations == ()
