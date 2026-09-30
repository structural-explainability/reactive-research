# ============================================================
# tests/test_identifiers.py
# ============================================================

"""Tests for Reactive Research identifiers."""

import pytest

from reactive_research.identifiers import (
    InvalidResearchIdentifierError,
    parse_research_identifier,
)


@pytest.mark.parametrize(
    "value",
    [
        "SE-210.Definition.2.4",
        "SE-210.Theorem.5.2",
        "SE-210.Proposition.4.14",
        "SE-210.Example.4.11",
        "SE-210.Remark.4.16c",
    ],
)
def test_parse_research_identifier_accepts_known_shapes(
    value: str,
) -> None:
    """Known research identifiers are accepted."""
    identifier = parse_research_identifier(value)

    assert str(identifier) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "Definition",
        ".SE-210.Definition.2.4",
        "SE-210 Definition 2.4",
    ],
)
def test_parse_research_identifier_rejects_invalid_shapes(
    value: str,
) -> None:
    """Malformed research identifiers are rejected."""
    with pytest.raises(InvalidResearchIdentifierError):
        parse_research_identifier(value)
