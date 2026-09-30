# ============================================================
# src/reactive_research/commands/resolve.py
# ============================================================

"""CLI adapter for research-object resolution."""

import argparse

from reactive_research.commands.common import (
    add_output_arguments,
    add_path_argument,
    add_resolution_arguments,
    emit_result,
)
from reactive_research.resolve import resolve_research


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the resolve command."""
    parser.description = (
        "Resolve research-object references against a registry or graph snapshot."
    )

    parser.add_argument(
        "identifier",
        nargs="?",
        help=(
            "Research-object identifier to resolve. "
            "If omitted, resolve repository references."
        ),
    )
    parser.add_argument(
        "--all",
        dest="resolve_all",
        action="store_true",
        help="Resolve all references declared by the repository.",
    )

    add_path_argument(parser)
    add_resolution_arguments(parser)
    add_output_arguments(parser)

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run research-object resolution."""
    if args.identifier is not None and args.resolve_all:
        print("error: IDENTIFIER and --all cannot be used together.")
        return 2

    result = resolve_research(
        path=args.path,
        identifier=args.identifier,
        resolve_all=args.resolve_all or args.identifier is None,
        registry=args.registry,
        snapshot=args.snapshot,
    )

    emit_result(
        result,
        output_format=args.format,
        output=args.output,
    )

    return 0 if result["resolved"] else 1
