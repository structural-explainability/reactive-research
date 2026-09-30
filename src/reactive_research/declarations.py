# ============================================================
# src/reactive_research/declarations.py
# ============================================================

"""Normalized declaration documents for Reactive Research."""

from pathlib import Path
from typing import Any

from reactive_research.models import (
    Diagnostic,
    ExtractionResult,
    ResearchDeclaration,
)
from reactive_research.versioning import package_version

_DECLARATION_FORMAT = "reactive-research-declarations"
_DECLARATION_FORMAT_VERSION = 1


def export_declarations(path: Path) -> dict[str, Any]:
    """Extract and export normalized declarations for one repository."""
    # WHY: Local import avoids a module cycle because extract.py uses
    # declaration_document() for its machine-readable result.
    from reactive_research.extract import extract_repository

    result = extract_repository(path)
    return declaration_document(result)


def declaration_document(
    result: ExtractionResult,
    *,
    extractor_version: str | None = None,
) -> dict[str, Any]:
    """Return a normalized declaration document."""
    current_version = extractor_version or package_version()
    repository = result.repository

    return {
        "format": _DECLARATION_FORMAT,
        "format_version": _DECLARATION_FORMAT_VERSION,
        "extractor_version": current_version,
        "path": str(repository.root),
        "repository": {
            "organization": repository.organization,
            "name": repository.name,
            "revision": repository.revision,
        },
        "valid": result.valid,
        "declarations": [
            declaration_record(
                declaration,
                organization=repository.organization,
                repository=repository.name,
                revision=repository.revision,
                extractor_version=current_version,
            )
            for declaration in result.declarations
        ],
        "diagnostics": [
            diagnostic_record(diagnostic) for diagnostic in result.diagnostics
        ],
    }


def declaration_record(
    declaration: ResearchDeclaration,
    *,
    organization: str | None,
    repository: str,
    revision: str | None,
    extractor_version: str,
) -> dict[str, object]:
    """Return one normalized research declaration."""
    source_path = declaration.source.path

    return {
        "identifier": str(declaration.identifier),
        "relation": declaration.relation.value,
        "organization": organization,
        "repository": repository,
        "revision": revision,
        "source_path": source_path.as_posix(),
        "source_line": declaration.source.line,
        "source_kind": _source_kind(source_path),
        "extractor_version": extractor_version,
    }


def diagnostic_record(
    diagnostic: Diagnostic,
) -> dict[str, object]:
    """Return one normalized diagnostic."""
    source_path: str | None = None
    source_line: int | None = None

    if diagnostic.source is not None:
        source_path = diagnostic.source.path.as_posix()
        source_line = diagnostic.source.line

    return {
        "code": diagnostic.code,
        "severity": diagnostic.severity.value,
        "message": diagnostic.message,
        "source_path": source_path,
        "source_line": source_line,
    }


def is_declaration_document(value: object) -> bool:
    """Return whether a value has the normalized declaration-document shape."""
    if not isinstance(value, dict):
        return False

    return (
        value.get("format") == _DECLARATION_FORMAT
        and value.get("format_version") == _DECLARATION_FORMAT_VERSION
        and isinstance(value.get("declarations"), list)
    )


def _source_kind(path: Path) -> str:
    """Return a stable source-kind label from a source path."""
    suffix = path.suffix.lower().removeprefix(".")
    return suffix or "unknown"
