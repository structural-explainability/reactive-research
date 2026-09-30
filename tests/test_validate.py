# ============================================================
# tests/test_validate.py
# ============================================================

"""Tests for Reactive Research validation."""

from pathlib import Path

from reactive_research.validate import validate_research


def test_validate_accepts_valid_local_declaration(
    tmp_path: Path,
) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "# RR.DEFINES: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )

    result = validate_research(
        path=tmp_path,
        strict=False,
    )

    assert result["valid"]
    assert result["declaration_count"] == 1

    assert {diagnostic["code"] for diagnostic in result["diagnostics"]} == {
        "RR.MISSING_REVISION"
    }


def test_validate_strict_rejects_missing_revision(
    tmp_path: Path,
) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "# RR.DEFINES: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )

    result = validate_research(
        path=tmp_path,
        strict=True,
    )

    assert not result["valid"]


def test_validate_rejects_duplicate_local_definition(
    tmp_path: Path,
) -> None:
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

    result = validate_research(
        path=tmp_path,
        strict=False,
    )

    assert not result["valid"]

    assert "RR.DUPLICATE_LOCAL_DEFINITION" in {
        diagnostic["code"] for diagnostic in result["diagnostics"]
    }


def test_validate_rejects_unsupported_relation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "# RR.UNKNOWN: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )

    result = validate_research(
        path=tmp_path,
        strict=False,
    )

    assert not result["valid"]

    assert {diagnostic["code"] for diagnostic in result["diagnostics"]} == {
        "RR.UNSUPPORTED_RELATION"
    }


def test_validate_rejects_malformed_identifier(
    tmp_path: Path,
) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "# RR.DEFINES: not a valid identifier\n",
        encoding="utf-8",
    )

    result = validate_research(
        path=tmp_path,
        strict=False,
    )

    assert not result["valid"]

    assert {diagnostic["code"] for diagnostic in result["diagnostics"]} == {
        "RR.INVALID_IDENTIFIER"
    }
