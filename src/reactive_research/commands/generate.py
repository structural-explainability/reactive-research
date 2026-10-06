# ============================================================
# src/reactive_research/commands/generate.py
# ============================================================

"""CLI adapter for generating current Reactive Research views."""

import argparse
import json
from pathlib import Path
from typing import Any

from reactive_research.graph import graph_projection, mermaid_graph
from reactive_research.snapshot import observe_workspace

_DOWNSTREAM_RELATIONS = {
    "depends-on",
    "implements",
    "formalizes",
    "specifies",
    "tests",
    "pilots",
    "evaluates",
    "derives-from",
}


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the generate command."""
    parser.description = (
        "Generate Reactive Research views from the current research workspace."
    )

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Root of the research family to observe.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory for generated Reactive Research views.",
    )

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Generate current Reactive Research views."""
    root = args.root.resolve()
    output = args.output.resolve()

    current = observe_workspace(root)
    repository_graph = graph_projection(current, view="repositories")

    # Preserve the complete detailed graph views.
    evolution = mermaid_graph(
        repository_graph,
        category="evolution",
    )
    propagation = mermaid_graph(
        repository_graph,
        category="propagation",
    )

    # Add smaller views around Transformation.
    transformation_neighborhood = _neighborhood_scope(
        graph=repository_graph,
        root_names={"se-theory-transformation"},
        max_hops=1,
    )
    transformation_downstream = _downstream_scope(
        graph=repository_graph,
        root_names={"se-theory-transformation"},
        relations=_DOWNSTREAM_RELATIONS,
        max_depth=2,
    )

    transformation_neighborhood_mermaid = mermaid_graph(
        transformation_neighborhood,
        category="propagation",
    )
    transformation_downstream_mermaid = mermaid_graph(
        transformation_downstream,
        category="propagation",
    )

    output.mkdir(parents=True, exist_ok=True)

    # Full detailed artifacts.
    _write_json(
        output / "observation.json",
        current,
    )
    _write_json(
        output / "repository-graph.json",
        repository_graph,
    )
    _write_text(
        output / "evolution.mmd",
        evolution,
    )
    _write_text(
        output / "propagation.mmd",
        propagation,
    )

    # Scoped Transformation artifacts.
    _write_json(
        output / "transformation-neighborhood.json",
        transformation_neighborhood,
    )
    _write_text(
        output / "transformation-neighborhood.mmd",
        transformation_neighborhood_mermaid,
    )
    _write_json(
        output / "transformation-downstream.json",
        transformation_downstream,
    )
    _write_text(
        output / "transformation-downstream.mmd",
        transformation_downstream_mermaid,
    )

    # Generated documentation page.
    _write_text(
        output / "index.md",
        _render_index(
            transformation_neighborhood_mermaid=(transformation_neighborhood_mermaid),
            transformation_downstream_mermaid=(transformation_downstream_mermaid),
        ),
    )

    return 0


def _root_ids(
    graph: dict[str, Any],
    root_names: set[str],
) -> set[str]:
    """Return node IDs matching selected repository names or IDs."""
    return {
        node["id"]
        for node in graph.get("nodes", [])
        if node.get("name") in root_names or node.get("id") in root_names
    }


def _neighborhood_scope(
    *,
    graph: dict[str, Any],
    root_names: set[str],
    max_hops: int,
) -> dict[str, Any]:
    """Return an undirected neighborhood around selected repositories."""
    roots = _root_ids(
        graph,
        root_names,
    )

    if not roots:
        return _subgraph(
            graph,
            set(),
        )

    visited = set(roots)
    frontier = set(roots)

    for _ in range(max_hops):
        next_frontier: set[str] = set()

        for edge in graph.get("edges", []):
            source = edge["source"]
            target = edge["target"]

            if source in frontier and target not in visited:
                next_frontier.add(target)

            if target in frontier and source not in visited:
                next_frontier.add(source)

        visited.update(next_frontier)
        frontier = next_frontier

        if not frontier:
            break

    return _subgraph(
        graph,
        visited,
    )


