#!/usr/bin/env python3
"""Package the shared Scopture skills with the OpenAI Agent Plugin manifest."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from package_common import copy_directory, package_root_contents_zip, update_json_version


def main() -> int:
    parser = argparse.ArgumentParser(description="Package the Scopture OpenAI plugin.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--skills-dir", default=".release-staging/skills")
    parser.add_argument("--out-dir", default="dist")
    args = parser.parse_args()

    version = args.version.lstrip("v")
    plugin_source = REPO_ROOT / "openai-plugin"
    skills_source = (REPO_ROOT / args.skills_dir).resolve()
    out_dir = (REPO_ROOT / args.out_dir).resolve()
    manifest_source = plugin_source / "plugin.json"
    license_source = REPO_ROOT / "LICENSE"
    if not manifest_source.is_file() or not skills_source.is_dir():
        raise FileNotFoundError("OpenAI plugin manifest or staged shared skills were not found")

    out_dir.mkdir(parents=True, exist_ok=True)
    output_zip = out_dir / "scopture-openai-plugin.zip"
    with tempfile.TemporaryDirectory(prefix="scopture-openai-") as temp_dir:
        package_root = Path(temp_dir) / "package"
        copy_directory(plugin_source, package_root)
        update_json_version(package_root / "plugin.json", version)
        packaged_skills = package_root / "skills"
        if packaged_skills.exists():
            shutil.rmtree(packaged_skills)
        copy_directory(skills_source, packaged_skills)
        if license_source.is_file() and not (package_root / "LICENSE").is_file():
            shutil.copy2(license_source, package_root / "LICENSE")
        package_root_contents_zip(package_root, output_zip)

    print(f"Created {output_zip}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
