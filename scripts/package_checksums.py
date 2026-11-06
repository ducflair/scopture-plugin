#!/usr/bin/env python3
"""Write checksums for all release archives in the output directory."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_common import sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SHA-256 checksums for release archives.")
    parser.add_argument("--out-dir", default="dist", help="Directory containing release archives")
    args = parser.parse_args()
    out_dir = (Path(__file__).resolve().parent.parent / args.out_dir).resolve()
    if not out_dir.is_dir():
        raise FileNotFoundError(f"Release output directory not found: {out_dir}")

    archives = sorted(
        path for path in out_dir.iterdir()
        if path.is_file() and (path.suffix == ".zip" or path.name.endswith(".tar.gz"))
    )
    if not archives:
        raise ValueError(f"No release archives found in {out_dir}")
    checksums = out_dir / "checksums.txt"
    checksums.write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in archives),
        encoding="utf-8",
    )
    print(f"Wrote {checksums} for {len(archives)} archive(s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