def _downstream_scope(
    *,
    graph: dict[str, Any],
    root_names: set[str],
    relations: set[str],
    max_depth: int,
) -> dict[str, Any]:
    """Return downstream consumers of selected upstream repositories.

    Dependency-style repository relationships are represented as:

        consumer --relation--> upstream

    Downstream traversal therefore follows those relationships in reverse
    from the selected upstream repository.
    """
    roots = _root_ids(
        graph,
        root_names,
    )

    if not roots:
        return _subgraph(
            graph,
            set(),
        )

    visited = set(roots)
    frontier = set(roots)

    for _ in range(max_depth):
        next_frontier: set[str] = set()

        for edge in graph.get("edges", []):
            relation = edge.get("relation")
            source = edge["source"]
            target = edge["target"]

            if relation in relations and target in frontier and source not in visited:
                next_frontier.add(source)

        visited.update(next_frontier)
        frontier = next_frontier

        if not frontier:
            break

    return _subgraph(
        graph,
        visited,
    )


def _subgraph(
    graph: dict[str, Any],
    node_ids: set[str],
) -> dict[str, Any]:
    """Return the induced subgraph for selected node IDs."""
    return {
        "snapshot_id": graph.get("snapshot_id"),
        "nodes": [node for node in graph.get("nodes", []) if node["id"] in node_ids],
        "edges": [
            edge
            for edge in graph.get("edges", [])
            if edge["source"] in node_ids and edge["target"] in node_ids
        ],
    }


def _render_index(
    *,
    transformation_neighborhood_mermaid: str,
    transformation_downstream_mermaid: str,
) -> str:
    """Render the generated research page."""
    return f"""# Generated Research Views

These views are generated from the current Reactive Research observation of the
research family.

The full detailed research graphs and structured observation are retained.
The smaller views below provide focused entry points for inspection.

## Transformation Neighborhood

This diagram depicts the repositories directly connected to
`se-theory-transformation` in the current Reactive Research observation.

Reactive Research first observes supported relationship evidence across the
research family and builds a repository-level graph.
The evidence may come from sources such as repository declarations,
dependency information, formalization references, and Reactive Research annotations.

For this view, the generator selects `se-theory-transformation` and every
repository connected to it by one recorded relationship in either direction.
All recorded relationship types are eligible for this view.

The diagram therefore shows the immediate context around Transformation:
which repositories are directly related to it and the type of each recorded
relationship.

Only one level of connections is included.
Relationships beyond direct neighbors are not included.

```mermaid
{transformation_neighborhood_mermaid.rstrip()}
```

Generated artifacts:

- [Transformation neighborhood Mermaid](transformation-neighborhood.mmd)
- [Transformation neighborhood JSON](transformation-neighborhood.json)

## Transformation Downstream

This diagram depicts repositories that rely on
`se-theory-transformation`, either directly or through another repository.

It is generated from the same repository-level graph as the Transformation
Neighborhood view, but it selects only relationships that indicate downstream
use or dependency.

The included relationship types are:

- `depends-on`
- `implements`
- `formalizes`
- `specifies`
- `tests`
- `pilots`
- `evaluates`
- `derives-from`

The first level contains repositories with one of these recorded relationships
to Transformation.

The second level contains repositories with one of these relationships to a
repository in the first level.

The traversal stops after two levels to keep the diagram limited in scope.

Unlike the Transformation Neighborhood view, this diagram does not include
every recorded relationship around Transformation.
It depicts only the selected relationships
used to trace **downstream reliance**.

```mermaid
{transformation_downstream_mermaid.rstrip()}
```

Generated artifacts:

- [Transformation downstream Mermaid](transformation-downstream.mmd)
- [Transformation downstream JSON](transformation-downstream.json)

## Full Detailed Research Graphs

The complete drawings are retained for detailed inspection.

- [Full research evolution](evolution.mmd)
- [Full research propagation](propagation.mmd)

## Full Structured Research Data

- [Full observation](observation.json)
- [Repository graph](repository-graph.json)

Regenerate these artifacts from the `reactive-research` repository root:

```powershell
uv run reactive-research generate --root .. --output docs/en/output
```
"""


def _write_json(
    path: Path,
    value: Any,
) -> None:
    """Write a generated JSON artifact."""
    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_text(
    path: Path,
    value: str,
) -> None:
    """Write a generated text artifact."""
    path.write_text(
        value.rstrip() + "\n",
        encoding="utf-8",
    )
