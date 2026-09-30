"""Command-line interface for the Structural Assurability pilot."""

import argparse


def main(argv: list[str] | None = None) -> int:
    """Display the pilot's command-line help."""
    parser = argparse.ArgumentParser(
        prog="se-pilot-structural-assurability",
        description="Structural Assurability applied-research pilot.",
    )
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
