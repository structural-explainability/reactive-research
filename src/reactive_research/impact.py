# ============================================================
# src/reactive_research/impact.py
# ============================================================

"""Analyze downstream Reactive Research impact."""

from collections import deque
from pathlib import Path
from typing import Any, Literal

from reactive_research.observation import canonical, digest
from reactive_research.snapshot import load_snapshot, observe_workspace

ImpactDepth = Literal["direct", "transitive"]

# consumer -> upstream; these edges are followed in reverse for impact.
# Context/provenance edges are opt-in and terminal, never build propagation.
PROPAGATING = frozenset(
    {
        "depends-on",
        "implements",
        "formalizes",
        "specifies",
        "tests",
        "pilots",
        "evaluates",
        "derives-from",
        "should-revalidate",
    }
)
CONTEXT = frozenset(
    {"cites", "informs", "revises", "supersedes", "contributes-to", "evidences"}
)
FORWARD = frozenset(
    {"informs", "contributes-to", "evidences", "should-revalidate", "freezes"}
)


def select_node(graph: dict[str, Any], identifier: str) -> dict[str, Any]:
    """Resolve a node ID or an unambiguous observed label."""
    matches = [
        n for n in graph["nodes"] if n["id"] == identifier or n["label"] == identifier
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one observed node for {identifier!r}; found {len(matches)}. Use a node ID."
        )
    return matches[0]


