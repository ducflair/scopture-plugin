# Setup & Quick Start (/docs/get_started/setup)



## Installation [#installation]

The `duc` ecosystem provides dedicated SDKs and tools for TypeScript, Python, Rust, and file format conversion workflows.

### TypeScript / JavaScript (`ducjs`) [#typescript--javascript-ducjs]

Install `ducjs` via your preferred package manager:

```bash
bun add ducjs
# or
npm install ducjs
```

`ducjs` uses an embedded WebAssembly SQLite engine, enabling `.duc` file reading and writing across Node.js, Bun, Deno, and web browsers without native binary compilation.

### Python (`ducpy`) [#python-ducpy]

Install `ducpy` via `uv` or `pip`:

```bash
uv add ducpy
# or
pip install ducpy
```

### Rust (`ducrs`) [#rust-ducrs]

Add `duc` to your `Cargo.toml`:

```toml
[dependencies]
duc = "*"
```

***

## Interoperability Packages [#interoperability-packages]

The repository provides format converters for integrating `.duc` with industry standards:

| Package  | Format | Purpose                                   |
| -------- | ------ | ----------------------------------------- |
| `ducpdf` | PDF    | Vector PDF export and PDF text extraction |
| `ducsvg` | SVG    | Bidirectional SVG import and export       |

{/* | `ducdxf` | DXF | AutoCAD DXF file interchange import and export | */}