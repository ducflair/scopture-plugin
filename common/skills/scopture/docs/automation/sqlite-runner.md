# SQLite Runner (/docs/automation/sqlite-runner)



Scopture exposes the relational contents of a `.duc` drawing through `ducpy.DucSQL`. Use MCP `run_sqlite` for remote drawings, or CLI `run-sql` for a local file or remote drawing ID. Both remote interfaces use the same validated backend operation.

Resolve a named drawing with `list_available_drawings` before querying it. See the [Duc SQL schema](https://ducflair.github.io/duc/reference/sql/) for the drawing database model; inspect available tables and columns rather than assuming application database tables exist inside a `.duc` file.

## Read One or More Drawings [#read-one-or-more-drawings]

Send tool arguments like these to `run_sqlite`:

```json
{
  "drawingIds": ["drawing-a", "drawing-b"],
  "mode": "per-drawing",
  "query": "SELECT id, element_type FROM {db}.elements WHERE element_type = ?",
  "parameters": ["model"],
  "maxRows": 100,
  "waitForCompletionMs": 0
}
```

`per-drawing` runs the query separately against each drawing. Bare table names also work. `{db}` expands to the current database alias; returned rows include their drawing identity. The runner opens drawing databases sequentially, and `maxRows` limits the combined result across the request.

Use `PRAGMA {db}.table_info(elements)` to inspect columns or `SELECT name FROM {db}.sqlite_master WHERE type = 'table'` to inspect tables. Read modes accept `SELECT`, `WITH`, and read-only `PRAGMA`; database connections also enforce read-only access.

## Join Drawings [#join-drawings]

Use `attached` mode and explicit SQL-safe aliases when a query needs more than one drawing at once:

```json
{
  "drawingIds": ["drawing-a", "drawing-b"],
  "mode": "attached",
  "aliases": {"drawing-a": "source", "drawing-b": "reference"},
  "query": "SELECT s.id FROM source.elements s JOIN reference.elements r ON s.id = r.id",
  "maxRows": 100
}
```

Without custom aliases, the runner derives them from drawing IDs as `db_<drawingId>`, replacing unsupported characters with underscores and resolving duplicates. Use the returned `drawings` metadata to identify each alias.

## Apply a Change [#apply-a-change]

`mutate` accepts exactly one drawing and requires edit access and execution permission. It supports data changes to drawing content. Use the dedicated tools for Issues and charter records. The transaction commits against the drawing revision read by the job. If that revision changes, inspect the latest drawing before retrying. Use unqualified table names and bind values with `parameters`.

```json
{
  "drawingIds": ["drawing-a"],
  "mode": "mutate",
  "query": "UPDATE elements SET label = ? WHERE id = ?",
  "parameters": ["Revised mount", "element-id"],
  "waitForCompletionMs": 0
}
```

Mutations are persisted through Scopture’s drawing update and versioning path. Read the targeted records first and verify them afterward. Remote Issues and Charter records are managed through their own tools; changing drawing SQL does not replace those services, and deletion of Issues or Charter items must be done manually in Scopture.

## Limits and Background Jobs [#limits-and-background-jobs]

| Setting          | Limit                                                       |
| ---------------- | ----------------------------------------------------------- |
| `per-drawing`    | 100 drawing IDs per request                                 |
| `attached`       | 10 distinct drawing IDs, matching SQLite’s attachment limit |
| `mutate`         | One drawing ID                                              |
| `maxRows`        | 500 by default; at most 5,000 combined rows                 |
| Query size       | 100,000 characters                                          |
| Bound parameters | At most 100 strings, numbers, booleans, or nulls            |

A request creates one job. Server jobs wait in a durable queue with at most four concurrent workers. Each job can start as soon as a worker is available. Large drawings and attached joins still consume more worker time and memory, so select the necessary fields and use result limits.

`waitForCompletionMs` defaults to `0`: submission returns a `jobId` promptly. Poll it with `check_python_run_job`, for example:

```json
{"jobId": "returned-job-id", "waitForCompletionMs": 10000}
```

Keep polling the same ID while its status is `queued`, `running`, or `applying`. A short HTTP wait is separate from the worker runtime; a pending job continues after the response. Do not resubmit a pending mutation. Each HTTP polling call waits at most 15 seconds, including the time already spent preparing that request, while a server worker can execute for up to 15 minutes. Jobs expire after 24 hours.

If submission finishes during its requested wait, `run_sqlite.result` contains `columns`, `rows`, `rowCount`, `truncated`, and drawing aliases. Otherwise, the completed job’s stdout contains the same result after the `__SCOPTURE_RUN_SQLITE_RESULT__` marker. Failed jobs include an error; read-only SQL jobs can be polled with read access.

## CLI Examples [#cli-examples]

```bash
scopture run-sql ./assembly.duc "SELECT id, element_type FROM elements" --raw
scopture run-sql <drawing-id> "SELECT id, element_type FROM elements" --raw
scopture run-sql ./assembly.duc "UPDATE elements SET label = 'Mount' WHERE id = 'element-id'" --mutate
```

Local files run directly in the CLI and need no Python setup, account, or connection. For remote IDs, the CLI runs the query locally by default and uses the backend to authorize the snapshot and commit writes. Add `--server` to use cloud compute. Local execution against a remote drawing accepts drawing-content edits. Use the dedicated workflows for external files, Issues, and charter records. Multi-drawing aliases, bound parameters, and row limits are exposed by MCP `run_sqlite`.

See [MCP Tool](/docs/automation/mcp-tool), [CLI Tool](/docs/automation/cli-tool), and [Python Sandbox](/docs/automation/python-sandbox) for setup and the broader execution model.