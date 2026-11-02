# Versions and Revisions (/docs/concepts/versions-and-revisions)



## Drawing History in Scopture [#drawing-history-in-scopture]

Scopture exposes a drawing’s history so reviewers can preserve milestones, inspect earlier states, and recover from an unwanted change. Create a named checkpoint before a formal review, approval, handoff, major import, or other boundary that should remain easy to identify.

Name the event or accepted state rather than the person who created it, for example, “Coordination review accepted” or “Before structural model revision.”

## Preview Before Restoring [#preview-before-restoring]

Preview a historical state to confirm that it contains the intended drawing, project context, and referenced artifacts. Restore it only when the active drawing should continue from that point. Restoration is permission-controlled and is different from ordinary canvas undo.

Scopture also records bounded background and agent operations in drawing history. This makes an automated change inspectable and recoverable through the same application workflow as other project changes.

Desktop file recovery is separate from drawing history. The `.duc` file is the durable local save; temporary application storage retains pending edits for crash recovery. When reopening a file with pending edits, choose whether to restore the recovered state or open the saved file. See [Local Saves and Recovery](/docs/concepts/drawings-sharing-and-export#local-saves-and-recovery).

## Source-File Revisions [#source-file-revisions]

A source-file revision and a drawing-history entry serve different review tasks. Replacing or revising an IFC, STEP, DXF, PDF, or other referenced asset updates the source being examined; a drawing checkpoint preserves the broader Scopture context around it.

Keep the revised source associated with the same review narrative, then create a checkpoint when the project reaches a meaningful state. Existing issues and decisions can then be evaluated against the changed artifact without treating its context as disposable.

The version graph, checkpoints, deltas, restoration rules, external-file records, and active revision mechanics are Duc format concerns. See [Version Control](https://duc.ducflair.com/docs/concepts/version-control) and [External Files & Revisions](https://duc.ducflair.com/docs/concepts/external-files) for those details.