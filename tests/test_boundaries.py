"""Behavioral tests for the boundaries observation."""

import json
from pathlib import Path

import pytest

from reactive_research.boundaries import (
    boundaries_report,
    manifest_boundaries,
    observe_boundaries,
    parse_doubts,
)
from reactive_research.cli import main

DOUBTS_TEXT = """\
# Research Doubts

## Register 1. Doubts About Assumptions

### UM-001. (OPEN) Common Ground

#### Research criterion

Scientific Adequacy

#### Concern

Can it be established?

### UM-002. (RESOLVED) Joint Satisfiability

#### Concern

What if the assumptions conflict?

#### Resolution

A witness shows the assumptions are jointly satisfiable.

The witness is limited to two frameworks.

## Register 3. Undercutting

### UC-001. (STANDING RULES) Hypothesis

```markdown
### UM-099. (OPEN) Inside a fence is not an entry
```

### SL-1. Entry Without Status
"""


def write_repository(
    root: Path,
    name: str,
    *,
    includes: list[str],
    excludes: list[str],
    doubts: str | None = None,
    depends: str = "",
) -> Path:
    path = root / name
    path.mkdir()
    include_lines = "".join(f'    "{text}",\n' for text in includes)
    exclude_lines = "".join(f'    "{text}",\n' for text in excludes)
    (path / "SE_MANIFEST.toml").write_text(
        f'schema_version = "0.5.2"\n'
        f'[repository]\nname = "{name}"\norganization = "example-org"\n'
        f'class = "theory"\nstatus = "active"\n'
        f"[depends]\n{depends}"
        f"[scope]\nincludes = [\n{include_lines}]\nexcludes = [\n{exclude_lines}]\n",
        encoding="utf-8",
    )
    if doubts is not None:
        (path / "DOUBTS.md").write_text(doubts, encoding="utf-8")
    return path


def test_parse_doubts_reads_ids_statuses_and_short_fields() -> None:
    entries, diagnostics = parse_doubts(DOUBTS_TEXT)

    assert [entry["id"] for entry in entries] == ["UM-001", "UM-002", "UC-001", "SL-1"]
    by_id = {entry["id"]: entry for entry in entries}
    assert by_id["UM-001"]["status"] == "OPEN"
    assert by_id["UM-001"]["criterion"] == "Scientific Adequacy"
    assert by_id["UM-001"]["section"] == "Register 1. Doubts About Assumptions"
    assert by_id["UM-002"]["status"] == "RESOLVED"
    assert by_id["UM-002"]["resolution"] == (
        "A witness shows the assumptions are jointly satisfiable."
    )
    assert by_id["UC-001"]["status"] == "STANDING RULES"
    assert by_id["SL-1"]["status"] is None
    assert [item["code"] for item in diagnostics] == ["RR.DOUBT_STATUS_MISSING"]


def test_parse_doubts_ignores_headings_inside_code_fences() -> None:
    entries, _ = parse_doubts(DOUBTS_TEXT)

    assert "UM-099" not in [entry["id"] for entry in entries]


def test_parse_doubts_reports_duplicate_ids() -> None:
    text = "### UM-001. (OPEN) First\n\n### UM-001. (OPEN) Second\n"

    entries, diagnostics = parse_doubts(text)

    assert len(entries) == 2
    assert [item["code"] for item in diagnostics] == ["RR.DUPLICATE_DOUBT_ID"]
    assert diagnostics[0]["line"] == 3


def test_manifest_boundaries_reports_malformed_scope() -> None:
    manifest = {
        "repository": {"name": "example"},
        "scope": {"includes": "not a list", "excludes": ["kept"]},
        "depends": {"required": ["upstream"], "optional": [{"repo": "legacy"}]},
    }

    declared, diagnostics = manifest_boundaries(manifest, "SE_MANIFEST.toml")

    assert declared["includes"] == []
    assert declared["excludes"] == ["kept"]
    assert declared["depends"] == {"required": ["upstream"], "optional": ["legacy"]}
    assert [item["code"] for item in diagnostics] == ["RR.MALFORMED_SCOPE"]


def test_observation_is_deterministic_and_reports_missing_manifest(
    tmp_path: Path,
) -> None:
    write_repository(
        tmp_path,
        "upstream",
        includes=["Shared Topic", "Own Topic"],
        excludes=["Downstream Topic"],
        doubts=DOUBTS_TEXT,
    )
    write_repository(
        tmp_path,
        "downstream",
        includes=["shared  topic", "Downstream Topic"],
        excludes=["Nobody Owns This"],
    )
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare / "README.md").write_text("# bare\n", encoding="utf-8")

    first = observe_boundaries(tmp_path)
    second = observe_boundaries(tmp_path)

    assert first == second
    assert first["snapshot_id"].startswith("sha256:")
    names = [repository["path"] for repository in first["repositories"]]
    assert names == ["bare", "downstream", "upstream"]

    codes = [item["code"] for item in first["diagnostics"]]
    assert "RR.MANIFEST_NOT_FOUND" in codes

    provisional = first["provisional"]
    assert provisional["status"] == "provisional"
    assert [item["repositories"] for item in provisional["repeated_includes"]] == [
        ["downstream", "upstream"]
    ]
    assert provisional["excludes_without_exact_include"] == [
        {"text": "Nobody Owns This", "repository": "downstream"}
    ]


def test_observation_does_not_modify_repositories(tmp_path: Path) -> None:
    repo = write_repository(
        tmp_path, "upstream", includes=["Topic"], excludes=[], doubts=DOUBTS_TEXT
    )
    before = {
        path.name: path.read_bytes()
        for path in sorted(repo.iterdir())
        if path.is_file()
    }

    observe_boundaries(tmp_path)

    after = {
        path.name: path.read_bytes()
        for path in sorted(repo.iterdir())
        if path.is_file()
    }
    assert before == after


def test_report_groups_doubts_by_status_and_keeps_resolution(tmp_path: Path) -> None:
    write_repository(
        tmp_path, "upstream", includes=["Topic"], excludes=["Other"], doubts=DOUBTS_TEXT
    )

    report = boundaries_report(observe_boundaries(tmp_path))

    assert "## Open" in report
    assert "- UM-001 (OPEN): Common Ground" in report
    assert "## Resolved" in report
    assert (
        "Resolution: A witness shows the assumptions are jointly satisfiable." in report
    )
    assert "## Standing Rules" in report
    assert "- SL-1 (no status): Entry Without Status" in report
    assert "## Provisional Candidates" in report
    assert "## Scope" not in report


def test_scope_view_lists_includes_and_excludes(tmp_path: Path) -> None:
    write_repository(tmp_path, "upstream", includes=["Topic A"], excludes=["Topic B"])

    report = boundaries_report(observe_boundaries(tmp_path), view="scope")

    assert "## Scope" in report
    assert "- Topic A" in report
    assert "- Topic B" in report
    assert "## Open" not in report


def test_cli_writes_json_only_to_the_explicit_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_repository(workspace, "upstream", includes=["Topic"], excludes=[])
    output = tmp_path / "out" / "boundaries.json"

    code = main(
        [
            "boundaries",
            "--path",
            str(workspace),
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )

    assert code == 0
    assert capsys.readouterr().out == ""
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["format"] == "reactive-research-boundaries"
    assert document["repositories"][0]["name"] == "upstream"
    assert not (workspace / "upstream" / "boundaries.json").exists()
