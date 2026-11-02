# Scopture Claude Plugin

Connect Claude Code and Claude.ai directly to Scopture to inspect, analyze, and manage collaborative drawings, models, issues, and project charters.

## Overview

Scopture is a collaborative visual workspace and design review platform for complex models, drawings, and multidisciplinary projects. This plugin equips Claude with direct access to Scopture's Model Context Protocol (MCP) server alongside comprehensive domain knowledge skills for analyzing design artifacts, validating drawing requirements, and tracing decisions.

### Key Capabilities

- **Drawing and Model Inspection:** Retrieve live drawing hierarchy, view active canvas selections, inspect model parameters, and analyze spatial coordinates.
- **Project Charters and Decisions:** Read project goals, design constraints, and architectural decisions embedded in the drawing's charter to maintain alignment with stakeholder expectations.
- **Issue and Review Management:** Search open issues, review visual markup notes, triage defect pins, and update resolution states without switching contexts.
- **DUC Container Manipulation:** Query and inspect `.duc` containers (SQLite-based design files) with complete relational schema knowledge and Python automation guidance.

## Bundled Skills

This plugin packages authoritative agent skills to guide Claude when interacting with design data:

- **`scopture`**: Step-by-step guidance for reviewing Scopture canvases, inspecting element trees, and managing issues and project charters.
- **`scopture-cli`**: Syntax, workflows, and automated execution patterns for the Scopture command-line interface.
- **`duc`**: Relational database schema reference, Python `ducpy` API reference, and spatial data extraction for `.duc` project containers.

## MCP Server Connection

The plugin connects Claude to Scopture's hosted Model Context Protocol endpoint:
- **Server Name:** `scopture`
- **Transport Type:** HTTP
- **Endpoint URL:** `https://api.scopture.com/mcp`

All communication uses secure HTTPS transport with authenticated endpoints.

## Installation and Usage

### Claude Code CLI

To install this plugin locally in Claude Code, run:

```bash
claude plugin install scopture
```

To validate the plugin structure before submission:

```bash
claude plugin validate ./scopture-claude-plugin
```

### Claude Directory Submission

This plugin is structured to comply with all Anthropic directory pre-submission requirements. You can submit the repository via the Claude developer portal at `https://claude.ai/directory/manage` using the `scopture-claude-plugin` directory path.

## License

This plugin is licensed under the [MIT License](LICENSE).
