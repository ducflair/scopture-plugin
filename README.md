# Scopture Agent Plugins and Skills

Engineering agent skills, Model Context Protocol (MCP) integrations, and automation tools for Scopture and DUC. These skills equip AI assistants and coding agents with domain knowledge to inspect models, review drawings, manage issues, and trace technical decisions across project workflows.

## MCP app

The repository root is a portable Agent Plugins package. `plugin.json` describes Scopture, and `mcp.json` connects compatible clients to the public Streamable HTTP server at `https://api.scopture.com/mcp`. The server handles OAuth authorization; this repository contains no access tokens or client secrets.

For Grok Bot Directory or Cursor Directory, submit this public repository URL:

```text
https://github.com/ducflair/scopture-plugin
```

## Install

```bash
npx skills add ducflair/scopture-plugin --skill duc
```

Or install all skills from this repository:

```bash
npx skills add ducflair/scopture-plugin
```

## Development

```bash
# Validate each skill folder
python3 scripts/validate_skills.py

# Test skill discovery
npx skills add . --list
```
