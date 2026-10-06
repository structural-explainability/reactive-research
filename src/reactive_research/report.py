"""Human-readable obligations derived from structured impact results."""

from typing import Any


def obligation_report(result: dict[str, Any]) -> str:
    """Render attention, evidence and protection without authorizing mutation."""
    source = result["source"]
    state = _state(source)
    lines = [
        f"# Research obligations: {source['label']}",
        "",
        f"Snapshot: `{result['snapshot_id']}`",
        "",
        f"Change basis: {result['change_basis']}; detected: {result['change_detected']}",
        "",
        f"Source state: `{state}`",
        "",
        "Impact means attention is required; it does not establish a scientific defect or authorize an edit.",
        "",
    ]
    if not result["obligations"]:
        lines.append("No obligations reached through the selected relationships.")
    for obligation in result["obligations"]:
        consumer = obligation["consumer"]
        evidence = obligation["evidence"]
        lines.extend(
            [
                f"## {consumer['label']} — {obligation['disposition']}",
                "",
                obligation["reason"],
                "",
                f"Relationship: `{obligation['relationship']}` ({obligation['edge']['kind']}); reach: {obligation['reach']}.",
                f"Evidence: `{evidence['project']}/{evidence['path']}` line {evidence.get('line') or 'n/a'} ({evidence['state']}).",
                f"Consumer revision/state: `{_state(consumer)}`.",
                f"Constraints: `{obligation['constraints']}`.",
                "",
            ]
        )
    return "\n".join(lines)


def _state(node: dict[str, Any]) -> Any:
    """Show provenance without dumping the repository's entire file census."""
    state = node.get("state")
    return (
        {k: v for k, v in state.items() if k != "files"}
        if state
        else node.get("definitions", [])
    )
