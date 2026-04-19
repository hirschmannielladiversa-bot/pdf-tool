# PDFproject

**Version: 1.3.0** (2026-04-19) — 詳細は [CHANGELOG.md](../CHANGELOG.md) 参照

画像からPDFへの変換とPDF操作ツール集。

## ツール一覧

### 1. 画像→PDF変換 (img2pdf.py)

PNG/JPEG画像を1つのPDFにまとめるツール。

### 2. PDF分割 (pdf_splitter.py)

PDFをページ範囲指定で複数ファイルに分割するツール。

### 3. PDF結合 (pdf_merger.py)

複数のPDFファイルを1つに結合するツール。

### 4. PDFページ操作 (pdf_edit.py)

PDFのページ削除・並べ替え・挿入を行うツール。

### 5. PDFページ番号挿入 (pdf_page_number.py)

PDFの各ページに自動でページ番号を挿入するツール。

### 6. PDFバッチ処理 (pdf_batch.py) ⭐ NEW

複数のPDFファイルに対して同じ操作を一括実行するツール。

## Requirements

- macOS
- Python 3.13+
- 依存ライブラリ（下記参照）

### インストール

```bash
pip install -r requirements.txt
```

主な依存ライブラリ：
- Pillow（画像処理）
- pypdf（PDF操作）
- reportlab（PDFページ番号挿入）
- tkinter（GUI、macOS標準）

---

## 1. 画像→PDF変換 (img2pdf.py)

### Quick Start

GUIで画像を選んで変換:

```bash
python3 img2pdf.py --select-files
```

または `StartImg2Pdf.command` をダブルクリック。

### CLI Examples

```bash
# 1枚だけ変換
python3 img2pdf.py page1.png -o output.pdf

# 複数画像をまとめる
python3 img2pdf.py page1.png page2.jpg -o merged.pdf

# ディレクトリ内の画像をまとめる
python3 img2pdf.py ./screenshots -o report.pdf

# サブディレクトリも含める
python3 img2pdf.py ./pages --recursive -o book.pdf
```

### Options

- `-o`, `--output`: 出力PDFファイル
- `--select-files`: GUIダイアログで画像と保存先を選択
- `--recursive`: サブフォルダも探索
- `-q`, `--quality`: 画質 1-100（既定値: 95）
- `--verbose`: 詳細ログ表示

### Notes

- 対応形式: PNG, JPG, JPEG
- 透過PNGは白背景に合成
- ファイル名は自然順で処理

---

## 2. PDF分割 (pdf_splitter.py)

PDFをページ範囲指定で複数ファイルに分割。

### Quick Start

GUIでファイルと範囲を選択:

```bash
python3 pdf_splitter.py --select-files
```

### CLI Examples

```bash
# 基本的な使い方
python3 pdf_splitter.py input.pdf --ranges "1-3,4-7,8-10" --output-dir ./split

# 単一ページの抽出
python3 pdf_splitter.py document.pdf --ranges "5" -o ./pages

# コロン区切りも使用可能
python3 pdf_splitter.py report.pdf --ranges "1:5 10:15" -o ./out

# 詳細ログ表示
python3 pdf_splitter.py input.pdf --ranges "1-10" -o ./split --verbose
```

### ページ範囲の指定方法

| 形式 | 説明 | 例 |
|------|------|-----|
| `1-3` | 1ページから3ページ | `1-3,4-7` |
| `1:3` | 1ページから3ページ（コロン区切り） | `1:3 4:7` |
| `5` | 単一ページ | `1-3,5,7-9` |
| 複数範囲 | カンマまたはスペース区切り | `1-3,4-7,8-10` |

### 出力ファイル名

- 範囲: `input_p1-3.pdf`
- 単一ページ: `input_p5.pdf`

### Options

- `--ranges`: ページ範囲（必須、またはGUIモード）
- `-o`, `--output-dir`: 出力ディレクトリ（既定値: 入力ファイルと同じ場所）
- `--select-files`: GUIダイアログで選択
- `--verbose`: 詳細ログ表示

### 使用例

