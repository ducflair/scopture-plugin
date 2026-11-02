# Blocks (/docs/concepts/elements/blocks)



## 1. What is a Block? (The Master Definition) [#1-what-is-a-block-the-master-definition]

A **Block** (`DucBlock`) is an **authoritative, reusable definition of a set of elements**.

* **Single Source of Truth**: There is **only ONE master Block definition of a kind** stored in the document’s block registry.
* **Blueprint**: A Block defines the geometry, visual styles, and spatial arrangement of a reusable component.

***

## 2. What is a Block Instance? [#2-what-is-a-block-instance]

A **Block Instance** (`DucBlockInstanceElement`) is a live spatial reference placed on the drawing canvas that derives its geometry and layout from a master Block definition.

<Mermaid
  chart="flowchart TD
    M[&#x22;Master Block Definition (1x)&#x22;]
    M --> I1[&#x22;Canvas Instance #1&#x22;]
    M --> I2[&#x22;Canvas Instance #2&#x22;]
    M --> I3[&#x22;Canvas Instance #3&#x22;]"
/>

* **One-to-Many Relationship**: While a document contains only one master Block definition, **multiple instances** can be placed across the canvas relative to that single block.
* **Automatic Synchronization**: When the master Block definition is updated, **all live instances will automatically synchronize** to reflect the design change instantly.

***

## 3. Instance Overrides [#3-instance-overrides]

* **Granular Customization**: An instance can override specific properties of its inner elements without detaching from the master Block.
* **Selective Synchronization**: When the master Block is modified, all non-overridden properties of every instance update automatically, while individual instance overrides are preserved.

***

## 4. Duplication Arrays [#4-duplication-arrays]

* **Pattern-Based Replication**: A single block instance can define a linear or grid duplication array with specified counts and spatial offsets.
* **Unified Management**: The entire array is managed as a single logical entity, automatically rendering repeated instances across calculated spatial offsets while remaining fully synchronized with the master Block definition.

***

## 5. Block Collections [#5-block-collections]

As engineering projects grow to contain hundreds of reusable blocks, organizing these assets becomes critical.

A **Block Collection** (`DucBlockCollection`) is an organizational folder or pocket of blocks:

<Mermaid
  chart="flowchart TD
    C[&#x22;Mechanical Library (Collection)&#x22;]
    C --> V[&#x22;Valves (Sub-Collection)&#x22;]
    C --> F[&#x22;Flanges (Sub-Collection)&#x22;]
    V --> B1[&#x22;Ball Valve 2-Inch (Block)&#x22;]
    V --> B2[&#x22;Gate Valve 4-Inch (Block)&#x22;]
    F --> B3[&#x22;ANSI 150 Flange (Block)&#x22;]"
/>

* **Not Canvas Groups**: Unlike visual groups on the canvas (`groupIds`), a Collection is a structural data organization hierarchy within the document container.
* **Nested Folder Structures**: Collections can contain blocks and sub-collections, allowing engineering teams to build clean, categorized asset libraries directly inside the `.duc` file.