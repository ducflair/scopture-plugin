# PDF Adapter (ducpdf) (/docs/pdf/overview)



## Overview [#overview]

`ducpdf` is the dedicated PDF exporter package for `.duc` project state. Built with TypeScript and Rust WebAssembly bindings (`duc2pdf`), its purpose is converting `.duc` files into vector PDF files.

***

## Core Capabilities [#core-capabilities]

* **`.duc` to PDF Export**: Renders canvas elements, vector geometry, typography, and plot layouts into vector PDF pages.
* **WASM Acceleration**: Powered by the underlying `duc2pdf` Rust WebAssembly engine for fast, high-fidelity PDF rendering.
* **Cross-Platform**: Operates across Node.js, Bun, browser contexts, and edge functions.