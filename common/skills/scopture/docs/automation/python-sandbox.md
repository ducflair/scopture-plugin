# Python Sandbox (/docs/automation/python-sandbox)



Scopture’s Python sandbox runs Model Elements and drawing automation in a managed **Python 3.12** environment. Use it to compute geometry, analyse engineering models, produce visual results and apply deliberate drawing updates.

## Where Code Runs [#where-code-runs]

* **Desktop:** the installed local sandbox is the default for both local and remote drawings, including background output and thumbnail generation. Remote drawing access still requires authorization.
* **CLI:** `scopture run-python` starts its own worker from the installed runtime profile while the desktop app is closed. It works offline with a local `.duc` after setup. A remote drawing ID still needs a session and network access. Pass `--server` with a remote ID to opt into cloud compute.
* **Browser and mobile:** an authorized cloud drawing on an entitled paid plan uses the server worker. Offline Python execution requires desktop.

Desktop and server derive their dependencies from the same sandbox `pyproject.toml` and lockfile and use the same worker implementation. Native wheels, operating-system libraries and graphics backends still require platform-specific verification.

Desktop jobs wait in a local queue. Up to four workers run at once, reduced according to available CPU and memory while reserving resources for the app. Queued jobs do not fail just because all worker slots are occupied.

The desktop installer includes uv and a locked runtime profile. First preparation installs Python and its dependencies into Scopture’s user storage. Later launches reuse the prepared environment offline; updates reuse unchanged environments and [uv’s package cache](https://docs.astral.sh/uv/concepts/cache/). Scopture does not install packages into your host Python or use arbitrary user site-packages. Development uses the workspace `ducpy`; distribution builds resolve and lock the published version when packaging.

## Two Execution Contexts [#two-execution-contexts]

A **Model Element** runs its Python source and imports drawing-local dependencies. Its output is a persisted artifact, separate from its source and thumbnail. Saved output can be viewed without re-executing the model.

A **drawing-level job**, invoked through the CLI or MCP, receives a drawing snapshot and can inspect or patch the document. Reading the drawing and emitting an output do not themselves modify it: call `update_drawing(...)` for an intended change.

### Submitting and Polling Jobs [#submitting-and-polling-jobs]

MCP `run_python_code` returns a `jobId`; `waitForCompletionMs` defaults to `0`. Submit once and poll that ID with `check_python_run_job` until it completes or fails. Each polling call waits at most 15 seconds, even when a longer wait is requested. Drawing updates commit in the background. Keep the same job ID while it is queued, running, or applying. The CLI polls automatically and prints the ID for `scopture check-job` if the job takes longer than its wait.

Python patch jobs retain an immutable base and merge into the latest saved drawing after validation. Unrelated records and unchanged values, including regenerated output and dimensions, are preserved; overlapping edits report the affected record. SQL snapshot replacements still require the exact base revision. A known editor’s save failure blocks a drawing commit. If the collaboration service is unreachable, the commit uses the saved snapshot and conditional storage writes and returns a synchronization warning.

Import installed libraries explicitly and declare model output:

```python
from build123d import Box
emit_output(Box(20, 10, 5), kind="parametric")
```

## Embedded Methods and Values [#embedded-methods-and-values]

| Interface                                                   | Purpose                                                                                                                                               |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `emit_output(value, kind=..., mime_type=..., filename=...)` | Declare the rendering root’s output. Use one output per root.                                                                                         |
| `get_svg_from_mermaid(source, css="")`                      | Render Mermaid with Pele and return a standalone SVG string.                                                                                          |
| `show(*objects, **options)`                                 | Compatibility helper for supported CAD/IFC objects, including `ocp_vscode.show`. Prefer explicit `emit_output` for new scripts.                       |
| `get_drawing()`                                             | Return current `.duc` bytes when the job has a drawing snapshot; it is not a drawing metadata dictionary.                                             |
| `update_drawing(patch)`                                     | Serialize and validate an intended drawing patch, then merge records by ID. Omitted records remain. Rendering and export jobs reject drawing updates. |
| `get_external_files(*file_ids)`                             | Return a dictionary of mounted file IDs to byte payloads.                                                                                             |
| `resolve_external_file(file_id)`                            | Return the mounted workspace path for a file ID.                                                                                                      |
| `external_files`                                            | Mounted file metadata indexed by ID; entries include a workspace `path`.                                                                              |
| `drawing_files`                                             | Drawing file metadata supplied to the job.                                                                                                            |
| `FontEnum([...])`                                           | Declare a font selection parameter with iteration, key access, and identifier-safe attributes.                                                        |
| `resolve_font(family)`                                      | Return a mounted font’s local TTF path for libraries requiring a filename.                                                                            |
| `duc_model.<stable-module-name>`                            | Import values and functions from another Python Model Element in this drawing.                                                                        |

File helpers only expose inputs mounted for the current job. Drawing snapshot helpers require that context; do not assume a standalone Model Element run receives a complete drawing file.

`ducpy.parse_duc()` is path-based. To inspect snapshot bytes, write them to a workspace `.duc` path and parse that path. Use `ducpy`’s installed API reference for builders and serialization, rather than assuming sandbox helper names are `ducpy` methods.

### Fonts [#fonts]

```python
FONTS = FontEnum(["Noto Sans", "Roboto"])
family = FONTS.Noto_Sans  # also FONTS["Noto Sans"] or iteration over FONTS
font_path = resolve_font(family)
```

The selected TTF must be mounted for the job; declaring a name does not install a font. `resolve_font` raises an error when that family is unavailable. `build123d.Text(..., font=family)` resolves the mounted TTF automatically; other libraries can use the returned path directly.

## Output Contract [#output-contract]

| `kind`       | Viewer/output                                             |
| ------------ | --------------------------------------------------------- |
| `parametric` | Supported B-Rep/mesh objects or a tessellated CAD preview |
| `ifc`        | IFC model                                                 |
| `dxf`        | DXF drawing                                               |
| `image`      | Raster image bytes or a workspace image path              |
| `svg`        | SVG markup/bytes or a workspace SVG path                  |
| `pdf`        | PDF bytes or a workspace PDF path                         |
| `table`      | Structured table data                                     |

A logic-only parameter/helper module needs no output. Imported dependencies’ `show(...)` and `emit_output(...)` calls do not replace the root output. HTML and video are not Model Element output kinds; keep them as explicit file assets where appropriate. See the [Model Element output contract](https://duc.ducflair.com/docs/concepts/elements/model-element) for supported values and envelope details.

```python
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

force_n = 80.0
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot([0, 1, 2], [0, force_n / 2, force_n])
ax.set(xlabel="Time / s", ylabel="Force / N")
output = io.BytesIO()
fig.savefig(output, format="png")
plt.close(fig)
emit_output(output.getvalue(), kind="image", mime_type="image/png", filename="force.png")
```

### Emit a Mermaid Diagram [#emit-a-mermaid-diagram]

Pass Mermaid source to the built-in `get_svg_from_mermaid` helper, then emit the returned SVG as your Model Element’s output:

```python
svg = get_svg_from_mermaid("""
    flowchart LR
    A[Plan] --> B[Build]
    B --> C[Review]
""", css="--pele-surface: #e5eeff; --pele-border: #2457a6;")
emit_output(svg, kind="svg", filename="workflow.svg")
```

Pele runs inside the sandbox without any imports or external runtime setup. The helper removes common indentation and trims surrounding whitespace, so multiline strings can start on a blank line. Invalid Mermaid fails the run with the parser’s message, line, column, and source excerpt when available.

The SVG uses the Scopture theme by default. The optional `css` argument accepts inline `--pele-*` variable declarations up to 4 KiB. Pass declarations directly, without selectors or braces. Variables you omit keep their default values.

## Reuse Geometry in Simulations [#reuse-geometry-in-simulations]

Keep the mechanical model in one Model Element. Import its actual solids, meshes, dimensions or functions from each study, then emit that study’s own image or table. Avoid copying the source assembly into every simulation.

Use the editor’s import completion to insert the stable module name; IDs containing punctuation use an encoded `element_...` name. Labels are readable aliases only when unambiguous. See [Model Parameters](/docs/concepts/model-parameters) and [Model Modularization](https://duc.ducflair.com/docs/concepts/model-modularization).

```python
# In a study; replace the module name with the source model's stable name.
from duc_model.geometry import shaft, shaft_diameter
```

In this example the source Model Element must have the stable ID `geometry` and export both names. Prefer reusable definitions and values in shared modules; each consuming study owns its calculation assumptions and output.

## Drawing Updates [#drawing-updates]

Submit complete changed records, including element revision fields, to the MCP `update_drawing` tool or CLI `update-drawing` command when the patch is already JSON. For scripted changes, call the injected `update_drawing({"elements": [...]})` helper. The helper accepts a state dictionary, a compatible `ducpy` object, or valid `.duc` bytes. Dictionary and object inputs pass structural validation before embedded code executes. Matching IDs update existing records, new IDs add records, and omitted records remain unchanged. Preserve existing IDs and memberships; do not submit the entire drawing merely to change one item. Inspect the result, then render it for visual QA.

## Capability mapping [#capability-mapping]

| Capability                               | Expected result                                                               | Python package(s)                                 |
| ---------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------- |
| CAD solids / STEP                        | Parametric geometry, B-Rep, STEP import/export                                | `build123d, cadquery-ocp`                         |
| BIM / IFC                                | Building objects and properties                                               | `ifcopenshell`                                    |
| 2D CAD / DXF                             | Layers, blocks, entities and drawings                                         | `ezdxf`                                           |
| Mesh generation                          | Surface/volume mesh, B-Rep meshing, physical groups                           | `netgen-mesher` / `gmsh`                          |
| Mesh conversion                          | FEM/CFD format and field exchange                                             | `meshio`                                          |
| Geometry QA                              | Watertightness, 3D manifold booleans, topology, intersections                 | `trimesh, manifold3d, shapely, rtree`             |
| 3D simulation images                     | Mesh/scalar fields, slices, streamlines, PNG screenshots                      | `pyvista`                                         |
| Interactive simulation views             | Standalone HTML assets; Model viewers do not execute HTML                     | `plotly`                                          |
| Simulation animations                    | Rendered frame sequences; GIF and MP4 through the bundled encoder             | `imageio, imageio-ffmpeg`                         |
| Point-cloud registration                 | Denoise, align and compare scans                                              | `open3d, laspy`                                   |
| GIS / site data                          | Vector queries, coordinate systems                                            | `geopandas, pyproj`                               |
| Terrain rasters                          | DEM and geospatial raster I/O                                                 | `rasterio`                                        |
| Section properties                       | Area, inertia, torsion, warping, plastic moduli                               | `sectionproperties`                               |
| Frame / truss / plate FEA                | Member forces, reactions, deflection, P–Delta, tension/compression-only       | `PyNiteFEA`                                       |
| Structural modes / linear buckling       | Generalized eigenmodes and linearized stability                               | `scikit-fem, scipy`                               |
| Geotechnical springs                     | Idealized Winkler foundation, mat subgrade and nodal spring response          | `PyNiteFEA, scipy`                                |
| Multibody dynamics / flexible contact    | Rigid/flexible bodies, joints, collisions, nonlinear time-history integration | `exudyn`                                          |
| Custom FEM / 3D linear elasticity        | Weak forms, 3D linear stress and modal prototypes                             | `scikit-fem`                                      |
| Nonlinear 3D solid mechanics (prototype) | Large deformations, hyperelasticity, automatic differentiation, continuation  | `felupe, scikit-fem`                              |
| Sparse PDE linear systems                | Krylov solvers, sparse assembly and multigrid preconditioning                 | `scipy, pyamg`                                    |
| Optimized numerical kernels              | JIT-compile custom CPU numerical loops                                        | `numba, numpy`                                    |
| Fatigue screening                        | Rainflow cycles, S–N life, cumulative damage                                  | `pylife, rainflow`                                |
| Structural criterion checks              | Evaluate engineer-approved allowables                                         | `numpy, pint`                                     |
| Topology prototypes                      | Explore candidate layouts, not final designs                                  | `scikit-fem, pymoo`                               |
| Pipe / duct sizing                       | Pressure drops, friction, flow correlations                                   | `fluids, scipy`                                   |
| Incompressible CFD                       | 2D/3D Navier—Stokes, velocity and pressure fields                             | `phiflow`                                         |
| Lattice Boltzmann CFD                    | 1D/2D/3D numerical flow simulations                                           | `pylbm`                                           |
| CFD-to-heat prototype                    | Script fluid boundary fields into solid heat PDE                              | `phiflow, FiPy`                                   |
| Heat exchangers                          | Heat-transfer correlations and sizing                                         | `ht, fluids`                                      |
| Fluid properties                         | Enthalpy, density, phase properties                                           | `CoolProp, thermo`                                |
| Refrigeration / heat pumps               | Refrigerant cycle and state calculations                                      | `CoolProp, ht`                                    |
| Ground-source heat pumps                 | Borehole field thermal response                                               | `pygfunction`                                     |
| Psychrometrics                           | Dew point, humidity, moist-air enthalpy                                       | `psychrolib, CoolProp`                            |
| Transient heat / transport PDE           | Finite-volume diffusion, advection and reaction terms                         | `FiPy`                                            |
| Reaction kinetics / combustion           | Chemical equilibrium, species, reactors                                       | `cantera`                                         |
| Smoke tracer prototype                   | Advection—diffusion of prescribed species (not fire CFD)                      | `FiPy`                                            |
| Room acoustics                           | Reverberation, impulse responses                                              | `pyroomacoustics`                                 |
| Water networks                           | Pipe flow, pressure and network quality                                       | `wntr`                                            |
| Stormwater / sewer hydraulics            | Rainfall, runoff, routing and sewer flows                                     | `pyswmm, swmm-toolkit`                            |
| Groundwater time-series                  | Simulate and calibrate groundwater heads over time                            | `pastas`                                          |
| Groundwater PDE (prototype)              | Script Darcy flow with prescribed hydraulic coefficients                      | `scikit-fem, scipy`                               |
| Flood modelling (2D)                     | Shallow-water overland depth, velocity, extent                                | `landlab` ; `anuga` is an excluded optional extra |
| Bridge scour screening                   | Calculate approved empirical envelopes                                        | `numpy, scipy`                                    |
| Solar PV                                 | Irradiance and photovoltaic yield                                             | `pvlib`                                           |
| Solar shadow screening                   | Solar positions and ray/geometry intersection                                 | `pvlib, trimesh, manifold3d`                      |
| Daylight simulation                      | Ray-traced illuminance, daylight factor and glare metrics                     | `pyradiance`                                      |
| Simple building thermal model            | Scripted thermal RC-network energy balances                                   | `scipy, control`                                  |
| Whole-building energy simulation         | Dynamic multizone building energy and HVAC simulation                         | `pyenergyplus-lbnl`                               |
| Battery simulation                       | Cell electrochemistry, charge/discharge and aging models                      | `pybamm`                                          |
| RF / microwave networks                  | S-parameters, signal-chain and transmission-line analysis                     | `scikit-rf`                                       |
| Electromagnetic fields (prototype)       | 3D Maxwell FDTD wave propagation                                              | `fdtd`                                            |
| Electrical power flow                    | AC/DC networks and faults                                                     | `pandapower`                                      |
| Energy-grid optimization                 | Generation, storage, LP/MILP dispatch studies                                 | `pypsa, highspy`                                  |
| Controls                                 | State space, stability and response                                           | `control, scipy`                                  |
| Sensor analysis                          | Filter, align and assess time series                                          | `pandas, scipy`                                   |
| Sensitivity                              | Sobol, Morris and input influence                                             | `SALib`                                           |
| Uncertainty / reliability                | Uncertainty propagation and reliability                                       | `openturns`                                       |
| Constrained optimization                 | LP/MILP/QP/conic solvers and multiobjective Pareto search                     | `scipy, highspy, clarabel, pymoo`                 |
| Multidisciplinary optimization           | Coupled models and derivatives                                                | `openmdao`                                        |
| One-way fluid-to-structure prototype     | Apply computed fluid loads to scripted elastic model                          | `phiflow, scikit-fem`                             |
| Manufacturability screening              | Offsets, thickness and manifold geometry checks                               | `build123d, trimesh, manifold3d`                  |
| Scan-based inspection                    | Compare measured cloud with model                                             | `open3d, laspy`                                   |
| Units / dimensions                       | Convert quantities, detect unit errors                                        | `pint`                                            |
| Basis / evidence schema                  | Implement typed records and validation                                        | `pydantic`                                        |
| T0–T3 scoring                            | Implement evidence levels and dependency caps                                 | `pydantic, networkx`                              |
| Content-addressed evidence               | Canonical JSON and cryptographic hashes                                       | `rfc8785` (plus stdlib `hashlib`)                 |
| Provenance                               | Trace sources, calculations and dependencies                                  | `prov, networkx`                                  |
| Portable evidence packages               | Export interoperable research records                                         | `rocrate`                                         |
| Digital signatures                       | Sign and verify evidence payloads                                             | `cryptography`                                    |
| Reproducible workflows                   | Execute analysis DAGs and reruns                                              | `snakemake`                                       |
| Verification tests                       | Benchmarks, property tests and regressions                                    | `pytest, hypothesis, pytest-benchmark`            |
| Engineering reports / 2D plots           | Graphs, heatmaps, PDF, DOCX and spreadsheets                                  | `matplotlib, typst, python-docx, openpyxl`        |

This is a capability map for the declared library families, not a claim that every workflow is a turnkey solver. The project includes these families in the shared base environment. ANUGA (`flood-gpl`) is optional and excluded from both standard desktop and server profiles. Consult the selected package’s own license and API when preparing a worker or distributing results.

## Visual Results and Runtime Limits [#visual-results-and-runtime-limits]

Use [Matplotlib](https://matplotlib.org/stable/users/explain/figure/backends.html) with `Agg` for PNG/SVG charts, and [PyVista](https://docs.pyvista.org/) for off-screen mesh/field screenshots. Plotly can generate standalone HTML; [Kaleido static export requires Chrome/Chromium](https://plotly.com/python/static-image-export/), which is not a dependency of this Python profile.

Jobs run in worker processes with network, subprocess and sensitive-host-path guards. The process adapter permits the locked environment’s bundled FFmpeg, Radiance and EnergyPlus executables; arbitrary shell commands, Python child processes and network sockets remain blocked. Snakemake workflows that launch arbitrary external commands require a separate worker. Use `from Pynite import FEModel3D` for PyNiteFEA and `import phi` for PhiFlow; their distribution names differ from their import names.

Headless Linux images also need the native shared libraries required by their wheels, including OpenGL/X11 and OpenMP where applicable. Open3D’s Linux wheels require a sufficiently new glibc. Large native stacks belong in container-backed workers rather than ordinary Lambda zip deployments. These constraints are part of deployment verification, not capabilities Python dependencies alone can guarantee.

The numerical libraries enable custom finite-element, finite-volume, CFD, thermal and optimization workflows. They do not supply a validated general industrial turbulence, plasticity/contact, aquifer, fire or two-way fluid/structure solver. Define inputs, units, mesh, boundary conditions and numerical methods explicitly; check convergence and benchmark results before using them for engineering decisions. Library availability indicates computability, not physical validation, standards compliance or an authorized design release.