Scopture connects an AI assistant directly to physical engineering projects, CAD models, and collaborative technical drawings. Instead of treating engineering projects as static files, it gives the assistant real-time visibility and editing control over the entire design canvas and its underlying engineering data.

Here is what you can do with Scopture:

- Create and modify 3D CAD and BIM models: Generate parametric mechanical parts, brackets, enclosures, and multi-component assemblies using build123d. Generate IFC-compliant building models, structural frames, walls, slabs, and MEP routing using IfcOpenShell.
- Draft and edit 2D engineering drawings: Create schematics, wiring diagrams, piping and instrumentation diagrams (P&IDs), architectural floor plans, and annotations. Import, inspect, and export DXF and DWG vector data for CNC or laser fabrication.
- Run engineering simulations and drawing-level Python code: Execute Python scripts equipped with engineering and scientific libraries like NumPy, SciPy, SymPy, Matplotlib, and Pint. The runtime has visibility over the entire drawing, allowing the assistant to calculate clearances, coordinate multi-element alignments, generate plots, and batch-update geometry across the entire project.
- Generate technical documentation: Compile calculation reports, specification summaries, and engineering data sheets directly alongside drawing elements using PDF rendering.
- Pin and track visual issues: Inspect open action items, navigate reviewer feedback, and pin new issues directly to specific 3D components or 2D drawing coordinates (for example, flagging a shaft misalignment on a gearbox or questioning a clearance issue).
- Trace project charters, requirements, and decisions: Review architectural constraints, project goals, and documented engineering decisions directly attached to drawings, ensuring modifications remain aligned with original requirements.
- Inspect and query project containers directly: Query the underlying relational SQLite database within .duc project files, extracting component lists, spatial coordinates, layers, and project history via SQL.
- Perform visual quality assurance: Capture canvas screenshots, inspect rendered geometry, and visually verify that generated assemblies and dimensions match user specifications before finalizing changes.

Typical tasks you can ask the assistant to perform include:

"What's the current state of the project?"
"Pin an issue to the gearbox asking whether the latest mount change affected shaft alignment or clearances."
"Add a luxury hotel reception to the Empire State on a new drawing and verify the 3D model."
"Review the current drawing canvas and identify any structural or clearance conflicts."
"Add a custom mounting bracket to an existing motor assembly and verify shaft alignment."
"Generate an IFC-compliant structural grid on a new drawing sheet."
"Pin an issue to a specific mechanical part asking the team to verify thermal expansion tolerances."
"Run a calculation script across the drawing to size ductwork and automatically update the corresponding schematic labels."
"Extract a bill of materials and component schedule by querying the project container."


Github plugin repository: https://github.com/ducflair/scopture-plugin
MCP server endpoint: https://api.scopture.com/mcp
