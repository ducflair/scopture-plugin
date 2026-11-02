#!/usr/bin/env python3
"""
Validates OpenAI, Claude, and Model Context Protocol (MCP) Registry packages
against official schemas and submission guidelines:
- OpenAI Plugin: https://developers.openai.com/plugins/build/plugins
- Claude Plugin: https://claude.com/docs/plugins/pre-submission-checklist
- MCP Registry: https://registry.modelcontextprotocol.io/
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
    cleaned = re.sub(r"```[\s\S]*?```", " ", markdown_text)
    cleaned = re.sub(r"`[^`]+`", " ", cleaned)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    words = re.findall(r"\b[A-Za-z0-9_-]+\b", cleaned)
    return len(words)


def validate_openai_plugin(plugin_dir: Path) -> tuple[list[str], list[str]]:
    """Validate OpenAI plugin against Agent Plugins 1.0.0 and com.openai extension rules."""
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
    """Validate Claude plugin against Anthropic pre-submission checklist."""
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

    # 3. README
    readme_path = plugin_dir / "README.md"
    if not readme_path.is_file():
        errors.append("Claude plugin missing README.md")
    else:
        text = readme_path.read_text(encoding="utf-8")
        if not text.strip():
            errors.append("README.md is empty.")

    # 4. LICENSE
    license_path = plugin_dir / "LICENSE"
    if not license_path.is_file() and not manifest.get("license"):
        errors.append("Claude plugin missing LICENSE file and no 'license' set in manifest.")

    # 5. Directory lints: privacyPolicyUrl and icon (Anthropic Directory pre-submission checklist)
    privacy_url = manifest.get("privacyPolicyUrl")
    if not privacy_url:
        errors.append("Claude plugin missing required 'privacyPolicyUrl' in .claude-plugin/plugin.json")
    elif not privacy_url.startswith("https://"):
        errors.append(f"'privacyPolicyUrl' must start with https:// (got '{privacy_url}')")

    icon_field = manifest.get("icon")
    icon_file = plugin_dir / (icon_field or ".claude-plugin/icon.png")
    if not icon_file.is_file():
        errors.append(
            "Claude plugin missing icon file at .claude-plugin/icon.png (required by Claude Developer Portal)"
        )
    else:
        icon_size = icon_file.stat().st_size
        if icon_size > 2 * 1024 * 1024:
            errors.append(f"Plugin icon exceeds 2 MB limit ({icon_size:,} bytes)")
        try:
            with icon_file.open("rb") as f:
                header = f.read(24)
                if header.startswith(b"\x89PNG\r\n\x1a\n"):
                    import struct
                    w, h = struct.unpack(">II", header[16:24])
                    if w != h:
                        errors.append(f"Plugin icon must be square (got {w}x{h} px)")
                    elif w < 512 or w > 2048:
                        errors.append(f"Plugin icon must be 512-2048 px on each side (got {w}x{h} px)")
        except Exception as e:
            notes.append(f"Could not verify PNG dimensions: {e}")

    # 6. Bundled Skills directory (ensure skills/ is discovered by Claude portal)
    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        errors.append("Claude plugin missing 'skills/' directory. Claude portal will report 'No skills, agents, commands, or hooks'.")
    else:
        skill_subdirs = [s for s in skills_dir.iterdir() if s.is_dir() and not s.name.startswith(".")]
        if not skill_subdirs:
            errors.append("Claude plugin 'skills/' directory contains no skill folders.")
        for s in skill_subdirs:
            if not (s / "SKILL.md").is_file():
                errors.append(f"Skill '{s.name}' in Claude plugin missing required 'SKILL.md'.")
        notes.append(f"Detected {len(skill_subdirs)} bundled skill(s): {', '.join(sorted(s.name for s in skill_subdirs))}")

    # 7. File checks (forbidden files, size limits)
    ignore_dirs = {".git", "node_modules", "dist", ".gemini", ".venv", "venv", "__pycache__"}
    for root, dirs, files in os.walk(plugin_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            if f in FORBIDDEN_FILES:
                errors.append(f"Forbidden OS file found: {Path(root, f).relative_to(plugin_dir)}")
            file_path = Path(root, f)
            try:
                if file_path.stat().st_size > MAX_FILE_BYTES:
                    errors.append(f"File {file_path.relative_to(plugin_dir)} exceeds {MAX_FILE_BYTES} bytes.")
            except Exception:
                pass

    # 8. Execute Anthropic's official 'claude plugin validate' CLI
    claude_bin = find_claude_cli()
    if claude_bin:
        try:
            res = subprocess.run(
                [claude_bin, "plugin", "validate", str(plugin_dir)],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                errors.append(f"Anthropic 'claude plugin validate' failed:\n{res.stdout}\n{res.stderr}")
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


def validate_mcp_registry_server(server_json_path: Path) -> tuple[list[str], list[str]]:
    """Validate server.json against official Model Context Protocol Registry rules."""
    errors = []
    notes = []
    if not server_json_path.is_file():
        return errors, notes

    try:
        data = json.loads(server_json_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"server.json is not valid JSON: {e}"], notes

    if data.get("$schema") != "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json":
        errors.append("server.json $schema must be 'https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json'")

    name = data.get("name", "")
    if not name or "/" not in name:
        errors.append("server.json 'name' must be namespaced (e.g. 'io.github.org/server' or 'com.domain/server')")

    title = data.get("title")
    if not title:
        errors.append("server.json missing 'title'")

    desc = data.get("description", "")
    if not desc:
        errors.append("server.json missing 'description'")
    elif len(desc) > 100:
        errors.append(f"server.json 'description' exceeds MCP Registry maximum of 100 characters ({len(desc)} chars)")

    if not data.get("version"):
        errors.append("server.json missing 'version'")

    remotes = data.get("remotes", [])
    if not remotes and not data.get("packages"):
        errors.append("server.json must specify either 'remotes' or 'packages'")

    for idx, r in enumerate(remotes):
        rtype = r.get("type")
        if rtype not in ("streamable-http", "sse"):
            errors.append(f"remotes[{idx}] type '{rtype}' must be 'streamable-http' or 'sse'")
        rurl = r.get("url", "")
        if not rurl.startswith("https://"):
            errors.append(f"remotes[{idx}] url must be https://: '{rurl}'")

    mcp_pub = shutil.which("mcp-publisher")
    if mcp_pub:
        notes.append(f"mcp-publisher CLI detected ({mcp_pub}). Run 'mcp-publisher validate server.json' for live registry API check.")

    return errors, notes


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    openai_dir = repo_root / "scopture-openai-plugin"
    claude_dir = repo_root
    server_json_path = repo_root / "server.json"

    print("Validating plugin and MCP server packages...\n")

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
    print("Validating Claude plugin at repository root:")
    claude_errors, claude_notes = validate_claude_plugin(claude_dir)
    if claude_errors:
        total_errors += len(claude_errors)
        print("  ✗ Claude plugin validation FAILED:")
        for err in claude_errors:
            print(f"      - {err}")
    else:
        print("  ✓ Claude plugin: PASSED (manifest, README, license, mcp valid)")
        for n in claude_notes:
            print(f"      ({n})")
    print()

    # Validate MCP Registry server.json if present
    if server_json_path.is_file():
        print(f"Validating MCP Registry server metadata at {server_json_path.relative_to(repo_root)}:")
        mcp_errors, mcp_notes = validate_mcp_registry_server(server_json_path)
        if mcp_errors:
            total_errors += len(mcp_errors)
            print("  ✗ MCP Registry server.json validation FAILED:")
            for err in mcp_errors:
                print(f"      - {err}")
        else:
            print("  ✓ MCP Registry server.json: PASSED (schema, namespace, remotes valid)")
            for n in mcp_notes:
                print(f"      ({n})")
        print()

    if total_errors > 0:
        print(f"Validation FAILED with {total_errors} error(s).", file=sys.stderr)
        return 1

    print("All plugins and MCP server definitions validated successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
