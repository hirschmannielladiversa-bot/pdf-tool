#!/usr/bin/env python3
"""
build_packages.py — Produce OS-specific distribution zips.

1. Runs build_bundled.py first so pdf_tool_bundled.html is up to date.
2. Regenerates SHA256SUMS.txt for the files inside deploy/pdf_tool.
3. Zips two variants into deploy/packages/:
     - PDF_Tool_Mac.zip     (full set, includes 本体：ダブルクリックで作動.html)
     - PDF_Tool_Windows.zip (ASCII-only names; NO full-width colon file —
                             see WINDOWS_DEBUG_NOTES.md for background)
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

# The Japanese-named copy that Mac users see in Finder as "本体：ダブルクリックで作動.html".
# This file causes opening failures on Windows due to U+FF1A + NFD/NFC mismatch,
# so we only include it in the Mac package.
MAC_FRIENDLY_FILENAME = "本体：ダブルクリックで作動.html"

# Files common to both packages (paths are relative to DEPLOY_DIR)
COMMON_FILES = [
    "pdf_tool.html",                  # lib-referencing form
    "pdf_tool_bundled.html",          # single-file bundle (ASCII name)
    "使い方ガイド.html",              # usage guide (kept in both — normal Japanese chars)
    "LICENSE.txt",
]

# lib/ assets (shared)
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
  Mac 版 (PDF_Tool_Mac.zip) と Windows 版は 中身 (HTML / JS / フォント)
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


def run_build_bundled():
    print("[1/4] running build_bundled.py …")
    r = subprocess.run(
        [sys.executable, str(BUILD_BUNDLED_SCRIPT)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        sys.exit("build_bundled.py failed")
    print(r.stdout.strip())


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def regenerate_sha256sums():
    print("[2/4] regenerating SHA256SUMS.txt …")
    lines = []
    for rel in COMMON_FILES + [f"lib/{n}" for n in LIB_FILES]:
        p = DEPLOY_DIR / rel
        if not p.exists():
            print(f"  WARNING: missing {rel}")
            continue
        lines.append(f"{sha256_file(p)}  {rel}")
    # Include the Japanese-named file too if it exists.
    jp_file = DEPLOY_DIR / MAC_FRIENDLY_FILENAME
    if jp_file.exists():
        lines.append(f"{sha256_file(jp_file)}  {MAC_FRIENDLY_FILENAME}")
    sums = "\n".join(lines) + "\n"
    (DEPLOY_DIR / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    print(f"  {len(lines)} files hashed")


def refresh_mac_friendly_copy():
    """Keep 本体：ダブルクリックで作動.html in sync with pdf_tool_bundled.html."""
    src = DEPLOY_DIR / "pdf_tool_bundled.html"
    dst = DEPLOY_DIR / MAC_FRIENDLY_FILENAME
    shutil.copyfile(src, dst)
    print(f"  refreshed mac-friendly copy: {MAC_FRIENDLY_FILENAME}")


def zip_files(zip_path: Path, entries):
    """entries: list of (disk_path, arcname)"""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for disk, arc in entries:
            if not disk.exists():
                print(f"  SKIP missing: {disk}")
                continue
            zf.write(disk, arc)
    print(f"  → {zip_path.name} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")


def build_mac_zip():
    print("[3/4] building Mac zip …")
    entries = []
    # Common files
    for name in COMMON_FILES + ["SHA256SUMS.txt"]:
        entries.append((DEPLOY_DIR / name, f"pdf_tool/{name}"))
    # Japanese-named "本体" file — Mac-only
    jp = DEPLOY_DIR / MAC_FRIENDLY_FILENAME
    entries.append((jp, f"pdf_tool/{MAC_FRIENDLY_FILENAME}"))
    # lib/
    for name in LIB_FILES:
        entries.append((LIB_DIR / name, f"pdf_tool/lib/{name}"))
    zip_files(PACKAGES_DIR / "PDF_Tool_Mac.zip", entries)


def build_windows_zip():
    print("[4/4] building Windows zip …")
    entries = []
    for name in COMMON_FILES + ["SHA256SUMS.txt"]:
        entries.append((DEPLOY_DIR / name, f"pdf_tool/{name}"))
    # NOTE: intentionally NOT including 本体：ダブルクリックで作動.html
    for name in LIB_FILES:
        entries.append((LIB_DIR / name, f"pdf_tool/lib/{name}"))
    # Add Windows-specific README (generated on the fly, not persisted on disk).
    readme_path = PACKAGES_DIR / "_README_Windows_tmp.txt"
    PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(WINDOWS_README_TXT, encoding="utf-8")
    entries.append((readme_path, "pdf_tool/README_Windows.txt"))
    try:
        zip_files(PACKAGES_DIR / "PDF_Tool_Windows.zip", entries)
    finally:
        if readme_path.exists():
            readme_path.unlink()


def main():
    run_build_bundled()
    refresh_mac_friendly_copy()
    regenerate_sha256sums()
    build_mac_zip()
    build_windows_zip()
    print("\n✓ all done.")
    print(f"  Mac:     {PACKAGES_DIR / 'PDF_Tool_Mac.zip'}")
    print(f"  Windows: {PACKAGES_DIR / 'PDF_Tool_Windows.zip'}")


if __name__ == "__main__":
    main()
