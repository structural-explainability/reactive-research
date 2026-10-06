"""Tests for command-line interface."""

import pytest

from reactive_research.cli import main


def test_cli_displays_help_by_default(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invoking the CLI without arguments displays help."""
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "Extract, validate, resolve, graph, impact, snapshot, generate," in output
    assert "Reactive Research views" in output


def test_cli_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The --help argument exits successfully."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert "usage:" in capsys.readouterr().out


def test_non_graph_commands_do_not_offer_mermaid() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["extract", "--format", "mermaid"])
    assert exc_info.value.code == 2
