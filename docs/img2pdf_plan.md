# 画像→PDF変換CLIツール実装プラン

## プロジェクト概要

複数の画像ファイル（PNG/JPEG）を1つのPDFファイルに変換するコマンドラインツールを作成します。

## 要件

- **アプリケーションタイプ**: CLIツール（コマンドライン）
- **変換機能**: 複数画像を1つのPDFファイルにまとめる
- **サポート画像フォーマット**: PNG, JPEG
- **プラットフォーム**: macOS
- **依存関係**: 最小限（Pillowのみ、既にインストール済み）

## 推奨アプローチ

### ライブラリ選定

**採用: Pillow（PIL）のみ**

理由：
- 既にインストール済み（Pillow 11.3.0）
- PNG/JPEG読み込み + PDF保存が標準サポート
- 複数画像の結合が可能（`save_all=True`, `append_images`）
- 軽量で高速、追加依存関係不要

### ファイル構成

**単一ファイル方式**

ファイルパス: `/Users/takagimotonori/img2pdf.py`

理由：
- 既存のホームディレクトリスクリプトと同じパターン（`process_average.py`等）
- 機能がシンプル（約250-300行で実装可能）
- 配布・実行が容易

構成:
```python
#!/usr/bin/env python3
"""
Image to PDF Converter CLI Tool
Converts multiple PNG/JPEG images into a single PDF file
"""

# Imports
import argparse
import sys
from pathlib import Path
from PIL import Image

# Constants
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg'}

# Functions
def validate_image_files(paths: list[Path]) -> list[Path]
def convert_images_to_pdf(image_paths: list[Path], output_path: Path, quality: int, verbose: bool)
def main()

if __name__ == '__main__':
    main()
```

## 実装の詳細

### コマンドライン引数設計

基本使用例:
```bash
# 最小構成
python3 img2pdf.py image1.png image2.jpg -o output.pdf

# ワイルドカード使用
python3 img2pdf.py *.png -o report.pdf

# 詳細出力
python3 img2pdf.py photo*.jpg -o album.pdf --verbose
```

引数仕様:
| 引数 | タイプ | 必須 | 説明 | デフォルト |
|------|--------|------|------|-----------|
| `images` | 位置引数 | ✓ | 変換する画像ファイルパス（複数可） | - |
| `-o, --output` | オプション | ✓ | 出力PDFファイルパス | - |
| `-q, --quality` | オプション | - | JPEG品質（1-100） | `95` |
| `--verbose` | フラグ | - | 詳細な処理ログを出力 | `False` |

### 主要な処理フロー

```
起動
  ↓
コマンドライン引数パース（argparse）
  ↓
入力ファイル検証
  ├─ 存在確認
  ├─ 拡張子チェック（.png, .jpg, .jpeg）
  ├─ 読み取り権限確認
  └─ 最低1ファイル以上
  ↓
画像読み込み
  ├─ Pillow Image.open()
  ├─ RGBモード統一（PNGのRGBA → RGB変換）
  └─ エラーハンドリング（破損ファイル）
  ↓
PDF生成
  ├─ 1枚目: Image.save(output, 'PDF')
  └─ 2枚目以降: save_all=True, append_images=[...]
  ↓
成功メッセージ出力
  └─ 終了
```

### 核心コード（PDF生成部分）

```python
def convert_images_to_pdf(image_paths: list[Path], output_path: Path, quality: int, verbose: bool):
    """複数画像を1つのPDFに変換"""

    images = []

    for path in image_paths:
        if verbose:
            print(f"Reading: {path}")

        img = Image.open(path)

        # RGBAをRGBに変換（PDFはアルファチャンネル非対応）
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])  # アルファチャンネルをマスクに
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        images.append(img)

    # PDF保存
    if len(images) == 1:
        images[0].save(output_path, 'PDF', quality=quality)
    else:
        images[0].save(
            output_path,
            'PDF',
            save_all=True,
            append_images=images[1:],
            quality=quality
        )

    if verbose:
        print(f"✓ Created: {output_path}")
```

### エラーハンドリング

| エラー種類 | 検出タイミング | 対応 |
|-----------|--------------|------|
| ファイル不存在 | 引数検証時 | エラーメッセージ + `exit(1)` |
| 非対応フォーマット | 引数検証時 | エラーメッセージ + `exit(1)` |
| 破損画像ファイル | 画像読み込み時 | `try-except` → エラーメッセージ + `exit(1)` |
| 読み取り/書き込み権限なし | ファイル操作時 | `PermissionError` → エラーメッセージ + `exit(1)` |

エラーメッセージは `sys.stderr` に出力し、ユーザーフレンドリーな内容にします。

例:
```python
print(f"Error: File not found: {path}", file=sys.stderr)
print(f"Error: Unsupported format: {path.suffix} (expected: .png, .jpg, .jpeg)", file=sys.stderr)
```

## 重要なファイル

