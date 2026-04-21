#!/usr/bin/env python3
"""
build_packages.py — Produce OS-specific distribution zips (JP and EN).

1. Runs build_bundled.py twice (--lang ja and --lang en) to produce:
     - pdf_tool_bundled.html       (Japanese-default)
     - pdf_tool_bundled_en.html    (English-default)
2. Builds four zip packages in deploy/packages/:
     - PDF_Tool_Mac_JP.zip     (entry: 本体：ダブルクリックで作動.html, guide: 使い方ガイド.html)
     - PDF_Tool_Mac_EN.zip     (entry: PDF_Tool.html,                  guide: usage_guide.html)
     - PDF_Tool_Windows_JP.zip (entry: pdf_tool_bundled.html,          guide: 使い方ガイド.html)
     - PDF_Tool_Windows_EN.zip (entry: pdf_tool_bundled.html,          guide: usage_guide.html)
   Each zip embeds its own SHA256SUMS.txt.
"""

import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY_DIR = ROOT / "deploy" / "pdf_tool"
LIB_DIR = DEPLOY_DIR / "lib"
PACKAGES_DIR = ROOT / "deploy" / "packages"
BUILD_BUNDLED_SCRIPT = ROOT / "src" / "build_bundled.py"

# The Japanese-named copy that Mac JP users double-click in Finder.
# Excluded from Windows packages due to U+FF1A + NFD/NFC issues on Windows.
MAC_FRIENDLY_FILENAME_JP = "本体：ダブルクリックで作動.html"
# ASCII entry point for Mac EN package.
MAC_FRIENDLY_FILENAME_EN = "PDF_Tool.html"

# Bundled single-file HTMLs per language (on disk in DEPLOY_DIR).
BUNDLED_FILES = {
    "ja": DEPLOY_DIR / "pdf_tool_bundled.html",
    "en": DEPLOY_DIR / "pdf_tool_bundled_en.html",
}

# Usage guide per language.
GUIDE_FILES = {
    "ja": "使い方ガイド.html",
    "en": "usage_guide.html",
}

# Files common to all four packages (no guide — that's lang-specific).
COMMON_FILES_BASE = [
    "pdf_tool.html",    # lib-referencing form (advanced users)
    "LICENSE.txt",
]

# lib/ assets (shared across all packages).
LIB_FILES = [
    "pdf.min.js",
    "pdf-lib.min.js",
    "fontkit.umd.min.js",
    "pdf.worker.min.js",
    "SawarabiGothic-Regular.ttf",
]

WINDOWS_README_TXT = """PDF Tool — Windows 版 (オフライン単一ファイル)

◆ 推奨: pdf_tool_bundled.html をダブルクリック
  ブラウザで開いて、すぐに PDF を編集できます。
  ネット接続は不要です（ブラウザ内だけで処理されます）。

◆ 開けない / 真っ黒になる場合
  1. このフォルダごと Windows のローカルドライブ (例: デスクトップ) に
     コピーしてから pdf_tool_bundled.html を開いてください。
     外付け SSD/USB 直接だと開けないケースがあります。
  2. それでも開かない場合は、Edge または Chrome を先に起動しておき、
     pdf_tool_bundled.html をブラウザ ウィンドウにドラッグ & ドロップしてください。
  3. F12 キーでブラウザの開発者ツールを開き、エラーがあれば確認してください。

◆ 代替: ライブラリ分離版
  pdf_tool.html + lib/ フォルダ をセットで配置して開く形でも動きます。

◆ Mac 版との関係
  Mac 版 (PDF_Tool_Mac_JP.zip) と Windows 版は 中身 (HTML / JS / フォント)
  が同一で、機能も操作方法も完全に同じです。違いはエントリ用のファイル名
  だけで、Mac 版には日本語ファイル名 "本体：ダブルクリックで作動.html"
  が含まれ、Windows 版には pdf_tool_bundled.html だけが含まれます。
  使い方ガイド.html は共通のものを同梱しているので、両 OS で参照できます。

◆ 主な機能
  - テキスト / ハイライト / 枠線 / 取り消し線 / ペン / 消しゴム注釈
  - Word 風コメント: 「コメント」ツールでページ上をクリック → 右のガターに
    吹き出しが出現。ドラッグで位置調整、フィルハンドルでサイズ変更、
    A-/A+ ボタンで文字サイズ、「返信」ボタンで返信サブウィンドウを追加
  - ページ番号挿入、画像 → PDF 変換、PDF 結合
  - 複数ページ選択: サムネイルを Shift+クリック / Ctrl+クリック で複数選択し、
    まとめてドラッグ、Shift+←/→ で範囲を広げる、←/→ (Shift なし) で
    選択中ページをまとめて1ステップずつ移動
  - ズーム: ツールバーの − / 100% / ＋ ボタンで表示倍率を変更 (40% 〜 400%)
  - フォント切替: プルダウンから埋め込みフォントを選択 (初期値: Sawarabi Gothic)
    カスタムフォント (.ttf / .otf) を読み込んで追加することも可能
  - JP / EN 切替: ツールバーの JP / EN ボタンで表示言語をいつでも切り替え可能

◆ 選択の挙動 (注意)
  - テキスト注釈: 選択するとプロパティパネルが出っぱなしになります。
    Escape / 別ツール切替 / 削除ボタン で閉じます。
  - 枠線・ハイライト: 選択するとハンドルが出ます。
    ページの空白部分クリック または Enter キーで確定 (ハンドル消える)。
    枠線の "内部" のどこをクリックしても選択できます (線の上だけでは
    ありません)。

◆ 既知事項
  Windows 版では、ファイル名に全角コロンを含む日本語名のファイル
  (本体：ダブルクリックで作動.html) は同梱していません。
  これは Windows で開けなくなる既知の問題を避けるためです。
"""

