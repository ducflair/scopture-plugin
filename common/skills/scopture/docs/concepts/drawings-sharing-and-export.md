# Drawings, Sharing, and Export (/docs/concepts/drawings-sharing-and-export)



## Local and Remote Drawings [#local-and-remote-drawings]

Scopture supports desktop local files and remote drawings with the same underlying `.duc` project state:

| Feature             | Local drawing                                        | Remote drawing                                                                            |
| ------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Primary storage** | A real `.duc` file on the desktop filesystem         | Scopture cloud storage within an organization                                             |
| **Offline work**    | Solo desktop editing and native Python execution     | Temporary local recovery state; shared operations and remote compute require connectivity |
| **Collaboration**   | Single-device working state                          | Live collaborators, presence, shared issues, and managed access                           |
| **Access**          | Controlled by access to the device and exported file | Controlled through roles, direct access, organization access, and public links            |

A local drawing can be moved to the cloud when the drawing and its required assets are available for upload. A local filesystem path does not grant the cloud access to that file.

### Client Access [#client-access]

| Client and drawing                                     | Editing and saves                                    |
| ------------------------------------------------------ | ---------------------------------------------------- |
| Desktop local drawing                                  | Solo editing; filesystem `.duc` saves                |
| Free browser access to public or community drawings    | Read-only                                            |
| Browser local file                                     | Read-only; no offline editing or durable local saves |
| Mobile local folders and `.duc` files                  | Read-only                                            |
| Authenticated paid cloud drawing on a supported client | Cloud editing with the required drawing permission   |

Cloud access follows the plan of the drawing’s organization. A public link alone does not enable editing or compute.

## Local Saves and Recovery [#local-saves-and-recovery]

New desktop local drawings receive a `.duc` file in Scopture’s application data directory. **Reveal source in folder** opens the file’s location. **Save As** writes the drawing to a chosen path and updates the source location after the save succeeds.

Autosave and explicit saves write the native file. Scopture also keeps temporary state in the Origin Private File System (OPFS) for autosave recovery and reconciliation. This recovery copy is separate from the durable `.duc` file.

When a native file is reopened with pending recovered edits, Scopture offers **Restore recovered changes** or **Open saved file**. If another application or window changed the file on disk, Scopture refuses to overwrite that newer content until the states are reconciled. Keep a separate copy with **Save As** when both versions are needed.

On macOS, right-click Scopture’s Dock icon for **Open Recent** and **New Window**. Each window has its own drawing and menu actions.

***

## Workspace Organization [#workspace-organization]

The dashboard is the project entry point outside the canvas. It surfaces recent drawings and issue activity, while the file explorer organizes remote drawings in nested folders and provides search, movement, and trash recovery. Organization membership determines which shared workspace and files a person can reach.

Local drawings remain listed as device-resident work. They should not be treated as shared cloud files until they are explicitly moved to a remote workspace.

***

## External Files [#external-files]

When a drawing uses a PDF, image, document, spreadsheet, or engineering model, Scopture resolves the asset when it is displayed, reviewed, or exported. Desktop offline drawings can **Embed a copy** or **Link local file** when choosing a supported asset.

An embedded copy travels inside the saved `.duc`. A local link stores an explicit relative or absolute locator and omits that revision’s bytes from the native file. Relative links resolve against the owning `.duc` directory. **Save As** rebases them to keep pointing to the same files. Absolute links keep their native target path.

Local links require native permission to read the target. A missing or inaccessible reference offers **Locate file**, which lets you choose the replacement and grant access. Changes to a linked source update its input revision so dependent model output can regenerate. Carry linked files with the drawing, or embed them, when handing the project to another device. Local links are restricted to desktop offline drawings and are not mounted in remote Python jobs.

The storage structure, external-file identity, revisions, and active payload selection are defined by Duc rather than the Scopture interface. See [External Files & Revisions](https://duc.ducflair.com/docs/concepts/external-files) for those mechanics.

***

## Access and Collaboration [#access-and-collaboration]

Remote drawings support live presence and synchronized editing, including shared navigation and model-review context. Access can be granted directly to a person, inherited through an organization role, or provided through a public link.

Workspace permissions distinguish **view**, **comment**, **edit**, and **full** access. Effective editing also requires authentication and an entitled paid cloud plan. Public-link settings can additionally control:

* password protection;
* whether export is allowed;
* whether interactive 3D mode is available; and
* whether an unprotected drawing can be discovered.

Authenticated access takes precedence when a participant already has a stronger direct or organization permission. Use named access for ongoing collaborators and public links for clearly bounded external reviews.

***

## Import and Export [#import-and-export]

Scopture can export a portable `.duc` drawing or produce presentation and interchange outputs for narrower purposes:

* canvas, selection, view, crop, or plot output as PNG, SVG, or PDF;
* a text-based drawing representation when structured inspection is needed;
* supported engineering-model outputs whose available formats depend on the model type; and
* the source representation of supported code-generated models.

An image or PDF export communicates a view. A model export communicates geometry. A `.duc` export is intended for continuing with the drawing and its project context. Choose the output according to what the recipient must inspect or continue editing.

For what the portable file contains and how it is structured, see the [Duc architecture](https://duc.ducflair.com/docs/concepts/architecture).

<Callout type="warn" title="Sharing and export are separate permissions">
  Access to a public drawing does not necessarily allow its assets to be exported or its models to be opened in 3D. Configure those capabilities explicitly for the review being shared.
</Callout>