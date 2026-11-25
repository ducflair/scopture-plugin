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
from urllib.parse import urlparse
from package_common import merge_json_objects

RESERVED_NAMES = {"claude", "anthropic", "official", "plugin", "mcp", "test"}
PLUGIN_NAME_REGEX = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
AGENT_PLUGIN_NAME_REGEX = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
FORBIDDEN_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX"}
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MiB


def validate_portable_agent_plugin(plugin_dir: Path) -> tuple[list[str], list[str]]:
    """Validate the repository-root Agent Plugins package used by directories."""
    errors = []
    notes = []
    manifest_path = plugin_dir / "plugin.json"
    mcp_path = plugin_dir / "mcp.json"
    if not manifest_path.is_file():
        errors.append("Missing required root 'plugin.json' portable manifest.")
        return errors, notes
    if not mcp_path.is_file():
        errors.append("Missing required root 'mcp.json' MCP configuration.")
        return errors, notes

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"Root plugin.json is not valid JSON: {e}"], notes

    if not isinstance(manifest, dict):
        errors.append("Root plugin.json must contain a JSON object.")
        manifest = {}
    allowed_manifest_fields = {
        "$schema", "name", "version", "description", "author", "homepage",
        "repository", "license", "keywords", "extensions",
    }
    unknown_manifest_fields = set(manifest) - allowed_manifest_fields
    if unknown_manifest_fields:
        errors.append(f"Root plugin.json contains unsupported fields: {', '.join(sorted(unknown_manifest_fields))}.")
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        errors.append("Root plugin.json must target the Agent Plugins 1.0.0 schema.")
    name = manifest.get("name")
    if not isinstance(name, str) or not name or not AGENT_PLUGIN_NAME_REGEX.fullmatch(name) or "--" in name or ".." in name:
        errors.append("Root plugin.json 'name' must use lowercase letters, numbers, hyphens, or periods and start/end alphanumerically.")
    for field in ("version", "description", "homepage", "repository", "license"):
        if field in manifest and not isinstance(manifest[field], str):
            errors.append(f"Root plugin.json '{field}' must be a string.")
    author = manifest.get("author")
    if author is not None and (
        not isinstance(author, dict)
        or set(author) - {"name", "email", "url"}
        or any(not isinstance(value, str) for value in author.values())
    ):
        errors.append("Root plugin.json 'author' must contain only string name, email, or url fields.")
    keywords = manifest.get("keywords")
    if keywords is not None and (
        not isinstance(keywords, list) or any(not isinstance(keyword, str) for keyword in keywords)
    ):
        errors.append("Root plugin.json 'keywords' must be an array of strings.")
    extensions = manifest.get("extensions")
    if extensions is not None and (
        not isinstance(extensions, dict)
        or any(not isinstance(value, dict) for value in extensions.values())
    ):
        errors.append("Root plugin.json 'extensions' must map namespaces to objects.")

    try:
        mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
    except Exception as e:
        return errors + [f"Root mcp.json is not valid JSON: {e}"], notes

    if not isinstance(mcp, dict):
        errors.append("Root mcp.json must contain a JSON object.")
        mcp = {}
    if set(mcp) - {"$schema", "mcpServers"}:
        errors.append("Root mcp.json may contain only '$schema' and 'mcpServers'.")
    if mcp.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json":
        errors.append("Root mcp.json must target the Agent Plugins 1.0.0 MCP schema.")
    servers = mcp.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        errors.append("Root mcp.json must define at least one MCP server.")
    else:
        for server_name, server in servers.items():
            if not isinstance(server, dict):
                errors.append(f"MCP server '{server_name}' must be a configuration object.")
                continue
            if server.get("type") not in ("streamable-http", "sse"):
                errors.append(f"MCP server '{server_name}' must use a supported remote transport.")
            if set(server) - {"type", "url", "headers"}:
                errors.append(f"MCP server '{server_name}' contains fields not supported by the remote transport.")
            url = server.get("url")
            parsed_url = urlparse(url) if isinstance(url, str) else None
            if (
                parsed_url is None
                or parsed_url.scheme != "https"
                or not parsed_url.netloc
                or parsed_url.username is not None
                or parsed_url.password is not None
                or parsed_url.fragment
            ):
                errors.append(f"MCP server '{server_name}' must use an absolute HTTPS URL without credentials or a fragment.")
            headers = server.get("headers")
            if headers is not None and (
                not isinstance(headers, dict)
                or any(not isinstance(key, str) or not isinstance(value, str) for key, value in headers.items())
            ):
                errors.append(f"MCP server '{server_name}' headers must be string key/value pairs.")

    if not (plugin_dir / "README.md").is_file():
        errors.append("Portable Agent Plugins package is missing root README.md.")
    if errors:
        return errors, notes
    notes.append("Root Agent Plugins manifest and remote MCP configuration are valid.")
    return errors, notes


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

    # 1. Compose the release manifest from the shared base and OpenAI-only overlay.
    base_manifest_path = plugin_dir.parent / "plugin.json"
    overlay_path = plugin_dir / "manifest-overlay.json"
    if not base_manifest_path.is_file():
        errors.append("Missing shared root 'plugin.json' manifest.")
        return errors, notes
    if not overlay_path.is_file():
        errors.append("Missing OpenAI 'manifest-overlay.json'.")
        return errors, notes

    try:
        base_manifest = json.loads(base_manifest_path.read_text(encoding="utf-8"))
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"Shared manifest or OpenAI overlay is not valid JSON: {e}"], notes

    if not isinstance(base_manifest, dict) or not isinstance(overlay, dict):
        return ["Shared manifest and OpenAI overlay must both be JSON objects."], notes
    if set(overlay) - {"name", "extensions"}:
        errors.append("OpenAI manifest overlay may override only 'name' and 'extensions'.")
    overlay_extensions = overlay.get("extensions", {})
    if not isinstance(overlay_extensions, dict) or set(overlay_extensions) - {"com.openai"}:
        errors.append("OpenAI manifest overlay may contain only the 'com.openai' extension object.")
    try:
        manifest = merge_json_objects(base_manifest, overlay)
    except TypeError as e:
        return errors + [str(e)], notes

    merged_extensions = manifest.get("extensions", {})
    merged_openai_extension = (
        merged_extensions.get("com.openai", {}) if isinstance(merged_extensions, dict) else {}
    )
    openai_interface = (
        merged_openai_extension.get("interface", {})
        if isinstance(merged_openai_extension, dict)
        else {}
    )
    if isinstance(openai_interface, dict):
        openai_interface.setdefault("longDescription", manifest.get("description", ""))
    if (plugin_dir / "plugin.json").exists() or (plugin_dir / "mcp.json").exists():
        errors.append("OpenAI source must not duplicate the shared root plugin.json or mcp.json.")

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
    extensions = manifest.get("extensions", {})
    ext = extensions.get("com.openai", {}) if isinstance(extensions, dict) else {}
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

            short_desc = interface.get("shortDescription", "")
            if len(short_desc) > 30:
                errors.append(
                    f"extensions.com.openai.interface.shortDescription ('{short_desc}') exceeds 30 characters ({len(short_desc)} chars). Subtitle must be 30 characters or fewer."
                )

            support_url = interface.get("supportURL")
            if not support_url:
                errors.append("extensions.com.openai.interface missing required 'supportURL'.")
            elif not support_url.startswith("https://"):
                errors.append(f"extensions.com.openai.interface.supportURL must start with https://: '{support_url}'")

            logo_rel = interface.get("logo") or interface.get("icon")
            logo_file = (plugin_dir / logo_rel) if logo_rel else None
            if not logo_file or not logo_file.is_file():
                if (plugin_dir / "assets" / "icon.png").is_file():
                    logo_file = plugin_dir / "assets" / "icon.png"
                elif (plugin_dir / "icon.png").is_file():
                    logo_file = plugin_dir / "icon.png"
                else:
                    errors.append("OpenAI plugin missing app icon asset (required by OpenAI portal).")

    # 2. mcp.json
    mcp_path = plugin_dir.parent / "mcp.json"
    if not mcp_path.is_file():
        errors.append("Missing shared root 'mcp.json' MCP configuration.")
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
        else:
            word_count = count_non_code_words(text)
            if word_count < 40:
                errors.append(
                    f"README.md has only {word_count} non-code words. Claude pre-submission checklist requires >= 40 words."
                )

    # 4. LICENSE
    license_path = plugin_dir / "LICENSE"
    if not license_path.is_file() and not manifest.get("license"):
        errors.append("Claude plugin missing LICENSE file and no 'license' set in manifest.")

    # 5. Anthropic directory listing metadata
    for url_field in ["documentationUrl", "supportUrl", "privacyPolicyUrl", "termsOfServiceUrl"]:
        val = manifest.get(url_field)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"Claude plugin missing required '{url_field}' in .claude-plugin/plugin.json")
        elif not val.startswith("https://"):
            errors.append(f"'{url_field}' must start with https:// (got '{val}')")

    icon_ref = manifest.get("icon")
    icon_file = None
    if icon_ref is not None:
        if not isinstance(icon_ref, str) or not icon_ref.strip():
            errors.append("Claude plugin 'icon' must be a non-empty relative path when provided")
            icon_ref = None
    if icon_ref:
        icon_path = Path(icon_ref)
        plugin_root = plugin_dir.resolve()
        resolved_icon = (plugin_root / icon_path).resolve()
        if (
            icon_path.is_absolute()
            or ".." in icon_path.parts
            or not resolved_icon.is_relative_to(plugin_root)
        ):
            errors.append(f"Claude plugin 'icon' must be a relative path inside the plugin (got '{icon_ref}')")
        elif not resolved_icon.is_file():
            errors.append(f"Claude plugin icon file does not exist: '{icon_ref}'")
        else:
            icon_file = resolved_icon

    if icon_file:
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
    openai_dir = repo_root / "openai-plugin"
    claude_dir = repo_root / "common"
    server_json_path = repo_root / "server.json"

    print("Validating plugin and MCP server packages...\n")

    total_errors = 0

    # Validate the portable package scanned by Grok Bot and Cursor directories.
    print("Validating repository-root Agent Plugins package:")
    portable_errors, portable_notes = validate_portable_agent_plugin(repo_root)
    if portable_errors:
        total_errors += len(portable_errors)
        print("  ✗ Root Agent Plugins validation FAILED:")
        for err in portable_errors:
            print(f"      - {err}")
    else:
        print("  ✓ Root Agent Plugins package: PASSED")
        for note in portable_notes:
            print(f"      ({note})")
    print()

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
