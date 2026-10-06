"""Behavioral tests for immutable observation snapshots."""

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from reactive_research.cli import main
from reactive_research.declarations import export_declarations
from reactive_research.graph import graph_projection, mermaid_graph
from reactive_research.observation import discover_projects, read_project
from reactive_research.resolve import resolve_research
from reactive_research.snapshot import load_snapshot, observe_workspace


def git_command(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *args],
        text=True,
    ).strip()


def commit(root: Path, message: str) -> str:
    git_command(root, "add", ".")
    git_command(
        root,
        "-c",
        "user.name=RR test",
        "-c",
        "user.email=rr@example.invalid",
        "commit",
        "-m",
        message,
    )
    return git_command(root, "rev-parse", "HEAD")


def project(root: Path, name: str, *, source: str = "", depends: str = "") -> Path:
    path = root / name
    path.mkdir()
    (path / "SE_MANIFEST.toml").write_text(
        f'[repository]\nname="{name}"\nstatus="active"\n{depends}', encoding="utf-8"
    )
    (path / "source.py").write_text(source, encoding="utf-8")
    return path


def test_snapshot_deterministic_and_working_state_distinct(tmp_path: Path) -> None:
    repo = project(
        tmp_path, "provider", source="# RR.DEFINES: Example.Definition\nvalue=1\n"
    )
    git_command(repo, "init")
    first = commit(repo, "first")
    (repo / "source.py").write_text(
        "# RR.DEFINES: Example.Definition\nvalue=2\n", encoding="utf-8"
    )
    status_before = git_command(repo, "status", "--porcelain")
    current = observe_workspace(tmp_path)
    repeated = observe_workspace(tmp_path)
    assert current == repeated
    state = next(n for n in current["nodes"] if n["kind"] == "repository")["state"]
    assert state["head"] == first
    assert state["mode"] == "working"
    assert state["differs_from_head"] is True
    assert state["observed_revision"].startswith("working:sha256:")
    historical = observe_workspace(tmp_path, revisions={"provider": first})
    assert historical["snapshot_id"] != current["snapshot_id"]
    historical_state = next(
        n for n in historical["nodes"] if n["kind"] == "repository"
    )["state"]
    assert historical_state["mode"] == "committed"
    assert historical_state["observation"] == "git-tree"
    assert git_command(repo, "status", "--porcelain") == status_before
    assert git_command(repo, "rev-parse", "HEAD") == first
    assert "value=2" in (repo / "source.py").read_text()


def test_unborn_tracked_content_and_non_git(tmp_path: Path) -> None:
    repo = project(tmp_path, "new")
    git_command(repo, "init")
    git_command(repo, "add", ".")
    data, state = read_project(repo)
    assert "source.py" in data
    assert state["head"] is None and state["mode"] == "working"
    assert state["source_revision"] is None
    (repo / ".venv").mkdir()
    (repo / ".venv" / "README.md").write_text("ignored")
    assert discover_projects(tmp_path) == [repo]