参考パターン:
- `/Users/takagimotonori/process_average.py` - エラーハンドリング例
- `/Users/takagimotonori/check_sheets.py` - ファイル検証パターン
- `/Volumes/tkg SSD/game/mario_game.py` - shebang、docstring、定数定義のパターン

実装ファイル:
- `/Users/takagimotonori/img2pdf.py` - メインスクリプト（新規作成）

## 検証方法（テスト手順）

### テストデータ準備

```bash
# テスト用ディレクトリ作成
mkdir -p /Users/takagimotonori/img2pdf_test
cd /Users/takagimotonori/img2pdf_test

# テスト画像生成
python3 << 'EOF'
from PIL import Image, ImageDraw

# 1. RGB PNG
img = Image.new('RGB', (800, 600), color='blue')
draw = ImageDraw.Draw(img)
draw.text((400, 300), "Page 1", fill='white', anchor='mm')
img.save('page1.png')

# 2. RGB JPEG
img = Image.new('RGB', (800, 600), color='red')
draw = ImageDraw.Draw(img)
draw.text((400, 300), "Page 2", fill='white', anchor='mm')
img.save('page2.jpg')

# 3. RGBA PNG（透過）
img = Image.new('RGBA', (800, 600), color=(0, 255, 0, 128))
draw = ImageDraw.Draw(img)
draw.text((400, 300), "Page 3", fill='black', anchor='mm')
img.save('page3_rgba.png')

print("✓ Test images created")
EOF
```

### テストケース

| # | テスト内容 | コマンド | 期待結果 |
|---|-----------|---------|---------|
| 1 | 単一PNG変換 | `python3 ~/img2pdf.py page1.png -o test1.pdf` | 1ページPDF生成 |
| 2 | 複数PNG変換 | `python3 ~/img2pdf.py page1.png page2.jpg -o test2.pdf` | 2ページPDF生成（順序保持） |
| 3 | RGBA PNG対応 | `python3 ~/img2pdf.py page3_rgba.png -o test3.pdf` | 白背景で変換 |
| 4 | 詳細出力 | `python3 ~/img2pdf.py page*.png -o test4.pdf --verbose` | 処理ログ表示 |
| 5 | 存在しないファイル | `python3 ~/img2pdf.py nofile.png -o test.pdf` | エラーメッセージ + exit(1) |
| 6 | 非対応フォーマット | `echo 'test' > test.txt && python3 ~/img2pdf.py test.txt -o test.pdf` | エラーメッセージ + exit(1) |

### PDF確認方法

```bash
# macOSでPDFを開く
open test2.pdf

# またはPreviewで確認
# - ページ数が正しいか
# - 画像の順序が保持されているか
# - 透過PNG（RGBA）が白背景で表示されるか
```

## 実装チェックリスト

### コア機能
- [x] argparseによるCLI引数パース
- [x] 画像ファイル検証（存在・フォーマット）
- [x] PNG/JPEG読み込み
- [x] RGBA→RGB変換（透過PNG対応）
- [x] 複数画像のPDF結合
- [x] エラーハンドリング
- [x] 成功メッセージ出力

### 品質
- [x] shebang行追加（`#!/usr/bin/env python3`）
- [x] Docstring追加
- [x] 型ヒント使用
- [x] エラーメッセージの明確化
- [x] Verbose出力対応

### テスト
- [ ] 単一画像変換
- [ ] 複数画像変換
- [ ] RGBA PNG対応
- [ ] エラーケース（不存在、非対応形式）
- [ ] 実際のPDFをmacOSで開いて確認

## 実装ステータス

**完了**: `/Users/takagimotonori/img2pdf.py` の実装が完了しました。

次のステップ:
1. テストデータの準備
2. 各テストケースの実行
3. PDF出力の確認

## 将来の拡張性（オプション）

フェーズ2候補機能:
- ページサイズ指定（A4, Letter等）
- 画像リサイズ（大きすぎる画像の自動縮小）
- ディレクトリ一括変換（`-d DIR`で全画像変換）
- 自然順ソート（`img1, img2, img10`を正しく並べ替え）
- PDFメタデータ設定（タイトル、作者情報）

## 実装後の使用方法

```bash
# 基本使用
cd /path/to/images
python3 ~/img2pdf.py *.png -o report.pdf

# 絶対パス指定
python3 ~/img2pdf.py /path/to/img1.jpg /path/to/img2.png -o ~/Desktop/output.pdf

# 詳細出力
python3 ~/img2pdf.py photo*.jpg -o album.pdf --verbose

# 品質調整（ファイルサイズ削減）
python3 ~/img2pdf.py *.jpg -o compressed.pdf -q 70
```

## まとめ

このプランに基づいて実装すれば、約250-300行の実用的なCLIツールが完成します。Pillowのみを使用し、既存環境で追加インストールなしで動作します。

実装の焦点:
1. **シンプルさ**: 単一ファイル、最小限の依存関係
2. **実用性**: エラーハンドリング、詳細出力オプション
3. **拡張性**: 将来的な機能追加が容易な設計
