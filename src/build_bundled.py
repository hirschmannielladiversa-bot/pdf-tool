#!/usr/bin/env python3
"""
build_bundled.py — Generate a fully self-contained single-file HTML version
of the PDF Tool editor by inlining all lib/ dependencies into pdf_tool.html.

Inputs  : deploy/pdf_tool/pdf_tool.html
          deploy/pdf_tool/lib/{pdf.min.js, pdf-lib.min.js, fontkit.umd.min.js,
                               pdf.worker.min.js, SawarabiGothic-Regular.ttf}
Output  : deploy/pdf_tool/pdf_tool_bundled.html    (--lang ja, default)
          deploy/pdf_tool/pdf_tool_bundled_en.html  (--lang en)

Inlining strategy:
  - pdf.min.js, pdf-lib.min.js, fontkit.umd.min.js   → inlined as <script>…</script>
  - pdf.worker.min.js                                → base64-embedded + Blob URL
  - SawarabiGothic-Regular.ttf                       → base64 data URL

CSP requirements (already set in source pdf_tool.html) stay intact:
  - 'unsafe-inline' + 'unsafe-eval' (pdf-lib / fontkit use eval)
  - blob: in script-src / worker-src (PDF.js worker)
  - connect-src with no http(s):  → zero exfiltration
"""

import argparse
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY_DIR = ROOT / "deploy" / "pdf_tool"
LIB_DIR = DEPLOY_DIR / "lib"
SRC_HTML = DEPLOY_DIR / "pdf_tool.html"

OUT_HTML_BY_LANG = {
    "ja": DEPLOY_DIR / "pdf_tool_bundled.html",
    "en": DEPLOY_DIR / "pdf_tool_bundled_en.html",
}

INLINE_SCRIPTS = [
    ("lib/pdf.min.js", "pdf.min.js"),
    ("lib/pdf-lib.min.js", "pdf-lib.min.js"),
    ("lib/fontkit.umd.min.js", "fontkit.umd.min.js"),
]
WORKER_FILE = "pdf.worker.min.js"
TTF_FILE = "SawarabiGothic-Regular.ttf"


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def inline_script_tag(src_label: str, js_content: str) -> str:
    # Escape </script> sequences inside embedded JS to prevent premature tag close.
    safe = js_content.replace("</script", "<\\/script")
    return f"<script>\n/* inlined from {src_label} */\n{safe}\n</script>"


def build(lang: str = "ja") -> None:
    if lang not in ("ja", "en"):
        print(f"ERROR: unsupported lang '{lang}'", file=sys.stderr)
        sys.exit(1)

    if not SRC_HTML.exists():
        print(f"ERROR: source HTML not found: {SRC_HTML}", file=sys.stderr)
        sys.exit(1)

    html = read_text(SRC_HTML)

    # 1. Replace <script src="lib/x.js"></script> with inlined <script>…</script>
    for src_attr, fname in INLINE_SCRIPTS:
        lib_path = LIB_DIR / fname
        if not lib_path.exists():
            print(f"ERROR: missing lib file: {lib_path}", file=sys.stderr)
            sys.exit(1)
        tag_old = f'<script src="{src_attr}"></script>'
        if tag_old not in html:
            print(f"ERROR: expected tag not found in HTML: {tag_old}", file=sys.stderr)
            sys.exit(1)
        js_content = read_text(lib_path)
        html = html.replace(tag_old, inline_script_tag(src_attr, js_content), 1)
        print(f"  inlined {src_attr} ({len(js_content):,} chars)")

    # 2. Replace PDF.js worker assignment with a Blob URL from base64.
    worker_path = LIB_DIR / WORKER_FILE
    if not worker_path.exists():
        print(f"ERROR: missing worker file: {worker_path}", file=sys.stderr)
        sys.exit(1)
    worker_b64 = base64.b64encode(read_bytes(worker_path)).decode("ascii")
    old_worker_line = 'pdfjsLib.GlobalWorkerOptions.workerSrc = "lib/pdf.worker.min.js";'
    if old_worker_line not in html:
        print("ERROR: worker assignment line not found", file=sys.stderr)
        sys.exit(1)
    new_worker_block = (
        "// PDF.js worker inlined as base64 → Blob URL (CSP: worker-src blob:)\n"
        f'const __PDF_WORKER_B64 = "{worker_b64}";\n'
        "const __pdfWorkerBlob = new Blob(\n"
        "  [Uint8Array.from(atob(__PDF_WORKER_B64), c => c.charCodeAt(0))],\n"
        '  { type: "application/javascript" }\n'
        ");\n"
        "pdfjsLib.GlobalWorkerOptions.workerSrc = URL.createObjectURL(__pdfWorkerBlob);"
    )
    html = html.replace(old_worker_line, new_worker_block, 1)
    print(f"  inlined worker ({len(worker_b64):,} b64 chars)")

    # 3. Replace the JP font fetch URL with a data URL.
    ttf_path = LIB_DIR / TTF_FILE
    if not ttf_path.exists():
        print(f"ERROR: missing TTF: {ttf_path}", file=sys.stderr)
        sys.exit(1)
    ttf_b64 = base64.b64encode(read_bytes(ttf_path)).decode("ascii")
    ttf_data_url = f"data:font/ttf;base64,{ttf_b64}"
    old_url_line = '"lib/SawarabiGothic-Regular.ttf",'
    if old_url_line not in html:
        print("ERROR: JP font URL line not found", file=sys.stderr)
        sys.exit(1)
    html = html.replace(old_url_line, f'"{ttf_data_url}",', 1)
    print(f"  inlined TTF ({len(ttf_b64):,} b64 chars)")

    # 4. Apply language-specific default.
    if lang == "en":
        html = html.replace(
            '<html lang="ja" data-default-lang="ja">',
            '<html lang="en" data-default-lang="en">',
            1,
        )

    out_path = OUT_HTML_BY_LANG[lang]
    out_path.write_text(html, encoding="utf-8")
    size_mb = len(html.encode("utf-8")) / (1024 * 1024)
    print(f"✓ wrote {out_path.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["ja", "en"], default="ja",
                        help="default interface language (default: ja)")
    args = parser.parse_args()
    build(lang=args.lang)
