# Scopture Plugin & Agent Skills

An integrated workspace package providing Model Context Protocol (MCP) tooling and domain-specific agent skills for inspecting physical engineering models, reviewing technical drawings, tracking issues, and managing design decisions.

## Overview

This package equips AI assistants and engineering workflows with direct access to Scopture's hosted Model Context Protocol services and local file manipulation libraries:

- **Model & Drawing Inspection:** Retrieve drawing element trees, inspect 2D geometries and 3D CAD/BIM assemblies, analyze spatial coordinates, and capture visual views.
- **Design Review & Issues:** Triage defects, query open review comments, place visual issue markers, and track resolution lifecycles directly against drawing assets.
- **Project Charters & Decisions:** Access embedded design goals, technical requirements, and architectural trade-offs to keep engineering decisions traceable.
- **DUC Container Support:** Parse, query, and construct `.duc` SQLite design containers using Python (`ducpy`) and relational schema definitions.

## Included Skills

- **`scopture`**: Guidance for canvas operations, model exploration, issue tracking, and charter management.
- **`scopture-cli`**: Terminal workflows, automated queries, batch mutations, and headless rendering commands.
- **`duc`**: Comprehensive relational schema reference, Python builder patterns, and file format specifications.

## MCP Endpoint

The package connects to the Scopture Model Context Protocol endpoint:
- **Server Name:** `scopture`
- **Transport Type:** Streamable HTTP
- **URL:** `https://api.scopture.com/mcp`

## License

Distributed under the [MIT License](LICENSE).
