"""Shared helpers used by provider-specific release packagers."""

import hashlib
import json
import os
import re
import shutil
import tarfile
import zipfile
from pathlib import Path

IGNORED_FILE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX"}


def update_frontmatter_version(content: str, version: str) -> str:
    """Inject or update version strictly inside YAML frontmatter metadata."""
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)(.*)", content, re.DOTALL)
    if not match:
        raise ValueError("File does not start with valid '---' YAML frontmatter delimiters.")

    fm, body = match.groups()
    fm = re.sub(r"^version:\s*.*$\r?\n?", "", fm, flags=re.MULTILINE)
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
    return f"---\n{fm.strip()}\n---\n{body.lstrip()}"


def update_json_version(file_path: Path, version: str) -> None:
    """Set a top-level version in a JSON file."""
    data = json.loads(file_path.read_text(encoding="utf-8"))
    data["version"] = version
    file_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def copy_directory(source: Path, destination: Path) -> None:
    """Copy a package tree without desktop metadata files."""
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*IGNORED_FILE_NAMES))


def package_directory_tar(source: Path, target: Path, arcname: str) -> None:
    """Create a gzip archive containing the source under arcname."""
    with tarfile.open(target, "w:gz") as archive:
        archive.add(source, arcname=arcname)


def package_directory_zip(source: Path, target: Path, arcname: str) -> None:
    """Create a ZIP containing the source under arcname."""
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(source):
            for name in files:
                if name in IGNORED_FILE_NAMES:
                    continue
                path = Path(root) / name
                relative = path.relative_to(source)
                archive.write(path, f"{arcname}/{relative.as_posix()}")


def package_root_contents_zip(source: Path, target: Path) -> None:
    """Create a ZIP with package files at the archive root."""
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(source):
            for name in files:
                if name in IGNORED_FILE_NAMES:
                    continue
                path = Path(root) / name
                relative = path.relative_to(source)
                archive.write(path, relative.as_posix())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            digest.update(chunk)
    return digest.hexdigest()
