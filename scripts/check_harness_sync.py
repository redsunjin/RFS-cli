#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rfs_cli.harness_sync import find_sync_errors, read_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that roadmap next slices and TODO open items stay aligned."
    )
    parser.add_argument(
        "--roadmap",
        type=Path,
        default=Path("docs/roadmap.md"),
        help="Path to the roadmap markdown file.",
    )
    parser.add_argument(
        "--todo",
        type=Path,
        default=Path("docs/todo.md"),
        help="Path to the TODO markdown file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = find_sync_errors(read_text(args.roadmap), read_text(args.todo))

    if errors:
        print("Harness sync check failed.")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Harness sync check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
