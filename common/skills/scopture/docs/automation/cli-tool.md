# Command-Line Interface (/docs/automation/cli-tool)



The Scopture desktop package includes the `scopture-cli` executable. It can open the desktop app, inspect local `.duc` files, and access remote drawings using your authenticated account.

## Install with the Desktop App [#install-with-the-desktop-app]

Install [Scopture desktop](/download), then launch the app once. Scopture installs the CLI and renderer into its user command directory and adds it to your shell PATH. Open a new terminal after the first launch. The preparation screen installs the locked Python tools into user storage. Desktop updates reuse the environment when its profile is unchanged and reuse cached packages when dependencies change.

On installation and after a desktop update, Scopture also syncs its `duc`, `scopture`, and `scopture-cli` agent skills from the skill pack bundled at build time into `~/.agents/skills`. Other skill folders are preserved. An unsuccessful sync is retried on the next launch.

```bash
scopture --version
scopture --help
```

## Open and Inspect a Drawing [#open-and-inspect-a-drawing]

Open a local file in the desktop app:

```bash
scopture ./assembly.duc
```

Inspection commands read the file directly and do not require a cloud account:

```bash
scopture drawing get ./assembly.duc --json
scopture elements list ./assembly.duc --element-type model --json
scopture files list ./assembly.duc --json
scopture cat ./assembly.duc
```

Rename the drawing by changing its charter title. This updates the name stored in a local `.duc` file or a remote drawing; it does not rename the local file on disk:

```bash
scopture charter rename ./assembly.duc "Assembly Rev B"
scopture charter rename <drawing-id> "Cloud Assembly Rev B"
```

`cat` streams one element per line as NDJSON. Use `--json` for a structured response envelope or `--raw` for the unwrapped JSON value from other commands. JSON success and failure responses go to stdout; human errors go to stderr. Element lists return arrays and SQL reads return `rows_count`/`rows` on both local and remote targets. Use `scopture <command> --help` for that command’s arguments.

## Use a Remote Drawing [#use-a-remote-drawing]

Sign in through the desktop app, then check whether the CLI can use its stored session:

```bash
scopture auth status
scopture drawing list --json
scopture drawing get <drawing-id> --json
```

Authentication resolves in this order: `--token`, the `SCOPTURE_TOKEN` environment variable, then the operating system credential store used by the desktop app. Remote commands retain drawing and integration permission checks. Cloud execution requires an eligible plan in the drawing’s organization and available execution allowance.

## Query or Run Python [#query-or-run-python]

```bash
scopture run-sql ./assembly.duc "SELECT id, element_type FROM elements LIMIT 10" --json
scopture run-python ./assembly.duc --file ./inspect_model.py --json
```

Use `run-sql --mutate` for an intended SQL write. Local Python uses the same managed Python 3.12 environment as the desktop app, with dependencies locked from the sandbox profile. The CLI can prepare it without opening the app; first setup needs an internet connection, and completed environments work offline. uv reuses its normal package cache while keeping Python and its environment in Scopture’s user storage. Host Python and user site-packages are excluded. `SCOPTURE_PYTHON_PATH` and `SCOPTURE_PYTHON_WORKER_PATH` are available only in development builds.

For a local `.duc` file, both commands work offline without signing in once Python setup is complete. Local SQL runs directly in the CLI and needs no Python setup.

For a remote drawing ID, both commands start a local worker even with the desktop app closed. Sign in and stay online to download the authorized snapshot and commit any changes. Add `--server` to either command to run the job on Scopture’s cloud. The CLI reports missing sign-in, denied access, and exhausted cloud allowance. See [Python Sandbox](/docs/automation/python-sandbox) for execution details.

Model scripts use the same [`emit_output(...)` contract](https://duc.ducflair.com/docs/concepts/elements/model-element) as the desktop and cloud runtimes. Human output includes Python stdout/stderr; use `--json` to inspect artifact envelopes. `--model-output-kind none` suppresses artifacts, including explicit `emit_output` declarations, while preserving prints and drawing updates.

## Apply a Drawing Patch [#apply-a-drawing-patch]

```bash
scopture update-drawing <drawing-id> ./patch.json --json
cat patch.json | scopture update-drawing <drawing-id> - --no-wait --json
scopture check-job <job-id> --wait-ms 10000 --json
```

Send complete records in collections such as `elements` and `layers`. Existing IDs replace their records, new IDs add records, and omitted records stay in the drawing. The command submits the patch to the cloud sandbox for validation and commit. For local files or patches constructed in code, use `run-python`.

The CLI waits briefly for remote jobs and prints the existing job ID if more time is needed. Use `check-job` to resume polling that ID. A conflict means the drawing changed after the worker read it. Inspect the latest drawing before preparing another update.

## Create and Render [#create-and-render]

```bash
scopture drawing create --name "Assembly" --out ./assembly.duc
scopture drawing create --name "Cloud assembly"
scopture render ./assembly.duc --width 1600 --height 1200 -o canvas.png
scopture render ./assembly.duc --viewport 100 200 800 600 --width 1600 --height 1200 -o viewport.png
scopture render <drawing-id> --element <model-id> --view top -o model.png
scopture render <drawing-id> --element <model-id> --view-config ./view.json -o model-custom.png
```

Omit `--out` on `drawing create` to create a remote drawing. Render targets accept local paths or remote IDs. `--viewport` selects scene coordinates; `--width` and `--height` set output pixels. Model view options require `--element`. The view JSON supports camera, display, material, clipping, and explode settings.

Whole-canvas snapshots reuse saved model thumbnails. Explicit model renders evaluate their geometry for the requested camera; missing canvas previews are generated with bounded concurrency and cached locally. Local CAD exports accept `--element <model-id>` for STEP, STL, IFC and the other supported geometry formats. `active-3d-model` also needs an explicit element when multiple models exist. `diff` accepts local paths and remote drawing IDs; remote comparisons download authorized snapshots into temporary storage. `--server` applies to remote Python and SQL targets.

STL exports accept optional tessellation settings on local and remote targets:

```bash
scopture export ./assembly.duc --element <model-id> --format stl --tolerance 0.2 --angular-tolerance 0.5 -o preview.stl
```

Larger settings produce fewer triangles and a coarser surface approximation. Angular tolerance is in radians. Generated STL exports default to linear setting `0.01` and angular setting `0.25`; use `--tolerance 0.001 --angular-tolerance 0.1` for the previous fine settings. These settings control tessellation, not the CAD source. A linked STL already contains triangles; use its original CAD source to control tessellation.

## Issue Lifecycle [#issue-lifecycle]

These commands accept a local `.duc` path or a remote drawing ID:

```bash
scopture issues create ./assembly.duc --title "Inspect mount" --content "Check fatigue" --json
scopture issues close ./assembly.duc <issue-id>
scopture issues reopen ./assembly.duc <issue-id>
scopture issues dismiss ./assembly.duc <issue-id> --reason "Duplicate"
scopture issues update ./assembly.duc <issue-id> --title "Inspect revised mount"
```

Status changes append timestamped entries to the Issue conversation. Reopening or closing preserves the last dismissal reason, while each dismissal event keeps its own reason. Remote Issue updates use the Issue service and its permission checks; SQL writes to drawing content do not update remote Issue records.