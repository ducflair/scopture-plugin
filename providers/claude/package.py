#!/usr/bin/env python3
"""Package the shared Scopture skills and MCP config as a Claude plugin."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from package_common import copy_directory, package_root_contents_zip, update_json_version


def main() -> int:
    parser = argparse.ArgumentParser(description="Package the Scopture Claude plugin.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--skills-dir", default=".release-staging/skills")
    parser.add_argument("--out-dir", default="dist")
    args = parser.parse_args()

    version = args.version.lstrip("v")
    plugin_source = REPO_ROOT / "common"
    skills_source = (REPO_ROOT / args.skills_dir).resolve()
    out_dir = (REPO_ROOT / args.out_dir).resolve()
    source_manifest = plugin_source / ".claude-plugin" / "plugin.json"
    if not source_manifest.is_file() or not skills_source.is_dir():
        raise FileNotFoundError("Claude plugin manifest or staged shared skills were not found")

    out_dir.mkdir(parents=True, exist_ok=True)
    output_zip = out_dir / f"claude-scopture-plugin-{version}.zip"
    with tempfile.TemporaryDirectory(prefix="scopture-claude-") as temp_dir:
        package_root = Path(temp_dir) / "package"
        package_root.mkdir()

        copy_directory(plugin_source / ".claude-plugin", package_root / ".claude-plugin")
        update_json_version(package_root / ".claude-plugin" / "plugin.json", version)
        for file_name in (".mcp.json", "README.md"):
            source = plugin_source / file_name
            if source.is_file():
                shutil.copy2(source, package_root / file_name)
        license_source = REPO_ROOT / "LICENSE"
        if license_source.is_file():
            shutil.copy2(license_source, package_root / "LICENSE")
        copy_directory(skills_source, package_root / "skills")
        package_root_contents_zip(package_root, output_zip)

    print(f"Created {output_zip}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
