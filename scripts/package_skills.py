#!/usr/bin/env python3
"""Version and archive the shared skills used by every provider package."""

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_docs import (
    SKILL_DOC_SOURCES,
    fetch_and_populate_skill_docs,
    fetch_ducpy_reference,
    fetch_sql_reference,
)
from package_common import (
    copy_directory,
    package_directory_tar,
    package_directory_zip,
    update_frontmatter_version,
    update_json_version,
)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    default_version = json.loads(
        (repo_root / "common" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["version"]

    parser = argparse.ArgumentParser(description="Package the shared Scopture skills for all providers.")
    parser.add_argument("--version", default=default_version, help="Release version (defaults to the source plugin version)")
    parser.add_argument("--skills-dir", default="common/skills", help="Source directory containing skill folders")
    parser.add_argument("--staging-dir", default=".release-staging/skills", help="Versioned shared skills for provider packagers")
    parser.add_argument("--out-dir", default="dist", help="Directory for standalone skill archives")
    parser.add_argument("--in-place", action="store_true", help="Also write release versions into source SKILL.md files")
    parser.add_argument("--fetch-remote-docs", action="store_true", help="Refresh documentation from its configured sources")
    args = parser.parse_args()

    version = args.version.lstrip("v")
    skills_root = (repo_root / args.skills_dir).resolve()
    staging_root = (repo_root / args.staging_dir).resolve()
    out_dir = (repo_root / args.out_dir).resolve()
    if not skills_root.is_dir():
        raise FileNotFoundError(f"Skills directory not found: {skills_root}")

    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    skill_folders = sorted(path for path in skills_root.iterdir() if path.is_dir() and not path.name.startswith("."))
    if not skill_folders:
        raise ValueError(f"No skill folders found in {skills_root}")

    print(f"Staging {len(skill_folders)} shared skill(s) for release {version}...")
    for source in skill_folders:
        skill_name = source.name
        source_skill_file = source / "SKILL.md"
        if not source_skill_file.is_file():
            print(f"Warning: skipping {skill_name}; SKILL.md is missing", file=sys.stderr)
            continue

        staged_folder = staging_root / skill_name
        copy_directory(source, staged_folder)
        staged_skill_file = staged_folder / "SKILL.md"
        updated_content = update_frontmatter_version(source_skill_file.read_text(encoding="utf-8"), version)
        staged_skill_file.write_text(updated_content, encoding="utf-8")
        if args.in_place:
            source_skill_file.write_text(updated_content, encoding="utf-8")

        docs_missing = skill_name in SKILL_DOC_SOURCES and not (staged_folder / "docs").is_dir()
        if args.fetch_remote_docs or docs_missing:
            try:
                fetch_and_populate_skill_docs(
                    skill_name=skill_name,
                    base_url=SKILL_DOC_SOURCES[skill_name],
                    docs_dir=staged_folder / "docs",
                )
            except Exception as error:
                raise RuntimeError(f"Failed to fetch documentation for '{skill_name}': {error}") from error

        if skill_name == "duc" and (args.fetch_remote_docs or not (staged_folder / "docs-ducpy").is_dir()):
            try:
                fetch_ducpy_reference(staged_folder / "docs-ducpy")
                fetch_sql_reference(staged_folder / "docs-sql")
            except Exception as error:
                raise RuntimeError(f"Failed to fetch ducpy/SQL reference for '{skill_name}': {error}") from error

        package_directory_tar(staged_folder, out_dir / f"{skill_name}-{version}.tar.gz", arcname=skill_name)
        package_directory_zip(staged_folder, out_dir / f"{skill_name}-{version}.zip", arcname=skill_name)
        print(f"  Packaged {skill_name}")

    server_json = repo_root / "server.json"
    if server_json.is_file():
        update_json_version(server_json, version)

    print(f"Shared skills staged in {staging_root}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
