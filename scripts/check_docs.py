#!/usr/bin/env python3
"""
Validates that documentation tracked in the git tree matches live remote docs.

Fetches the latest documentation from remote sources into a temporary directory,
computes deterministic SHA-256 hashes of tracked vs. fetched folders, and verifies
they are 100% in sync.

Tracked documentation targets:
- skills/scopture/docs   <-> https://site.scopture.com
- skills/duc/docs        <-> https://duc.ducflair.com
- skills/duc/docs-ducpy  <-> https://ducflair.github.io/duc/reference/python/
- skills/duc/docs-sql    <-> https://ducflair.github.io/duc/reference/sql/
"""

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

# Ensure local script directory is on sys.path for fetch_docs import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_docs import (
    SKILL_DOC_SOURCES,
    fetch_and_populate_skill_docs,
    fetch_ducpy_reference,
    fetch_sql_reference,
)

IGNORED_FILE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def hash_directory(dir_path: Path) -> str:
    """Compute a deterministic SHA-256 hash across all files in a directory."""
    h = hashlib.sha256()
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            if file_path.name in IGNORED_FILE_NAMES:
                continue
            rel_path = file_path.relative_to(dir_path).as_posix()
            h.update(rel_path.encode("utf-8"))
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
    return h.hexdigest()


def compare_directories(local_dir: Path, remote_dir: Path) -> dict:
    """Compare two directories and return added, removed, and modified files."""
    local_files = {
        p.relative_to(local_dir).as_posix(): p
        for p in local_dir.rglob("*")
        if p.is_file() and p.name not in IGNORED_FILE_NAMES
    }
    remote_files = {
        p.relative_to(remote_dir).as_posix(): p
        for p in remote_dir.rglob("*")
        if p.is_file() and p.name not in IGNORED_FILE_NAMES
    }

    only_local = sorted(set(local_files.keys()) - set(remote_files.keys()))
    only_remote = sorted(set(remote_files.keys()) - set(local_files.keys()))
    modified = []

    for path_str in sorted(set(local_files.keys()) & set(remote_files.keys())):
        if local_files[path_str].read_bytes() != remote_files[path_str].read_bytes():
            modified.append(path_str)

    return {
        "only_local": only_local,
        "only_remote": only_remote,
        "modified": modified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that git-tracked docs folders match live remote documentation."
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Root skills directory (default: skills)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    skills_root = (repo_root / args.skills_dir).resolve()

    if not skills_root.is_dir():
        print(f"Error: skills directory not found: {skills_root}", file=sys.stderr)
        return 1

    targets = [
        {
            "name": "scopture docs",
            "local_dir": skills_root / "scopture" / "docs",
            "fetcher": lambda dest: fetch_and_populate_skill_docs(
                "scopture", SKILL_DOC_SOURCES["scopture"], dest
            ),
        },
        {
            "name": "duc docs",
            "local_dir": skills_root / "duc" / "docs",
            "fetcher": lambda dest: fetch_and_populate_skill_docs(
                "duc", SKILL_DOC_SOURCES["duc"], dest
            ),
        },
        {
            "name": "duc ducpy reference",
            "local_dir": skills_root / "duc" / "docs-ducpy",
            "fetcher": lambda dest: fetch_ducpy_reference(dest),
        },
        {
            "name": "duc sql reference",
            "local_dir": skills_root / "duc" / "docs-sql",
            "fetcher": lambda dest: fetch_sql_reference(dest),
        },
    ]

    print("Checking git-tracked docs against live remote documentation...\n")

    has_errors = False

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)

        for idx, target in enumerate(targets):
            name = target["name"]
            local_dir = target["local_dir"]
            rel_display = local_dir.relative_to(repo_root).as_posix()

            if not local_dir.is_dir():
                print(f"  ✗ {rel_display}: Local directory does not exist!", file=sys.stderr)
                has_errors = True
                continue

            fetched_dest = tmp_root / f"target_{idx}"
            try:
                target["fetcher"](fetched_dest)
            except Exception as e:
                print(f"  ✗ {rel_display}: Failed fetching remote documentation: {e}", file=sys.stderr)
                has_errors = True
                continue

            local_hash = hash_directory(local_dir)
            fetched_hash = hash_directory(fetched_dest)

            if local_hash == fetched_hash:
                print(f"  ✓ {rel_display} (SHA: {local_hash[:12]}...): UP TO DATE")
            else:
                has_errors = True
                diff = compare_directories(local_dir, fetched_dest)
                print(f"  ✗ {rel_display}: OUT OF DATE (git tree != remote)", file=sys.stderr)
                print(f"      local hash:   {local_hash}", file=sys.stderr)
                print(f"      remote hash:  {fetched_hash}", file=sys.stderr)
                if diff["only_local"]:
                    print(f"      Stale in git (deleted upstream): {diff['only_local']}", file=sys.stderr)
                if diff["only_remote"]:
                    print(f"      Missing from git (new upstream): {diff['only_remote']}", file=sys.stderr)
                if diff["modified"]:
                    print(f"      Modified files: {diff['modified']}", file=sys.stderr)

    print()
    if has_errors:
        print(
            "Documentation check FAILED!\n"
            "Tracked docs in the git tree do not match the remote documentation.\n"
            "Please update the docs by running:\n"
            "  npm run remote-docs\n"
            "and stage/commit the changes.",
            file=sys.stderr,
        )
        return 1

    print("All tracked documentation folders match remote documentation perfectly!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
