# ============================================================
# src/reactive_research/repository.py
# ============================================================

"""Repository discovery for Reactive Research."""

from pathlib import Path
import subprocess
import tomllib

from reactive_research.models import RepositoryContext

_MANIFEST_NAMES = (
    "SE_MANIFEST.toml",
    "MANIFEST.toml",
)


def discover_repository_context(path: Path) -> RepositoryContext:
    """Discover repository identity and revision."""
    root = path.resolve()

    organization: str | None = None
    name = root.name

    manifest_path = _find_manifest(root)
    if manifest_path is not None:
        manifest = _load_toml(manifest_path)

        repository = manifest.get("repository")
        if isinstance(repository, dict):
            repository_name = repository.get("name")
            repository_organization = repository.get("organization")

            if isinstance(repository_name, str) and repository_name:
                name = repository_name

            if isinstance(repository_organization, str) and repository_organization:
                organization = repository_organization

        # Compatibility with older SE manifests.
        repo = manifest.get("repo")
        if isinstance(repo, dict):
            repository_name = repo.get("name")
            if isinstance(repository_name, str) and repository_name:
                name = repository_name

    return RepositoryContext(
        root=root,
        organization=organization,
        name=name,
        revision=_git_revision(root),
    )


def _find_manifest(root: Path) -> Path | None:
    """Find a supported repository manifest."""
    for filename in _MANIFEST_NAMES:
        candidate = root / filename
        if candidate.is_file():
            return candidate

    return None


def _load_toml(path: Path) -> dict[str, object]:
    """Load one TOML document."""
    with path.open("rb") as file:
        return tomllib.load(file)


def _git_revision(root: Path) -> str | None:
    """Return the current Git commit SHA when available."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )

    if result.returncode != 0:
        return None

    revision = result.stdout.strip()
    return revision or None
