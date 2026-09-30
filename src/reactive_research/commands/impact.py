# ============================================================
# src/reactive_research/commands/impact.py
# ============================================================

"""CLI adapter for Reactive Research impact analysis."""

import argparse

from reactive_research.commands.common import (
    add_output_arguments,
    add_path_argument,
    add_resolution_arguments,
    emit_result,
)
from reactive_research.impact import analyze_impact


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the impact command."""
    parser.description = (
        "Identify downstream research affected by a changed research object."
    )

    parser.add_argument(
        "identifier",
        help="Changed research-object identifier.",
    )

    depth = parser.add_mutually_exclusive_group()
    depth.add_argument(
        "--direct",
        dest="depth",
        action="store_const",
        const="direct",
        help="Report directly affected objects only.",
    )
    depth.add_argument(
        "--transitive",
        dest="depth",
        action="store_const",
        const="transitive",
        help="Report direct and transitive impact.",
    )

    parser.set_defaults(depth="transitive")

    parser.add_argument(
        "--from-snapshot",
        help="Previous graph snapshot.",
    )
    parser.add_argument(
        "--to-snapshot",
        help="Current graph snapshot.",
    )

    add_path_argument(parser)
    add_resolution_arguments(parser)
    add_output_arguments(parser)

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run downstream impact analysis."""
    result = analyze_impact(
        path=args.path,
        identifier=args.identifier,
        depth=args.depth,
        registry=args.registry,
        snapshot=args.snapshot,
        from_snapshot=args.from_snapshot,
        to_snapshot=args.to_snapshot,
    )

    emit_result(
        result,
        output_format=args.format,
        output=args.output,
    )
    return 0
