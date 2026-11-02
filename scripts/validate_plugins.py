#!/usr/bin/env python3
"""
Validates OpenAI and Claude agent plugin packages against official schemas
and submission guidelines:
- OpenAI Plugin: https://developers.openai.com/plugins/build/plugins
- Claude Plugin: https://claude.com/docs/plugins/pre-submission-checklist
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RESERVED_NAMES = {"claude", "anthropic", "official", "plugin", "mcp", "test"}
PLUGIN_NAME_REGEX = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
FORBIDDEN_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX"}
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MiB


def count_non_code_words(markdown_text: str) -> int:
    """Count non-code words in markdown (excluding fenced code blocks and inline code)."""
    # Remove fenced code blocks
    cleaned = re.sub(r"```[\s\S]*?```", " ", markdown_text)
    # Remove inline code
    cleaned = re.sub(r"`[^`]+`", " ", cleaned)
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    words = re.findall(r"\b[A-Za-z0-9_-]+\b", cleaned)
    return len(words)


def validate_openai_plugin(plugin_dir: Path) -> tuple[list[str], list[str]]:
    """
    Validate OpenAI plugin against Agent Plugins 1.0.0 and com.openai extension rules.
    OpenAI validates plugin bundles during portal upload / submission; locally,
    the package is validated against agent-plugins schema and com.openai rules.
    """
    errors = []
    notes = []
    if not plugin_dir.is_dir():
        return [f"OpenAI plugin directory not found: {plugin_dir}"], notes

    # 1. Manifest plugin.json
    manifest_path = plugin_dir / "plugin.json"
    if not manifest_path.is_file():
        errors.append("Missing required 'plugin.json' at root of OpenAI plugin directory.")
        return errors, notes

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"plugin.json is not valid JSON: {e}"], notes

    # Schema check
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        errors.append("plugin.json $schema must be 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'")

    # Name check
    name = manifest.get("name")
    if not name:
        errors.append("plugin.json missing required 'name' field.")
    elif len(name) > 64:
        errors.append(f"plugin.json 'name' exceeds 64 characters ({len(name)} chars).")
    elif not PLUGIN_NAME_REGEX.match(name):
        errors.append(f"plugin.json 'name' ('{name}') does not match expected kebab-case pattern.")

    # Version, description, license
    if not manifest.get("version"):
        errors.append("plugin.json missing 'version' field.")
    if not manifest.get("description"):
        errors.append("plugin.json missing 'description' field.")
    if not manifest.get("license") and not (plugin_dir / "LICENSE").is_file():
        errors.append("plugin.json missing 'license' field and no LICENSE file found in plugin directory.")

    # Author
    author = manifest.get("author")
    if not isinstance(author, dict) or not author.get("name"):
        errors.append("plugin.json missing author object with 'name' field.")

    # com.openai extensions
    ext = manifest.get("extensions", {}).get("com.openai", {})
    if not ext:
        errors.append("plugin.json missing 'extensions.com.openai' object.")
    else:
        interface = ext.get("interface", {})
        if not interface:
            errors.append("extensions.com.openai missing 'interface' object.")
        else:
            for req in ["displayName", "shortDescription", "longDescription", "developerName", "category"]:
                if not interface.get(req):
                    errors.append(f"extensions.com.openai.interface missing '{req}'")

    # 2. mcp.json
    mcp_path = plugin_dir / "mcp.json"
    if not mcp_path.is_file():
        errors.append("Missing required 'mcp.json' at root of OpenAI plugin directory.")
    else:
        try:
            mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
            if mcp.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json":
                errors.append("mcp.json $schema must be 'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json'")
            servers = mcp.get("mcpServers", {})
            if not servers:
                errors.append("mcp.json missing 'mcpServers' object.")
            for sname, scfg in servers.items():
                stype = scfg.get("type")
                if stype not in ("stdio", "streamable-http", "sse"):
                    errors.append(f"MCP server '{sname}' has invalid type '{stype}'")
        except Exception as e:
            errors.append(f"mcp.json is not valid JSON: {e}")

    # 3. Documentation & License
    if not (plugin_dir / "README.md").is_file():
        errors.append("OpenAI plugin missing README.md")
    if not (plugin_dir / "LICENSE").is_file() and not manifest.get("license"):
        errors.append("OpenAI plugin missing LICENSE file and no 'license' set in plugin.json")

    return errors, notes


def find_claude_cli() -> str | None:
    """Find the path to the official Anthropic Claude CLI executable (v2+ with plugin support)."""
    candidates = [
        str(Path.home() / ".local" / "bin" / "claude"),
        "/usr/local/bin/claude",
        "/opt/homebrew/bin/claude",
    ]
    which_claude = shutil.which("claude")
    if which_claude and which_claude not in candidates:
        candidates.append(which_claude)

    for c in candidates:
        p = Path(c)
        if p.is_file() and os.access(p, os.X_OK):
            try:
                res = subprocess.run([str(p), "plugin", "--help"], capture_output=True, text=True, timeout=5)
                if res.returncode == 0 and "validate" in res.stdout:
                    return str(p)
            except Exception:
                continue
    return None


def validate_claude_plugin(plugin_dir: Path) -> tuple[list[str], list[str]]:
    """
    Validate Claude plugin against Anthropic pre-submission checklist,
    including running Anthropic's official 'claude plugin validate --strict' CLI.
    """
    errors = []
    notes = []
    if not plugin_dir.is_dir():
        return [f"Claude plugin directory not found: {plugin_dir}"], notes

    # 1. Manifest .claude-plugin/plugin.json
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not manifest_path.is_file():
        errors.append("Missing required '.claude-plugin/plugin.json' manifest.")
        return errors, notes

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f".claude-plugin/plugin.json is not valid JSON: {e}"], notes

    # Name check
    name = manifest.get("name")
    if not name:
        errors.append(".claude-plugin/plugin.json missing 'name' field.")
    else:
        if len(name) > 64:
            errors.append(f"Plugin name exceeds 64 characters ({len(name)} chars).")
        if not PLUGIN_NAME_REGEX.match(name):
            errors.append(f"Plugin name '{name}' must use lowercase letters, numbers, and hyphens only.")
        if name in RESERVED_NAMES:
            errors.append(f"Plugin name '{name}' is a reserved term (claude, anthropic, official, etc.).")

    # Author
    author = manifest.get("author")
    if not isinstance(author, dict) or not author.get("name"):
        errors.append(".claude-plugin/plugin.json missing author object with 'name' field.")

    # Description and version
    if not manifest.get("description"):
        errors.append(".claude-plugin/plugin.json missing 'description' field.")
    if not manifest.get("version"):
        errors.append(".claude-plugin/plugin.json missing 'version' field.")

    # 2. MCP servers (.mcp.json)
    mcp_path = plugin_dir / ".mcp.json"
    if mcp_path.is_file():
        try:
            mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
            servers = mcp.get("mcpServers", {})
            for sname, scfg in servers.items():
                stype = scfg.get("type")
                if stype not in ("http", "sse", "ws", "stdio"):
                    errors.append(f"MCP server '{sname}' in .mcp.json has invalid type '{stype}' (expected http/sse/ws).")
                surl = scfg.get("url")
                if surl and not (surl.startswith("https://") or surl.startswith("wss://")):
                    errors.append(f"MCP server '{sname}' URL must use https:// or wss://: '{surl}'")
        except Exception as e:
            errors.append(f".mcp.json is not valid JSON: {e}")

    # 3. README (at least 40 non-code words)
    readme_path = plugin_dir / "README.md"
    if not readme_path.is_file():
        errors.append("Claude plugin missing README.md")
    else:
        text = readme_path.read_text(encoding="utf-8")
        word_count = count_non_code_words(text)
        if word_count < 40:
            errors.append(
                f"README.md has only {word_count} non-code words. Claude pre-submission checklist requires >= 40 words."
            )

    # 4. LICENSE
    license_path = plugin_dir / "LICENSE"
    if not license_path.is_file() and not manifest.get("license"):
        errors.append("Claude plugin missing LICENSE file and no 'license' set in manifest.")

    # 5. File checks (forbidden files, size limits)
    for root, dirs, files in os.walk(plugin_dir):
        for f in files:
            if f in FORBIDDEN_FILES:
                errors.append(f"Forbidden OS file found: {Path(root, f).relative_to(plugin_dir)}")
            file_path = Path(root, f)
            try:
                if file_path.stat().st_size > MAX_FILE_BYTES:
                    errors.append(f"File {file_path.relative_to(plugin_dir)} exceeds {MAX_FILE_BYTES} bytes.")
            except Exception:
                pass

    # 6. Execute Anthropic's official 'claude plugin validate --strict' CLI
    claude_bin = find_claude_cli()
    if claude_bin:
        try:
            res = subprocess.run(
                [claude_bin, "plugin", "validate", "--strict", str(plugin_dir)],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                errors.append(f"Anthropic 'claude plugin validate --strict' failed:\n{res.stdout}\n{res.stderr}")
            else:
                notes.append(f"Validated with official Anthropic CLI ({claude_bin}): ✔ Validation passed")
        except Exception as e:
            errors.append(f"Failed to execute '{claude_bin} plugin validate': {e}")
    else:
        notes.append(
            "Note: 'claude' CLI not installed globally on this host. Pre-submission rules verified internally.\n"
            "      To run Anthropic's CLI directly: npm install -g @anthropic-ai/claude-code"
        )

    return errors, notes


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    openai_dir = repo_root / "scopture-openai-plugin"
    claude_dir = repo_root / "scopture-claude-plugin"

    print("Validating plugin packages...\n")

    total_errors = 0

    # Validate OpenAI Plugin
    print(f"Validating OpenAI plugin at {openai_dir.relative_to(repo_root)}:")
    openai_errors, openai_notes = validate_openai_plugin(openai_dir)
    if openai_errors:
        total_errors += len(openai_errors)
        print("  ✗ OpenAI plugin validation FAILED:")
        for err in openai_errors:
            print(f"      - {err}")
    else:
        print("  ✓ OpenAI plugin: PASSED (manifest, schema, mcp, docs valid)")
        for n in openai_notes:
            print(f"      ({n})")
    print()

    # Validate Claude Plugin
    print(f"Validating Claude plugin at {claude_dir.relative_to(repo_root)}:")
    claude_errors, claude_notes = validate_claude_plugin(claude_dir)
    if claude_errors:
        total_errors += len(claude_errors)
        print("  ✗ Claude plugin validation FAILED:")
        for err in claude_errors:
            print(f"      - {err}")
    else:
        print("  ✓ Claude plugin: PASSED (manifest, README >= 40 words, license, mcp valid)")
        for n in claude_notes:
            print(f"      ({n})")
    print()

    if total_errors > 0:
        print(f"Validation FAILED with {total_errors} error(s).", file=sys.stderr)
        return 1

    print("All plugins validated successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
