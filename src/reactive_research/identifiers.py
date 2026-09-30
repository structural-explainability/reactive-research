# ============================================================
# src/reactive_research/identifiers.py
# ============================================================

"""Research-object identifier parsing and validation.

Examples:
SE-210.Definition.2.4
SE-210.Definition.4.3
SE-210.Theorem.5.2
SE-210.Proposition.4.14
SE-210.Example.4.11
SE-210.Remark.4.16c
"""

import re

from reactive_research.models import ResearchIdentifier

_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9_-]*"
    r"(?:\.[A-Za-z0-9][A-Za-z0-9_-]*)+$"
)


class InvalidResearchIdentifierError(ValueError):
    """Raised when a research-object identifier is malformed."""


def parse_research_identifier(value: str) -> ResearchIdentifier:
    """Parse and validate a research-object identifier."""
    normalized = value.strip()

    if not normalized:
        raise InvalidResearchIdentifierError("Research identifier must not be empty.")

    if not _IDENTIFIER_PATTERN.fullmatch(normalized):
        raise InvalidResearchIdentifierError(
            f"Invalid research identifier: {normalized!r}"
        )

    return ResearchIdentifier(normalized)
