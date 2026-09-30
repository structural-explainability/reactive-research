# ============================================================
# src/reactive_research/extract.py
# ============================================================

"""Extract Reactive Research declarations.

Can be provided in any source file with an eligible suffix.

Examples:
# RR.DEFINES: SE-210.Definition.4.3
# rr.defines: SE-210.Definition.4.3
# REACTIVE-RESEARCH.DEFINES: SE-210.Definition.4.3
# reactive-research.defines: SE-210.Definition.4.3
"""

from pathlib import Path
import re
from typing import Any

from reactive_research.identifiers import (
    InvalidResearchIdentifierError,
    parse_research_identifier,
)
from reactive_research.models import (
    Diagnostic,
    DiagnosticSeverity,
    ExtractionResult,
    ResearchDeclaration,
    ResearchRelation,
    SourceLocation,
)
from reactive_research.repository import discover_repository_context

_NAMESPACE = r"(?:RR|REACTIVE-RESEARCH)"
_RELATION = r"(?P<relation>DEFINES|IMPLEMENTS)"

_ANNOTATION_PATTERNS = {
    ".py": re.compile(
        rf"^\s*#\s*{_NAMESPACE}\.{_RELATION}:\s*"
        r"(?P<identifier>[A-Za-z][A-Za-z0-9_.-]*)\s*$",
        re.IGNORECASE,
    ),
    ".toml": re.compile(
        rf"^\s*#\s*{_NAMESPACE}\.{_RELATION}:\s*"
        r"(?P<identifier>[A-Za-z][A-Za-z0-9_.-]*)\s*$",
        re.IGNORECASE,
    ),
    ".lean": re.compile(
        rf"^\s*--\s*{_NAMESPACE}\.{_RELATION}:\s*"
        r"(?P<identifier>[A-Za-z][A-Za-z0-9_.-]*)\s*$",
        re.IGNORECASE,
    ),
    ".tex": re.compile(
        rf"^\s*%\s*{_NAMESPACE}\.{_RELATION}:\s*"
        r"(?P<identifier>[A-Za-z][A-Za-z0-9_.-]*)\s*$",
        re.IGNORECASE,
    ),
    ".md": re.compile(
        rf"^\s*<!--\s*{_NAMESPACE}\.{_RELATION}:\s*"
        r"(?P<identifier>[A-Za-z][A-Za-z0-9_.-]*)\s*-->\s*$",
        re.IGNORECASE,
    ),
}

_INCLUDED_SUFFIXES = set(_ANNOTATION_PATTERNS)

_IGNORED_DIRECTORIES = {
    ".git",
    ".lake",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site",
    "tests",
}

_IGNORED_FILE_NAMES = {
    "CHANGELOG.md",
    "README.md",
}


def extract_repository(path: Path) -> ExtractionResult:
    """Extract Reactive Research declarations from one repository."""
    repository = discover_repository_context(path)

    declarations: list[ResearchDeclaration] = []
    diagnostics: list[Diagnostic] = []

    for source_path in _source_files(repository.root):
        source_declarations, source_diagnostics = _extract_file(
            source_path,
            root=repository.root,
        )
        declarations.extend(source_declarations)
        diagnostics.extend(source_diagnostics)

    diagnostics.extend(_duplicate_definition_diagnostics(declarations))

    return ExtractionResult(
        repository=repository,
        declarations=tuple(declarations),
        diagnostics=tuple(diagnostics),
    )


def extract_research(
    *,
    path: Path,
    check: bool = False,
) -> dict[str, Any]:
    """Extract declarations and return the CLI representation."""
    result = extract_repository(path)

    return {
        "command": "extract",
        "path": str(result.repository.root),
        "repository": result.repository.name,
        "organization": result.repository.organization,
        "revision": result.repository.revision,
        "check": check,
        "valid": result.valid,
        "defines": [_declaration_dict(declaration) for declaration in result.defines],
        "implements": [
            _declaration_dict(declaration) for declaration in result.implements
        ],
        "diagnostics": [
            _diagnostic_dict(diagnostic) for diagnostic in result.diagnostics
        ],
    }


def _source_files(root: Path) -> list[Path]:
    """Return deterministic source files eligible for extraction."""
    paths: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if path.name in _IGNORED_FILE_NAMES:
            continue

        if path.suffix.lower() not in _INCLUDED_SUFFIXES:
            continue

        relative = path.relative_to(root)

        if any(part in _IGNORED_DIRECTORIES for part in relative.parts):
            continue

        paths.append(path)

    return sorted(paths)


def _extract_file(
    path: Path,
    *,
    root: Path,
) -> tuple[list[ResearchDeclaration], list[Diagnostic]]:
    """Extract authoritative declarations from one source file."""
    declarations: list[ResearchDeclaration] = []
    diagnostics: list[Diagnostic] = []

    pattern = _ANNOTATION_PATTERNS.get(path.suffix.lower())
    if pattern is None:
        return declarations, diagnostics

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return declarations, diagnostics

    relative_path = path.relative_to(root)

    for line_number, line in enumerate(text.splitlines(), start=1):
        match = pattern.fullmatch(line)
        if match is None:
            continue

        location = SourceLocation(
            path=relative_path,
            line=line_number,
        )

        relation = ResearchRelation(match.group("relation").upper())
        raw_identifier = match.group("identifier")

        try:
            identifier = parse_research_identifier(raw_identifier)
        except InvalidResearchIdentifierError as error:
            diagnostics.append(
                Diagnostic(
                    code="RR.INVALID_IDENTIFIER",
                    message=str(error),
                    severity=DiagnosticSeverity.ERROR,
                    source=location,
                )
            )
            continue

        declarations.append(
            ResearchDeclaration(
                relation=relation,
                identifier=identifier,
                source=location,
            )
        )

    return declarations, diagnostics


def _duplicate_definition_diagnostics(
    declarations: list[ResearchDeclaration],
) -> list[Diagnostic]:
    """Report research objects defined more than once locally."""
    definitions: dict[str, list[ResearchDeclaration]] = {}

    for declaration in declarations:
        if declaration.relation is not ResearchRelation.DEFINES:
            continue

        definitions.setdefault(
            str(declaration.identifier),
            [],
        ).append(declaration)

    diagnostics: list[Diagnostic] = []

    for identifier, matches in sorted(definitions.items()):
        if len(matches) < 2:
            continue

        for declaration in matches:
            diagnostics.append(
                Diagnostic(
                    code="RR.DUPLICATE_LOCAL_DEFINITION",
                    message=(
                        f"{identifier} is defined more than once in this repository."
                    ),
                    severity=DiagnosticSeverity.ERROR,
                    source=declaration.source,
                )
            )

    return diagnostics


def _declaration_dict(
    declaration: ResearchDeclaration,
) -> dict[str, object]:
    """Convert one declaration to the CLI representation."""
    return {
        "relation": declaration.relation.value,
        "identifier": str(declaration.identifier),
        "source_path": declaration.source.path.as_posix(),
        "source_line": declaration.source.line,
    }


def _diagnostic_dict(
    diagnostic: Diagnostic,
) -> dict[str, object]:
    """Convert one diagnostic to the CLI representation."""
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
