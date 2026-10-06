# ============================================================
# src/reactive_research/cli.py
# ============================================================

"""Command-line interface for Reactive Research.

Generally:

extract > validate > resolve > graph > impact > snapshot > generate > inspect
"""

import argparse
from collections.abc import Callable, Sequence

from reactive_research.commands import (
    extract,
    generate,
    graph,
    impact,
    inspect,
    resolve,
    snapshot,
    validate,
)
from reactive_research.versioning import package_version

CommandHandler = Callable[[argparse.Namespace], int]


def build_parser() -> argparse.ArgumentParser:
    """Build the Reactive Research command-line parser."""
    parser = argparse.ArgumentParser(
        prog="reactive-research",
        description=(
            "Extract, validate, resolve, graph, impact, snapshot, generate, "
            "and inspect typed Reactive Research views."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version()}",
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
    generate.configure(
        subparsers.add_parser(
            "generate",
            help="Generate human-facing Reactive Research documentation.",
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
    try:
        return handler(args)
    except (OSError, ValueError) as error:
        parser.exit(2, f"reactive-research: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
