# ============================================================
# src/reactive_research/commands/inspect.py
# ============================================================

"""CLI adapter for Reactive Research inspection."""

import argparse

from reactive_research.commands.common import (
    add_output_arguments,
    add_path_argument,
    add_resolution_arguments,
    emit_result,
)
from reactive_research.inspect import inspect_research_object


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the inspect command."""
    parser.description = "Explain a research object, repository, or relationship."

    parser.add_argument(
        "target",
        help="Research-object identifier or repository.",
    )

    add_path_argument(parser)
    add_resolution_arguments(parser)
    add_output_arguments(parser)

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Inspect a research object or repository."""
    result = inspect_research_object(
        path=args.path,
        target=args.target,
        registry=args.registry,
        snapshot=args.snapshot,
    )

    emit_result(
        result,
        output_format=args.format,
        output=args.output,
    )
    return 0
