# ============================================================
# src/reactive_research/commands/snapshot.py
# ============================================================

"""CLI adapter for Reactive Research graph snapshots."""

import argparse

from reactive_research.commands.common import (
    add_output_arguments,
    add_path_argument,
    add_resolution_arguments,
    emit_result,
)
from reactive_research.snapshot import snapshot_research_graph


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the snapshot command."""
    parser.description = (
        "Create or inspect a reproducible Reactive Research graph snapshot."
    )

    parser.add_argument(
        "--show",
        metavar="SNAPSHOT_ID",
        help="Inspect an existing snapshot instead of creating one.",
    )

    add_path_argument(parser)
    add_resolution_arguments(parser)
    add_output_arguments(parser)

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Create or inspect a graph snapshot."""
    result = snapshot_research_graph(
        path=args.path,
        registry=args.registry,
        base_snapshot=args.snapshot,
        show=args.show,
    )

    emit_result(
        result,
        output_format=args.format,
        output=args.output,
    )
    return 0
