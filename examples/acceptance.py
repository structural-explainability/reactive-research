"""Run read-only acceptance examples against the current research family.

This script is an acceptance harness for the Reactive Research implementation.
It is not the normal command for generating Reactive Research documentation.

The acceptance workflow observes the entire Structural Explainability research
family rooted at ``..``. Its purpose includes verifying that observation and
analysis do not modify the repositories being observed.

For that reason, acceptance output MUST be written outside the observed
research-family root.
Writing acceptance artifacts anywhere beneath ``..`` would
change the filesystem being observed and would prevent the run
from demonstrating that the observed research family remained unchanged.

The observed research family does not need to begin in a clean working state.
Existing staged, unstaged, deleted, and untracked changes are part of the
initial observation. The acceptance workflow records that state and verifies
that the run itself does not change the observed Git HEAD/status state.

Run from the reactive-research repository root with an explicitly authorized
output location outside the observed research-family root:

uv run --no-sync python examples/acceptance.py --root .. --output reactive-research-acceptance-output

The generated acceptance artifacts include research graphs, obligations,
structured JSON, snapshot evidence, repository-preservation results, and
frozen-evidence integrity results.

These artifacts support acceptance review of the implementation. They are
separate from the normal human-facing Reactive Research documentation.

Normal Reactive Research use should run through the project CLI and generate
inspectable research documentation in situ under ``docs/en/output``.
"""

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess

from reactive_research.graph import graph_projection, mermaid_graph
from reactive_research.impact import impact_obligations
from reactive_research.observation import discover_projects, git
from reactive_research.report import obligation_report
from reactive_research.snapshot import observe_workspace

parser = argparse.ArgumentParser(
    description="Read-only acceptance cases for the Structural Explainability family."
)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument(
    "--output", type=Path, required=True, help="Keep outside the observed family."
)
args = parser.parse_args()
ROOT = args.root.resolve()
OUT = args.output.resolve()
if OUT == ROOT or ROOT in OUT.parents:
    parser.error("Acceptance outputs must be outside the observed research family.")
OUT.mkdir(parents=True, exist_ok=True)


def save(name, value):
    """Write an explicit acceptance deliverable outside the observed family."""
    (OUT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def provenance():
    """Record all discovered Git HEADs and statuses for preservation checks."""
    return {
        p.relative_to(ROOT).as_posix(): {
            "head": git(p, "rev-parse", "HEAD"),
            "status": git(p, "status", "--porcelain=v1", "--untracked-files=all"),
        }
        for p in discover_projects(ROOT)
        if (p / ".git").exists()
    }


before = provenance()
print("Observing current workspace", flush=True)
current = observe_workspace(ROOT)
save("observation.json", current)
print(
    "Current",
    current["snapshot_id"],
    "nodes",
    len(current["nodes"]),
    "edges",
    len(current["edges"]),
    "projects",
    sum(n["kind"] == "repository" for n in current["nodes"]),
    flush=True,
)
repeated = observe_workspace(ROOT)
assert current == repeated, "Identical current observations must be deterministic"

print("Reading historical SE-100 v1.0.0 without checkout", flush=True)
paper_before = observe_workspace(
    ROOT, revisions={"paper-100-neutral-substrate": "v1.0.0"}
)
save("se100-before.json", paper_before)
paper_impact = impact_obligations(
    current, "se100.def.FrameworkInvariant", previous=paper_before
)
assert paper_impact["change_detected"]
assert any(
    "neutral-substrate" in o["consumer"].get("project", o["consumer"]["id"])
    for o in paper_impact["obligations"]
)
save("se100-impact.json", paper_impact)
(OUT / "se100-obligations.md").write_text(
    obligation_report(paper_impact), encoding="utf-8"
)

print("Reading Transformation v0.5.0 without checkout", flush=True)
transformation_before = observe_workspace(
    ROOT, revisions={"theory/se-theory-transformation": "v0.5.0"}
)
save("transformation-before.json", transformation_before)
transformation_impact = impact_obligations(
    current, "se-theory-transformation", previous=transformation_before
)
assert transformation_impact["change_detected"]
for name in ("se-theory-identity-regimes", "se-theory-persistence"):
    assert any(
        o["consumer"].get("name") == name for o in transformation_impact["obligations"]
    )
save("transformation-impact.json", transformation_impact)
(OUT / "transformation-obligations.md").write_text(
    obligation_report(transformation_impact), encoding="utf-8"
)

print("Checking PURL Freeze 01 context and byte commitments", flush=True)
freeze_context = impact_obligations(
    current, "se-verification-operational-identity", relations={"informs"}
)
save("freeze-context-impact.json", freeze_context)
freeze_before = observe_workspace(
    ROOT,
    revisions={
        "se-pilot-identity-preservation-supply-chain-software": "ef3a5dacdf1a483f41d87ee955d365376e63a220"
    },
)
save("freeze-before.json", freeze_before)
freeze_impact = impact_obligations(
    current,
    "se-pilot-identity-preservation-supply-chain-software",
    previous=freeze_before,
)
assert freeze_impact["change_detected"]
guards = [
    o for o in freeze_impact["obligations"] if o["reach"] == "protection-boundary"
]
assert len(guards) == 7, f"Expected seven protected artifacts, got {len(guards)}"
assert all(o["consumer"]["protection"]["hash_matches"] for o in guards)
freeze_bytes = {}
for obligation in guards:
    member = obligation["consumer"]
    protection = member["protection"]
    project = next(n for n in current["nodes"] if n["id"] == member["project"])
    location = ROOT / project["path"]
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={location.as_posix()}",
            "--no-optional-locks",
            "-C",
            str(location),
            "show",
            protection["frozen_content_commit"] + ":" + member["label"],
        ],
        capture_output=True,
        check=True,
    )
    committed_sha = hashlib.sha256(result.stdout).hexdigest()
    working_sha = hashlib.sha256((location / member["label"]).read_bytes()).hexdigest()
    assert committed_sha == working_sha == protection["expected_sha256"]
    freeze_bytes[member["label"]] = {
        "committed_sha256": committed_sha,
        "current_sha256": working_sha,
        "expected_sha256": protection["expected_sha256"],
        "matches": True,
    }
