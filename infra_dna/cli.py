"""Command-line entrypoint for YAML parsing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .consumers import PrintToConsole
from .parser import GraphParser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate infrastructure graph YAML.")
    parser.add_argument("arch_path", nargs="?", default="arch", help="Path to the arch directory")
    parser.add_argument(
        "--print-records",
        action="store_true",
        help="Print validated entities and relations after a successful parse",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    consumers = [PrintToConsole()] if args.print_records else []
    parser = GraphParser(Path(args.arch_path), consumers=consumers)
    result = parser.parse()

    if result.errors:
        for error in result.errors:
            print(error.format(), file=sys.stderr)
        return 1

    print(f"Validated {len(result.entities)} entities and {len(result.relations)} relations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
