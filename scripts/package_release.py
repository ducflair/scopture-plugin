#!/usr/bin/env python3
"""Package shared skills and providers implementing --version/--skills-dir/--out-dir."""

import argparse
import json
import os
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
    parser.add_argument(
        "--microsoft-oauth-reference-id",
        default=os.environ.get("MICROSOFT_OAUTH_REFERENCE_ID"),
        help="Microsoft OAuth configuration reference ID (or set MICROSOFT_OAUTH_REFERENCE_ID)",
    )
    args = parser.parse_args()
    if not args.microsoft_oauth_reference_id:
        parser.error("--microsoft-oauth-reference-id or MICROSOFT_OAUTH_REFERENCE_ID is required")
    version = args.version.lstrip("v")

    provider_commands = []
    for package_script in sorted((repo_root / "providers").glob("*/package.py")):
        command = [
            sys.executable,
            str(package_script.relative_to(repo_root)),
            "--version",
            version,
            "--skills-dir",
            args.staging_dir,
            "--out-dir",
            args.out_dir,
        ]
        if package_script.parent.name == "microsoft":
            command.extend(["--oauth-reference-id", args.microsoft_oauth_reference_id])
        provider_commands.append(command)

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
        *provider_commands,
        [
            sys.executable,
            "scripts/generate_offer_testing_guide.py",
            "--version",
            version,
            "--out-dir",
            args.out_dir,
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
