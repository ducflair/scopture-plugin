# Scopture OpenAI Plugin

Connect ChatGPT and Codex directly to Scopture to inspect, analyze, and manage collaborative drawings, models, issues, and project charters.

## Overview

Scopture is a modern collaborative design and visual workspace. This plugin connects your agent environment directly to Scopture via the Model Context Protocol (MCP) and bundles powerful agent skills for design inspection, container manipulation, and project governance.

Key capabilities include:
- **Canvas and Model Inspection:** Inspect live drawing canvas state, 2D/3D elements, selected objects, and embedded parameters.
- **Project Charters and Decisions:** Review project goals, architectural constraints, and traced design decisions directly from drawing charters.
- **Issue Tracking:** Query open issues, navigate visual pins, review reviewer feedback, and create or resolve action items.
- **DUC Container Support:** Parse and query `.duc` files (relational SQLite container files) with authoritative schema documentation and Python (`ducpy`) tools.

## Included Skills

When packaged for release, this plugin bundles the following skills:
- **`scopture`**: Tools and workflows for canvas state inspection, design reviews, issue management, and project charters.
- **`scopture-cli`**: Command-line reference and automated execution patterns for the Scopture CLI.
- **`duc`**: Relational database schema reference, Python `ducpy` API guides, and spatial data extraction for `.duc` project containers.

## MCP Server Configuration

This plugin connects to Scopture's streamable HTTP MCP server:
- **URL**: `https://api.scopture.com/mcp`
- **Protocol**: Model Context Protocol (MCP) streamable-http with OAuth 2.0 Dynamic Client Registration (DCR).

## License

This plugin is released under the [MIT License](LICENSE).
