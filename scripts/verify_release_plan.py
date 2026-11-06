#!/usr/bin/env python3
"""Prevent publishing packages built for a different semantic-release version."""

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify semantic-release matches the package plan.")
    parser.add_argument("--version", required=True, help="Version calculated by semantic-release")
    parser.add_argument("--plan-file", default=".release-staging/release-version", help="File written by the release planner")
    args = parser.parse_args()
    plan_path = (Path(__file__).resolve().parent.parent / args.plan_file).resolve()
    planned = plan_path.read_text(encoding="utf-8").strip()
    if planned != args.version:
        raise ValueError(f"Release plan is {planned}, but semantic-release selected {args.version}")
    print(f"Verified release package version {planned}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
