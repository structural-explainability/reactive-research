"""Small observation adapters for existing declarations, dependencies and freezes."""

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import tomllib
from typing import Any

from reactive_research.declarations import declaration_record, diagnostic_record
from reactive_research.extract import (
    _IGNORED_DIRECTORIES,
    _IGNORED_FILE_NAMES,
    extract_source_text,
)
from reactive_research.observation import digest


@dataclass(frozen=True)
class Relationship:
    """One observed typed edge, retaining evidence and version constraints."""

    source: str
    target: str
    relation: str
    kind: str
    evidence: dict[str, Any]
    constraint: dict[str, Any]

    def record(self) -> dict[str, Any]:
        """Return a stable JSON edge with a content-addressed identity."""
        value = asdict(self)
        return {"id": "edge:" + digest(value), **value}


def text(data: dict[str, bytes], name: str) -> str:
    """Decode an observed text surface without altering its bytes."""
    return data.get(name, b"").decode("utf-8", errors="replace")


def toml(
    data: dict[str, bytes], name: str, diagnostics: list[dict[str, Any]]
) -> dict[str, Any]:
    """Read a TOML surface, preserving parse failure as a diagnostic."""
    if name not in data:
        return {}
    try:
        return tomllib.loads(text(data, name))
    except tomllib.TOMLDecodeError as error:
        diagnostics.append(
            {"code": "RR.SURFACE_PARSE", "path": name, "message": str(error)}
        )
        return {}


