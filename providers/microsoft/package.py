#!/usr/bin/env python3
"""Build the Microsoft 365 Copilot Cowork app package for Partner Center."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from package_common import IGNORED_FILE_NAMES, copy_directory, package_root_contents_zip, update_json_version

MAX_COMPANION_FILES = 20
MAX_COMPANION_FILE_BYTES = 5 * 1024 * 1024
MAX_COMPANION_TOTAL_BYTES = 10 * 1024 * 1024
MAX_SKILLS = 20


def bundle_reference_tree(
    skill_root: Path,
    source_root: Path,
    destination: Path,
    exclude_top_level: set[str] | None = None,
) -> None:
    """Flatten documentation into a searchable file labelled with original source paths."""
    files = sorted(
        path for path in source_root.rglob("*")
        if path.is_file()
        and not (exclude_top_level and path.relative_to(source_root).parts[0] in exclude_top_level)
    )
    if not files:
        raise ValueError(f"No reference files found under {source_root}")

    sections = []
    for source in files:
        if source.name in IGNORED_FILE_NAMES:
            continue
        if source.suffix.lower() not in {".md", ".txt"}:
            raise ValueError(f"Unsupported DUC reference file type: {source}")
        relative = source.relative_to(skill_root).as_posix()
        sections.append(f"## Source: `{relative}`\n\n{source.read_text(encoding='utf-8').strip()}\n")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n\n---\n\n".join(sections), encoding="utf-8")


def adapt_duc_skill(skill_root: Path) -> None:
    """Retain the DUC documentation while fitting Cowork's companion-file limit."""
    reference_dir = skill_root / "references"
    bundle_reference_tree(
        skill_root,
        skill_root / "docs-ducpy" / "autoapi",
        reference_dir / "ducpy-api.md",
    )

    guides_dir = skill_root / "docs-ducpy"
    if any(path.is_file() for path in guides_dir.iterdir()):
        bundle_reference_tree(
            skill_root,
            guides_dir,
            reference_dir / "ducpy-guides-and-examples.md",
            exclude_top_level={"autoapi"},
        )
    bundle_reference_tree(skill_root, skill_root / "docs", reference_dir / "duc-concepts-and-guides.md")
    bundle_reference_tree(skill_root, skill_root / "docs-sql", reference_dir / "sqlite-schema.md")

    skill_file = skill_root / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")
    replacements = {
        "bundled directly inside the relative `./docs/`, `./docs-ducpy/`, and `./docs-sql/` folders of this skill.":
            "bundled as on-demand reference files under `./references/`. Each source document begins with a `## Source:` path heading.",
        "**Bundled `ducpy` API reference** (`./docs-ducpy/llms.txt`, `./docs-ducpy/*.md`)":
            "**Bundled `ducpy` API reference** (`./references/ducpy-api.md`, `./references/ducpy-guides-and-examples.md`)",
        "**Bundled SQLite schema reference** (`./docs-sql/schema.md`, `./docs-sql/llms.txt`)":
            "**Bundled SQLite schema reference** (`./references/sqlite-schema.md`)",
        "**Bundled DUC concept guides** (`./docs/llms.txt`, `./docs/*.md`)":
            "**Bundled DUC concept guides** (`./references/duc-concepts-and-guides.md`)",
        "**Existing worked examples** (`./docs-ducpy/examples.md`)":
            "**Existing worked examples** (`./references/ducpy-guides-and-examples.md`)",
    }
    for original, replacement in replacements.items():
        if original not in content:
            raise ValueError(f"Expected DUC skill text was not found for Microsoft packaging: {original}")
        content = content.replace(original, replacement)
    skill_file.write_text(content, encoding="utf-8")

    for directory in ("docs-ducpy", "docs", "docs-sql"):
        shutil.rmtree(skill_root / directory)


def create_icons(source_icon: Path, package_root: Path) -> None:
    """Generate Cowork's 192px color icon and 32px single-color outline icon with Sharp."""
    subprocess.run(
        [
            "node",
            str(REPO_ROOT / "providers" / "microsoft" / "create_icons.mjs"),
            str(source_icon),
            str(package_root),
        ],
        cwd=REPO_ROOT,
        check=True,
    )


