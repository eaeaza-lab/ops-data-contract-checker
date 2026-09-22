"""Command-line entry point for the checker skeleton."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ops-contract-checker",
        description="Validate synthetic CSV and JSON exports against versioned data contracts.",
    )
    parser.add_argument(
        "--version", action="version", version="ops-contract-checker 0.1.0"
    )
    return parser


def main() -> int:
    build_parser().parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
