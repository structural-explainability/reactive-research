# ============================================================
# src/reactive_research/readme_sources.py
# ============================================================

"""Observe boundaries for repositories linked from an organization README.

WHY: An organization profile README is the declared list of its repositories.
Reading boundaries from that list avoids a hand-maintained registry.
REQ: Read-only toward every remote. Only manifests and DOUBTS.md are fetched.
REQ: A repository that cannot be reached is reported, never silently dropped.
"""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from reactive_research.boundaries import observe_boundaries

FETCH_TIMEOUT_SECONDS = 30
CLONE_TIMEOUT_SECONDS = 120
SPARSE_PATHS = (
    "/SE_MANIFEST.toml",
    "/MANIFEST.toml",
    "/se-manifest.toml",
    "/DOUBTS.md",
)
EXCLUDED_REPOSITORIES = frozenset({".github"})
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

Fetch = Callable[[str], str]
CloneUrl = Callable[[str, str], str]


def raw_readme_url(source: str) -> str:
    """Return a fetchable URL, converting a GitHub blob URL to its raw form."""
    parsed = urlparse(source)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc == "github.com" and len(parts) >= 5 and parts[2] == "blob":
        organization, repository, _, branch, *rest = parts
        return (
            f"https://raw.githubusercontent.com/{organization}/{repository}/"
            f"{branch}/{'/'.join(rest)}"
        )
    return source


def organization_of(source: str) -> str | None:
    """Return the GitHub organization named by a URL source, if any."""
    parsed = urlparse(source)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc == "github.com" and parts:
        return parts[0]
    if parsed.netloc == "raw.githubusercontent.com" and parts:
        return parts[0]
    return None


def readme_repositories(text: str, organization: str) -> list[str]:
    """Return repository names linked in README text, in first-seen order.

    Links inside HTML comments are ignored, as are other organizations and
    repositories in EXCLUDED_REPOSITORIES.
    """
    visible = _COMMENT.sub("", text)
    pattern = re.compile(
        rf"github\.com/{re.escape(organization)}/([A-Za-z0-9._-]+)", re.IGNORECASE
    )
    names: list[str] = []
    for match in pattern.finditer(visible):
        name = match.group(1).removesuffix(".git")
        if name and name not in EXCLUDED_REPOSITORIES and name not in names:
            names.append(name)
    return names


def fetch_text(url: str) -> str:
    """Fetch a text document over HTTPS."""
    request = Request(url, headers={"User-Agent": "reactive-research"})
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def github_clone_url(organization: str, name: str) -> str:
    """Return the HTTPS clone URL for a GitHub repository."""
    return f"https://github.com/{organization}/{name}.git"


def sparse_clone(url: str, destination: Path) -> str | None:
    """Clone only manifest and DOUBTS files; return an error message on failure."""
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    steps = (
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--no-checkout",
            "--quiet",
            url,
            str(destination),
        ],
        [
            "git",
            "-C",
            str(destination),
            "sparse-checkout",
            "set",
            "--no-cone",
            *SPARSE_PATHS,
        ],
        ["git", "-C", str(destination), "checkout", "--quiet"],
    )
    for command in steps:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=environment,
                timeout=CLONE_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return "git timed out"
        if result.returncode != 0:
            lines = (result.stderr or result.stdout).strip().splitlines()
            return lines[-1] if lines else f"git exited {result.returncode}"
    return None


def observe_readme(
    source: str,
    *,
    organization: str | None = None,
    fetch: Fetch | None = None,
    clone_url: CloneUrl | None = None,
    jobs: int = 8,
) -> dict[str, Any]:
    """Observe boundaries for every repository the README links.

    ``source`` is a URL or a local file path. A local path needs ``organization``.
    """
    local = Path(source)
    if local.is_file():
        text = local.read_text(encoding="utf-8")
    else:
        text = (fetch or fetch_text)(raw_readme_url(source))

    organization = organization or organization_of(source)
    if organization is None:
        raise ValueError(
            "The organization cannot be derived from the source; use --org."
        )

    names = readme_repositories(text, organization)
    diagnostics: list[dict[str, Any]] = [
        {
            "code": "RR.README_SOURCE",
            "severity": "info",
            "project": source,
            "message": (
                f"{len(names)} repositories of {organization} are linked "
                "from the README."
            ),
        }
    ]

    with tempfile.TemporaryDirectory(prefix="rr-readme-") as scratch:
        workspace = Path(scratch)

        def clone(name: str) -> tuple[str, str | None]:
            return name, sparse_clone(
                (clone_url or github_clone_url)(organization, name), workspace / name
            )

        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            outcomes = list(pool.map(clone, names))

        for name, error in outcomes:
            if error is not None:
                diagnostics.append(
                    {
                        "code": "RR.REPOSITORY_UNAVAILABLE",
                        "severity": "warning",
                        "project": name,
                        "message": f"Repository could not be read: {error}",
                    }
                )

        return observe_boundaries(workspace, extra_diagnostics=diagnostics)