10ページのPDFを3つに分割:

```bash
python3 pdf_splitter.py document.pdf --ranges "1-3,4-7,8-10" -o ./split
```

特定ページのみ抽出:

```bash
python3 pdf_splitter.py report.pdf --ranges "1,5,10" -o ./pages
```

---

## 3. PDF結合 (pdf_merger.py)

複数のPDFファイルを1つに結合。

### Quick Start

GUIでファイルを選択:

```bash
python3 pdf_merger.py --select-files
```

### CLI Examples

```bash
# 基本的な使い方（2つ以上のPDFが必要）
python3 pdf_merger.py file1.pdf file2.pdf -o merged.pdf

# 複数のPDFを結合
python3 pdf_merger.py doc1.pdf doc2.pdf doc3.pdf --output combined.pdf

# ワイルドカードを使用
python3 pdf_merger.py chapter*.pdf -o book.pdf

# 詳細ログ表示
python3 pdf_merger.py file1.pdf file2.pdf -o merged.pdf --verbose
```

### 結合の順序

入力ファイルの順序がそのまま結合順序になります。

```bash
# file1.pdf → file2.pdf → file3.pdf の順で結合
python3 pdf_merger.py file1.pdf file2.pdf file3.pdf -o output.pdf
```

### Options

- `-o`, `--output`: 出力PDFファイル（必須、またはGUIモード）
- `--select-files`: GUIダイアログで選択
- `--verbose`: 詳細ログ表示

### 使用例

複数の章を1つの文書に結合:

```bash
python3 pdf_merger.py intro.pdf chapter1.pdf chapter2.pdf conclusion.pdf -o book.pdf
```

スキャンした複数ページを1つのPDFに:

```bash
python3 pdf_merger.py scan_page*.pdf -o scanned_document.pdf
```

---

## 4. PDFページ操作 (pdf_edit.py)

PDFのページ削除・並べ替え・挿入を行うツール。

### Quick Start

GUIでファイルと操作を選択:

```bash
python3 pdf_edit.py --select-files
```

### CLI Examples

```bash
# ページ削除（1,3,5-7ページを削除）
python3 pdf_edit.py input.pdf --delete "1,3,5-7" -o output.pdf

# ページ並べ替え（3,1,2,4-10の順に）
python3 pdf_edit.py input.pdf --reorder "3,1,2,4-10" -o output.pdf

# ページ挿入（source.pdfの1-3ページを5ページ目の位置に挿入）
python3 pdf_edit.py input.pdf --insert "source.pdf:1-3@5" -o output.pdf

# 複数操作の組み合わせ
python3 pdf_edit.py input.pdf --delete "1,5" --reorder "2,1,3-10" -o output.pdf

# 詳細ログ表示
python3 pdf_edit.py input.pdf --delete "1-5" -o output.pdf --verbose
```

### 操作の詳細

#### ページ削除 (--delete)

指定したページを削除します。

| 形式 | 説明 | 例 |
|------|------|-----|
| `1` | 単一ページ削除 | `--delete "1"` |
| `1-5` | 範囲削除 | `--delete "1-5"` |
| `1,3,5` | 複数ページ削除 | `--delete "1,3,5"` |
| `1-3,5-7` | 複数範囲削除 | `--delete "1-3,5-7"` |

#### ページ並べ替え (--reorder)

ページの順序を変更します。全ページを指定する必要があります。

| 形式 | 説明 | 例 |
|------|------|-----|
| `3,1,2` | 3ページのPDFを並べ替え | `--reorder "3,1,2"` |
| `1-5,10,6-9` | 範囲を含む並べ替え | `--reorder "1-5,10,6-9"` |
| `10,9,8,7,6,5,4,3,2,1` | 逆順 | `--reorder "10-1"` |

#### ページ挿入 (--insert)

別のPDFから指定ページを挿入します。

形式: `source.pdf:pages@position`

| 例 | 説明 |
|-----|------|
| `source.pdf:1@5` | source.pdfの1ページ目を5ページ目の位置に挿入 |
| `source.pdf:1-3@5` | source.pdfの1-3ページを5ページ目の位置に挿入 |
| `source.pdf:1,3,5@1` | source.pdfの1,3,5ページを先頭に挿入 |

