#!/usr/bin/env python3
"""
Annotation data model, persistence, and PDF rendering.

Annotation types:
  - highlight: semi-transparent coloured rectangle
  - text: placed text string with font/size/colour
  - freehand: series of line segments
  - rectangle: stroked (and optionally filled) rectangle
  - comment: invisible marker with text (not rendered into PDF)

All coordinates are stored in PDF points (1 pt = 1/72 inch).
"""

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont

# Register Japanese CID font for text annotations
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

# Register Times New Roman TTF (macOS) for English text
_TIMES_NEW_ROMAN = "TimesNewRoman"
_TNR_PATHS = [
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/Library/Fonts/Times New Roman.ttf",
]
for _p in _TNR_PATHS:
    if os.path.exists(_p):
        try:
            pdfmetrics.registerFont(TTFont(_TIMES_NEW_ROMAN, _p))
            break
        except Exception:
            pass
else:
    # Fallback to built-in Times-Roman if TTF not available
    _TIMES_NEW_ROMAN = "Times-Roman"


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _sidecar_path(pdf_path: str) -> str:
    """Return the sidecar JSON path for a given PDF."""
    return pdf_path + ".annotations.json"


def save_to_json(annotations: list[dict[str, Any]], path: str) -> None:
    """Persist annotations list to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)


def load_from_json(path: str) -> list[dict[str, Any]] | None:
    """Load annotations from a JSON file.  Returns None if file missing."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_annotations(pdf_path: str, annotations_json: str) -> dict:
    """Save annotations JSON string to sidecar file for *pdf_path*."""
    try:
        annotations = json.loads(annotations_json)
        sidecar = _sidecar_path(pdf_path)
        save_to_json(annotations, sidecar)
        return {"success": True, "path": sidecar}
    except Exception as e:
        return {"success": False, "error": str(e)}


def load_annotations(pdf_path: str) -> str | None:
    """Load annotations for *pdf_path*, returning JSON string or None."""
    sidecar = _sidecar_path(pdf_path)
    data = load_from_json(sidecar)
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    """Convert '#RRGGBB' or '#RGB' to (r, g, b) floats 0-1."""
    color = HexColor(hex_str)
    return (color.red, color.green, color.blue)


def _render_highlight(c, ann: dict) -> None:
    """Render a semi-transparent highlight rectangle."""
    color = ann.get("color", "#FFFF00")
    alpha = ann.get("opacity", 0.4)
    r, g, b = _hex_to_rgb(color)

    c.saveState()
    c.setFillColorRGB(r, g, b)
    c.setStrokeColorRGB(r, g, b)
    c.setFillAlpha(alpha)
    c.setStrokeAlpha(0)
    x = ann["x"]
    y = ann["y"]
    w = ann["width"]
    h = ann["height"]
    c.rect(x, y, w, h, stroke=0, fill=1)
    c.restoreState()


def _has_cjk(text: str) -> bool:
    """Return True if text contains any Japanese/CJK character."""
    for ch in text:
        code = ord(ch)
        # Hiragana, Katakana, CJK Unified Ideographs, Fullwidth forms
        if (0x3040 <= code <= 0x309F) or \
           (0x30A0 <= code <= 0x30FF) or \
           (0x4E00 <= code <= 0x9FFF) or \
           (0xFF00 <= code <= 0xFFEF) or \
           (0x3000 <= code <= 0x303F):
            return True
    return False


def _render_text(c, ann: dict) -> None:
    """Render a text annotation with multi-line and Japanese/Latin font support."""
    color = ann.get("color", "#000000")
    font_size = ann.get("fontSize", 12)
    text = ann.get("text", "")
    r, g, b = _hex_to_rgb(color)

    # Use Japanese font if text contains CJK, otherwise Times New Roman for Latin
    font_name = "HeiseiKakuGo-W5" if _has_cjk(text) else _TIMES_NEW_ROMAN

    c.saveState()
    c.setFillColorRGB(r, g, b)
    c.setFont(font_name, font_size)

    # Split text into lines and word-wrap to box width if available
    lines = _wrap_text(text, font_name, font_size, ann.get("width"))

    line_height = font_size * 1.4
    x = ann["x"]
    y = ann["y"]
    # Draw each line moving DOWN in screen coords (i.e. decreasing Y in PDF coords)
    for i, line in enumerate(lines):
        c.drawString(x, y - i * line_height, line)
    c.restoreState()


