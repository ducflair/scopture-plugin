# Why DUC Exists (/docs/concepts/why-duc-exists)



Engineering projects do not move from design to delivery in a single pass.

Drawings and models are developed, reviewed, changed, and reviewed again. Each cycle creates new information around the design: references, annotations, external files, revisions, relationships, and application state.

The main design files usually survive. The structure connecting everything around them often does not.

## The recurring engineering cycle [#the-recurring-engineering-cycle]

<Mermaid
  chart="%%{init: {
  &#x22;flowchart&#x22;: {
    &#x22;curve&#x22;: &#x22;basis&#x22;,
    &#x22;nodeSpacing&#x22;: 50,
    &#x22;rankSpacing&#x22;: 55,
    &#x22;htmlLabels&#x22;: true
  }
}}%%

flowchart TB
    classDef blueNode fill:#EAF4FC,stroke:#54A0E2,stroke-width:3px,color:#1F2937;
    classDef greenNode fill:#EDF7F1,stroke:#52B755,stroke-width:3px,color:#1F2937;
    classDef orangeNode fill:#FDF3E7,stroke:#F5A642,stroke-width:3px,color:#1F2937;
    classDef ducNode fill:#F3EEFC,stroke:#8B5CF6,stroke-width:3px,color:#1F2937;

    subgraph EngineeringCycle[&#x22;Recurring engineering cycle&#x22;]
        direction LR

        A[&#x22;Design Intent<br/>Development&#x22;]:::blueNode
        B[&#x22;Design<br/>Review&#x22;]:::greenNode
        C[&#x22;Change and<br/>Delivery&#x22;]:::orangeNode

        A --> B
        B --> C
        C -->|&#x22;Next revision&#x22;| A
    end

    D[&#x22;.duc document&#x22;]:::ducNode

    EngineeringCycle -.-> D

    style EngineeringCycle fill:none,stroke:#6B7280,stroke-width:1.5px;"
/>

Different tools may be used at each stage.

A CAD or BIM application may create the design. Another application may prepare the review. Feedback may arrive through annotations, documents, or imported files. The next revision may then return to the original authoring tool.

Without a shared document model, the technical workspace has to be reconstructed at every transition.

## Where DUC fits [#where-duc-fits]

DUC provides a persistent document layer beneath this cycle.

Applications can read from and write to the same structured document as the project moves through development, review, change, and delivery.

A `.duc` document can preserve the wider workspace around the design, including:

* Native drawing entities;
* External models, documents, and media;
* Revisions of external files;
* Annotations and metadata;
* Relationships between elements;
* Views and document organization;
* Extensible application state.

This information becomes part of the document instead of remaining trapped inside one application or scattered across unrelated files.

## More than a folder of files [#more-than-a-folder-of-files]

A folder can contain every asset used by a project without representing how those assets relate to each other.

It does not inherently describe which revision is being used, which annotation belongs to which element, how objects are arranged, or which views are meaningful.

DUC makes this structure explicit.

The document represents not only the assets, but also the technical workspace built around them.

## A foundation, not a replacement [#a-foundation-not-a-replacement]

DUC does not replace specialized formats such as STEP, IFC, DXF, PDF, or other engineering file types.

It also does not replace the tools used to create, review, or deliver technical work.

Those assets and tools continue to serve their existing purposes. DUC provides the document structure that allows them to participate in the same workspace.

The applications may change throughout the project. The underlying technical context does not need to be discarded and rebuilt each time.

## The underlying idea [#the-underlying-idea]

Engineering work is more than its final drawing or model.

The references, external assets, relationships, revisions, and document state surrounding that design are also part of the technical artifact.

DUC exists to give that wider technical workspace a structured and portable form.