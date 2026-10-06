"""Deterministic, content-addressed observations of existing research surfaces."""

import json
from pathlib import Path
from typing import Any

from reactive_research.observation import (
    canonical,
    digest,
    discover_projects,
    read_project,
)
from reactive_research.surfaces import observe_surfaces, toml

FORMAT = "reactive-research-observation"
FORMAT_VERSION = 1


def observe_workspace(
    path: Path, *, revisions: dict[str, str] | None = None, registry: str | None = None
) -> dict[str, Any]:
    """Observe discovered projects, optionally substituting named committed trees."""
    root = path.resolve()
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    declarations: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    aliases: dict[str, set[str]] = {}
    discovered = discover_projects(root)
    unknown = set(revisions or {}) - {
        p.relative_to(root).as_posix() for p in discovered
    }
    if unknown:
        raise ValueError(
            f"Revision selections do not identify discovered roots: {sorted(unknown)}"
        )
    for project_root in discovered:
        relative = project_root.relative_to(root).as_posix()
        pid = "repo:" + relative
        data, state = read_project(project_root, (revisions or {}).get(relative))
        manifest_name = next(
            (
                n
                for n in ("SE_MANIFEST.toml", "MANIFEST.toml", "se-manifest.toml")
                if n in data
            ),
            None,
        )
        manifest = toml(data, manifest_name, diagnostics) if manifest_name else {}
        identity = manifest.get("repository", manifest.get("repo", {}))
        if not isinstance(identity, dict):
            identity = {}
        lake = toml(data, "lakefile.toml", diagnostics)
        python = toml(data, "pyproject.toml", diagnostics).get("project", {})
        name = identity.get("name") or project_root.name
        node = {
            "id": pid,
            "kind": "repository",
            "label": name,
            "name": name,
            "path": relative,
            "organization": identity.get("organization"),
            "class": identity.get("class"),
            "lifecycle": identity.get("status", "unspecified"),
            "state": state,
            "manifest": manifest_name,
            "declared_version": identity.get(
                "version", lake.get("version", python.get("version"))
            ),
        }
        nodes[pid] = node
        for alias in (name, project_root.name, lake.get("name"), python.get("name")):
            if isinstance(alias, str):
                aliases.setdefault(alias, set()).add(pid)
        found, relationships, records, errors = observe_surfaces(node, data)
        for candidate in found:
            nid = candidate["id"]
            if nid in nodes and candidate["kind"] == "object":
                nodes[nid]["definitions"].extend(candidate["definitions"])
            else:
                nodes[nid] = candidate
        edges.extend(relationships)
        declarations.extend(records)
        diagnostics.extend(errors)

    if registry is not None:
        # Reuse repository-published declarations rather than a master list.
        from reactive_research.resolve import _load_declaration_file

        location = Path(registry)
        files = [location] if location.is_file() else sorted(location.glob("*.json"))
        if not files:
            raise ValueError(f"No declaration documents found at {registry}")
        for file in files:
            document = _load_declaration_file(file)
            for record in document["declarations"]:
                if record.get("relation") != "DEFINES":
                    diagnostics.append(
                        {"code": "RR.REGISTRY_RELATION_NOT_OBSERVED", "record": record}
                    )
                    continue
                if any(
                    all(
                        d.get(k) == record.get(k)
                        for k in (
                            "identifier",
                            "repository",
                            "revision",
                            "source_path",
                            "source_line",
                        )
                    )
                    for d in declarations
                ):
                    continue
                oid = "object:" + record["identifier"]
                nodes.setdefault(
                    oid,
                    {
                        "id": oid,
                        "label": record["identifier"],
                        "kind": "object",
                        "definitions": [],
                    },
                )["definitions"].append(
                    {
                        **record,
                        "state": "registry-declaration",
                        "adapter": "normalized-declarations",
                    }
                )
                declarations.append(record)

    resolved_edges: list[dict[str, Any]] = []
    for original in edges:
        edge = dict(original)
        for endpoint in ("source", "target"):
            raw = edge[endpoint]
            if not raw.startswith("alias:"):
                continue
            alias = raw.removeprefix("alias:")
            matches = sorted(aliases.get(alias, set()))
            edge["declared_" + endpoint] = alias
            edge[endpoint + "_candidates"] = matches
            edge[endpoint] = matches[0] if len(matches) == 1 else "unresolved:" + alias
            if endpoint == "target":
                edge["candidates"] = matches
            if len(matches) != 1:
                edge["resolution"] = "ambiguous" if matches else "unresolved"
            if edge[endpoint] not in nodes:
                nodes[edge[endpoint]] = {
                    "id": edge[endpoint],
                    "label": alias,
                    "kind": "unresolved",
                    "lifecycle": "unresolved",
                }
        target = edge["target"]
        if "resolution" not in edge:
            edge["resolution"] = (
                "resolved"
                if target in nodes and nodes[target]["kind"] != "unresolved"
                else "unresolved"
            )
        if target not in nodes:
            nodes[target] = {
                "id": target,
                "label": target.split(":", 1)[-1],
                "kind": "unresolved",
                "lifecycle": "unresolved",
            }
        if edge["resolution"] != "resolved":
            diagnostics.append(
                {
                    "code": "RR.UNRESOLVED_EDGE",
                    "source": edge["source"],
                    "target": target,
                    "resolution": edge["resolution"],
                    "evidence": edge["evidence"],
                }
            )
        resolved_edges.append(edge)
    for node in nodes.values():
        if node["kind"] == "object":
            definitions = sorted(node["definitions"], key=canonical)
            node["definitions"] = definitions
            node["resolution"] = (
                "resolved" if len(definitions) == 1 else "duplicate-definition"
            )
            node["content_digest"] = digest(definitions)
            if len(definitions) > 1:
                diagnostics.append(
                    {
                        "code": "RR.DUPLICATE_DEFINITION",
                        "identifier": node["label"],
                        "definitions": definitions,
                    }
                )
    for edge in resolved_edges:
        if nodes[edge["target"]].get("resolution") == "duplicate-definition":
            edge["resolution"] = "duplicate-definition"
        edge["id"] = "edge:" + digest({k: v for k, v in edge.items() if k != "id"})
    payload = {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "observer_version": 1,
        "scope": "Discovered Git/project roots; excludes caches, build outputs and symlinks. No scientific validation inferred.",
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": sorted(
            {e["id"]: e for e in resolved_edges}.values(), key=lambda e: e["id"]
        ),
        "declarations": sorted(declarations, key=canonical),
        "diagnostics": sorted(diagnostics, key=canonical),
    }
    return {**payload, "snapshot_id": "sha256:" + digest(payload)}


def load_snapshot(reference: str, registry: str | None = None) -> dict[str, Any]:
    """Load and integrity-check a snapshot file or registry content-addressed ID."""
    path = Path(reference)
    if reference.startswith("sha256:"):
        if registry is None:
            raise ValueError("Resolving a snapshot ID requires --registry DIR.")
        path = Path(registry) / (reference.removeprefix("sha256:") + ".json")
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("format") != FORMAT
        or value.get("format_version") != FORMAT_VERSION
    ):
        raise ValueError("Not a supported Reactive Research observation snapshot.")
    payload = {k: v for k, v in value.items() if k != "snapshot_id"}
    if value.get("snapshot_id") != "sha256:" + digest(payload):
        raise ValueError(
            "Snapshot content does not match its content-addressed identifier."
        )
    return value


def snapshot_research_graph(
    *,
    path: Path,
    registry: str | None,
    base_snapshot: str | None,
    show: str | None,
    revisions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Create or inspect a reproducible observation; output storage is explicit."""
    if show is not None:
        return load_snapshot(show, registry)
    if base_snapshot is not None:
        load_snapshot(base_snapshot, registry)
    return observe_workspace(path, revisions=revisions, registry=registry)
