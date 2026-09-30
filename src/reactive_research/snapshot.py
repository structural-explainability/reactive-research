# ============================================================
# src/reactive_research/snapshot.py
# ============================================================

"""Create and inspect Reactive Research graph snapshots."""

from pathlib import Path
from typing import Any


def snapshot_research_graph(
    *,
    path: Path,
    registry: str | None,
    base_snapshot: str | None,
    show: str | None,
) -> dict[str, Any]:
    """Create or inspect a reproducible graph snapshot."""
    action = "show" if show is not None else "create"

    return {
        "command": "snapshot",
        "status": "scaffolded",
        "action": action,
        "path": str(path.resolve()),
        "registry": registry,
        "base_snapshot": base_snapshot,
        "snapshot_id": show,
        "repositories": [],
        "objects": [],
        "relationships": [],
    }