def validate_skills(skills_root: Path) -> list[dict[str, str]]:
    folders = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if not folders:
        raise ValueError(f"No skill folders found in {skills_root}")
    if len(folders) > MAX_SKILLS:
        raise ValueError(f"Microsoft allows at most {MAX_SKILLS} skills per package")

    entries = []
    for folder in folders:
        skill_file = folder / "SKILL.md"
        if not skill_file.is_file():
            raise ValueError(f"Skill folder is missing SKILL.md: {folder}")
        files = [path for path in folder.rglob("*") if path.is_file()]
        companions = [path for path in files if path != skill_file]
        if len(companions) > MAX_COMPANION_FILES:
            raise ValueError(f"{folder.name} has more than {MAX_COMPANION_FILES} companion files")

        total_bytes = 0
        for companion in companions:
            relative_parts = companion.relative_to(folder).parts
            if any(part.startswith(".") or part in IGNORED_FILE_NAMES for part in relative_parts):
                raise ValueError(f"Hidden or system file is not allowed in a skill: {companion}")
            size = companion.stat().st_size
            if size > MAX_COMPANION_FILE_BYTES:
                raise ValueError(f"Skill companion exceeds 5 MB: {companion}")
            total_bytes += size
        if total_bytes > MAX_COMPANION_TOTAL_BYTES:
            raise ValueError(f"Skill {folder.name} exceeds 10 MB of companion files")
        entries.append({"folder": f"./skills/{folder.name}"})
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Package Scopture skills and MCP for Copilot Cowork.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--plugin-dir", default="microsoft-plugin")
    parser.add_argument("--skills-dir", default=".release-staging/skills")
    parser.add_argument("--out-dir", default="dist")
    args = parser.parse_args()

    version = args.version.lstrip("v")
    plugin_source = (REPO_ROOT / args.plugin_dir).resolve()
    skills_source = (REPO_ROOT / args.skills_dir).resolve()
    out_dir = (REPO_ROOT / args.out_dir).resolve()
    manifest_source = plugin_source / "manifest.json"
    if not manifest_source.is_file():
        raise FileNotFoundError(f"Microsoft plugin manifest not found: {manifest_source}")
    if not skills_source.is_dir():
        raise FileNotFoundError(f"Staged shared skills not found: {skills_source}")

    mcp_config = json.loads((REPO_ROOT / "common" / ".mcp.json").read_text(encoding="utf-8"))
    mcp_servers = mcp_config.get("mcpServers", {})
    if len(mcp_servers) != 1:
        raise ValueError("Expected exactly one remote MCP server in common/.mcp.json")
    mcp_server = next(iter(mcp_servers.values()))
    mcp_url = mcp_server.get("url", "")
    if mcp_server.get("type") != "http" or not mcp_url.startswith("https://"):
        raise ValueError("The Microsoft connector requires an HTTPS remote MCP server")

    out_dir.mkdir(parents=True, exist_ok=True)
    output_zip = out_dir / f"microsoft-scopture-plugin-{version}.zip"

    with tempfile.TemporaryDirectory(prefix="scopture-cowork-") as temp_dir:
        package_root = Path(temp_dir) / "package"
        copy_directory(plugin_source, package_root)
        packaged_skills = package_root / "skills"
        if packaged_skills.exists():
            shutil.rmtree(packaged_skills)
        shutil.copytree(skills_source, packaged_skills, ignore=shutil.ignore_patterns(*IGNORED_FILE_NAMES))

        duc_skill = packaged_skills / "duc"
        if duc_skill.is_dir():
            adapt_duc_skill(duc_skill)
        skill_entries = validate_skills(packaged_skills)
        create_icons(REPO_ROOT / "common" / ".claude-plugin" / "icon.png", package_root)

        manifest_path = package_root / "manifest.json"
        update_json_version(manifest_path, version)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["agentSkills"] = skill_entries
        # Cowork handles Dynamic Client Registration for this endpoint; omit authorization intentionally.
        manifest["agentConnectors"][0]["toolSource"]["remoteMcpServer"]["mcpServerUrl"] = mcp_url
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        package_root_contents_zip(package_root, output_zip)

    print(f"Created {output_zip} ({output_zip.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
