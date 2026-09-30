# ============================================================
# src/reactive_research/models.py
# ============================================================

"""Core data models for Reactive Research."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class ResearchRelation(StrEnum):
    """Supported relationships between repositories and research objects."""

    DEFINES = "DEFINES"
    IMPLEMENTS = "IMPLEMENTS"


class DiagnosticSeverity(StrEnum):
    """Severity of one Reactive Research diagnostic."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ResearchIdentifier:
    """Stable identifier for one addressable research object."""

    value: str

    def __str__(self) -> str:
        """Return the canonical identifier string."""
        return self.value


@dataclass(frozen=True)
class SourceLocation:
    """Location of one declaration in repository source."""

    path: Path
    line: int


@dataclass(frozen=True)
class ResearchDeclaration:
    """One typed relationship to an addressable research object."""

    relation: ResearchRelation
    identifier: ResearchIdentifier
    source: SourceLocation


@dataclass(frozen=True)
class RepositoryContext:
    """Identity and revision of the repository being examined."""

    root: Path
    organization: str | None
    name: str
    revision: str | None


@dataclass(frozen=True)
class Diagnostic:
    """One extraction or validation finding."""

    code: str
    message: str
    severity: DiagnosticSeverity
    source: SourceLocation | None = None


@dataclass(frozen=True)
class ExtractionResult:
    """Complete result of extracting one repository."""

    repository: RepositoryContext
    declarations: tuple[ResearchDeclaration, ...] = field(default_factory=tuple)
    diagnostics: tuple[Diagnostic, ...] = field(default_factory=tuple)

    @property
    def defines(self) -> tuple[ResearchDeclaration, ...]:
        """Return all DEFINES declarations."""
        return tuple(
            declaration
            for declaration in self.declarations
            if declaration.relation is ResearchRelation.DEFINES
        )

    @property
    def implements(self) -> tuple[ResearchDeclaration, ...]:
        """Return all IMPLEMENTS declarations."""
        return tuple(
            declaration
            for declaration in self.declarations
            if declaration.relation is ResearchRelation.IMPLEMENTS
        )

    @property
    def valid(self) -> bool:
        """Return whether extraction produced no error diagnostics."""
        return not any(
            diagnostic.severity is DiagnosticSeverity.ERROR
            for diagnostic in self.diagnostics
        )
