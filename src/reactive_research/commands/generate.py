# ============================================================
# src/reactive_research/commands/generate.py
# ============================================================

"""CLI adapter for generating current Reactive Research views."""

import argparse
import json
from pathlib import Path
from typing import Any

from reactive_research.graph import graph_projection, mermaid_graph
from reactive_research.snapshot import observe_workspace


def configure(parser: argparse.ArgumentParser) -> None:
    """Configure the generate command."""
    parser.description = (
        "Generate human-facing Reactive Research views from the current "
        "research workspace."
    )

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Root of the research family to observe.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory for generated Reactive Research views.",
    )

    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Generate current Reactive Research views."""
    root = args.root.resolve()
    output = args.output.resolve()

    current = observe_workspace(root)
    repository_graph = graph_projection(current, view="repositories")

    evolution = mermaid_graph(repository_graph, category="evolution")
    propagation = mermaid_graph(repository_graph, category="propagation")

    output.mkdir(parents=True, exist_ok=True)

    _write_json(output / "observation.json", current)
    _write_json(output / "repository-graph.json", repository_graph)

    _write_text(output / "evolution.mmd", evolution)
    _write_text(output / "propagation.mmd", propagation)

    _write_text(
        output / "index.md",
        _render_index(
            evolution=evolution,
            propagation=propagation,
        ),
    )

    return 0


def _render_index(*, evolution: str, propagation: str) -> str:
    """Render the human-facing generated research view."""
    return f"""# Generated Research Views

These views are generated from the current Reactive Research observation of the
research family.

The Mermaid diagrams and structured JSON are generated from the same observed
research graph.

## Research Evolution

```mermaid
{evolution.rstrip()}
```

Source: [evolution.mmd](evolution.mmd)

## Research Propagation

```mermaid
{propagation.rstrip()}
```

Source: [propagation.mmd](propagation.mmd)

## Structured Data

- [Full observation](observation.json)
- [Repository graph](repository-graph.json)

Regenerate these artifacts from the `reactive-research` repository root:

```powershell
uv run reactive-research generate --root .. --output docs/en/output
```
"""


def _write_json(path: Path, value: Any) -> None:
    """Write a generated JSON artifact."""
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    """Write a generated text artifact."""
    path.write_text(value.rstrip() + "\n", encoding="utf-8")
