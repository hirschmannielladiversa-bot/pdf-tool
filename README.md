# PDF Tool

A privacy-first, offline PDF editor that runs entirely in your browser.
No server, no upload, no installation — just double-click and edit.

**Current version: v1.4.0**

## Features

- **Text** annotations — type anywhere on the PDF
- **Highlight**, **Frame**, **Strikethrough** — drag to annotate
- **Pen** — freehand drawing
- **Word-style Comments** — margin callouts with replies, connected to the page by leader lines
- **Page management** — reorder, multi-select, delete, and rotate pages
- **Page numbers** — auto-insert with configurable position and format
- **Image → PDF** — combine PNG / JPEG files into a single PDF
- **Merge PDFs** — append another PDF to the current document
- **Font switching** — built-in Sawarabi Gothic + load custom `.ttf` / `.otf`
- **Zoom** — 40% to 400% display scale; annotation sizes are zoom-independent
- **JP / EN toggle** — switch the interface language at any time

## Privacy

All processing happens inside your browser. No data ever leaves your computer.
Works fully offline — you can disable Wi-Fi while editing.

## Download

Grab the latest release from the [Releases](../../releases) page. Four packages are available:

| Package | OS | Language | Entry file |
|---|---|---|---|
| `PDF_Tool_Mac_JP.zip` | Mac | Japanese | `本体：ダブルクリックで作動.html` |
| `PDF_Tool_Mac_EN.zip` | Mac | English | `PDF_Tool.html` |
| `PDF_Tool_Windows_JP.zip` | Windows | Japanese | `pdf_tool_bundled.html` |
| `PDF_Tool_Windows_EN.zip` | Windows | English | `pdf_tool_bundled.html` |

Each package is self-contained. Double-click the entry file to open the tool in your browser.

> **Tip:** After opening, you can always switch the display language with the **JP / EN** button
> in the toolbar — regardless of which package you downloaded.

## Usage Guides

- Japanese: `使い方ガイド.html` (included in JP packages)
- English: `usage_guide.html` (included in EN packages)

## System Requirements

- **OS:** Windows, macOS, or Linux
- **Browser:** Chrome, Edge, Safari, or Firefox (latest version recommended)
- **Internet:** Not required

## Build from Source

```bash
# Generate all four distribution packages
python3 src/build_packages.py
# Output: deploy/packages/PDF_Tool_{Mac,Windows}_{JP,EN}.zip
```

```bash
# Generate a single bundled HTML (optional)
python3 src/build_bundled.py --lang ja   # → deploy/pdf_tool/pdf_tool_bundled.html
python3 src/build_bundled.py --lang en   # → deploy/pdf_tool/pdf_tool_bundled_en.html
```

## License

See `LICENSE.txt` (included in each package) for the licenses of bundled third-party libraries
(PDF.js, pdf-lib, fontkit, Sawarabi Gothic).