def test_snapshot_integrity_resolution_and_cli(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project(tmp_path, "provider", source="# RR.DEFINES: Example.Definition\n")
    project(tmp_path, "consumer", source="# RR.IMPLEMENTS: Example.Definition\n")
    snapshot = observe_workspace(tmp_path)
    output = tmp_path / "snapshot.json"
    output.write_text(json.dumps(snapshot), encoding="utf-8")
    assert load_snapshot(str(output)) == snapshot
    # Snapshot resolution must not reread a modified live provider.
    (tmp_path / "provider" / "source.py").write_text("removed", encoding="utf-8")
    result = resolve_research(
        path=tmp_path / "missing",
        identifier="Example.Definition",
        resolve_all=False,
        registry=None,
        snapshot=str(output),
    )
    assert result["resolved"]
    assert result["results"][0]["definitions"][0]["state"] == "working"
    invalid = resolve_research(
        path=tmp_path,
        identifier="invalid identifier!",
        resolve_all=False,
        registry=None,
        snapshot=str(output),
    )
    assert invalid["diagnostics"][0]["code"] == "RR.INVALID_IDENTIFIER"
    assert (
        main(
            [
                "graph",
                "--snapshot",
                str(output),
                "--format",
                "mermaid",
                "--category",
                "evolution",
            ]
        )
        == 0
    )
    assert "implements / semantic" in capsys.readouterr().out
    assert main(["snapshot", "--show", str(output), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["snapshot_id"] == snapshot["snapshot_id"]
    snapshot["nodes"][0]["label"] = "tampered"
    output.write_text(json.dumps(snapshot), encoding="utf-8")
    with pytest.raises(ValueError, match="content-addressed"):
        load_snapshot(str(output))


def test_paper_labels_reference_and_freeze(tmp_path: Path) -> None:
    repo = project(tmp_path, "paper")
    (repo / "SE_MANIFEST.toml").write_text(
        '[repository]\nname="paper"\nclass="paper"\n', encoding="utf-8"
    )
    (repo / "paper.tex").write_text(
        "\\begin{definition}\n\\label{se100.def.Example}\nBody\n\\end{definition}",
        encoding="utf-8",
    )
    lean = project(tmp_path, "formal")
    (lean / "example.lean").write_text(
        "/-!\nThis module formalizes:\n- `se100.def.Example`\n\nA proof.\n-/\n",
        encoding="utf-8",
    )
    frozen_bytes = b"evidence\r\n"
    (lean / "evidence.txt").write_bytes(frozen_bytes)
    sha = hashlib.sha256(frozen_bytes).hexdigest()
    (lean / "FREEZE_01.md").write_text(
        f"**Status:** FROZEN\n- `{sha}`  `evidence.txt`\n", encoding="utf-8"
    )
    snapshot = observe_workspace(tmp_path)
    assert any(
        e["relation"] == "formalizes" and e["resolution"] == "resolved"
        for e in snapshot["edges"]
    )
    frozen = next(n for n in snapshot["nodes"] if n.get("lifecycle") == "frozen")
    assert frozen["protection"]["hash_matches"]
    assert "formalizes" in mermaid_graph(snapshot, category="evolution")
    projection = graph_projection(snapshot, view="repositories")
    assert any(
        e["source"] == "repo:formal" and e["target"] == "repo:paper"
        for e in projection["edges"]
    )
    (lean / "evidence.txt").write_bytes(b"changed")
    changed = observe_workspace(tmp_path)
    assert any(d["code"] == "RR.FREEZE_HASH_MISMATCH" for d in changed["diagnostics"])


def test_alias_ambiguity_not_silently_overwritten(tmp_path: Path) -> None:
    first = project(tmp_path, "one")
    second = project(tmp_path, "two")
    for repo in (first, second):
        (repo / "lakefile.toml").write_text('name="shared"\n', encoding="utf-8")
    consumer = project(tmp_path, "consumer")
    (consumer / "lakefile.toml").write_text(
        '[[require]]\nname="shared"\nrev="main"\n', encoding="utf-8"
    )
    graph = observe_workspace(tmp_path)
    edge = next(e for e in graph["edges"] if e.get("declared_target") == "shared")
    assert edge["resolution"] == "ambiguous" and len(edge["candidates"]) == 2


def test_external_published_definitions_and_content_addressed_load(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    provider = project(tmp_path, "external", source="# RR.DEFINES: Example.External\n")
    project(workspace, "consumer", source="# RR.IMPLEMENTS: Example.External\n")
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "declarations.json").write_text(
        json.dumps(export_declarations(provider)), encoding="utf-8"
    )
    graph = observe_workspace(workspace, registry=str(registry))
    edge = next(e for e in graph["edges"] if e["relation"] == "implements")
    assert edge["resolution"] == "resolved"
    definition = next(
        n for n in graph["nodes"] if n["id"] == "object:Example.External"
    )["definitions"][0]
    assert definition["state"] == "registry-declaration"
    snapshot_id = graph["snapshot_id"]
    (registry / (snapshot_id.removeprefix("sha256:") + ".json")).write_text(
        json.dumps(graph), encoding="utf-8"
    )
    assert load_snapshot(snapshot_id, str(registry)) == graph
    with pytest.raises(ValueError, match="requires"):
        load_snapshot(snapshot_id)


def test_independent_git_site_is_not_a_generated_site(tmp_path: Path) -> None:
    repo = project(tmp_path, "site")
    git_command(repo, "init")
    assert discover_projects(tmp_path) == [repo]


def test_malformed_surface_and_repeated_unresolved_edges(tmp_path: Path) -> None:
    project(tmp_path, "one", source="# RR.IMPLEMENTS: Example.Missing\n")
    repo = project(tmp_path, "two", source="# RR.IMPLEMENTS: Example.Missing\n")
    (repo / "lakefile.toml").write_text("[broken", encoding="utf-8")
    graph = observe_workspace(tmp_path)
    assert all(e["resolution"] == "unresolved" for e in graph["edges"])
    assert any(d["code"] == "RR.SURFACE_PARSE" for d in graph["diagnostics"])
