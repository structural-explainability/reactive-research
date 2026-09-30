# ============================================================
# src/reactive_research/cli.py
# ============================================================

"""Command-line interface for Reactive Research."""

import argparse
from collections.abc import Callable, Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib

from reactive_research.commands import (
    extract,
    graph,
    impact,
    inspect,
    resolve,
    snapshot,
    validate,
)

CommandHandler = Callable[[argparse.Namespace], int]


def _package_version() -> str:
    """Return the Reactive Research package version."""
    try:
        return version("reactive-research")
    except PackageNotFoundError:
        pyproject_path = Path(__file__).parents[2] / "pyproject.toml"

        with pyproject_path.open("rb") as file:
            pyproject = tomllib.load(file)

        project = pyproject.get("project")
        if not isinstance(project, dict):
            raise TypeError("pyproject.toml does not contain a [project] table.")

        package_version = project.get("version")
        if not isinstance(package_version, str) or not package_version:
            raise RuntimeError("pyproject.toml does not define project.version.")

        return package_version


def build_parser() -> argparse.ArgumentParser:
    """Build the Reactive Research command-line parser."""
    parser = argparse.ArgumentParser(
        prog="reactive-research",
        description=(
            "Build, validate, resolve, inspect, and analyze "
            "typed Reactive Research graphs."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_package_version()}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
    )

    extract.configure(
        subparsers.add_parser(
            "extract",
            help="Extract research-object declarations.",
        )
    )
    validate.configure(
        subparsers.add_parser(
            "validate",
            help="Validate Reactive Research declarations.",
        )
    )
    resolve.configure(
        subparsers.add_parser(
            "resolve",
            help="Resolve research-object references.",
        )
    )
    graph.configure(
        subparsers.add_parser(
            "graph",
            help="Build or inspect a typed research graph.",
        )
    )
    impact.configure(
        subparsers.add_parser(
            "impact",
            help="Analyze downstream impact from a research-object change.",
        )
    )
    snapshot.configure(
        subparsers.add_parser(
            "snapshot",
            help="Create or inspect a reproducible graph snapshot.",
        )
    )
    inspect.configure(
        subparsers.add_parser(
            "inspect",
            help="Explain a research object, repository, or relationship.",
        )
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Reactive Research command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    handler: CommandHandler = args.handler
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
