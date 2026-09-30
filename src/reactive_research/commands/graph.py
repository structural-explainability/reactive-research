# ============================================================
# src/reactive_research/commands/graph.py
# ============================================================

"""CLI adapter for Reactive Research graph operations."""

import argparse

from reactive_research.commands.common import (
    add_output_arguments,
    add_path_argument,
    add_resolution_arguments,
    emit_result,
)
from reactive_research.graph import build_research_graph


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the graph command."""
    parser.description = "Build or inspect the typed Reactive Research graph."

    parser.add_argument(
        "target",
        nargs="?",
        help="Optional research object or repository to focus on.",
    )
    parser.add_argument(
        "--view",
        choices=("objects", "repositories"),
        default="objects",
        help="Graph projection to display. Default: objects.",
    )

    add_path_argument(parser)
    add_resolution_arguments(parser)
    add_output_arguments(parser)

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Build or inspect the research graph."""
    result = build_research_graph(
        path=args.path,
        target=args.target,
        view=args.view,
        registry=args.registry,
        snapshot=args.snapshot,
    )

    emit_result(
        result,
        output_format=args.format,
        output=args.output,
    )
    return 0
