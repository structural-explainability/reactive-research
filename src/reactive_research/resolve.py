# ============================================================
# src/reactive_research/resolve.py
# ============================================================

"""Resolve Reactive Research identifiers."""

import json
from pathlib import Path
from typing import Any

from reactive_research.declarations import (
    export_declarations,
    is_declaration_document,
)
from reactive_research.identifiers import (
    InvalidResearchIdentifierError,
    parse_research_identifier,
)

_DEFINES = "DEFINES"
_IMPLEMENTS = "IMPLEMENTS"


class RegistryLoadError(ValueError):
    """Raised when declaration registry input cannot be loaded."""


def resolve_research(
    *,
    path: Path,
    identifier: str | None,
    resolve_all: bool,
    registry: str | None,
    snapshot: str | None,
) -> dict[str, Any]:
    """Resolve research-object references."""
    if snapshot is not None:
        from reactive_research.snapshot import load_snapshot

        graph = load_snapshot(snapshot, registry)
        if identifier is not None:
            try:
                identifier = str(parse_research_identifier(identifier))
            except InvalidResearchIdentifierError as error:
                return {
                    "command": "resolve",
                    "resolved": False,
                    "results": [],
                    "snapshot_id": graph["snapshot_id"],
                    "diagnostics": [
                        {
                            "code": "RR.INVALID_IDENTIFIER",
                            "severity": "error",
                            "message": str(error),
                        }
                    ],
                }
        definitions = {
            node["label"]: node.get("definitions", [])
            for node in graph["nodes"]
            if node["kind"] == "object"
        }
        targets = (
            [identifier]
            if identifier is not None
            else sorted(
                {
                    edge["target"].removeprefix("object:")
                    for edge in graph["edges"]
                    if resolve_all
                    and edge["relation"] == "implements"
                    and edge["target"].startswith("object:")
                }
            )
        )
        results = [
            _resolve_identifier(target, definitions=definitions) for target in targets
        ]
        return {
            "command": "resolve",
            "path": str(path.resolve()),
            "identifier": identifier,
            "resolve_all": resolve_all,
            "registry": registry,
            "snapshot": snapshot,
            "resolved": all(result["status"] == "resolved" for result in results),
            "results": results,
            "diagnostics": [],
            "snapshot_id": graph["snapshot_id"],
        }

    current_document = export_declarations(path)
    try:
        registry_documents = _load_registry_documents(
            registry,
            current_document=current_document,
        )
    except RegistryLoadError as error:
        return {
            "command": "resolve",
            "path": str(path.resolve()),
            "identifier": identifier,
            "resolve_all": resolve_all,
            "registry": registry,
            "snapshot": snapshot,
            "resolved": False,
            "results": [],
            "diagnostics": [
                {
                    "code": "RR.REGISTRY_LOAD_ERROR",
                    "severity": "error",
                    "message": str(error),
                }
            ],
        }

    targets, target_error = _resolution_targets(
        current_document=current_document,
        identifier=identifier,
        resolve_all=resolve_all,
    )

    if target_error is not None:
        return {
            "command": "resolve",
            "path": str(path.resolve()),
            "identifier": identifier,
            "resolve_all": resolve_all,
            "registry": registry,
            "snapshot": snapshot,
            "resolved": False,
            "results": [],
            "diagnostics": [target_error],
        }

    declarations = _registry_declarations(registry_documents)

    definitions = _definitions_by_identifier(declarations)

    results = [
        _resolve_identifier(
            target,
            definitions=definitions,
        )
        for target in targets
    ]

    resolved = all(result["status"] == "resolved" for result in results)

    return {
        "command": "resolve",
        "path": str(path.resolve()),
        "identifier": identifier,
        "resolve_all": resolve_all,
        "registry": registry,
        "snapshot": snapshot,
        "resolved": resolved,
        "results": results,
        "diagnostics": [],
    }


def _resolution_targets(
    *,
    current_document: dict[str, Any],
    identifier: str | None,
    resolve_all: bool,
) -> tuple[list[str], dict[str, str] | None]:
    """Return identifiers requested for resolution."""
    if identifier is not None:
        try:
            parsed = parse_research_identifier(identifier)
        except InvalidResearchIdentifierError as error:
            return [], {
                "code": "RR.INVALID_IDENTIFIER",
                "severity": "error",
                "message": str(error),
            }

        return [str(parsed)], None

    if not resolve_all:
        return [], None

    declarations = current_document.get(
        "declarations",
        [],
    )

    targets = {
        declaration["identifier"]
        for declaration in declarations
        if isinstance(declaration, dict)
        and declaration.get("relation") == _IMPLEMENTS
        and isinstance(
            declaration.get("identifier"),
            str,
        )
    }

    return sorted(targets), None


def _load_registry_documents(
    registry: str | None,
    *,
    current_document: dict[str, Any],
) -> list[dict[str, Any]]:
    """Load normalized declaration documents used for resolution."""
    documents = [current_document]

    if registry is None:
        return documents

    registry_path = Path(registry).resolve()

    if not registry_path.exists():
        raise RegistryLoadError(f"Registry location does not exist: {registry_path}")

    if registry_path.is_file():
        documents.append(_load_declaration_file(registry_path))
        return documents

    if not registry_path.is_dir():
        raise RegistryLoadError(
            f"Registry location is not a file or directory: {registry_path}"
        )

    registry_files = sorted(registry_path.glob("*.json"))

    for registry_file in registry_files:
        documents.append(_load_declaration_file(registry_file))

    return documents


def _load_declaration_file(
    path: Path,
) -> dict[str, Any]:
    """Load one normalized declaration document."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        raise RegistryLoadError(
            f"Could not load registry file {path}: {error}"
        ) from error

    if not is_declaration_document(value):
        raise RegistryLoadError(
            f"Registry file is not a supported Reactive "
            f"Research declaration document: {path}"
        )

    return value


def _registry_declarations(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return unique declarations from registry documents."""
    declarations: list[dict[str, Any]] = []
    seen: set[tuple[object, ...]] = set()

    for document in documents:
        values = document.get("declarations", [])

        if not isinstance(values, list):
            continue

        for declaration in values:
            if not isinstance(declaration, dict):
                continue

            key = (
                declaration.get("relation"),
                declaration.get("identifier"),
                declaration.get("organization"),
                declaration.get("repository"),
                declaration.get("revision"),
                declaration.get("source_path"),
                declaration.get("source_line"),
            )

            if key in seen:
                continue

            seen.add(key)
            declarations.append(declaration)

    return declarations


def _definitions_by_identifier(
    declarations: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Index authoritative definitions by identifier."""
    definitions: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for declaration in declarations:
        if declaration.get("relation") != _DEFINES:
            continue

        identifier = declaration.get("identifier")
        if not isinstance(identifier, str):
            continue

        definitions.setdefault(
            identifier,
            [],
        ).append(declaration)

    return definitions


def _resolve_identifier(
    identifier: str,
    *,
    definitions: dict[
        str,
        list[dict[str, Any]],
    ],
) -> dict[str, Any]:
    """Resolve one identifier against authoritative definitions."""
    matches = definitions.get(identifier, [])

    if not matches:
        status = "unresolved"
    elif len(matches) == 1:
        status = "resolved"
    else:
        status = "duplicate-definition"

    return {
        "identifier": identifier,
        "status": status,
        "definitions": matches,
    }