WINDOWS_README_TXT_EN = """PDF Tool — Windows version (offline single-file)

◆ Recommended: double-click pdf_tool_bundled.html
  Opens in your browser and lets you edit PDFs immediately.
  No internet connection required (all processing stays in your browser).

◆ If the file won't open or shows a black screen
  1. Copy this entire folder to a local Windows drive (e.g. Desktop) and then
     open pdf_tool_bundled.html. Opening directly from an external SSD/USB
     can cause launch failures on some systems.
  2. If that still doesn't work, open Edge or Chrome first, then drag and drop
     pdf_tool_bundled.html onto the browser window.
  3. Press F12 to open the browser developer tools and check the console for
     any error messages.

◆ Alternative: library-reference variant
  pdf_tool.html + lib/ folder can also be used by placing them together and
  opening pdf_tool.html in a browser.

◆ Relationship to the Mac version
  The Mac version (PDF_Tool_Mac_EN.zip) and this Windows version are
  identical in content (HTML / JS / fonts) and functionality. The only
  difference is the entry filename:
    Mac     -> PDF_Tool.html
    Windows -> pdf_tool_bundled.html
  The usage guide (usage_guide.html) is shared between both OS versions.

◆ Main features
  - Text / Highlight / Frame / Strikethrough / Pen / Eraser annotations
  - Word-style comments: select the "Comment" tool, click or drag on the page
    -> a callout appears to the right. Drag to reposition, use the fill handle
    to resize, A-/A+ to change font size, "Reply" to add reply sub-cards
  - Insert page numbers, convert images to PDF, merge PDFs
  - Multi-page select: Shift+click / Ctrl+click thumbnails to select multiple
    pages; drag to reorder, Shift+<-/-> to extend selection, <-/-> (no Shift)
    to move selected pages one step at a time
  - Zoom: - / 100% / + buttons in the toolbar (40% - 400%)
  - Font switching: choose from the dropdown (default: Sawarabi Gothic);
    load custom .ttf/.otf fonts via "Load custom font..."
  - JP / EN toggle: switch the interface language at any time with the
    JP / EN button in the toolbar

◆ Selection behavior (note)
  - Text annotations: selecting shows the properties panel persistently.
    Close it with Escape, by switching tools, or by pressing Delete.
  - Frame / Highlight: selecting shows resize handles.
    Click a blank page area or press Enter to confirm (handles disappear).
    You can click anywhere inside the frame area to select it -- not only
    on the border line itself.
"""


