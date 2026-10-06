"""Tests for typed obligation traversal and protection boundaries."""

import hashlib
import json
from pathlib import Path

import pytest

from reactive_research.cli import main
from reactive_research.graph import mermaid_graph
from reactive_research.impact import impact_obligations
from reactive_research.report import obligation_report
from reactive_research.snapshot import observe_workspace
from tests.test_observation import commit, git_command, project


def test_direct_transitive_cycles_and_semantics(tmp_path: Path) -> None:
    project(
        tmp_path,
        "upstream",
        source="# RR.DEFINES: Example.Source\n# RR.IMPLEMENTS: Example.Third\n",
    )
    project(
        tmp_path,
        "consumer",
        source="# RR.IMPLEMENTS: Example.Source\n# RR.DEFINES: Example.Second\n",
    )
    project(
        tmp_path,
        "third",
        source="# RR.IMPLEMENTS: Example.Second\n# RR.DEFINES: Example.Third\n",
    )
    graph = observe_workspace(tmp_path)
    direct = impact_obligations(graph, "Example.Source", depth="direct")
    assert {o["consumer"]["id"] for o in direct["obligations"]} == {"repo:consumer"}
    # Repository-owned definitions are not silently semantic dependencies:
    # changing an implementation doesn't prove its other defined claims changed.
    transitive = impact_obligations(graph, "Example.Source")
    assert {o["consumer"]["id"] for o in transitive["obligations"]} == {"repo:consumer"}
    assert all(o["disposition"] == "semantic review" for o in transitive["obligations"])
    assert not impact_obligations(graph, "Example.Source", previous=graph)[
        "obligations"
    ]
    with pytest.raises(ValueError, match="Unsupported"):
        impact_obligations(graph, "Example.Source", relations={"magic"})


def test_build_chain_pin_visibility_and_determinism(tmp_path: Path) -> None:
    project(tmp_path, "se-upstream")
    for name, dependency in (("consumer", "se-upstream"), ("third", "consumer")):
        repo = project(tmp_path, name)
        (repo / "lakefile.toml").write_text(
            f'[[require]]\nname="{dependency}"\nrev="v1.0.0"\n', encoding="utf-8"
        )
    graph = observe_workspace(tmp_path)
    direct = impact_obligations(graph, "se-upstream", depth="direct")
    assert {o["consumer"]["label"] for o in direct["obligations"]} == {"consumer"}
    transitive = impact_obligations(graph, "se-upstream")
    assert {o["consumer"]["label"] for o in transitive["obligations"]} == {
        "consumer",
        "third",
    }
    assert transitive == impact_obligations(graph, "se-upstream")
    assert {o["disposition"] for o in transitive["obligations"]} >= {
        "verification required",
        "semantic review",
        "mechanical candidate",
    }
    assert "PENDING MECHANICAL PROPAGATION" in obligation_report(transitive)
    assert "classDef mechanical" in mermaid_graph(transitive, category="impact")


def test_informs_opt_in_terminal_and_frozen_guard(tmp_path: Path) -> None:
    project(tmp_path, "theory", source="# RR.DEFINES: Example.Theory\n")
    pilot = project(tmp_path, "pilot")
    (pilot / "README.md").write_text(
        "This pilot is motivated by:\n- https://github.com/example/theory\n",
        encoding="utf-8",
    )
    project(tmp_path, "downstream", source="# RR.DEPENDS: Example.Theory\n")
    content = b"frozen evidence"
    (pilot / "evidence.txt").write_bytes(content)
    sha = hashlib.sha256(content).hexdigest()
    (pilot / "FREEZE_01.md").write_text(
        f"**Status:** FROZEN\n- `{sha}`  `evidence.txt`\n", encoding="utf-8"
    )
    project(tmp_path, "successor", depends='[depends]\nrequired=["pilot"]\n')
    graph = observe_workspace(tmp_path)
    default = impact_obligations(graph, "theory")
    assert not any(o["consumer"]["label"] == "pilot" for o in default["obligations"])
    contextual = impact_obligations(
        graph, "theory", relations={"informs", "depends-on"}
    )
    assert any(
        o["consumer"]["label"] == "pilot" and o["disposition"] == "semantic review"
        for o in contextual["obligations"]
    )
    assert not any(
        o["consumer"]["label"] == "successor" for o in contextual["obligations"]
    )
    guards = [
        o for o in contextual["obligations"] if o["reach"] == "protection-boundary"
    ]
    assert len(guards) == 1 and guards[0]["disposition"].startswith("frozen/protected")
    assert "DO NOT MODIFY FROZEN EVIDENCE" in obligation_report(contextual)
    assert (pilot / "evidence.txt").read_bytes() == content


def test_removed_change_cli_report_and_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project(tmp_path, "provider", source="# RR.DEFINES: Example.Source\n")
    project(tmp_path, "consumer", source="# RR.TESTS: Example.Source\n")
    before = observe_workspace(tmp_path)
    (tmp_path / "provider" / "source.py").write_text(
        "# RR.DEFINES: Example.Source\nchanged=True", encoding="utf-8"
    )
    after = observe_workspace(tmp_path)
    before_file = tmp_path / "before.json"
    after_file = tmp_path / "after.json"
    before_file.write_text(json.dumps(before), encoding="utf-8")
    after_file.write_text(json.dumps(after), encoding="utf-8")
    assert (
        main(
            [
                "impact",
                "Example.Source",
                "--from-snapshot",
                str(before_file),
                "--to-snapshot",
                str(after_file),
            ]
        )
        == 0
    )
    assert "verification required" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        main(["impact", "missing", "--snapshot", str(after_file)])
    assert exc.value.code == 2


def test_cycles_pinned_revision_and_frozen_consumer_stop(tmp_path: Path) -> None:
    source = project(tmp_path, "upstream")
    git_command(source, "init")
    old = commit(source, "first")
    (source / "source.py").write_text("changed=True", encoding="utf-8")
    new = commit(source, "second")
    consumer = project(
        tmp_path, "consumer", depends='[depends]\nrequired=["upstream"]\n'
    )
    (consumer / "lakefile.toml").write_text(
        '[[require]]\nname="upstream"\nrev="old"\n', encoding="utf-8"
    )
    (consumer / "lake-manifest.json").write_text(
        json.dumps({"packages": [{"name": "upstream", "rev": old}]}), encoding="utf-8"
    )
    (source / "lakefile.toml").write_text(
        '[[require]]\nname="consumer"\n', encoding="utf-8"
    )
    graph = observe_workspace(tmp_path)
    result = impact_obligations(graph, "upstream")
    assert any(
        o["disposition"] == "mechanical candidate"
        and o["constraints"].get("resolved_revision") == old
        for o in result["obligations"]
    )
    assert result["source"]["state"]["head"] == new
    assert len(result["obligations"]) < 10
    (consumer / "SE_MANIFEST.toml").write_text(
        '[repository]\nname="consumer"\nstatus="frozen"\n[depends]\nrequired=["upstream"]\n',
        encoding="utf-8",
    )
    project(tmp_path, "downstream", depends='[depends]\nrequired=["consumer"]\n')
    protected_graph = observe_workspace(tmp_path)
    protected = impact_obligations(protected_graph, "upstream")
    assert all(
        o["consumer"]["label"] == "consumer"
        and o["disposition"].startswith("frozen/protected")
        for o in protected["obligations"]
    )
    assert not any(
        o["consumer"]["label"] == "downstream" for o in protected["obligations"]
    )
