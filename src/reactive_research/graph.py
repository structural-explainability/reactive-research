# ============================================================
# src/reactive_research/graph.py
# ============================================================

"""Build and query Reactive Research graphs."""

from pathlib import Path
from typing import Any, Literal

from reactive_research.impact import CONTEXT, PROPAGATING, select_node
from reactive_research.snapshot import load_snapshot, observe_workspace

GraphView = Literal["objects", "repositories"]


def graph_projection(
    graph: dict[str, Any], *, view: GraphView = "objects", target: str | None = None
) -> dict[str, Any]:
    """Derive an object graph or repository projection without new declarations."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = graph["edges"]
    if view == "repositories":

        def owner(identifier: str) -> str:
            node = nodes[identifier]
            if node.get("lifecycle") in {"frozen", "frozen-record", "protected"}:
                return identifier
            definitions = node.get("definitions", [])
            if len(definitions) == 1 and definitions[0].get("project") in nodes:
                return definitions[0]["project"]
            return node.get("project", identifier)

        edges = [
            {
                **e,
                "source": owner(e["source"]),
                "target": owner(e["target"]),
                "observed_source": e["source"],
                "observed_target": e["target"],
            }
            for e in edges
            if owner(e["source"]) != owner(e["target"])
        ]
        used = {e[k] for e in edges for k in ("source", "target")}
        nodes = {
            k: n for k, n in nodes.items() if n["kind"] == "repository" or k in used
        }
    if target is not None:
        selected = select_node({"nodes": list(nodes.values())}, target)["id"]
        adjacent = {selected}
        adjacent.update(
            e[k]
            for e in edges
            if selected in (e["source"], e["target"])
            for k in ("source", "target")
        )
        nodes = {k: n for k, n in nodes.items() if k in adjacent}
        edges = [e for e in edges if e["source"] in nodes and e["target"] in nodes]
    return {
        "command": "graph",
        "snapshot_id": graph["snapshot_id"],
        "view": view,
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": edges,
    }


def mermaid_graph(graph: dict[str, Any], *, category: str = "propagation") -> str:
    """Render deterministic Mermaid directly from the shared JSON graph boundary."""
    if category not in {"evolution", "propagation", "impact"}:
        raise ValueError(f"Unknown graph category: {category}")
    evolution = CONTEXT | {"formalizes", "implements", "pilots", "evaluates", "freezes"}
    allowed = evolution if category == "evolution" else PROPAGATING | {"freezes"}
    edges = [
        e for e in graph["edges"] if category == "impact" or e["relation"] in allowed
    ]
    used = {e[k] for e in edges for k in ("source", "target")}
    if category == "impact":
        used.update(n["id"] for n in graph["nodes"])
    nodes = sorted(
        (n for n in graph["nodes"] if n["id"] in used), key=lambda n: n["id"]
    )
    names = {n["id"]: f"n{i}" for i, n in enumerate(nodes)}

    def escape(value: object) -> str:
        return (
            str(value)
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("|", "&#124;")
            .replace("\n", " ")
        )

    lines = [
        "flowchart LR",
        "  %% Typed arrows read source --relation--> target. Dependency impact follows reverse arrows; influence/protection follows forward arrows.",
    ]
    dispositions: dict[str, set[str]] = {}
    for obligation in graph.get("obligations", []):
        dispositions.setdefault(obligation["consumer"]["id"], set()).add(
            obligation["disposition"]
        )
    for node in nodes:
        state = node.get("state", {})
        revision = (state.get("source_revision") or "")[:8]
        label = f"{node['label']} [{state.get('mode', node.get('resolution', 'observed'))} {revision}]"
        if node.get("declared_version"):
            label += f" / declared {node['declared_version']}"
        if state.get("commit_time"):
            label += " / commit " + state["commit_time"][:10]
        lines.append(f'  {names[node["id"]]}["{escape(label)}"]')
        disposition = dispositions.get(node["id"], set())
        if disposition:
            lines[-1] = (
                f'  {names[node["id"]]}["{escape(label + " / " + ", ".join(sorted(disposition)))}"]'
            )
        style = "ordinary"
        if node.get("lifecycle") in {"frozen", "frozen-record", "protected"}:
            style = "protected"
        elif node["id"] == graph.get("identifier"):
            style = "changed"
        elif "mechanical candidate" in disposition:
            style = "mechanical"
        elif "semantic review" in disposition:
            style = "semantic"
        elif "verification required" in disposition:
            style = "verification"
        elif node["kind"] == "unresolved":
            style = "unresolved"
        lines.append(f"  class {names[node['id']]} {style}")
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for edge in edges:
        constraint = edge.get("constraint", {})
        key = (
            edge["source"],
            edge["target"],
            edge["relation"],
            edge["kind"],
            str(
                constraint.get("requested_revision") or constraint.get("version") or ""
            ),
            edge.get("resolution", "unresolved"),
        )
        groups.setdefault(key, []).append(edge)
    for key in sorted(groups):
        matches = groups[key]
        edge = matches[0]
        label = f"{edge['relation']} / {edge['kind']}"
        constraint = edge.get("constraint", {})
        pin = constraint.get("requested_revision") or constraint.get("version")
        if pin:
            label += f" / {pin}"
        if edge.get("resolution") != "resolved":
            label += f" / {edge.get('resolution')}"
        if len(matches) > 1:
            label += f" / {len(matches)} evidence edges"
        arrow = "-.->" if edge["relation"] in CONTEXT else "-->"
        lines.append(
            f'  {names[edge["source"]]} {arrow}|"{escape(label)}"| {names[edge["target"]]}'
        )
    lines.extend(
        [
            "  classDef changed fill:#fde68a,stroke:#92400e,stroke-width:3px",
            "  classDef protected fill:#fecaca,stroke:#991b1b,stroke-width:3px",
            "  classDef mechanical fill:#bfdbfe,stroke:#1d4ed8",
            "  classDef semantic fill:#e9d5ff,stroke:#7e22ce",
            "  classDef verification fill:#bbf7d0,stroke:#166534",
            "  classDef unresolved fill:#e5e7eb,stroke:#4b5563,stroke-dasharray:5 5",
            "  classDef ordinary fill:#f8fafc,stroke:#64748b",
        ]
    )
    return "\n".join(lines)


def build_research_graph(
    *,
    path: Path,
    target: str | None,
    view: GraphView,
    registry: str | None,
    snapshot: str | None,
) -> dict[str, Any]:
    """Build or inspect a typed Reactive Research graph."""
    graph = (
        load_snapshot(snapshot, registry)
        if snapshot
        else observe_workspace(path, registry=registry)
    )
    return graph_projection(graph, view=view, target=target)