def run_build_bundled():
    print("[1/5] running build_bundled.py (ja + en) …")
    for lang in ["ja", "en"]:
        r = subprocess.run(
            [sys.executable, str(BUILD_BUNDLED_SCRIPT), "--lang", lang],
            cwd=str(ROOT), capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(r.stdout)
            print(r.stderr, file=sys.stderr)
            sys.exit(f"build_bundled.py --lang {lang} failed")
        last_line = r.stdout.strip().split("\n")[-1] if r.stdout.strip() else ""
        print(f"  [{lang}] {last_line}")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def zip_with_sha256(zip_path: Path, entries):
    """
    entries: list of (disk_path, arcname_in_zip)
    Computes per-zip SHA256SUMS.txt and embeds it as pdf_tool/SHA256SUMS.txt.
    """
    sha_lines = []
    for disk, arc in entries:
        if disk.exists():
            rel = arc.split("/", 1)[-1]  # strip leading 'pdf_tool/' folder
            sha_lines.append(f"{sha256_file(disk)}  {rel}")

    sha_tmp = zip_path.parent / "_SHA256SUMS_tmp.txt"
    sha_tmp.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for disk, arc in entries:
                if not disk.exists():
                    print(f"  SKIP missing: {disk}")
                    continue
                zf.write(disk, arc)
            zf.write(sha_tmp, "pdf_tool/SHA256SUMS.txt")
    finally:
        if sha_tmp.exists():
            sha_tmp.unlink()

    print(f"  → {zip_path.name} ({zip_path.stat().st_size / (1024 * 1024):.2f} MB)")


def _base_entries(lang: str):
    """Returns (disk_path, arcname) entries shared by Mac and Windows packages."""
    entries = []
    # Common non-guide files
    for name in COMMON_FILES_BASE:
        entries.append((DEPLOY_DIR / name, f"pdf_tool/{name}"))
    # Language-specific guide
    guide = GUIDE_FILES[lang]
    entries.append((DEPLOY_DIR / guide, f"pdf_tool/{guide}"))
    # lib/ assets
    for name in LIB_FILES:
        entries.append((LIB_DIR / name, f"pdf_tool/lib/{name}"))
    return entries


def build_mac_zip(lang: str):
    label = "JP" if lang == "ja" else "EN"
    step = 2 if lang == "ja" else 3
    print(f"[{step}/5] building Mac {label} zip …")

    bundled = BUNDLED_FILES[lang]
    entries = _base_entries(lang)
    # Bundled file as pdf_tool_bundled.html (ASCII, always present)
    entries.append((bundled, "pdf_tool/pdf_tool_bundled.html"))
    # OS-friendly named entry
    if lang == "ja":
        entries.append((bundled, f"pdf_tool/{MAC_FRIENDLY_FILENAME_JP}"))
    else:
        entries.append((bundled, f"pdf_tool/{MAC_FRIENDLY_FILENAME_EN}"))

    zip_name = f"PDF_Tool_Mac_{label}.zip"
    zip_with_sha256(PACKAGES_DIR / zip_name, entries)


def build_windows_zip(lang: str):
    label = "JP" if lang == "ja" else "EN"
    step = 4 if lang == "ja" else 5
    print(f"[{step}/5] building Windows {label} zip …")

    bundled = BUNDLED_FILES[lang]
    readme_txt = WINDOWS_README_TXT if lang == "ja" else WINDOWS_README_TXT_EN

    readme_tmp = PACKAGES_DIR / "_README_Windows_tmp.txt"
    PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    readme_tmp.write_text(readme_txt, encoding="utf-8")

    entries = _base_entries(lang)
    entries.append((bundled, "pdf_tool/pdf_tool_bundled.html"))
    # NOTE: intentionally NOT including the JP Mac-friendly filename
    entries.append((readme_tmp, "pdf_tool/README_Windows.txt"))

    zip_name = f"PDF_Tool_Windows_{label}.zip"
    try:
        zip_with_sha256(PACKAGES_DIR / zip_name, entries)
    finally:
        if readme_tmp.exists():
            readme_tmp.unlink()


def main():
    run_build_bundled()
    build_mac_zip("ja")
    build_mac_zip("en")
    build_windows_zip("ja")
    build_windows_zip("en")
    print("\n✓ all done.")
    for name in [
        "PDF_Tool_Mac_JP.zip",
        "PDF_Tool_Mac_EN.zip",
        "PDF_Tool_Windows_JP.zip",
        "PDF_Tool_Windows_EN.zip",
    ]:
        p = PACKAGES_DIR / name
        size = f"{p.stat().st_size / (1024*1024):.2f} MB" if p.exists() else "NOT FOUND"
        print(f"  {name}: {size}")


if __name__ == "__main__":
    main()
