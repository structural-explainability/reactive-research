# ============================================================
# src/reactive_research/impact.py
# ============================================================

"""Analyze downstream Reactive Research impact."""

from pathlib import Path
from typing import Any, Literal

ImpactDepth = Literal["direct", "transitive"]


def analyze_impact(
    *,
    path: Path,
    identifier: str,
    depth: ImpactDepth,
    registry: str | None,
    snapshot: str | None,
    from_snapshot: str | None,
    to_snapshot: str | None,
) -> dict[str, Any]:
    """Identify downstream objects potentially affected by a change."""
    return {
        "command": "impact",
        "status": "scaffolded",
        "path": str(path.resolve()),
        "identifier": identifier,
        "depth": depth,
        "registry": registry,
        "snapshot": snapshot,
        "from_snapshot": from_snapshot,
        "to_snapshot": to_snapshot,
        "directly_affected": [],
        "transitively_affected": [],
        "revalidation_required": [],
    }
