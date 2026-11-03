#!/usr/bin/env python3
"""
Publishes Scopture's server.json to the official Model Context Protocol (MCP) Registry.
https://registry.modelcontextprotocol.io/

In GitHub Actions CI:
- Authenticates seamlessly via GitHub OIDC (mcp-publisher login github-oidc)
- Requires 'permissions: id-token: write' in the workflow job
- Publishes under the GitHub organization namespace (io.github.ducflair/scopture)

Locally:
- Uses existing mcp-publisher login (or prompts for login if not authenticated)
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

MCP_PUBLISHER_VERSION = "v1.8.7"


def ensure_mcp_publisher() -> str:
    """Find local mcp-publisher or download it dynamically."""
    which_path = shutil.which("mcp-publisher")
    if which_path and os.access(which_path, os.X_OK):
        return which_path

    home_local = Path.home() / ".local" / "bin" / "mcp-publisher"
    if home_local.is_file() and os.access(home_local, os.X_OK):
        return str(home_local)

    # Download binary for current platform
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_name = "darwin" if "darwin" in system else "linux" if "linux" in system else "windows"
    arch_name = "arm64" if "arm" in machine or "aarch64" in machine else "amd64"

    archive_name = f"mcp-publisher_{os_name}_{arch_name}.tar.gz"
    download_url = (
        f"https://github.com/modelcontextprotocol/registry/releases/download/"
        f"{MCP_PUBLISHER_VERSION}/{archive_name}"
    )

    print(f"Downloading mcp-publisher {MCP_PUBLISHER_VERSION} for {os_name}/{arch_name}...")
    dest_dir = Path.home() / ".local" / "bin"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_bin = dest_dir / "mcp-publisher"

    with tempfile.TemporaryDirectory() as tmp:
        tar_path = Path(tmp) / archive_name
        req = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0 (Scopture Release Bot)"})
        with urllib.request.urlopen(req) as resp:
            tar_path.write_bytes(resp.read())

        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(tmp)

        extracted_bin = Path(tmp) / ("mcp-publisher.exe" if os_name == "windows" else "mcp-publisher")
        if not extracted_bin.is_file():
            raise RuntimeError(f"Failed to find extracted mcp-publisher binary in {tmp}")

        extracted_bin.chmod(0o755)
        shutil.copy2(extracted_bin, dest_bin)
        dest_bin.chmod(0o755)

    print(f"Installed mcp-publisher to {dest_bin}")
    return str(dest_bin)


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish server.json to the official MCP Registry.")
    parser.add_argument(
        "--version",
        help="Release version to set in server.json before publishing",
    )
    parser.add_argument(
        "--file",
        default="server.json",
        help="Path to server.json (default: server.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only, do not publish",
    )

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    server_path = (repo_root / args.file).resolve()

    if not server_path.is_file():
        print(f"Error: {server_path} not found.", file=sys.stderr)
        return 1

    # Update version in server.json if provided
    if args.version:
        clean_version = args.version.lstrip("v")
        data = json.loads(server_path.read_text(encoding="utf-8"))
        data["version"] = clean_version
        server_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"Updated {server_path.name} version to {clean_version}")

    mcp_publisher = ensure_mcp_publisher()

    # Always validate first
    print(f"Validating {server_path.name} against MCP Registry...")
    val_res = subprocess.run([mcp_publisher, "validate", str(server_path)], text=True)
    if val_res.returncode != 0:
        print("Validation failed. Aborting MCP Registry publish.", file=sys.stderr)
        return val_res.returncode

    if args.dry_run:
        print("Dry run complete: server.json is valid.")
        return 0

    # In GitHub Actions CI, authenticate via OIDC
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("Detected GitHub Actions environment. Logging in via github-oidc...")
        login_res = subprocess.run([mcp_publisher, "login", "github-oidc"], text=True)
        if login_res.returncode != 0:
            print("Failed to authenticate to MCP Registry via github-oidc.", file=sys.stderr)
            return login_res.returncode

    print("Publishing to https://registry.modelcontextprotocol.io...")
    pub_res = subprocess.run([mcp_publisher, "publish", str(server_path)], text=True)
    if pub_res.returncode != 0:
        print("Failed to publish server to MCP Registry.", file=sys.stderr)
        return pub_res.returncode

    print("✓ Successfully published server to MCP Registry!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
