# TypeScript (ducjs) (/docs/typescript/overview)



## Overview [#overview]

Because `.duc` is a standard **SQLite database**, `ducjs` packages an embedded WebAssembly SQLite engine. This allows it to run seamlessly in Node.js, Bun, Deno, and web browsers without requiring native binary dependencies.

***

## Capabilities [#capabilities]

* **Zero-Native Setup**: WebAssembly build ensures cross-platform runtime execution across browser and server environments.
* **Typed Schema Access**: High-level TypeScript interfaces for document state, elements, strokes, backgrounds, blocks, and charter tables.
* **Browser & Node Support**: Supports browser `File` / `Blob` inputs, `ArrayBuffer` serialization, and server-side file streams.