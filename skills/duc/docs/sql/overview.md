# Overview (/docs/sql/overview)



A `.duc` file is a **gzip-compressed SQLite database container**. This allows physical-engineering applications, SDKs, and AI tools to query, inspect, and mutate project state using standard SQL.

***

## Core Features [#core-features]

* **Relational Integrity**: Foreign key constraints and WAL mode ensure atomic, safe transactions across elements, styles, symbol blocks, and DAG version history.
* **Selective Mutations**: Execute targeted SQL `UPDATE` or `INSERT` queries directly against specified elements or attributes without re-serializing full documents.
* **FTS5 Full-Text Search**: Instant full-text search indexing across element labels, text primitives, embedded documents, code models, and PDF text.

For full schema details and interactive entity-relationship diagrams, visit the [SQL API Reference](/docs/sql/api).