def _wrap_text(text: str, font_name: str, font_size: float, max_width) -> list[str]:
    """Split text into lines respecting explicit newlines and word-wrapping to width."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    lines = []
    for raw_line in text.split("\n"):
        if not max_width or max_width <= 0:
            lines.append(raw_line)
            continue

        # For CJK, wrap by character; for Latin, wrap by word
        if _has_cjk(raw_line):
            current = ""
            for ch in raw_line:
                test = current + ch
                if stringWidth(test, font_name, font_size) > max_width and current:
                    lines.append(current)
                    current = ch
                else:
                    current = test
            if current:
                lines.append(current)
        else:
            words = raw_line.split(" ")
            current = ""
            for w in words:
                test = (current + " " + w).strip()
                if stringWidth(test, font_name, font_size) > max_width and current:
                    lines.append(current)
                    current = w
                else:
                    current = test
            if current:
                lines.append(current)
    return lines or [""]


def _render_freehand(c, ann: dict) -> None:
    """Render a freehand path (list of points)."""
    points = ann.get("points", [])
    if len(points) < 2:
        return

    color = ann.get("color", "#000000")
    line_width = ann.get("lineWidth", ann.get("strokeWidth", 2))
    r, g, b = _hex_to_rgb(color)

    c.saveState()
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(line_width)

    for i in range(len(points) - 1):
        x1, y1 = points[i]["x"], points[i]["y"]
        x2, y2 = points[i + 1]["x"], points[i + 1]["y"]
        c.line(x1, y1, x2, y2)

    c.restoreState()


def _render_rectangle(c, ann: dict) -> None:
    """Render a stroked rectangle."""
    stroke_color = ann.get("color", "#FF0000")
    fill_color = ann.get("fillColor", None)
    line_width = ann.get("lineWidth", ann.get("strokeWidth", 2))
    sr, sg, sb = _hex_to_rgb(stroke_color)

    c.saveState()
    c.setStrokeColorRGB(sr, sg, sb)
    c.setLineWidth(line_width)

    fill = 0
    if fill_color:
        fr, fg, fb = _hex_to_rgb(fill_color)
        c.setFillColorRGB(fr, fg, fb)
        fill_alpha = ann.get("fillOpacity", 0.2)
        c.setFillAlpha(fill_alpha)
        fill = 1

    c.rect(ann["x"], ann["y"], ann["width"], ann["height"], stroke=1, fill=fill)
    c.restoreState()


def _convert_coords(ann: dict, page_width: float, page_height: float) -> dict:
    """Convert annotation from screen coordinates (Y-down) to PDF coordinates (Y-up).

    The frontend stores positions in viewport units (pixels / scale),
    which correspond to the pdf.js viewport.  pdf.js viewports use the
    same unit as PDF points but with Y increasing downward.  reportlab
    and the PDF spec use Y increasing upward, so we flip:
        pdf_y = page_height - screen_y
    For shapes with height, we also adjust the origin to the bottom-left.
    """
    ann = dict(ann)  # shallow copy to avoid mutating the original

    if ann.get("type") in ("highlight", "rectangle"):
        ann["y"] = page_height - ann["y"] - ann.get("height", 0)
    elif ann.get("type") == "text":
        # Text baseline: drawString draws from bottom-left of first char
        ann["y"] = page_height - ann["y"] - ann.get("fontSize", 12)
    elif ann.get("type") in ("pen", "freehand"):
        if "points" in ann:
            ann["points"] = [
                {"x": p["x"], "y": page_height - p["y"]}
                for p in ann["points"]
            ]
    elif ann.get("type") == "comment":
        ann["y"] = page_height - ann["y"]

    return ann


_RENDERERS = {
    "highlight": _render_highlight,
    "text": _render_text,
    "freehand": _render_freehand,
    "pen": _render_freehand,  # frontend uses "pen", alias to freehand renderer
    "rectangle": _render_rectangle,
    # "comment" is intentionally NOT rendered (metadata only)
}


# ---------------------------------------------------------------------------
# Public rendering API
# ---------------------------------------------------------------------------

def render_to_pdf(
    input_path: str,
    output_path: str,
    annotations: list[dict[str, Any]],
) -> dict:
    """
    Burn annotations into a PDF using the reportlab overlay pattern.

    Each page gets a transparent overlay Canvas; annotations for that page
    are drawn on the overlay, which is then merged onto the original page.

    Returns {"success": True} or {"success": False, "error": "..."}.
    """
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Group annotations by page (1-indexed)
        by_page: dict[int, list[dict]] = {}
        for ann in annotations:
            page_num = ann.get("page", 1)
            by_page.setdefault(page_num, []).append(ann)

        for i, page in enumerate(reader.pages):
            page_num = i + 1
            page_anns = by_page.get(page_num, [])

            if page_anns:
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                packet = BytesIO()
                c = rl_canvas.Canvas(packet, pagesize=(page_width, page_height))

                for ann in page_anns:
                    # Convert from screen coords (Y down) to PDF coords (Y up)
                    ann = _convert_coords(ann, page_width, page_height)
                    ann_type = ann.get("type", "")
                    renderer = _RENDERERS.get(ann_type)
                    if renderer:
                        renderer(c, ann)

                c.save()
                packet.seek(0)

                overlay_reader = PdfReader(packet)
                page.merge_page(overlay_reader.pages[0])

            writer.add_page(page)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}
