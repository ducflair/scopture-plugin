# MCP Tool (/docs/automation/mcp-tool)



## Connect Scopture to Your AI Assistant [#connect-scopture-to-your-ai-assistant]

1. In your assistant’s MCP or custom connector settings, add a remote server named **Scopture**.
2. Paste this URL and select **Streamable HTTP** and **OAuth** if prompted:

```text
https://api.scopture.com/mcp
```

3. Connect, sign in to Scopture in the browser, and authorize the requested access.
4. Enable the Scopture tools in your conversation. Ask: “List my available drawings in Scopture.”

You do not need to install the desktop app or CLI to use this remote connection. See [AI Providers](/docs/automation/ai-providers) for the setup steps in ChatGPT, Claude, Gemini, Copilot, Grok, and Perplexity. Your provider’s plan and workspace policies determine whether custom connectors are available.

## Automation in Project Context [#automation-in-project-context]

Scopture exposes a Model Context Protocol (MCP) server and Command Line Interface (CLI) so compatible agents can work with drawings, models, charter records, issues, external files, and version history. Automation operates on the same project context that people review in the application; it is not a separate copy of the drawing.

The integration is intended for bounded engineering and review tasks: inspecting the active drawing, locating relevant elements, calculating or generating an addition, recording an issue or decision, and verifying the result in context.

***

## Connect an Agent [#connect-an-agent]

The MCP endpoint and connection controls are available from **Settings → Integrations**. Use the client’s OAuth flow when it supports remote MCP authentication. API keys are available for clients that cannot complete OAuth; they are scoped, revocable, displayed only when created, and should be stored as credentials.

Integration permissions separate three capabilities:

| Scope       | Capability                                                      |
| ----------- | --------------------------------------------------------------- |
| **Read**    | Inspect accessible drawings and their project context           |
| **Write**   | Change drawing records, charter data, issues, and related state |
| **Execute** | Run supported Python or SQL jobs against an accessible drawing  |

These scopes do not bypass drawing or organization permissions. The connected identity must also have the access required for the requested operation. Cloud Python execution additionally requires an entitled paid plan in the drawing’s organization.

***

## What an Agent Can Do [#what-an-agent-can-do]

Scopture’s MCP tools cover five functional areas:

* **Orient** — identify the active drawing, current application context, visible state, and available drawings.
* **Inspect** — search elements, read drawing records, retrieve external files, inspect versions, and capture screenshots.
* **Trace** — read and maintain the charter, requirements, constraints, decisions, issues, and issue messages.
* **Change** — create or update drawing content and switch application modes when an operation requires focused model interaction.
* **Compute and recover** — run Python or SQLite work, export assets, inspect job results, and restore a known version or automated change boundary.

Tool descriptions and input schemas are the authoritative reference for individual operations. They remain closer to the running service than a static copy of every argument in this documentation.

### MCP and CLI Coverage [#mcp-and-cli-coverage]

Remote CLI commands and MCP tools use the same validated backend operations and resource permissions. Protocol response envelopes differ; the underlying operations are shared.

| Capability                        | CLI                                              | MCP                                                        |
| --------------------------------- | ------------------------------------------------ | ---------------------------------------------------------- |
| Create/list/read drawings         | `drawing create/list/get`                        | `create_drawing`, `list_available_drawings`, `get_drawing` |
| Inspect/filter elements and files | `elements`, `cat`, `files`                       | `get_elements`, `get_external_files`                       |
| Canvas/model images and exports   | `render`, `export`                               | `get_drawing_screenshot`, `export_asset`                   |
| Python and SQL                    | `run-python`, `run-sql`                          | `run_python_code`, `run_sqlite`, `check_python_run_job`    |
| Issue lifecycle                   | `issues list/create/update/close/reopen/dismiss` | `list_issues`, `create_issues`, `update_issue`             |
| Charter inspection                | `charter get`                                    | `get_charter`                                              |