def impact_obligations(
    graph: dict[str, Any],
    identifier: str,
    *,
    previous: dict[str, Any] | None = None,
    depth: ImpactDepth = "transitive",
    relations: set[str] | None = None,
) -> dict[str, Any]:
    """Calculate bounded typed obligations without proposing or applying edits."""
    selected = PROPAGATING if relations is None else frozenset(relations)
    unknown = selected - PROPAGATING - CONTEXT - {"freezes"}
    if unknown:
        raise ValueError(f"Unsupported impact relationships: {sorted(unknown)}")
    nodes = {n["id"]: n for n in graph["nodes"]}
    source = select_node(graph, identifier)
    old_source = next(
        (n for n in (previous or {}).get("nodes", []) if n["id"] == source["id"]), None
    )
    changed = old_source != source if previous is not None else None
    obligations: list[dict[str, Any]] = []
    queue = deque([(source["id"], [], 0)])
    visited = {source["id"]}
    reached = {source["id"]}
    traversed: dict[str, dict[str, Any]] = {}

    def add(
        consumer: dict[str, Any],
        edge: dict[str, Any],
        chain: list[str],
        level: int,
        disposition: str,
        reason: str,
        reach: str = "impact",
    ) -> None:
        record = {
            "changed_source": source,
            "previous_source": old_source,
            "consumer": consumer,
            "relationship": edge["relation"],
            "edge": edge,
            "evidence": edge["evidence"],
            "constraints": edge["constraint"],
            "path": chain,
            "distance": level,
            "reach": reach,
            "disposition": disposition,
            "reason": reason,
            "lifecycle_constraints": {
                "source": source.get("lifecycle"),
                "consumer": consumer.get("lifecycle"),
                "protection": consumer.get("protection"),
                "authority": "Human review determines scientific validity and reconciliation.",
            },
        }
        obligations.append({"id": "obligation:" + digest(record), **record})

    if changed is not False:
        while queue:
            current, chain, level = queue.popleft()
            for edge in graph["edges"]:
                if edge["relation"] not in selected:
                    continue
                if edge["relation"] in FORWARD:
                    if edge["source"] != current:
                        continue
                    consumer_id = edge["target"]
                else:
                    if edge["target"] != current:
                        continue
                    consumer_id = edge["source"]
                if consumer_id == source["id"]:
                    continue
                consumer = nodes[consumer_id]
                new_chain = chain + [edge["id"]]
                reached.add(consumer_id)
                traversed[edge["id"]] = edge
                protected = consumer.get("lifecycle") in {
                    "frozen",
                    "frozen-record",
                    "protected",
                }
                if protected:
                    disposition = "frozen/protected — do not modify"
                    reason = "DO NOT MODIFY FROZEN EVIDENCE. Assess successor work under a new explicit freeze."
                elif (
                    edge["resolution"] != "resolved" or consumer["kind"] == "unresolved"
                ):
                    disposition = "unresolved"
                    reason = "Resolve the identity or ambiguous definition before interpreting impact."
                elif edge["kind"] == "build":
                    disposition = "verification required"
                    reason = "Recheck the selected dependency revision, imports and consumer verification; no automatic update."
                elif edge["relation"] in {
                    "tests",
                    "evaluates",
                    "pilots",
                    "should-revalidate",
                }:
                    disposition = "verification required"
                    reason = "Review whether verification must be rerun under the changed source state."
                else:
                    disposition = "semantic review"
                    reason = "Review the declared research relationship; matching terminology does not establish equivalence."
                    if edge["relation"] in CONTEXT:
                        reason = "Context/provenance notice only. Historical citation remains valid provenance; no build or update requirement."
                add(consumer, edge, new_chain, level + 1, disposition, reason)
                if (
                    edge["kind"] == "build"
                    and not protected
                    and disposition != "unresolved"
                ):
                    target = nodes[edge["target"]]
                    pinned = edge["constraint"].get("resolved_revision")
                    head = target.get("state", {}).get("source_revision")
                    if pinned and head and pinned != head:
                        add(
                            consumer,
                            edge,
                            new_chain,
                            level + 1,
                            "mechanical candidate",
                            "PENDING MECHANICAL PROPAGATION: lock selects a different committed revision. Review intentional pinning before proposing a successor pin.",
                        )
                    add(
                        consumer,
                        edge,
                        new_chain,
                        level + 1,
                        "semantic review",
                        "PENDING SEMANTIC REVIEW: determine whether the dependency change affects definitions actually used; build success cannot settle this.",
                    )
                if (
                    depth == "transitive"
                    and not protected
                    and disposition != "unresolved"
                    and edge["relation"] not in CONTEXT
                    and consumer_id not in visited
                ):
                    visited.add(consumer_id)
                    queue.append((consumer_id, new_chain, level + 1))

        # Protect scoped frozen members when their owner is reached. These are
        # guard notices, not invented semantic/build dependencies or propagation.
        owner_ids = reached | {nodes[n].get("project") for n in reached}
        for edge in graph["edges"]:
            if (
                edge["relation"] == "freezes"
                and nodes[edge["target"]].get("project") in owner_ids
            ):
                member = nodes[edge["target"]]
                if not any(
                    o["consumer"]["id"] == member["id"]
                    and o["disposition"].startswith("frozen/")
                    for o in obligations
                ):
                    add(
                        member,
                        edge,
                        [],
                        0,
                        "frozen/protected — do not modify",
                        "DO NOT MODIFY FROZEN EVIDENCE. Owner context is under review; this hash-committed member remains protected.",
                        "protection-boundary",
                    )
                    traversed[edge["id"]] = edge
                    reached.update((edge["source"], edge["target"]))
        for diagnostic in graph["diagnostics"]:
            if (
                diagnostic.get("code") == "RR.TECHNICAL_EDGE_NOT_IN_MANIFEST"
                and diagnostic.get("project") in reached
            ):
                consumer = nodes[diagnostic["project"]]
                edge = next(
                    (
                        e
                        for e in graph["edges"]
                        if e["source"] == consumer["id"]
                        and e.get("declared_target") == diagnostic["target"]
                        and e["kind"] == "build"
                    ),
                    None,
                )
                if edge and edge["target"] in reached:
                    add(
                        consumer,
                        edge,
                        [edge["id"]],
                        1,
                        "mechanical candidate",
                        "PENDING MECHANICAL PROPAGATION: existing Lake edge is missing from SE manifest graph visibility; review declaration alignment, without changing theory.",
                    )
    return {
        "command": "impact",
        "format_version": 1,
        "snapshot_id": graph["snapshot_id"],
        "previous_snapshot_id": previous.get("snapshot_id") if previous else None,
        "identifier": source["id"],
        "source": source,
        "change_detected": changed,
        "change_basis": "snapshot comparison"
        if previous
        else "caller-selected change scenario; not evidence of a newly observed change",
        "selected_relations": sorted(selected),
        "depth": depth,
        "obligations": sorted(
            {o["id"]: o for o in obligations}.values(), key=canonical
        ),
        "nodes": sorted((nodes[n] for n in reached), key=lambda n: n["id"]),
        "edges": sorted(traversed.values(), key=lambda e: e["id"]),
    }


def analyze_impact(
    *,
    path: Path,
    identifier: str,
    depth: ImpactDepth,
    registry: str | None,
    snapshot: str | None,
    from_snapshot: str | None,
    to_snapshot: str | None,
    relations: set[str] | None = None,
) -> dict[str, Any]:
    """Identify downstream objects potentially affected by a change."""
    selected = to_snapshot or snapshot
    graph = (
        load_snapshot(selected, registry)
        if selected
        else observe_workspace(path, registry=registry)
    )
    previous = load_snapshot(from_snapshot, registry) if from_snapshot else None
    return impact_obligations(
        graph, identifier, previous=previous, depth=depth, relations=relations
    )
