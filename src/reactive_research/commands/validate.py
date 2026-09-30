# ============================================================
# src/reactive_research/commands/validate.py
# ============================================================

"""CLI adapter for Reactive Research validation."""

import argparse

from reactive_research.commands.common import (
    add_output_arguments,
    add_path_argument,
    emit_result,
)
from reactive_research.validate import validate_research


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the validate command."""
    parser.description = (
        "Validate repository-local Reactive Research declarations and contracts."
    )

    add_path_argument(parser)
    add_output_arguments(parser)

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat applicable warnings as validation failures.",
    )

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run Reactive Research validation."""
    result = validate_research(
        path=args.path,
        strict=args.strict,
    )

    emit_result(
        result,
        output_format=args.format,
        output=args.output,
    )

    return 0 if result["valid"] else 1
