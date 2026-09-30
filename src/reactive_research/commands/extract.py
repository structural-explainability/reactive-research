# ============================================================
# src/reactive_research/commands/extract.py
# ============================================================

"""CLI adapter for research-object extraction."""

import argparse

from reactive_research.commands.common import (
    add_output_arguments,
    add_path_argument,
    emit_result,
)
from reactive_research.extract import extract_research


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the extract command."""
    parser.description = (
        "Extract Reactive Research declarations from authoritative source files."
    )

    add_path_argument(parser)
    add_output_arguments(parser)

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check extracted declarations without writing generated artifacts.",
    )

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run research-object extraction."""
    result = extract_research(
        path=args.path,
        check=args.check,
    )

    emit_result(
        result,
        output_format=args.format,
        output=args.output,
    )
    return 0
