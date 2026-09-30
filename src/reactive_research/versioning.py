# ============================================================
# src/reactive_research/versioning.py
# ============================================================

"""Package-version discovery for Reactive Research."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib

_PACKAGE_NAME = "reactive-research"


def package_version() -> str:
    """Return the Reactive Research package version."""
    try:
        return version(_PACKAGE_NAME)
    except PackageNotFoundError:
        pyproject_path = Path(__file__).parents[2] / "pyproject.toml"

        with pyproject_path.open("rb") as file:
            pyproject = tomllib.load(file)

        project = pyproject.get("project")
        if not isinstance(project, dict):
            raise TypeError("pyproject.toml does not contain a [project] table.")

        project_version = project.get("version")
        if not isinstance(project_version, str) or not project_version:
            raise RuntimeError("pyproject.toml does not define project.version.")

        return project_version
