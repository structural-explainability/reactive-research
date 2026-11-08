"""Behavioral tests for README-driven boundary observation."""

import json
from pathlib import Path
import subprocess

import pytest

from reactive_research.cli import main
from reactive_research.readme_sources import (
    observe_readme,
    organization_of,
    raw_readme_url,
    readme_repositories,
)

README = """\
# Org

[![Build](https://github.com/acme/.github/actions/workflows/ci.yml/badge.svg)](x)

| [alpha](https://github.com/acme/alpha) | first |
| [beta](https://github.com/acme/beta)   | second |
| [alpha again](https://github.com/acme/alpha) | duplicate |
| [elsewhere](https://github.com/other/gamma) | other org |
| [missing](https://github.com/acme/missing) | not reachable |

<!--
| [hidden](https://github.com/acme/hidden) | commented out |
-->
"""

MANIFEST = """\
[repository]
name = "{name}"
organization = "acme"
class = "theory"
kind = "lean"
status = "active"

[scope]
includes = ["{name} concept"]
excludes = []
"""

DOUBTS = """\
# Doubts

### UM-001. (OPEN) Something

#### Concern

Is it so?
"""


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.invalid",
            *args,
        ],
        check=True,
        capture_output=True,
    )


def _remote(root: Path, name: str, *, doubts: bool) -> Path:
    repository = root / name
    repository.mkdir(parents=True)
    _git(repository, "init", "--quiet", "-b", "main")
    (repository / "SE_MANIFEST.toml").write_text(MANIFEST.format(name=name))
    (repository / "README.md").write_text("not fetched\n")
    (repository / "src").mkdir()
    (repository / "src" / "big.lean").write_text("-- not fetched\n")
    if doubts:
        (repository / "DOUBTS.md").write_text(DOUBTS)
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "-m", "init")
    return repository


@pytest.fixture
def remotes(tmp_path: Path) -> Path:
    root = tmp_path / "remotes"
    _remote(root, "alpha", doubts=True)
    _remote(root, "beta", doubts=False)
    return root


def _clone_url(remotes: Path):
    def clone_url(organization: str, name: str) -> str:
        assert organization == "acme"
        return (remotes / name).as_uri()

    return clone_url


def test_readme_repositories_skips_comments_other_orgs_and_dot_github() -> None:
    assert readme_repositories(README, "acme") == ["alpha", "beta", "missing"]


def test_blob_url_becomes_raw_and_names_the_organization() -> None:
    url = "https://github.com/acme/.github/blob/main/profile/README.md"
    assert raw_readme_url(url) == (
        "https://raw.githubusercontent.com/acme/.github/main/profile/README.md"
    )
    assert organization_of(url) == "acme"
    assert raw_readme_url("https://example.invalid/r.md") == (
        "https://example.invalid/r.md"
    )


def test_observe_readme_reads_linked_repositories_and_reports_unreachable(
    remotes: Path,
) -> None:
    document = observe_readme(
        "https://github.com/acme/.github/blob/main/profile/README.md",
        fetch=lambda url: README,
        clone_url=_clone_url(remotes),
        jobs=2,
    )

    names = [repository["name"] for repository in document["repositories"]]
    assert names == ["alpha", "beta"]
    alpha = document["repositories"][0]
    assert alpha["includes"] == ["alpha concept"]
    assert [doubt["id"] for doubt in alpha["doubts"]] == ["UM-001"]
    assert alpha["source"]["mode"] == "committed"
    assert alpha["source"]["revision"]

    codes = {item["code"]: item for item in document["diagnostics"]}
    assert codes["RR.REPOSITORY_UNAVAILABLE"]["project"] == "missing"
    assert "3 repositories" in codes["RR.README_SOURCE"]["message"]


def test_observe_readme_fetches_only_manifest_and_doubts(
    remotes: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import reactive_research.readme_sources as module

    seen: dict[str, list[str]] = {}
    original = module.observe_boundaries

    def spy(workspace: Path, extra_diagnostics=None):
        for repository in workspace.iterdir():
            seen[repository.name] = sorted(
                p.relative_to(repository).as_posix()
                for p in repository.rglob("*")
                if p.is_file() and ".git" not in p.relative_to(repository).parts
            )
        return original(workspace, extra_diagnostics)

    monkeypatch.setattr(module, "observe_boundaries", spy)
    observe_readme(
        "https://github.com/acme/.github/blob/main/profile/README.md",
        fetch=lambda url: README,
        clone_url=_clone_url(remotes),
    )
    assert seen["alpha"] == ["DOUBTS.md", "SE_MANIFEST.toml"]
    assert seen["beta"] == ["SE_MANIFEST.toml"]


def test_local_readme_needs_an_organization(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(README, encoding="utf-8")
    with pytest.raises(ValueError, match="--org"):
        observe_readme(str(readme))


def test_workspace_is_removed_after_observation(
    remotes: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import reactive_research.readme_sources as module

    created: list[Path] = []
    original = module.observe_boundaries

    def spy(workspace: Path, extra_diagnostics=None):
        created.append(workspace)
        return original(workspace, extra_diagnostics)

    monkeypatch.setattr(module, "observe_boundaries", spy)
    observe_readme(
        "https://github.com/acme/.github/blob/main/profile/README.md",
        fetch=lambda url: README,
        clone_url=_clone_url(remotes),
    )
    assert created
    assert not created[0].exists()


def test_cli_from_readme_with_local_file(
    remotes: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import reactive_research.readme_sources as module

    monkeypatch.setattr(module, "github_clone_url", _clone_url(remotes))
    readme = tmp_path / "README.md"
    readme.write_text(README, encoding="utf-8")

    assert (
        main(
            [
                "boundaries",
                "--from-readme",
                str(readme),
                "--org",
                "acme",
                "--format",
                "json",
            ]
        )
        == 0
    )
    document = json.loads(capsys.readouterr().out)
    assert [r["name"] for r in document["repositories"]] == ["alpha", "beta"]


def test_cli_reports_missing_organization(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(README, encoding="utf-8")
    assert main(["boundaries", "--from-readme", str(readme)]) == 2
    assert "--org" in capsys.readouterr().err
