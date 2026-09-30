# ============================================================
# src/reactive_research/validate.py
# ============================================================

"""Validate repository-local Reactive Research declarations."""

from pathlib import Path
from typing import Any

from reactive_research.declarations import (
    declaration_document,
    diagnostic_record,
)
from reactive_research.extract import extract_repository
from reactive_research.identifiers import (
    InvalidResearchIdentifierError,
    parse_research_identifier,
)
from reactive_research.models import (
    Diagnostic,
    DiagnosticSeverity,
    ExtractionResult,
)


def validate_research(
    *,
    path: Path,
    strict: bool = False,
) -> dict[str, Any]:
    """Validate repository-local Reactive Research declarations."""
    extraction = extract_repository(path)
    diagnostics = validate_extraction(
        extraction,
        strict=strict,
    )

    document = declaration_document(extraction)

    valid = _diagnostics_are_valid(
        diagnostics,
        strict=strict,
    )

    return {
        "command": "validate",
        "path": str(extraction.repository.root),
        "repository": extraction.repository.name,
        "organization": extraction.repository.organization,
        "revision": extraction.repository.revision,
        "strict": strict,
        "valid": valid,
        "declaration_count": len(extraction.declarations),
        "declarations": document["declarations"],
        "diagnostics": [diagnostic_record(diagnostic) for diagnostic in diagnostics],
    }


def validate_extraction(
    extraction: ExtractionResult,
    *,
    strict: bool = False,
) -> tuple[Diagnostic, ...]:
    """Validate one previously extracted repository result."""
    del strict

    diagnostics = list(extraction.diagnostics)

    repository = extraction.repository

    if not repository.name.strip():
        diagnostics.append(
            Diagnostic(
                code="RR.MISSING_REPOSITORY_NAME",
                message="Repository name must not be empty.",
                severity=DiagnosticSeverity.ERROR,
            )
        )

    if extraction.declarations and repository.revision is None:
        diagnostics.append(
            Diagnostic(
                code="RR.MISSING_REVISION",
                message=(
                    "Repository contains Reactive Research declarations "
                    "but no Git revision could be determined."
                ),
                severity=DiagnosticSeverity.WARNING,
            )
        )

    for declaration in extraction.declarations:
        if declaration.source.path.is_absolute():
            diagnostics.append(
                Diagnostic(
                    code="RR.ABSOLUTE_SOURCE_PATH",
                    message=("Declaration source paths must be repository-relative."),
                    severity=DiagnosticSeverity.ERROR,
                    source=declaration.source,
                )
            )

        if declaration.source.line < 1:
            diagnostics.append(
                Diagnostic(
                    code="RR.INVALID_SOURCE_LINE",
                    message=("Declaration source line must be greater than zero."),
                    severity=DiagnosticSeverity.ERROR,
                    source=declaration.source,
                )
            )

        try:
            parse_research_identifier(str(declaration.identifier))
        except InvalidResearchIdentifierError as error:
            diagnostics.append(
                Diagnostic(
                    code="RR.INVALID_IDENTIFIER",
                    message=str(error),
                    severity=DiagnosticSeverity.ERROR,
                    source=declaration.source,
                )
            )

    return tuple(diagnostics)


def _diagnostics_are_valid(
    diagnostics: tuple[Diagnostic, ...],
    *,
    strict: bool,
) -> bool:
    """Return whether diagnostics satisfy the requested validation mode."""
    for diagnostic in diagnostics:
        if diagnostic.severity is DiagnosticSeverity.ERROR:
            return False

        if strict and diagnostic.severity is DiagnosticSeverity.WARNING:
            return False

    return True