save("freeze-impact.json", freeze_impact)
save("freeze-integrity.json", freeze_bytes)
(OUT / "freeze-obligations.md").write_text(
    obligation_report(freeze_impact), encoding="utf-8"
)

# Graphs are projections of the snapshot; selecting pilot nodes is presentation,
# not a separate relationship registry. Keep detailed full JSON available.
important = {
    "paper-100-neutral-substrate",
    "se-theory-neutral-substrate",
    "se-theory-transformation",
    "se-theory-identity-regimes",
    "se-theory-persistence",
    "se-verification-operational-identity",
    "se-pilot-identity-preservation-supply-chain-software",
}
projects = {n["id"] for n in current["nodes"] if n.get("name") in important}
ids = projects | {n["id"] for n in current["nodes"] if n.get("project") in projects}
selected_edges = [
    e
    for e in current["edges"]
    if e["source"] in ids
    and e["target"] in ids
    or e["source"] in ids
    and e["target"].startswith("object:se100.")
]
ids.update(e[k] for e in selected_edges for k in ("source", "target"))
presentation = {
    "snapshot_id": current["snapshot_id"],
    "nodes": [n for n in current["nodes"] if n["id"] in ids],
    "edges": selected_edges,
}
repo_view = graph_projection(presentation, view="repositories")
save("pilot-graph.json", presentation)
save("repository-graph.json", repo_view)
for name, graph, category in (
    ("evolution", repo_view, "evolution"),
    ("propagation", repo_view, "propagation"),
    ("impact", transformation_impact, "impact"),
    ("freeze-impact", freeze_impact, "impact"),
):
    (OUT / (name + ".mmd")).write_text(
        mermaid_graph(graph, category=category) + "\n", encoding="utf-8"
    )

after = provenance()
assert before == after, (
    "Observation and impact must preserve every discovered Git HEAD and status"
)
save(
    "repository-preservation.json",
    {"unchanged": True, "before": before, "after": after},
)
paper_root = ROOT / "paper-100-neutral-substrate"
neutral_root = ROOT / "theory/se-theory-neutral-substrate"
upstream_commit = git(paper_root, "rev-parse", "v1.1.0^{commit}")
response_commit = git(neutral_root, "rev-parse", "v0.10.0^{commit}")
assert upstream_commit is not None and response_commit is not None
upstream_time = git(paper_root, "show", "-s", "--format=%cI", upstream_commit)
response_time = git(neutral_root, "show", "-s", "--format=%cI", response_commit)
assert upstream_time is not None and response_time is not None
assert datetime.fromisoformat(response_time) > datetime.fromisoformat(upstream_time)
response_source = git(
    neutral_root,
    "show",
    response_commit + ":SE/NeutralSubstrate/FrameworkRelative/InvariantRefutation.lean",
)
assert response_source is not None
assert (
    "se100.remark.FrameworkInvariantRefutation" in response_source
    and "(hni :" in response_source
)
reconciliation = {
    "upstream_tag": "v1.1.0",
    "upstream_commit": upstream_commit,
    "upstream_commit_time": upstream_time,
    "response_tag": "v0.10.0",
    "response_commit": response_commit,
    "response_commit_time": response_time,
    "response_follows_upstream_release_commit": True,
    "evidence": [
        "CHANGELOG.md",
        "SE/NeutralSubstrate/FrameworkRelative/InvariantRefutation.lean",
    ],
    "explicit_negation_introduction_hypothesis_observed": True,
    "status": "Documented later formal response; Lean was not rerun and scientific discharge is not inferred.",
    "chronology_constraint": "The first formalization file commit precedes the paper release commit; coordinated working edits cannot be dated solely by release commits.",
}
save("reconciliation-evidence.json", reconciliation)
summary = {
    "snapshot_id": current["snapshot_id"],
    "deterministic_repeat": True,
    "projects": sum(n["kind"] == "repository" for n in current["nodes"]),
    "nodes": len(current["nodes"]),
    "edges": len(current["edges"]),
    "diagnostics": dict(Counter(d["code"] for d in current["diagnostics"])),
    "cases": {
        "se100": {
            "changed": paper_impact["change_detected"],
            "obligations": len(paper_impact["obligations"]),
            "later_response": reconciliation,
        },
        "transformation": {
            "changed": transformation_impact["change_detected"],
            "obligations": len(transformation_impact["obligations"]),
        },
        "freeze": {
            "observed_change": "Frozen content commit to newer current pilot implementation; existing commitments remain byte-identical.",
            "changed": freeze_impact["change_detected"],
            "protected": len(guards),
            "all_hashes_match": True,
            "context_scenario": "Opt-in verifier influence creates a terminal pilot review notice and protection guards, not a technical update requirement.",
            "context_protected": sum(
                o["reach"] == "protection-boundary"
                for o in freeze_context["obligations"]
            ),
        },
    },
    "observed_git_repositories_preserved": len(before),
}
save("acceptance.json", summary)
print(json.dumps(summary, indent=2), flush=True)
