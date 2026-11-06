# Agent Skills

Engineering agent skills, Model Context Protocol (MCP) integrations, and automation tools for Scopture and DUC. These skills equip AI assistants and coding agents with domain knowledge to inspect models, review drawings, manage issues, and trace technical decisions across project workflows.

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
