"""Command-line entrypoint for YAML parsing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .consumers import PrintToConsole
from .config import AppConfigLoader, ConfigError
from .neo4j_service import Neo4jService
from .neo4j_visitor import Neo4jVisitorHandler
from .parser import GraphParser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and load infrastructure graph YAML.")
    parser.add_argument("arch_path", nargs="?", default="arch", help="Path to the arch directory")
    parser.add_argument(
        "--print-records",
        action="store_true",
        help="Print validated entities and relations after a successful parse",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate YAML only and skip Neo4j loading",
    )
    parser.add_argument(
        "--config",
        help="Path to the runtime configuration file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip interactive confirmation before clearing and reloading Neo4j",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    parser = GraphParser(Path(args.arch_path))
    result = parser.parse(dispatch=False)

    if result.errors:
        for error in result.errors:
            print(error.format(), file=sys.stderr)
        return 1

    if args.validate_only:
        if args.print_records:
            parser.dispatch(result, consumers=[PrintToConsole()])
        print(
            f"Validated {len(result.entities)} entities and {len(result.relations)} relations."
        )
        print("Neo4j load skipped (--validate-only).")
        return 0

    try:
        config = AppConfigLoader(args.config).load()
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not _confirm_destructive_load(force=args.force):
        return 1

    consumers = []
    if args.print_records:
        consumers.append(PrintToConsole())

    neo4j_service = Neo4jService(
        uri=config.neo4j.uri,
        username=config.neo4j.username,
        password=config.neo4j.password,
        database=config.neo4j.database,
    )
    consumers.append(Neo4jVisitorHandler(neo4j_service))

    try:
        parser.dispatch(result, consumers=consumers)
    except Exception as exc:
        print(f"Neo4j load failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(result.entities)} entities and {len(result.relations)} relations."
    )
    database_label = config.neo4j.database or "default"
    print(
        f"Loaded graph into Neo4j database '{database_label}' at {config.neo4j.uri}."
    )
    return 0


def _confirm_destructive_load(force: bool) -> bool:
    if force:
        return True

    if not sys.stdin.isatty():
        print(
            "Refusing to clear and reload Neo4j without confirmation in a non-interactive environment.\n"
            "Re-run with --force to continue, or use --validate-only.",
            file=sys.stderr,
        )
        return False

    print(
        "This run will remove all nodes and relationships from the configured Neo4j database\n"
        "and rebuild it from the infra-dna YAML.\n\n"
        "Do not continue if this database contains data unrelated to infra-dna.\n"
    )
    response = input("Continue? [y/N] ").strip().lower()
    if response not in {"y", "yes"}:
        print("Neo4j load cancelled by user.", file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
