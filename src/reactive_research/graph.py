# ============================================================
# src/reactive_research/graph.py
# ============================================================

"""Build and query Reactive Research graphs."""

from pathlib import Path
from typing import Any, Literal

GraphView = Literal["objects", "repositories"]


def build_research_graph(
    *,
    path: Path,
    target: str | None,
    view: GraphView,
    registry: str | None,
    snapshot: str | None,
) -> dict[str, Any]:
    """Build or inspect a typed Reactive Research graph."""
    return {
        "command": "graph",
        "status": "scaffolded",
        "path": str(path.resolve()),
        "target": target,
        "view": view,
        "registry": registry,
        "snapshot": snapshot,
        "nodes": [],
        "edges": [],
    }
