# ============================================================
# src/reactive_research/commands/common.py
# ============================================================

"""Shared command-line helpers."""

import argparse
import json
from pathlib import Path
from typing import Any


def add_path_argument(parser: argparse.ArgumentParser) -> None:
    """Add a repository or workspace path argument."""
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("."),
        help="Repository or workspace path. Default: current directory.",
    )


def add_resolution_arguments(parser: argparse.ArgumentParser) -> None:
    """Add registry and snapshot resolution arguments."""
    parser.add_argument(
        "--registry",
        help="Registry location or identifier.",
    )
    parser.add_argument(
        "--snapshot",
        help="Registry snapshot to use for resolution.",
    )


def add_output_arguments(
    parser: argparse.ArgumentParser, *, graph_formats: bool = False
) -> None:
    """Add common output arguments."""
    parser.add_argument(
        "--format",
        choices=("text", "json", "mermaid") if graph_formats else ("text", "json"),
        default="text",
        help="Output format. Default: text.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write output to this file instead of stdout.",
    )


def emit_result(
    result: dict[str, Any],
    *,
    output_format: str,
    output: Path | None,
) -> None:
    """Render and emit one command result."""
    if output_format == "mermaid":
        from reactive_research.graph import mermaid_graph

        rendered = mermaid_graph(
            result,
            category=result.get(
                "category",
                "impact" if result.get("command") == "impact" else "propagation",
            ),
        )
    elif output_format == "json":
        rendered = json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    else:
        if result.get("command") == "impact":
            from reactive_research.report import obligation_report

            rendered = obligation_report(result)
        else:
            rendered = _render_text(result)

    if output is None:
        print(rendered)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        rendered + "\n",
        encoding="utf-8",
    )


def _render_text(result: dict[str, Any]) -> str:
    """Render a simple human-readable command result."""
    lines: list[str] = []

    for key, value in result.items():
        if isinstance(value, (dict, list, tuple)):
            rendered_value = json.dumps(
                value,
                indent=2,
                sort_keys=True,
            )
            lines.append(f"{key}:")
            lines.append(rendered_value)
        else:
            lines.append(f"{key}: {value}")

    return "\n".join(lines)
