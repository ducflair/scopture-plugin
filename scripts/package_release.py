#!/usr/bin/env python3
"""Package shared skills and providers implementing --version/--skills-dir/--out-dir."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    source_version = json.loads(
        (repo_root / "common" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["version"]
    parser = argparse.ArgumentParser(description="Build all Scopture release packages.")
    parser.add_argument("--version", default=source_version, help="Release version (defaults to the source plugin version)")
    parser.add_argument("--out-dir", default="dist", help="Directory for release archives")
    parser.add_argument("--staging-dir", default=".release-staging/skills", help="Directory for shared versioned skills")
    args = parser.parse_args()
    version = args.version.lstrip("v")

    commands = [
        [
            sys.executable,
            "scripts/package_skills.py",
            "--version",
            version,
            "--staging-dir",
            args.staging_dir,
            "--out-dir",
            args.out_dir,
        ],
        *[
            [
                sys.executable,
                str(package_script.relative_to(repo_root)),
                "--version",
                version,
                "--skills-dir",
                args.staging_dir,
                "--out-dir",
                args.out_dir,
            ]
            for package_script in sorted((repo_root / "providers").glob("*/package.py"))
        ],
        [sys.executable, "scripts/package_checksums.py", "--out-dir", args.out_dir],
    ]
    for command in commands:
        subprocess.run(command, cwd=repo_root, check=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
