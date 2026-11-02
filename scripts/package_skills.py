#!/usr/bin/env python3
"""
Packages individual skill folders and plugin bundles into standalone archives for release.

For each skill folder in skills/:
1. Injects release version into YAML frontmatter metadata (SKILL.md)
2. Packages into:
   - <skill_name>-<version>.tar.gz
   - <skill_name>-<version>.zip

For OpenAI Plugin (./scopture-openai-plugin):
1. Injects release version into plugin.json
2. Bundles the skills from skills/ (with docs and updated versions) into skills/
3. Packages root contents directly into:
   - scopture-openai-plugin.zip (per OpenAI specs: https://developers.openai.com/plugins/build/plugins)

For Claude Plugin (./scopture-claude-plugin):
1. Injects release version into .claude-plugin/plugin.json
2. Bundles the skills from skills/ into skills/
3. Packages into:
   - scopture-claude-plugin.zip (per Claude pre-submission checklist: https://claude.com/docs/plugins/pre-submission-checklist)

Generates SHA-256 checksums in checksums.txt.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

# Ensure local script directory is on sys.path for fetch_docs import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_docs import (
    SKILL_DOC_SOURCES,
    fetch_and_populate_skill_docs,
    fetch_ducpy_reference,
    fetch_sql_reference,
)

IGNORED_FILE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX"}


def update_frontmatter_version(content: str, version: str) -> str:
    """Inject or update version strictly inside metadata block in YAML frontmatter."""
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)(.*)", content, re.DOTALL)
    if not match:
        raise ValueError("File does not start with valid '---' YAML frontmatter delimiters.")

    fm = match.group(1)
    body = match.group(2)

    # 1. Remove top-level 'version' if present
    fm = re.sub(r"^version:\s*.*$\r?\n?", "", fm, flags=re.MULTILINE)

    # 2. Update or append 'metadata.version'
    if re.search(r"^metadata:", fm, re.MULTILINE):
        if re.search(r"(^metadata:.*?\n\s+version:\s*).*$", fm, re.DOTALL | re.MULTILINE):
            fm = re.sub(
                r"(^metadata:.*?\n\s+version:\s*).*$",
                rf'\g<1>"{version}"',
                fm,
                flags=re.MULTILINE,
            )
        else:
            fm = re.sub(r"(^metadata:\s*)$", rf'\1\n  version: "{version}"', fm, flags=re.MULTILINE)
    else:
        fm = fm.rstrip() + f'\nmetadata:\n  version: "{version}"\n'

    # Reconstruct document
    return f"---\n{fm.strip()}\n---\n{body.lstrip()}"


def update_json_version(file_path: Path, version: str) -> None:
    """Update version field in a JSON file preserving formatting."""
    data = json.loads(file_path.read_text(encoding="utf-8"))
    data["version"] = version
    file_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def package_directory_tar(src_dir: Path, target_tar: Path, arcname: str) -> None:
    """Create a gzip tarball containing the directory nested under arcname."""
    with tarfile.open(target_tar, "w:gz") as tar:
        tar.add(src_dir, arcname=arcname)


def package_directory_zip(src_dir: Path, target_zip: Path, arcname: str) -> None:
    """Create a zip archive containing the directory nested under arcname."""
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file in IGNORED_FILE_NAMES:
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(src_dir)
                zf.write(full_path, arcname=f"{arcname}/{rel_path.as_posix()}")


def package_root_contents_zip(src_dir: Path, target_zip: Path) -> None:
    """Create a zip archive containing the files directly at the root of the archive."""
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file in IGNORED_FILE_NAMES:
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(src_dir)
                zf.write(full_path, arcname=rel_path.as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Package skill folders and plugin bundles for release.")
    parser.add_argument(
        "--version",
        required=True,
        help="Release version string (e.g. 0.1.0, without leading 'v')",
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Directory containing skill subfolders (default: skills)",
    )
    parser.add_argument(
        "--openai-plugin-dir",
        default="scopture-openai-plugin",
        help="Directory containing OpenAI plugin (default: scopture-openai-plugin)",
    )
    parser.add_argument(
        "--claude-plugin-dir",
        default="scopture-claude-plugin",
        help="Directory containing Claude plugin (default: scopture-claude-plugin)",
    )
    parser.add_argument(
        "--out-dir",
        default="dist",
        help="Directory to write release archives into (default: dist)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Also write version metadata back to source SKILL.md and manifest files in the repository",
    )
    parser.add_argument(
        "--fetch-remote-docs",
        action="store_true",
        help="Force re-fetching remote documentation instead of using tracked git tree docs",
    )

    args = parser.parse_args()
    version = args.version.lstrip("v")
    repo_root = Path(__file__).resolve().parent.parent
    skills_root = (repo_root / args.skills_dir).resolve()
    openai_root = (repo_root / args.openai_plugin_dir).resolve()
    claude_root = (repo_root / args.claude_plugin_dir).resolve()
    out_dir = (repo_root / args.out_dir).resolve()
    license_file = repo_root / "LICENSE"

    if not skills_root.is_dir():
        print(f"Error: skills directory not found: {skills_root}", file=sys.stderr)
        return 1

    skill_folders = [d for d in skills_root.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if not skill_folders:
        print(f"Error: No skill folders found in {skills_root}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    print(f"Packaging {len(skill_folders)} skill(s) and plugins for release version {version}...")

    with tempfile.TemporaryDirectory() as staging_tmp:
        staging_root = Path(staging_tmp)
        skills_staging = staging_root / "skills"
        skills_staging.mkdir()

        # 1. Process and package each individual skill
        for folder in sorted(skill_folders, key=lambda p: p.name):
            skill_name = folder.name
            skill_md = folder / "SKILL.md"
            if not skill_md.is_file():
                print(f"Warning: Skipping {skill_name}, no SKILL.md found", file=sys.stderr)
                continue

            # Stage the whole skill folder (including docs tracked in git tree)
            staged_folder = skills_staging / skill_name
            shutil.copytree(folder, staged_folder)

            # Update SKILL.md with version metadata
            content = skill_md.read_text(encoding="utf-8")
            updated_content = update_frontmatter_version(content, version)
            (staged_folder / "SKILL.md").write_text(updated_content, encoding="utf-8")

            if args.in_place:
                skill_md.write_text(updated_content, encoding="utf-8")

            # If force fetch requested or docs folder missing, fetch live
            docs_missing = (skill_name in SKILL_DOC_SOURCES) and not (staged_folder / "docs").is_dir()
            if args.fetch_remote_docs or docs_missing:
                doc_url = SKILL_DOC_SOURCES[skill_name]
                try:
                    fetch_and_populate_skill_docs(
                        skill_name=skill_name,
                        base_url=doc_url,
                        docs_dir=staged_folder / "docs",
                    )
                except Exception as e:
                    print(
                        f"\n[CRITICAL ERROR] Failed to fetch documentation for skill '{skill_name}': {e}",
                        file=sys.stderr,
                    )
                    return 1

            if skill_name == "duc" and (args.fetch_remote_docs or not (staged_folder / "docs-ducpy").is_dir()):
                try:
                    fetch_ducpy_reference(staged_folder / "docs-ducpy")
                    fetch_sql_reference(staged_folder / "docs-sql")
                except Exception as e:
                    print(
                        f"\n[CRITICAL ERROR] Failed to fetch ducpy/sql reference for skill 'duc': {e}",
                        file=sys.stderr,
                    )
                    return 1

            # Archives for standalone skill
            tar_versioned = out_dir / f"{skill_name}-{version}.tar.gz"
            zip_versioned = out_dir / f"{skill_name}-{version}.zip"

            package_directory_tar(staged_folder, tar_versioned, arcname=skill_name)
            package_directory_zip(staged_folder, zip_versioned, arcname=skill_name)

            created_files.extend([tar_versioned, zip_versioned])
            print(f"  ✓ skill package: {tar_versioned.name}, {zip_versioned.name}")

        # 2. Package OpenAI Plugin (scopture-openai-plugin.zip)
        if openai_root.is_dir():
            openai_staging = staging_root / "openai-plugin"
            shutil.copytree(openai_root, openai_staging)

            # Update plugin.json version
            openai_manifest = openai_staging / "plugin.json"
            if openai_manifest.is_file():
                update_json_version(openai_manifest, version)
                if args.in_place and (openai_root / "plugin.json").is_file():
                    update_json_version(openai_root / "plugin.json", version)

            # Copy staged skills into plugin's skills/ directory
            plugin_skills_dir = openai_staging / "skills"
            if plugin_skills_dir.exists():
                shutil.rmtree(plugin_skills_dir)
            shutil.copytree(skills_staging, plugin_skills_dir)

            # Ensure LICENSE is present
            if license_file.is_file() and not (openai_staging / "LICENSE").is_file():
                shutil.copy2(license_file, openai_staging / "LICENSE")

            openai_zip = out_dir / "scopture-openai-plugin.zip"
            package_root_contents_zip(openai_staging, openai_zip)
            created_files.append(openai_zip)
            print(f"  ✓ openai plugin: {openai_zip.name}")

        # 3. Package Claude Plugin (scopture-claude-plugin.zip)
        if claude_root.is_dir():
            claude_staging = staging_root / "claude-plugin"
            shutil.copytree(claude_root, claude_staging)

            # Update .claude-plugin/plugin.json version
            claude_manifest = claude_staging / ".claude-plugin" / "plugin.json"
            if claude_manifest.is_file():
                update_json_version(claude_manifest, version)
                if args.in_place and (claude_root / ".claude-plugin" / "plugin.json").is_file():
                    update_json_version(claude_root / ".claude-plugin" / "plugin.json", version)

            # Copy staged skills into plugin's skills/ directory
            claude_skills_dir = claude_staging / "skills"
            if claude_skills_dir.exists():
                shutil.rmtree(claude_skills_dir)
            shutil.copytree(skills_staging, claude_skills_dir)

            # Ensure LICENSE is present
            if license_file.is_file() and not (claude_staging / "LICENSE").is_file():
                shutil.copy2(license_file, claude_staging / "LICENSE")

            claude_zip = out_dir / "scopture-claude-plugin.zip"
            package_root_contents_zip(claude_staging, claude_zip)
            created_files.append(claude_zip)
            print(f"  ✓ claude plugin: {claude_zip.name}")

        # 4. Update server.json version if present
        server_json = repo_root / "server.json"
        if server_json.is_file():
            update_json_version(server_json, version)

    # Write checksums for all created archives
    checksums_file = out_dir / "checksums.txt"
    checksum_lines = []
    for f in created_files:
        digest = sha256_file(f)
        checksum_lines.append(f"{digest}  {f.name}\n")

    checksums_file.write_text("".join(checksum_lines), encoding="utf-8")
    created_files.append(checksums_file)

    print(f"\nAll packages created in {out_dir}:")
    for f in created_files:
        print(f"  - {f.name} ({f.stat().st_size:,} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