def observe_surfaces(
    project: dict[str, Any],
    data: dict[str, bytes],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Translate existing source surfaces into nodes, edges and declarations."""
    pid = project["id"]
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    declarations: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    state = project["state"]

    def evidence(
        name: str, line: int | None = None, adapter: str = "declaration"
    ) -> dict[str, Any]:
        return {
            "project": pid,
            "path": name,
            "line": line,
            "source_revision": state["source_revision"],
            "state": state["mode"],
            "file_digest": state["files"].get(name),
            "adapter": adapter,
        }

    def edge(
        source: str,
        target: str,
        relation: str,
        name: str,
        kind: str = "semantic",
        constraint: dict[str, Any] | None = None,
        line: int | None = None,
        adapter: str = "declaration",
    ) -> None:
        edges.append(
            Relationship(
                source,
                target,
                relation,
                kind,
                evidence(name, line, adapter),
                constraint or {},
            ).record()
        )

    def artifact(name: str, *, lifecycle: str = "unspecified") -> str:
        aid = f"{pid}/artifact:{name}"
        nodes.setdefault(
            aid,
            {
                "id": aid,
                "label": name,
                "kind": "artifact",
                "project": pid,
                "lifecycle": lifecycle,
                "state": {k: v for k, v in state.items() if k != "files"},
                "content_digest": state["files"].get(name),
                "evidence": evidence(name),
            },
        )
        return aid

    def definition(
        identifier: str, name: str, line: int, content: bytes, adapter: str
    ) -> None:
        oid = "object:" + identifier
        definition_record = {
            "repository": project["name"],
            "organization": project.get("organization"),
            "project": pid,
            "revision": state["source_revision"],
            "state": state["mode"],
            "content_digest": hashlib.sha256(content).hexdigest(),
            "source_path": name,
            "source_line": line,
            "adapter": adapter,
        }
        node = nodes.setdefault(
            oid, {"id": oid, "label": identifier, "kind": "object", "definitions": []}
        )
        node["definitions"].append(definition_record)
        edge(pid, oid, "defines", name, "ownership", line=line, adapter=adapter)

    for name, content in sorted(data.items()):
        path = Path(name)
        value = text(data, name)
        if (
            not any(part in _IGNORED_DIRECTORIES for part in path.parts)
            and path.name not in _IGNORED_FILE_NAMES
        ):
            found, errors = extract_source_text(value, path=path)
            diagnostics.extend({**diagnostic_record(d), "project": pid} for d in errors)
            for declaration in found:
                identifier = str(declaration.identifier)
                raw = declaration.relation.value
                declarations.append(
                    declaration_record(
                        declaration,
                        organization=project.get("organization"),
                        repository=project["name"],
                        revision=state["source_revision"],
                        extractor_version="observation-1",
                    )
                    | {"state": state["mode"], "project": pid}
                )
                if raw == "DEFINES":
                    definition(identifier, name, declaration.source.line, content, "RR")
                else:
                    relation = (
                        "depends-on"
                        if raw == "DEPENDS"
                        else raw.lower().replace("_", "-")
                    )
                    edge(
                        pid,
                        "object:" + identifier,
                        relation,
                        name,
                        line=declaration.source.line,
                        adapter="RR",
                    )
        # A paper's explicit stable labels supply definitions, never name similarity.
        if path.suffix == ".tex" and project.get("class") == "paper":
            for match in re.finditer(r"\\label\{(se\d+\.[^}]+)\}", value):
                end = re.search(r"\\end\{[^}]+\}", value[match.end() :])
                stop = match.end() + end.end() if end else match.end()
                definition(
                    match[1],
                    name,
                    value[: match.start()].count("\n") + 1,
                    value[match.start() : stop].encode(),
                    "paper-label",
                )
        # Only a module's explicit 'formalizes' header counts as a formalization.
        if path.suffix == ".lean":
            header = re.search(
                r"This module formalizes:(.*?)(?:\n\n|-/)", value, re.DOTALL
            )
            if header:
                for match in re.finditer(r"`(se\d+\.[^`]+)`", header[1]):
                    edge(
                        artifact(name),
                        "object:" + match[1],
                        "formalizes",
                        name,
                        line=value[: header.start()].count("\n") + 1,
                        adapter="explicit-formalization-header",
                    )

    manifest_name = next(
        (
            n
            for n in ("SE_MANIFEST.toml", "MANIFEST.toml", "se-manifest.toml")
            if n in data
        ),
        None,
    )
    manifest = toml(data, manifest_name, diagnostics) if manifest_name else {}
    if manifest_name == "se-manifest.toml":
        diagnostics.append(
            {
                "code": "RR.LEGACY_MANIFEST_FILENAME",
                "project": pid,
                "path": manifest_name,
            }
        )
    declared_targets: set[str] = set()
    for required in ("required", "optional"):
        items = manifest.get("depends", {}).get(required, [])
        if not isinstance(items, list):
            diagnostics.append(
                {
                    "code": "RR.MALFORMED_DEPENDENCIES",
                    "project": pid,
                    "path": manifest_name,
                }
            )
            continue
        for item in items:
            record = {"repository": item} if isinstance(item, str) else item
            if not isinstance(record, dict):
                diagnostics.append(
                    {"code": "RR.UNRESOLVED_DEPENDENCY", "project": pid, "raw": item}
                )
                continue
            target = record.get("repository", record.get("repo"))
            if not isinstance(target, str):
                diagnostics.append(
                    {"code": "RR.UNRESOLVED_DEPENDENCY", "project": pid, "raw": record}
                )
                continue
            declared_targets.add(target)
            edge(
                pid,
                "alias:" + target,
                "depends-on",
                manifest_name or "",
                record.get("kind", "semantic"),
                {**record, "required": required == "required"},
                adapter="SE-manifest",
            )
            if "repo" in record:
                diagnostics.append(
                    {"code": "RR.LEGACY_DEPENDENCY_KEY", "project": pid, "raw": record}
                )

    lake = toml(data, "lakefile.toml", diagnostics)
    try:
        lock = (
            json.loads(text(data, "lake-manifest.json"))
            if "lake-manifest.json" in data
            else {}
        )
    except json.JSONDecodeError as error:
        diagnostics.append(
            {
                "code": "RR.SURFACE_PARSE",
                "project": pid,
                "path": "lake-manifest.json",
                "message": str(error),
            }
        )
        lock = {}
    packages = {
        p.get("name", "").strip("«»"): p
        for p in lock.get("packages", [])
        if isinstance(p, dict)
    }
    for requirement in lake.get("require", []):
        name = requirement.get("name")
        if not isinstance(name, str):
            continue
        pinned = packages.get(name, {})
        constraint = {
            "requested_revision": requirement.get("rev"),
            "resolved_revision": pinned.get("rev"),
            "url": requirement.get("git", pinned.get("url")),
            "lock_evidence": "lake-manifest.json" if pinned else None,
        }
        edge(
            pid,
            "alias:" + name,
            "depends-on",
            "lakefile.toml",
            "build",
            constraint,
            adapter="Lake",
        )
        if name not in declared_targets and name.startswith("se-"):
            diagnostics.append(
                {
                    "code": "RR.TECHNICAL_EDGE_NOT_IN_MANIFEST",
                    "project": pid,
                    "target": name,
                    "path": "lakefile.toml",
                    "disposition": "mechanical candidate",
                }
            )

    pyproject = toml(data, "pyproject.toml", diagnostics)
    for dependency in pyproject.get("project", {}).get("dependencies", []):
        if not isinstance(dependency, str):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)", dependency)
        if match:
            edge(
                pid,
                "alias:" + match[1],
                "depends-on",
                "pyproject.toml",
                "build",
                {"requirement": dependency},
                adapter="Python-runtime-dependency",
            )

    # Reference mappings assert paper identity and a specific Lean target.
    for name in sorted(data):
        if name.startswith("reference/") and name.endswith(".toml"):
            document = toml(data, name, diagnostics)
            for records in document.values():
                if not isinstance(records, dict):
                    continue
                for record in records.values():
                    if isinstance(record, dict) and isinstance(
                        record.get("cite_id"), str
                    ):
                        module = record.get("target_module")
                        source = (
                            artifact(module.replace(".", "/") + ".lean")
                            if isinstance(module, str)
                            else pid
                        )
                        edge(
                            source,
                            "object:" + record["cite_id"],
                            "formalizes" if module else "cites",
                            name,
                            constraint={
                                "lean_symbol": record.get("target_symbol"),
                                "mapping": record,
                            },
                            adapter="theory-reference",
                        )

    # The motivation paragraph explicitly introduces linked research as context.
    readme = text(data, "README.md")
    for block in re.finditer(
        r"[^\n]*motivated[^\n]*\n(?:.*\n){0,5}", readme, re.IGNORECASE
    ):
        for match in re.finditer(
            r"https://github\.com/[^/\s)]+/([A-Za-z0-9_.-]+)", block[0]
        ):
            edge(
                "alias:" + match[1],
                pid,
                "informs",
                "README.md",
                "context",
                {
                    "interpretation": "Explicit motivation; no technical dependency asserted."
                },
                line=readme[: block.start()].count("\n") + 1,
                adapter="explicit-motivation-link",
            )

    for name in sorted(data):
        if not Path(name).name.startswith("FREEZE") or not name.endswith(".md"):
            continue
        value = text(data, name)
        if not re.search(r"\*\*Status:\*\*\s*FROZEN\b", value):
            continue
        frozen = artifact(name, lifecycle="frozen-record")
        nodes[frozen]["lifecycle"] = "frozen-record"
        commit = re.search(r"Frozen content commit:\*\*\s*`([0-9a-f]{40})`", value)
        for match in re.finditer(r"- `([0-9a-f]{64})`\s+`([^`]+)`", value):
            expected, member = match.groups()
            protected = artifact(member, lifecycle="frozen")
            nodes[protected]["lifecycle"] = "frozen"
            nodes[protected]["protection"] = {
                "record": frozen,
                "expected_sha256": expected,
                "observed_sha256": state["files"].get(member),
                "hash_matches": state["files"].get(member) == expected,
                "frozen_content_commit": commit[1] if commit else None,
                "directive": "DO NOT MODIFY FROZEN EVIDENCE",
            }
            edge(
                frozen,
                protected,
                "freezes",
                name,
                "protection",
                nodes[protected]["protection"],
                line=value[: match.start()].count("\n") + 1,
                adapter="freeze-hash-commitment",
            )
            if state["files"].get(member) != expected:
                diagnostics.append(
                    {
                        "code": "RR.FREEZE_HASH_MISMATCH",
                        "project": pid,
                        "path": member,
                        "expected": expected,
                        "observed": state["files"].get(member),
                    }
                )
    return list(nodes.values()), edges, declarations, diagnostics
