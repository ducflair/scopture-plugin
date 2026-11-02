# Rust (ducrs) (/docs/rust/overview)



## Overview [#overview]

While the SQLite database schema defines the relational container format and schema, `ducrs` implements the core engine logic for binary parsing, gzip envelope decompression, DAG version control, chunk streaming, and serialization.

***

## Foundational Architecture [#foundational-architecture]

Every ecosystem SDK and adapter builds directly on top of `ducrs`:

<Mermaid
  chart="flowchart TD
    S[&#x22;SQLite Database Schema (.duc Container)&#x22;] --> R[&#x22;ducrs (Rust Core Engine)&#x22;]

    R --> JS[&#x22;ducjs (TypeScript / WASM Engine)&#x22;]
    R --> PY[&#x22;ducpy (Python / PyO3 Bindings)&#x22;]
    R --> PDF[&#x22;ducpdf / duc2pdf (PDF WASM Exporter)&#x22;]
    R --> SVG[&#x22;ducsvg (SVG Exporter)&#x22;]"
/>

* **Core Engine Foundation**: `ducrs` serves as the primary implementation of all binary container operations, validation rules, and schema migrations.
* **Python Bindings (`ducpy`)**: Exposes native CPython extension modules compiled via PyO3 for high-performance Python execution.
* **WebAssembly Bindings (`ducjs`, `duc2pdf`)**: Compiles to WebAssembly (`wasm32-unknown-unknown`) to power browser and Node.js JavaScript runtimes.

***

## Core Capabilities [#core-capabilities]

* **Zero-Cost Abstractions**: High-performance, type-safe structures mapping directly to SQLite relational tables without runtime overhead.
* **Memory Safety & Speed**: Memory-safe parsing, fast stream serialization, and low-latency database transactions.
* **Universal Compilation**: Compiles natively across macOS, Linux, Windows, iOS, Android, and WebAssembly targets.