### Options

- `-o`, `--output`: 出力PDFファイル（必須、またはGUIモード）
- `--delete`: 削除するページ
- `--reorder`: 並べ替え後のページ順序
- `--insert`: 挿入するページ（`source.pdf:pages@position`形式）
- `--select-files`: GUIダイアログで選択
- `--verbose`: 詳細ログ表示

### 使用例

10ページのPDFから不要なページを削除:

```bash
python3 pdf_edit.py document.pdf --delete "2,5,8-10" -o cleaned.pdf
```

章の順序を変更:

```bash
python3 pdf_edit.py book.pdf --reorder "1,3,2,4-10" -o reordered.pdf
```

表紙を別PDFから挿入:

```bash
python3 pdf_edit.py main.pdf --insert "cover.pdf:1@1" -o final.pdf
```

---

## 5. PDFページ番号挿入 (pdf_page_number.py)

PDFの各ページに自動でページ番号を挿入するツール。

### Quick Start

GUIでファイルと設定を選択:

```bash
python3 pdf_page_number.py --select-files
```

### CLI Examples

```bash
# 基本的な使い方（下部中央にページ番号）
python3 pdf_page_number.py input.pdf -o output.pdf

# 位置を指定（右下）
python3 pdf_page_number.py input.pdf -o output.pdf --position bottom-right

# フォーマット指定（"Page 1 of 10"形式）
python3 pdf_page_number.py input.pdf -o output.pdf --format "Page {page} of {total}"

# 表紙ページをスキップ
python3 pdf_page_number.py input.pdf -o output.pdf --skip-pages "1"

# フォントサイズ変更
python3 pdf_page_number.py input.pdf -o output.pdf --font-size 12

# 開始番号を指定（0から開始）
python3 pdf_page_number.py input.pdf -o output.pdf --start-number 0

# 詳細ログ表示
python3 pdf_page_number.py input.pdf -o output.pdf --verbose
```

### 位置指定

| 位置 | 説明 |
|------|------|
| `top-left` | 上部左 |
| `top-center` | 上部中央 |
| `top-right` | 上部右 |
| `bottom-left` | 下部左 |
| `bottom-center` | 下部中央（デフォルト） |
| `bottom-right` | 下部右 |

### フォーマット指定

| フォーマット | 出力例 |
|-------------|--------|
| `{page}` | `1` |
| `Page {page}` | `Page 1` |
| `{page}/{total}` | `1/10` |
| `- {page} -` | `- 1 -` |
| `第{page}ページ` | `第1ページ` |

`{page}`: 現在のページ番号  
`{total}`: 総ページ数

### Options

- `-o`, `--output`: 出力PDFファイル（必須、またはGUIモード）
- `--position`: ページ番号の位置（デフォルト: `bottom-center`）
- `--format`: ページ番号のフォーマット（デフォルト: `{page}`）
- `--font-size`: フォントサイズ（デフォルト: 10）
- `--start-number`: 開始ページ番号（デフォルト: 1）
- `--skip-pages`: スキップするページ（カンマ区切り）
- `--select-files`: GUIダイアログで選択
- `--verbose`: 詳細ログ表示

### 使用例

プレゼン資料に右下にページ番号:

```bash
python3 pdf_page_number.py presentation.pdf -o numbered.pdf --position bottom-right --format "{page}/{total}"
```

表紙と目次をスキップ:

```bash
python3 pdf_page_number.py book.pdf -o numbered.pdf --skip-pages "1,2"
```

0から開始するページ番号:

```bash
python3 pdf_page_number.py document.pdf -o numbered.pdf --start-number 0
```

---

## 6. PDFバッチ処理 (pdf_batch.py)

複数のPDFファイルに対して同じ操作を一括実行するツール。

### サポートする操作

- ページ番号追加（バッチ）
- PDF分割（バッチ）
- ページ削除（バッチ）

### CLI Examples

