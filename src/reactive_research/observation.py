"""Read-only filesystem and Git observations; no checkout or repository writes."""

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

IGNORED = frozenset(
    {
        ".git",
        ".venv",
        ".lake",
        "node_modules",
        "__pycache__",
        ".cache",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".tox",
        "site",
        "build",
        "dist",
    }
)
MARKERS = (
    "SE_MANIFEST.toml",
    "MANIFEST.toml",
    "se-manifest.toml",
    "pyproject.toml",
    "lakefile.toml",
    "package.json",
    "README.md",
)


def canonical(value: Any) -> str:
    """Serialize semantic data without timestamps or platform whitespace."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    """Hash a canonical JSON value."""
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def git(root: Path, *args: str) -> str | None:
    """Run one read-only Git query with checkout-scoped ownership trust."""
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={root.as_posix()}",
                "--no-optional-locks",
                "-C",
                str(root),
                *args,
            ],
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    return result.stdout.rstrip("\n") if result.returncode == 0 else None


def discover_projects(root: Path) -> list[Path]:
    """Discover roots from Git boundaries or existing project surfaces."""
    root = root.resolve()
    projects: list[Path] = []
    for directory, names, files in os.walk(root, followlinks=False):
        path = Path(directory)
        names[:] = sorted(
            n
            for n in names
            if (n not in IGNORED or (n != ".git" and (path / n / ".git").exists()))
            and not (path / n).is_symlink()
        )
        is_git = (path / ".git").exists()
        if is_git or any(marker in files for marker in MARKERS):
            projects.append(path)
            # A project's internal fixtures are not independent research projects.
            names[:] = []
    return sorted(projects)


@dataclass(frozen=True)
class SourceState:
    """Separate an observed content identity from its committed provenance."""

    head: str | None
    source_revision: str | None
    mode: str
    differs_from_head: bool | None
    content_digest: str
    exact_tags: tuple[str, ...]


def read_project(
    root: Path, revision: str | None = None
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Read working bytes or an immutable Git tree without checking it out."""
    head = (
        git(root, "rev-parse", "--verify", "HEAD") if (root / ".git").exists() else None
    )
    data: dict[str, bytes] = {}
    if revision is not None:
        resolved = git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")
        if not resolved:
            raise ValueError(f"Revision cannot be resolved in {root}: {revision}")
        entries = git(root, "ls-tree", "-r", "-z", resolved) or ""
        for entry in entries.split("\0"):
            if not entry:
                continue
            metadata, name = entry.split("\t", 1)
            mode, kind, oid = metadata.split()
            if (
                kind != "blob"
                or mode == "120000"
                or any(p in IGNORED for p in Path(name).parts)
            ):
                continue
            result = subprocess.run(
                [
                    "git",
                    "-c",
                    f"safe.directory={root.as_posix()}",
                    "--no-optional-locks",
                    "-C",
                    str(root),
                    "cat-file",
                    "blob",
                    oid,
                ],
                capture_output=True,
                check=True,
            )
            data[name] = result.stdout
        dirty: bool | None = False
        mode_name = "committed"
    else:
        resolved = head
        status = (
            git(root, "status", "--porcelain=v1", "--untracked-files=all")
            if head
            else None
        )
        dirty = bool(status) if status is not None else None
        mode_name = "working" if dirty or not head else "committed"
        tracked = (
            set((git(root, "ls-files", "-z") or "").split("\0"))
            if (root / ".git").exists()
            else set()
        )
        candidates = set(tracked)
        if (root / ".git").exists():
            candidates.update(
                (
                    git(root, "ls-files", "-z", "--others", "--exclude-standard") or ""
                ).split("\0")
            )
        else:
            for directory, names, files in os.walk(root, followlinks=False):
                path = Path(directory)
                names[:] = sorted(
                    n for n in names if n not in IGNORED and not (path / n).is_symlink()
                )
                candidates.update(
                    (path / n).relative_to(root).as_posix() for n in files
                )
        for name in sorted(candidates):
            path = root / name
            if (
                name
                and not any(p in IGNORED for p in Path(name).parts)
                and path.is_file()
                and not path.is_symlink()
            ):
                data[name] = path.read_bytes()
    hashes = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in sorted(data.items())
    }
    tags = (
        tuple(sorted((git(root, "tag", "--points-at", resolved) or "").splitlines()))
        if resolved
        else ()
    )
    state = SourceState(head, resolved, mode_name, dirty, digest(hashes), tags)
    return data, {
        **asdict(state),
        "exact_tags": list(tags),
        "commit_time": git(root, "show", "-s", "--format=%cI", resolved)
        if resolved
        else None,
        "files": hashes,
        "observation": "git-tree" if revision is not None else "filesystem",
        "observed_revision": resolved
        if revision is not None
        else "working:sha256:" + digest(hashes),
    }
