# Plot Elements (/docs/concepts/elements/plot-element)



## Overview [#overview]

In `.duc`, a **Plot Element** (`DucPlotElement` with `type: "plot"`) defines a finite paper space boundary within the infinite canvas.

While drawings and geometry span across continuous canvas space, physical deliverables require explicit boundaries. A Plot Element establishes defined page dimensions, margins, and clipping bounds for printing, plotter outputs, and multi-page PDF generation.

***

## Plot Element vs. Frame Element [#plot-element-vs-frame-element]

Both Plot Elements and Frame Elements inherit from a shared container foundation (`_DucStackElementBase`), but serve distinct roles:

| Feature               | Frame Element (`DucFrameElement`)                          | Plot Element (`DucPlotElement`)                                     |
| :-------------------- | :--------------------------------------------------------- | :------------------------------------------------------------------ |
| **Primary Role**      | Canvas organization, artboard grouping, and visual framing | Export configuration, deliverability, and printable page boundaries |
| **Canvas Behavior**   | Groups elements for spatial layout and viewport navigation | Captures enclosed elements for file export and paper printing       |
| **Layout Attributes** | Visual border styles and group metadata                    | Paper layout dimensions and explicit margins (`layout`)             |

***

## Export Integration with the PDF Adapter (`ducpdf`) [#export-integration-with-the-pdf-adapter-ducpdf]

The Plot Element functions as the primary export target when compiling `.duc` documents into external files.

When a document is exported via the [`ducpdf`](/docs/pdf/overview) adapter:

<Mermaid
  chart="flowchart LR
    P1[&#x22;Plot Element 1 (Sheet A1)&#x22;] --> D[&#x22;PDF Adapter (ducpdf)&#x22;] --> Page1[&#x22;PDF Page 1&#x22;]
    P2[&#x22;Plot Element 2 (Sheet A2)&#x22;] --> D --> Page2[&#x22;PDF Page 2&#x22;]"
/>

1. **Page Mapping**: Each Plot Element defined on the canvas compiles into an individual page within the generated PDF deliverable.
2. **Boundary Capture**: Enclosed canvas elements positioned within a Plot Element’s spatial region are captured, clipped to the defined paper margins, and rendered onto that plot’s PDF page.
3. **Multi-Page Deliverables**: A single `.duc` canvas containing multiple Plot Elements exports directly into a structured multi-page PDF document set.

***

## Plot Layout and Paper Margins (`PlotLayout`) [#plot-layout-and-paper-margins-plotlayout]

The spatial paper composition of a Plot Element is governed by its `layout` attribute:

```ts
export type PlotLayout = {
  margins: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
};

export type DucPlotElement = _DucStackElementBase & {
  type: "plot";
  layout: PlotLayout;
};
```

* **Paper Dimensions**: The element’s canvas `width` and `height` correspond directly to physical paper size dimensions.
* **Margin Insets (`margins`)**: Specifies explicit `top`, `right`, `bottom`, and `left` margin insets (`number`), defining printable boundary limits for enclosed elements.


# Duc Whitepaper (/blog/whitepaper)



To be written.


# License (/pages/license)



# Open Source License [#open-source-license]

The duc file format is protected and licensed under the MIT License. This decision aligns with our commitment to supporting open development and ensuring that our file format can be utilized and contributed to by a wide community of developers, designers, and engineers.

## What This Means for You [#what-this-means-for-you]

At `Ducflair` we envisioned a future where the `duc file format` is widely adopted and utilized across a variety of industries and applications. By licensing it under the `MIT License`, we’re ensuring that `duc` can be freely used, modified, and distributed by anyone, for any purpose, without fear of legal repercussions.
All of that to say that we are in favor to:

> **Support Innovative Minds that want to push us forward into a greater future**.

Whether you’re a developer looking to integrate the Duc file format into your software, a designer interested in exploring its capabilities, or a contributor eager to improve upon its foundations, the MIT License ensures that you can do so with confidence and clarity regarding intellectual property and rights.

## Overview [#overview]

| Permissions      | Limitations | Conditions                     |
| ---------------- | ----------- | ------------------------------ |
| ✅ Commercial use | ❌ Liability | ℹ License and copyright notice |
| ✅ Modification   | ❌ Warranty  |                                |
| ✅ Distribution   |             |                                |
| ✅ Private use    |             |                                |

## Extended [#extended]

```txt
                                MIT License

Copyright (c) 2024 Ducflair

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```