```bash
# バッチページ番号追加
python3 pdf_batch.py add-page-numbers --input-dir ./pdfs --output-dir ./numbered --position bottom-center

# バッチ分割
python3 pdf_batch.py split --input-dir ./pdfs --output-dir ./split --ranges "1-5,6-10"

# バッチページ削除
python3 pdf_batch.py delete --input-dir ./pdfs --output-dir ./edited --delete-pages "1"

# 詳細ログ表示
python3 pdf_batch.py add-page-numbers --input-dir ./pdfs --output-dir ./numbered --verbose
```

### バッチページ番号追加

ディレクトリ内の全PDFにページ番号を追加。

```bash
python3 pdf_batch.py add-page-numbers \
  --input-dir ./documents \
  --output-dir ./numbered \
  --position bottom-right \
  --format "Page {page} of {total}"
```

**Options**:
- `--input-dir`: 入力PDFディレクトリ
- `--output-dir`: 出力ディレクトリ
- `--position`: ページ番号の位置
- `--format`: フォーマット
- `--font-size`: フォントサイズ

### バッチ分割

ディレクトリ内の全PDFを分割。各PDFごとにサブディレクトリが作成されます。

```bash
python3 pdf_batch.py split \
  --input-dir ./documents \
  --output-dir ./split \
  --ranges "1-3,4-7,8-10"
```

**Options**:
- `--input-dir`: 入力PDFディレクトリ
- `--output-dir`: 出力ディレクトリ
- `--ranges`: ページ範囲

### バッチページ削除

ディレクトリ内の全PDFから指定ページを削除。

```bash
python3 pdf_batch.py delete \
  --input-dir ./documents \
  --output-dir ./edited \
  --delete-pages "1,5-7"
```

**Options**:
- `--input-dir`: 入力PDFディレクトリ
- `--output-dir`: 出力ディレクトリ
- `--delete-pages`: 削除するページ

### 処理サマリー

各バッチ操作の完了後、処理サマリーが表示されます：

```
============================================================
Batch Page Number Addition Summary
============================================================
Total files: 10
Success: 9
Failed: 1

Failed files:
  - corrupted.pdf: File is not a valid PDF
```

### 使用例

プレゼン資料フォルダに一括でページ番号:

```bash
python3 pdf_batch.py add-page-numbers \
  --input-dir ./presentations \
  --output-dir ./presentations_numbered \
  --position bottom-right \
  --format "{page}/{total}"
```

複数文書を一括分割:

```bash
python3 pdf_batch.py split \
  --input-dir ./contracts \
  --output-dir ./contract_pages \
  --ranges "1-2,3-10"
```

---

## Development

### テスト実行

```bash
# すべてのテスト実行
pytest

# カバレッジ確認
pytest --cov=. --cov-report=term-missing

# 特定のテストのみ
pytest tests/test_pdf_splitter.py -v
```

### プロジェクト構造

```
PDFproject/
├── img2pdf.py              # 画像→PDF変換
├── pdf_splitter.py         # PDF分割
├── pdf_merger.py           # PDF結合
├── pdf_edit.py             # PDFページ操作
├── pdf_page_number.py      # PDFページ番号挿入
├── pdf_batch.py            # PDFバッチ処理 ⭐ NEW
├── tests/                  # テストコード
│   ├── test_pdf_splitter.py
│   ├── test_pdf_merger.py
│   ├── test_pdf_edit.py
│   ├── test_pdf_page_number.py
│   └── test_pdf_batch.py   ⭐ NEW
├── requirements.txt        # 依存ライブラリ
└── README.md              # このファイル
```

---

## License

MIT

---

## 今後の予定

- [x] ~~PDF結合機能（複数PDFを1つに）~~ ✅ 実装済み
- [x] ~~PDFページ操作（挿入・削除・並べ替え）~~ ✅ 実装済み
- [x] ~~PDFページ番号挿入~~ ✅ 実装済み
- [x] ~~PDFバッチ処理~~ ✅ 実装済み
- [ ] PDF圧縮機能
- [ ] PDF暗号化・パスワード保護
