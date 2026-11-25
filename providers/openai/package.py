#!/usr/bin/env python3
"""Package the shared Scopture skills with the OpenAI Agent Plugin manifest."""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from package_common import copy_directory, merge_json_objects, package_root_contents_zip


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
    base_manifest_source = REPO_ROOT / "plugin.json"
    overlay_source = plugin_source / "manifest-overlay.json"
    mcp_source = REPO_ROOT / "mcp.json"
    license_source = REPO_ROOT / "LICENSE"
    if not base_manifest_source.is_file() or not overlay_source.is_file() or not mcp_source.is_file():
        raise FileNotFoundError("Shared plugin manifest, OpenAI manifest overlay, or MCP configuration was not found")
    if not skills_source.is_dir():
        raise FileNotFoundError(f"Staged shared skills were not found: {skills_source}")

    base_manifest = json.loads(base_manifest_source.read_text(encoding="utf-8"))
    manifest_overlay = json.loads(overlay_source.read_text(encoding="utf-8"))
    manifest = merge_json_objects(base_manifest, manifest_overlay)
    extensions = manifest.get("extensions", {})
    openai_extension = extensions.get("com.openai", {}) if isinstance(extensions, dict) else {}
    interface = openai_extension.get("interface", {}) if isinstance(openai_extension, dict) else {}
    if isinstance(interface, dict):
        interface.setdefault("longDescription", manifest.get("description", ""))
    manifest["version"] = version

    out_dir.mkdir(parents=True, exist_ok=True)
    output_zip = out_dir / f"openai-scopture-plugin-{version}.zip"
    with tempfile.TemporaryDirectory(prefix="scopture-openai-") as temp_dir:
        package_root = Path(temp_dir) / "package"
        package_root.mkdir()
        for source in plugin_source.iterdir():
            if source.name == "manifest-overlay.json":
                continue
            destination = package_root / source.name
            if source.is_dir():
                copy_directory(source, destination)
            else:
                shutil.copy2(source, destination)
        (package_root / "plugin.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        shutil.copy2(mcp_source, package_root / "mcp.json")
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
