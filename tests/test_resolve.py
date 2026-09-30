# ============================================================
# tests/test_resolve.py
# ============================================================

"""Tests for Reactive Research resolution."""

import json
from pathlib import Path

from reactive_research.declarations import export_declarations
from reactive_research.resolve import resolve_research


def test_resolve_finds_one_authoritative_definition(
    tmp_path: Path,
) -> None:
    provider = tmp_path / "provider"
    consumer = tmp_path / "consumer"
    registry = tmp_path / "registry"

    provider.mkdir()
    consumer.mkdir()
    registry.mkdir()

    (provider / "definition.py").write_text(
        "# RR.DEFINES: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )
    (consumer / "implementation.py").write_text(
        "# RR.IMPLEMENTS: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )

    provider_document = export_declarations(provider)

    (registry / "provider.json").write_text(
        json.dumps(provider_document),
        encoding="utf-8",
    )

    result = resolve_research(
        path=consumer,
        identifier="SE-210.Definition.4.3",
        resolve_all=False,
        registry=str(registry),
        snapshot=None,
    )

    assert result["resolved"]
    assert len(result["results"]) == 1

    resolution = result["results"][0]

    assert resolution["identifier"] == ("SE-210.Definition.4.3")
    assert resolution["status"] == "resolved"
    assert len(resolution["definitions"]) == 1


def test_resolve_all_uses_implements_declarations(
    tmp_path: Path,
) -> None:
    provider = tmp_path / "provider"
    consumer = tmp_path / "consumer"
    registry = tmp_path / "registry"

    provider.mkdir()
    consumer.mkdir()
    registry.mkdir()

    (provider / "definition.py").write_text(
        "# RR.DEFINES: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )
    (consumer / "implementation.py").write_text(
        "# RR.IMPLEMENTS: SE-210.Definition.4.3\n",
        encoding="utf-8",
    )

    (registry / "provider.json").write_text(
        json.dumps(export_declarations(provider)),
        encoding="utf-8",
    )

    result = resolve_research(
        path=consumer,
        identifier=None,
        resolve_all=True,
        registry=str(registry),
        snapshot=None,
    )

    assert result["resolved"]

    assert result["results"][0]["status"] == ("resolved")


def test_resolve_reports_unresolved_identifier(
    tmp_path: Path,
) -> None:
    consumer = tmp_path / "consumer"
    consumer.mkdir()

    result = resolve_research(
        path=consumer,
        identifier="SE-210.Definition.4.3",
        resolve_all=False,
        registry=None,
        snapshot=None,
    )

    assert not result["resolved"]

    assert result["results"][0]["status"] == ("unresolved")


def test_resolve_detects_duplicate_definitions(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    consumer = tmp_path / "consumer"
    registry = tmp_path / "registry"

    first.mkdir()
    second.mkdir()
    consumer.mkdir()
    registry.mkdir()

    for repository in (first, second):
        (repository / "definition.py").write_text(
            "# RR.DEFINES: SE-210.Definition.4.3\n",
            encoding="utf-8",
        )

    (registry / "first.json").write_text(
        json.dumps(export_declarations(first)),
        encoding="utf-8",
    )
    (registry / "second.json").write_text(
        json.dumps(export_declarations(second)),
        encoding="utf-8",
    )

    result = resolve_research(
        path=consumer,
        identifier="SE-210.Definition.4.3",
        resolve_all=False,
        registry=str(registry),
        snapshot=None,
    )

    assert not result["resolved"]

    assert result["results"][0]["status"] == ("duplicate-definition")
