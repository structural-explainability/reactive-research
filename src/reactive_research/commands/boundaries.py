# ============================================================
# src/reactive_research/commands/boundaries.py
# ============================================================

"""CLI adapter for observing declared research boundaries."""

import argparse
import json
import sys

from reactive_research.boundaries import boundaries_report, observe_boundaries
from reactive_research.commands.common import (
    add_output_arguments,
    add_path_argument,
)
from reactive_research.readme_sources import observe_readme


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the boundaries command."""
    parser.description = (
        "Observe manifest scope and DOUBTS.md entries across repositories. "
        "Read-only; the explicit --output option is the only write."
    )

    add_path_argument(parser)
    parser.add_argument(
        "--from-readme",
        metavar="SOURCE",
        help=(
            "Observe the repositories linked from an organization README "
            "(a GitHub URL or a local file) instead of --path. Only manifests "
            "and DOUBTS.md are fetched, into a temporary directory."
        ),
    )
    parser.add_argument(
        "--org",
        help="GitHub organization for --from-readme when SOURCE is a local file.",
    )
    parser.add_argument(
        "--view",
        choices=("index", "scope", "all"),
        default="index",
        help=(
            "Text view: index (doubts, diagnostics, candidates), "
            "scope (includes and excludes), or all. Default: index."
        ),
    )
    add_output_arguments(parser)

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Observe boundaries and emit the result."""
    if args.from_readme:
        try:
            document = observe_readme(args.from_readme, organization=args.org)
        except (OSError, ValueError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
    else:
        document = observe_boundaries(args.path)

    if args.format == "json":
        rendered = json.dumps(document, indent=2, sort_keys=True)
    else:
        rendered = boundaries_report(document, view=args.view).rstrip("\n")

    if args.output is None:
        print(rendered)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0
