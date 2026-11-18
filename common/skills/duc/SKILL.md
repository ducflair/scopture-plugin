---
name: duc
description: "Use this skill whenever a DUC drawing (`.duc` file) needs to be read, written, searched, created, inspected, or manipulated programmatically with the Python `ducpy` library. This includes constructing elements, styles, layers, blocks, and states with fluent builders; querying the relational schema through `DucSQL`; streaming external-file or version payloads; and validating coordinate placement or drawing relationships."
---

# DUC Core Canvas Library Skill

The `ducpy` Python library provides a fast, developer-friendly interface to read, write, search, and manipulate `.duc` project-state files. Under the hood, a current `.duc` file is a **gzip-compressed SQLite database**.

This skill deliberately stays compact. Detailed API signatures, concepts, schema tables, and worked examples are bundled directly inside the relative `./docs/`, `./docs-ducpy/`, and `./docs-sql/` folders of this skill.

---

### Source-of-Truth Hierarchy

Agents must adhere strictly to this priority order:

1. **Runtime introspection of the installed `ducpy` package**
2. **Bundled `ducpy` API reference** (`./docs-ducpy/llms.txt`, `./docs-ducpy/*.md`)
3. **Bundled SQLite schema reference** (`./docs-sql/schema.md`, `./docs-sql/llms.txt`)
4. **Bundled DUC concept guides** (`./docs/llms.txt`, `./docs/*.md`)
5. **Existing worked examples** (`./docs-ducpy/examples.md`)

> [!IMPORTANT]
> **Runtime Introspection & Verification Rule**
> Runtime introspection remains #1 because the installed package version might differ.
> **Rule**: *Never invent a `ducpy` method, parameter, return type, schema column, or builder stage. Retrieve the version-matched reference from the local docs or runtime introspection before generating implementation code.*

> [!TIP]
> **Runtime Environment for Testing & Introspection**
> Use `scopture run-python <file.duc>` via the CLI (or `run_python_code` via MCP) to test code and introspect `ducpy` against a real drawing. It has the full engineering stack pre-installed and is read-only unless `update_drawing(...)` is called. Don't set up a local Python environment.

---

## Key Design & Code Standards

* **Coordinate System & Units**: `x` and `y` are the element's top-left canvas position. Positive X extends rightward and positive Y extends downward. Linear, arrow, and freedraw points are local to that element origin. Angles are radians, and coordinates and dimensions use the element's declared scope.
* **Current File I/O Contract**: `parse_duc()` accepts a filesystem path and returns recursively wrapped `DucData` dictionaries with flattened snake_case fields. `serialize_duc()` writes a `.duc` file and returns its path; it does not return drawing bytes.
* **In-Place Mutation**: Use `duc.mutate_element()` for builder-created `ElementWrapper` or dataclass objects. Parsed `DucData` elements are dictionaries and should be edited through their existing fields. Never destroy and recreate an element merely to update it, because doing so can lose IDs, memberships, bindings, and other relationships.
* **Binding Preservation**: Preserve existing element IDs, `bound_elements`, group/region/block memberships, `frame_id`, `layer_id`, and instance relationships during edits.
* **Strict Builder Methods**: Methods are stage-specific. Confirm the active builder class and installed-version signature before invocation.
* **Modular Model Elements (Components & Assemblies)**: When creating complex 3D models or assemblies, do not write a single monolithic script. Break the design into modular Model Elements:
  - **Parameters**: Elements defining dimensions, configuration values, or domain rules.
  - **Component Geometry**: Elements providing reusable geometric parts or helper functions without calling `emit_output(...)`.
  - **Assembly Root**: A top-level Model Element that imports components using `from duc_model.<element_id> import ...`, combines them into an assembly, and calls `emit_output(..., kind="parametric")` once.
  Refer to [Model Modularization](./docs/concepts/model-modularization.md) for dependency graphs, patterns, and `duc_model` import conventions.
* **Section Views via `viewerState` (Non-Destructive Clipping)**: Never perform boolean subtraction cuts on 3D CAD models (e.g. subtracting a cutting block in code) just to generate a section view or cutaway. Instead, configure the view state: set `viewer_state.clipping` (or `with_viewer_state(...)` with active X, Y, or Z clipping planes) on the Model Element. The 3D viewer renders the dynamic cross-section cut while keeping the underlying CAD model geometry complete, intact, and ready for fabrication or export. Refer to [Model Element](./docs/concepts/elements/model-element.md).
* **Styling Elements (Default Fill & Stroke)**: When generating 2D CAD elements, always explicitly define styles with a default fill (background) or stroke; do not assume they are applied automatically. Refer to [Styling Elements](https://duc.ducflair.com/docs/guidelines/styling-elements) for constructing ordered `backgrounds` and `strokes` arrays using `duc.create_simple_styles`.
* **No Duplicated API Reference**: Do not add volatile builder examples, serialization snippets, or schema catalogs to this skill. Improve the corresponding Duc documentation instead so `llms.txt` remains the maintained source.

---

## Additional Adapter References

For Scopture execution, consult [Python Sandbox](../scopture/docs/automation/python-sandbox.md). `emit_output`, drawing snapshot/patch helpers and `duc_model` imports belong to that host runtime, not standalone `ducpy`.

The general DUC and `ducpy` routes above remain the primary sources. Use these versioned adapter references when a task targets another DUC interface:

- **SQL schema**: `https://ducflair.github.io/duc/reference/sql/`
- **Rust (`duc`)**: `https://ducflair.github.io/duc/reference/rust/duc/`
- **TypeScript / JavaScript (`ducjs`)**: `https://ducflair.github.io/duc/reference/typescript/`
- **PDF (`ducpdf`)**: `https://ducflair.github.io/duc/reference/pdf/`
- **SVG (`ducsvg`)**: `https://ducflair.github.io/duc/reference/svg`
