# PDFproject 使い方ガイド

**初心者向けの実践的な使い方ガイド**

---

## 目次

1. [クイックスタート](#クイックスタート)
2. [よくある使い方パターン](#よくある使い方パターン)
3. [ツール選択ガイド](#ツール選択ガイド)
4. [トラブルシューティング](#トラブルシューティング)
5. [FAQ](#faq)

---

## クイックスタート

### 初めての方へ

PDFprojectは6つのツールを提供しています。全てGUI（ダイアログ）とCLI（コマンドライン）の両方で使えます。

### GUIで使う（最も簡単）

すべてのツールは `--select-files` オプションでGUIモードで使えます：

```bash
# 画像をPDFに変換
python3 img2pdf.py --select-files

# PDFを分割
python3 pdf_splitter.py --select-files

# PDFを結合
python3 pdf_merger.py --select-files

# PDFページを編集
python3 pdf_edit.py --select-files

# ページ番号を追加
python3 pdf_page_number.py --select-files
```

バッチ処理はディレクトリ指定が必要なのでCLI推奨です。

### CLIで使う（柔軟性が高い）

コマンドラインで詳細な設定ができます。各ツールの詳細は[README.md](README.md)を参照。

---

## よくある使い方パターン

### パターン1: スキャンした画像をPDFにまとめる

**シナリオ**: スキャナーで複数ページをPNG/JPEGで保存した

```bash
# 1. すべての画像を1つのPDFに
python3 img2pdf.py ./scanned_images -o document.pdf

# 2. 画質を調整（95が既定値）
python3 img2pdf.py ./scanned_images -o document.pdf --quality 90
```

**GUIで**:
```bash
python3 img2pdf.py --select-files
# → ダイアログで画像を複数選択
# → 保存先を指定
```

---

### パターン2: 大きなPDFを複数ファイルに分割

**シナリオ**: 100ページのPDFを章ごとに分けたい

```bash
# 1-20, 21-50, 51-100ページに分割
python3 pdf_splitter.py document.pdf --ranges "1-20,21-50,51-100" -o ./chapters

# 出力:
# ./chapters/document_p1-20.pdf
# ./chapters/document_p21-50.pdf
# ./chapters/document_p51-100.pdf
```

**特定ページだけ抽出**:
```bash
# 1, 5, 10ページだけ
python3 pdf_splitter.py document.pdf --ranges "1,5,10" -o ./pages
```

---

### パターン3: 複数のPDFを1つにまとめる

**シナリオ**: 章ごとに分かれたPDFを1冊の本にする

```bash
# 順序を指定して結合
python3 pdf_merger.py cover.pdf chapter1.pdf chapter2.pdf conclusion.pdf -o book.pdf
```

**ワイルドカードで一括**:
```bash
# chapter1.pdf, chapter2.pdf, ... を順番に結合
python3 pdf_merger.py chapter*.pdf -o book.pdf
```

---

### パターン4: PDFの不要ページを削除・並べ替え

**シナリオ**: プレゼン資料から余分なページを削除

```bash
# 2, 5, 8-10ページを削除
python3 pdf_edit.py presentation.pdf --delete "2,5,8-10" -o cleaned.pdf
```

**ページの順序を変更**:
```bash
# 3ページ目を先頭に
python3 pdf_edit.py document.pdf --reorder "3,1,2,4-10" -o reordered.pdf
```

**表紙を別PDFから挿入**:
```bash
# cover.pdfの1ページ目を先頭に挿入
python3 pdf_edit.py main.pdf --insert "cover.pdf:1@1" -o final.pdf
```

---

### パターン5: PDFにページ番号を追加

**シナリオ**: プレゼン資料にページ番号を入れたい

```bash
# 右下に「1/10」形式でページ番号
python3 pdf_page_number.py presentation.pdf -o numbered.pdf \
  --position bottom-right \
  --format "{page}/{total}"
```

**表紙だけスキップ**:
```bash
# 1ページ目（表紙）はページ番号なし
python3 pdf_page_number.py document.pdf -o numbered.pdf --skip-pages "1"
```

**0から開始**:
```bash
# プログラミングドキュメント風に0から
python3 pdf_page_number.py code_doc.pdf -o numbered.pdf --start-number 0
```

---

### パターン6: 複数PDFに一括で同じ操作

**シナリオ**: フォルダ内の全PDFにページ番号を追加したい

```bash
# バッチページ番号追加
python3 pdf_batch.py add-page-numbers \
  --input-dir ./documents \
  --output-dir ./numbered \
  --position bottom-center
```

**複数PDFを一括分割**:
```bash
# フォルダ内の全PDFを同じ範囲で分割
python3 pdf_batch.py split \
  --input-dir ./documents \
  --output-dir ./split \
  --ranges "1-5,6-10"
```

**複数PDFから表紙を一括削除**:
```bash
# 全PDFの1ページ目を削除
python3 pdf_batch.py delete \
  --input-dir ./documents \
  --output-dir ./without_cover \
  --delete-pages "1"
```

---

## ツール選択ガイド

### こんな時はどのツールを使う？

| やりたいこと | 使うツール | コマンド例 |
|-------------|----------|-----------|
| 画像をPDFにしたい | `img2pdf.py` | `img2pdf.py *.png -o out.pdf` |
| PDFを複数に分けたい | `pdf_splitter.py` | `pdf_splitter.py input.pdf --ranges "1-5,6-10"` |
| 複数PDFを1つにしたい | `pdf_merger.py` | `pdf_merger.py file1.pdf file2.pdf -o out.pdf` |
| PDFのページを削除したい | `pdf_edit.py` | `pdf_edit.py input.pdf --delete "1,5" -o out.pdf` |
| PDFのページを並べ替えたい | `pdf_edit.py` | `pdf_edit.py input.pdf --reorder "3,1,2" -o out.pdf` |
| 別PDFからページを挿入したい | `pdf_edit.py` | `pdf_edit.py input.pdf --insert "src.pdf:1@5" -o out.pdf` |
| ページ番号を付けたい | `pdf_page_number.py` | `pdf_page_number.py input.pdf -o out.pdf` |
| 複数PDFに同じ操作をしたい | `pdf_batch.py` | `pdf_batch.py add-page-numbers --input-dir ./docs` |

---

## 実践例: 論文PDFの作成

複数の章とフィギュアから論文PDFを作る例：

```bash
# ステップ1: 画像（フィギュア）をPDFに
python3 img2pdf.py ./figures -o figures.pdf

# ステップ2: 章PDFと結合
python3 pdf_merger.py cover.pdf abstract.pdf intro.pdf methods.pdf figures.pdf discussion.pdf -o draft.pdf

# ステップ3: 不要ページを削除
python3 pdf_edit.py draft.pdf --delete "15,20-22" -o cleaned.pdf

# ステップ4: ページ番号を追加（表紙と目次はスキップ）
python3 pdf_page_number.py cleaned.pdf -o final.pdf \
  --skip-pages "1,2" \
  --position bottom-center \
  --format "- {page} -"
```

---

## トラブルシューティング

### 問題: ツールが見つからない

**エラー**: `command not found: python3`

**解決**:
```bash
# Pythonがインストールされているか確認
python3 --version

# macOSならHomebrewでインストール
brew install python@3.13
```

---

### 問題: モジュールが見つからない

**エラー**: `ModuleNotFoundError: No module named 'pypdf'`

**解決**:
```bash
# 依存ライブラリをインストール
pip install -r requirements.txt

# または個別インストール
pip install pypdf reportlab Pillow
```

---

### 問題: GUIダイアログが表示されない

**エラー**: `tkinter not available for GUI mode`

**解決**:

macOSでは通常tkinkerは標準インストールされています。表示されない場合：

```bash
# Python 3をHomebrewで再インストール
brew reinstall python@3.13
```

---

### 問題: PDFが壊れている

**エラー**: `File is not a valid PDF`

**解決**:

1. 元のPDFをAdobe Acrobat Readerで開けるか確認
2. 開けない場合はPDF自体が破損している可能性
3. 他のPDFで試してみる

---

### 問題: ページ範囲の指定がわからない

**例**:
```bash
# 単一ページ
--ranges "5"

# 連続範囲（1-5ページ）
--ranges "1-5"

# 複数範囲（1-5と10-15ページ）
--ranges "1-5,10-15"

# 混在（1-3, 5, 7-9ページ）
--ranges "1-3,5,7-9"

# スペース区切りも可能
--ranges "1-3 5 7-9"
```

---

### 問題: 出力ファイルが作られない

**チェック項目**:

1. 出力ディレクトリが存在するか
   ```bash
   mkdir -p ./output
   ```

2. 書き込み権限があるか
   ```bash
   ls -la ./output
   ```

3. ディスク容量は十分か
   ```bash
   df -h
   ```

4. 詳細ログで確認
   ```bash
   python3 pdf_splitter.py input.pdf --ranges "1-5" -o ./output --verbose
   ```

---

## FAQ

### Q1. 全ツールで共通のオプションは？

A. 以下のオプションはほぼ全ツールで使えます：

- `-o`, `--output` - 出力ファイル/ディレクトリ
- `--select-files` - GUIモード
- `--verbose` - 詳細ログ表示

---

### Q2. PDFのパスワード保護はできる？

A. 現在はサポートしていません。今後の実装予定に含まれています。

---

### Q3. PDFを圧縮できる？

A. 現在はサポートしていません。今後の実装予定に含まれています。

---

### Q4. 複数の操作を一度にできる？

A. `pdf_edit.py` では複数操作を組み合わせられます：

```bash
# 削除と並べ替えを同時に
python3 pdf_edit.py input.pdf \
  --delete "1,5" \
  --reorder "2,1,3-10" \
  -o output.pdf
```

---

### Q5. GUIとCLIのどちらを使うべき？

A.

**GUIがおすすめ**:
- 初めて使う
- 1回限りの操作
- ファイル選択が楽

**CLIがおすすめ**:
- 同じ操作を繰り返す
- スクリプトで自動化したい
- 細かい設定が必要

---

### Q6. エラーが出たときはどうする？

A.

1. `--verbose` オプションで詳細ログを確認
2. 入力ファイルが正常か確認（他のPDFビューアで開けるか）
3. 権限やディスク容量を確認
4. それでも解決しない場合はGitHub Issuesへ

---

### Q7. バッチ処理で一部のPDFだけ失敗する

A. バッチ処理は失敗しても継続します。最後にサマリーが表示されます：

```
============================================================
Batch Processing Summary
============================================================
Total files: 10
Success: 9
Failed: 1

Failed files:
  - corrupted.pdf: File is not a valid PDF
```

失敗したファイルだけ個別に確認してください。

---

### Q8. ページ番号の位置を細かく調整したい

A. 現在は6つの固定位置のみサポートしています：

- `top-left`, `top-center`, `top-right`
- `bottom-left`, `bottom-center`, `bottom-right`

ピクセル単位の調整は今後の機能追加予定です。

---

### Q9. 日本語のページ番号は使える？

A. はい、使えます：

```bash
python3 pdf_page_number.py input.pdf -o output.pdf \
  --format "第{page}ページ"
```

出力: `第1ページ`, `第2ページ`, ...

---

### Q10. スクリプトで自動化したい

A. シェルスクリプトで簡単に自動化できます：

```bash
#!/bin/bash
# auto_process.sh

# 1. 画像をPDFに
python3 img2pdf.py ./images -o temp.pdf

# 2. ページ番号を追加
python3 pdf_page_number.py temp.pdf -o final.pdf

# 3. 一時ファイル削除
rm temp.pdf

echo "完了: final.pdf"
```

実行:
```bash
chmod +x auto_process.sh
./auto_process.sh
```

---

## さらに詳しく

- **各ツールの詳細**: [README.md](README.md)
- **プロジェクト構成**: [CLAUDE.md](CLAUDE.md)
- **タスク管理**: [Plans.md](Plans.md)
- **テスト**: `pytest` でテスト実行

---

**最終更新**: 2026-03-22