For an inline rendered image, call `get_drawing_screenshot` with `viewport: { x, y, width, height }` in scene coordinates, or `elementId` plus `viewConfig` for model camera/display/clipping settings. Output `width`/`height` are pixels. No open client is required. `export_asset` supplies image/vector/CAD files as short-lived download URLs; it accepts the same viewport/view settings and STL `meshOptions`.

Download presigned URLs with HTTP **GET**. Their signatures authorize that method; a **HEAD** request can return 403 even when downloading with GET succeeds.

MCP additionally exposes Issue messages, user lookup, charter changes, version inspection/recovery, server text search and live model-mode commands. Saved checkpoints and deltas can be restored without an open client, preserving current Issues and charter and recording a rollback version. The CLI has no dedicated commands for those operations. Structural comparison of local or remote drawings, OS file destinations, desktop focus, offline drawings and local sandbox execution remain CLI capabilities.

Neither interface exposes deletion of Issues or Charter items. The user must delete them manually in Scopture. Use close or dismiss when that is the intended Issue action; SQL and Python drawing updates preserve existing Issue and message identities.

***

## Execution Model [#execution-model]

An effective agent workflow is:

1. Resolve the drawing and inspect its current context.
2. Retrieve only the records and external assets needed for the task.
3. Perform a narrow calculation, query, or edit.
4. Poll asynchronous Python or SQL work instead of submitting the same job again.
5. Verify the result through the updated records, a drawing screenshot, or Model Open mode.
6. Leave the automatic version delta as the recoverable boundary for the operation.

The remote MCP server operates on remote drawings. Local `.duc` files and native file links stay on the device and are not sent to remote execution. Use the [desktop CLI](/docs/automation/cli-tool) for terminal access to a local drawing.

***

## Python and SQLite [#python-and-sqlite]

The Python environment is an isolated Python 3.12 sandbox with Duc-aware drawing helpers and engineering libraries including NumPy, SciPy, SymPy, Pint, pandas, Matplotlib, and Fluids. It can read the current `.duc` data, resolve referenced files, perform engineering calculations, and submit drawing changes.

Model source declares one typed artifact with `emit_output(...)`. Its envelope identifies the renderer, MIME type, content hash, code and input fingerprints, and runtime version. This contract supports parametric 3D, IFC, DXF, image, SVG, PDF, and table outputs. A returned artifact is separate from a drawing mutation: use drawing updates when the operation must change the Model Element or its referenced files. See [Model Elements](https://duc.ducflair.com/docs/concepts/elements/model-element) for the API and persistence fields.

For an IfcOpenShell model, use `emit_output(ifc_model, kind="ifc")` to retain the IFC file and its IFC renderer. `show(ifc_model)` uses the default parametric capture and does not declare an IFC artifact.

Drawing updates use **patch semantics**. The update should contain only records that were added or changed:

* an existing ID updates the corresponding record;
* a new ID adds a record;
* omitted records remain unchanged; and
* an element is deleted by updating its `is_deleted` field to `true`.

It is therefore unnecessary—and undesirable—to fetch, rewrite, and submit the complete drawing for a localized change.

SQLite jobs provide direct structured access to the `.duc` database through the supported Duc query layer. Use them for targeted inspection or mutation when the task is naturally relational. Use Python when the task requires calculations, geometry generation, external-file processing, or multi-step drawing logic.

See the [SQLite Runner](/docs/automation/sqlite-runner) for per-drawing queries, attached databases, mutations, and asynchronous job handling.

<Callout type="warn" title="Prefer the narrowest valid mutation">
  Read the current state before writing, preserve existing IDs and relationships, and submit only the intended patch. Automated changes are versioned, but a recoverable history is not a substitute for a well-scoped operation.
</Callout>

***

## Verification and Recovery [#verification-and-recovery]

A successful tool response proves that an operation completed, not that the resulting drawing communicates the intended outcome. Agents should inspect the changed records and use a screenshot or interactive model view when visual placement or geometry matters.

Scopture records agent operations as automatic deltas in the drawing’s version graph. Those boundaries can be inspected and restored without treating automation as an opaque side channel.

For the underlying `.duc` storage and element model, see the [Duc documentation](https://duc.ducflair.com/docs/).