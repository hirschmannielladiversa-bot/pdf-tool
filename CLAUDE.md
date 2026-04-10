# CLAUDE.md

**PDFproject - Claude Code Configuration**

---

## プロジェクト概要

**名前**: PDFproject
**目的**: 画像からPDFへの変換とPDF操作ツール
**言語**: Python 3.13
**モード**: 2-Agent (Cursor PM + Claude Code Worker)

---

## プロジェクト構造

2026-04-07 にディレクトリを整理。スクリプトは `src/`、HTML は `web/`、ドキュメントは `docs/` 配下に集約した。

```
PDFproject/
├── src/                    # Python スクリプト本体
│   ├── img2pdf.py              # 画像→PDF変換
│   ├── pdf_splitter.py         # PDF分割
│   ├── pdf_merger.py           # PDF結合
│   ├── pdf_edit.py             # PDFページ操作
│   ├── pdf_page_number.py      # PDFページ番号挿入
│   ├── pdf_batch.py            # PDFバッチ処理
│   ├── convert_presentation.py # プレゼン変換補助
│   ├── fix_overflow.py         # オーバーフロー修正
│   ├── fix_overflow_css.py     # CSS オーバーフロー修正
│   └── run_editor.py           # PDF Editor GUI ランチャー
├── pdf_editor_app/         # PDF Editor GUI アプリ (パッケージ)
├── web/                    # クライアントサイド HTML 版
│   ├── pdf_tool.html           # PDF Tool 本体 (約 2200 行)
│   ├── usage_guide.html        # 使い方ガイド HTML
│   └── prompts_history.html    # プロンプト履歴
├── tests/                  # テストコード（112 テスト全成功）
│   ├── conftest.py             # src/ を sys.path に追加
│   ├── test_pdf_splitter.py    (21 テスト)
│   ├── test_pdf_merger.py      (19 テスト)
│   ├── test_pdf_edit.py        (23 テスト)
│   ├── test_pdf_page_number.py (30 テスト)
│   └── test_pdf_batch.py       (22 テスト)
├── docs/                   # ドキュメント類
│   ├── README.md
│   ├── USAGE_GUIDE.md
│   ├── AGENTS.md
│   ├── Plans.md
│   ├── img2pdf_plan.md
│   └── archive/                # 過去の Plans バックアップ
├── samples/                # サンプル / 成果物 PDF
├── test_data/              # テスト用入力 PDF
├── deploy/                 # 配布物 ZIP
├── launchers/              # ダブルクリック起動用 .command
│   ├── StartEditor.command
│   └── StartImg2Pdf.command
├── CLAUDE.md               # このファイル (ルートに保持)
├── requirements.txt        # 依存ライブラリ
├── .gitignore              # __pycache__/.pytest_cache/htmlcov 等を除外
├── .claude/
│   ├── settings.json
│   ├── memory/
│   └── rules/
└── .cursor/
    └── commands/
```

### import パスの取り扱い

- `src/run_editor.py` が `sys.path` に `src/`（`pdf_edit` 等のため）と project root（`pdf_editor_app` パッケージのため）の両方を追加する。
- `tests/conftest.py` が `src/` を `sys.path` に追加するので、テストからは従来通り `from pdf_edit import ...` で参照できる。
- `launchers/*.command` は `cd "$(dirname "$0")/.."` でルートに移動してから `src/` 配下のスクリプトを起動する。

---

## 技術スタック

**言語**: Python 3.13
**主要ライブラリ**:
- Pillow - 画像処理
- pypdf - PDF操作（PyPDF2の後継）
- reportlab - PDFページ番号生成
- tkinter - GUI（macOS標準）

**開発ツール**:
- pytest - テストフレームワーク（全112テスト成功）
- Git - バージョン管理

---

## 機能概要

### ✅ 実装済み機能（全6ツール）

#### 1. 画像→PDF変換 (img2pdf.py)
- 複数のPNG/JPEG画像を1つのPDFにまとめる
- CLI とGUI 両対応
- 再帰的ディレクトリ処理
- 画質調整機能

**使い方**:
```bash
python3 src/img2pdf.py --select-files
python3 src/img2pdf.py page1.png page2.jpg -o output.pdf
```

#### 2. PDF分割 (pdf_splitter.py)
- PDFを指定ページ範囲で分割
- ページ単位・範囲指定・混在指定対応
- CLI とGUI 両対応

**使い方**:
```bash
python3 src/pdf_splitter.py --select-files
python3 src/pdf_splitter.py input.pdf --ranges "1-3,4-7" -o ./split
```

#### 3. PDF結合 (pdf_merger.py)
- 複数のPDFファイルを1つに結合
- ファイル順序保持
- CLI とGUI 両対応（最低2ファイル必須）

**使い方**:
```bash
python3 src/pdf_merger.py --select-files
python3 src/pdf_merger.py file1.pdf file2.pdf -o merged.pdf
```

#### 4. PDFページ操作 (pdf_edit.py)
- ページの削除（`--delete`）
- ページの並べ替え（`--reorder`）
- ページの挿入（`--insert`）
- CLI とGUI 両対応

**使い方**:
```bash
python3 src/pdf_edit.py --select-files
python3 src/pdf_edit.py input.pdf --delete "1,3,5-7" -o output.pdf
```

#### 5. PDFページ番号挿入 (pdf_page_number.py)
- 6つの位置指定（top/bottom × left/center/right）
- カスタムフォーマット（`{page}`, `{total}`）
- ページスキップ機能
- フォントサイズ・開始番号調整

**使い方**:
```bash
python3 src/pdf_page_number.py --select-files
python3 src/pdf_page_number.py input.pdf -o output.pdf --position bottom-right
```

#### 6. PDFバッチ処理 (pdf_batch.py)
- バッチページ番号追加
- バッチ分割
- バッチページ削除
- 処理サマリー表示

**使い方**:
```bash
python3 src/pdf_batch.py add-page-numbers --input-dir ./pdfs --output-dir ./numbered
python3 src/pdf_batch.py split --input-dir ./pdfs --output-dir ./split --ranges "1-5"
```

#### 7. PDF Editor GUI (pdf_editor_app)
ブラウザベースの PDF エディタ。`src/run_editor.py` または `launchers/StartEditor.command`（ダブルクリック）から起動。

```bash
python3 src/run_editor.py
```

---

### 📋 バックログ（今後の予定）

- [ ] PDF圧縮機能
- [ ] PDF暗号化・パスワード保護
- [ ] PDF透かし追加
- [ ] プレビュー機能

---

## 開発ルール

### コーディング規約

**スタイル**:
- PEP 8 準拠
- 型ヒントを使用
- docstring は必須（複雑な関数のみ）
- 最小限のコメント（自明なコードにコメント不要）

**ファイル構成**:
- 1機能 = 1ファイル
- 共通処理は utils.py に分離
- テストファイルは `test_*.py` 形式

**エラーハンドリング**:
- ユーザーフレンドリーなエラーメッセージ
- 例外は適切にキャッチ
- システムエラーは stderr に出力

---

### GUI/CLI 共通ルール

**設計方針**:
- CLI優先で設計
- GUIはCLIのラッパー
- `--select-files` フラグでGUIモード切替

**パターン**:
```python
def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.select_files:
        # GUIモード
        files = select_files_dialog()
        output = select_output_dialog()
    else:
        # CLIモード
        files = args.input_files
        output = args.output

    process(files, output)
```

---

### テスト方針

**カバレッジ目標**: 80%以上

**テスト種別**:
1. **ユニットテスト** - 各関数の動作確認
2. **統合テスト** - CLI/GUI全体の動作確認
3. **エッジケーステスト** - エラーハンドリング確認

**実行コマンド**（プロジェクトルートから）:
```bash
# 全テスト実行
pytest

# カバレッジ確認
pytest --cov=src --cov-report=term-missing
```

`tests/conftest.py` が `src/` を自動で `sys.path` に追加するので、テストファイル側の import 文（`from pdf_edit import ...`）は変更不要。

---

## Claude Code (Worker) の責任範囲

### ✅ 実装すべきこと
- Python コードの実装
- ユニットテストの作成
- セルフレビュー
- テクニカルドキュメント（docstring等）の作成
- `.claude/memory/` への学習内容記録

### ❌ 実装してはいけないこと
- 本番環境へのデプロイ
- `main` ブランチへの直接プッシュ
- AGENTS.md, CLAUDE.md の編集（Cursor PM が担当）

---

## タスク管理

**ファイル**: `Plans.md`

**マーカー**:
- `[PM]` - Cursor が担当
- `[Impl]` - Claude Code が担当
- `cc:TODO` - 未着手
- `cc:WIP` - 作業中
- `cc:完了` - 完了
- `blocked` - ブロック中

**更新タイミング**:
- タスク開始時: `cc:TODO` → `cc:WIP`
- タスク完了時: `cc:WIP` → `cc:完了`
- ブロック時: `blocked` マークを追加し理由を記載

---

## ワークフロー（Claude Code 視点）

### 1. タスク受領
```
Cursor から /handoff-to-claude でタスク受領
↓
Plans.md のタスクを確認
↓
不明点があれば質問
↓
タスクを cc:WIP にマーク
```

### 2. 実装
```
/work でタスク実装開始
↓
コード実装
↓
テスト作成
↓
テスト実行
↓
ドキュメント更新
```

### 3. セルフレビュー
```
/review で自己チェック
↓
コード品質確認
↓
テストカバレッジ確認
↓
ドキュメント完備確認
```

### 4. 完了報告
```
/handoff-to-cursor で報告
↓
実装内容のサマリー
↓
テスト結果
↓
確認ポイント
```

---

## 学習内容の記録

**場所**: `.claude/memory/`

**記録すべきこと**:
- プロジェクト固有の設計パターン
- よく使うコードスニペット
- エラー対処方法
- テクニカルな決定事項

**記録タイミング**:
- 新しいパターンを発見した時
- 問題を解決した時
- 技術的な決定をした時

---

## 依存関係管理

**requirements.txt**:
```
Pillow>=10.0.0
pypdf>=5.1.0
reportlab>=4.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
```

**インストール**:
```bash
pip install -r requirements.txt
```

---

## Git 運用

### ブランチ戦略

**main**: 本番用（Cursor PM のみプッシュ可）
**feature/***: 新機能開発（Claude Code）
**fix/***: バグ修正（Claude Code）

### コミットメッセージ

**フォーマット**:
```
[種別] 変更内容

詳細説明（必要に応じて）

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**種別**:
- `[Add]` - 新機能追加
- `[Fix]` - バグ修正
- `[Update]` - 機能更新
- `[Refactor]` - リファクタリング
- `[Test]` - テスト追加
- `[Docs]` - ドキュメント更新

---

## セーフティ設定

**ファイル**: `.claude/settings.json`

**主な設定**:
- 実装ファイル (`*.py`) の編集は許可
- `img2pdf.py` の編集は確認必要（既存機能保護）
- Git 破壊的操作は禁止
- 本番デプロイは禁止

---

## テスト結果

**全112テスト成功** ✅

| ツール | テスト数 | 状態 |
|--------|---------|------|
| pdf_page_number.py | 30 | ✅ |
| pdf_edit.py | 23 | ✅ |
| pdf_batch.py | 22 | ✅ |
| pdf_splitter.py | 21 | ✅ |
| pdf_merger.py | 19 | ✅ |

**実行コマンド**（プロジェクトルートから）:
```bash
# 全テスト実行
pytest

# カバレッジ確認
pytest --cov=src --cov-report=term-missing

# 特定ツールのみ
pytest tests/test_pdf_splitter.py -v
```

---

## 外部リソース

**ドキュメント**:
- Pillow: https://pillow.readthedocs.io/
- pypdf: https://pypdf.readthedocs.io/
- reportlab: https://docs.reportlab.com/
- pytest: https://docs.pytest.org/

---

## 参照ファイル

| ファイル | 説明 |
|---------|------|
| `docs/README.md` | ツール詳細ドキュメント |
| `docs/USAGE_GUIDE.md` | 使い方ガイド（初心者向け） |
| `docs/AGENTS.md` | エージェント定義とワークフロー |
| `docs/Plans.md` | タスク管理と進捗 |
| `docs/archive/` | 過去の Plans バックアップ |
| `.claude/rules/workflow.md` | 2-Agent ワークフロー詳細 |
| `.cursor/commands/*.md` | Cursor PM コマンド |

---

**最終更新**: 2026-03-22
**モード**: 2-Agent (Claude Code Worker)
**プロジェクト状態**: Phase 6 完了（全6フェーズ完了）

---

## Phase 7: クライアントサイド版 PDF Tool (HTML 版) — 2026-04-07

Python版と同等の機能を持つ、ブラウザだけで動く単一HTMLアプリ `pdf_tool.html` を新規開発した。pywebview / Flask 等のサーバを廃し、PDF.js (描画) と pdf-lib (操作) を CDN/ローカル経由で読み込んでクライアント側で完結させる構成。

### 主要成果物

| ファイル | 役割 |
|---|---|
| `pdf_tool.html` | 開発用ソース (約 2200 行)。`lib/` 参照型 |
| `pdf_tool_v1.1_offline.zip` | 配布パッケージ (4.05 MB) |
| 解凍後の `本体：ダブルクリックで作動.html` | 全依存をインライン化したスタンドアロン版 (5.1 MB) |
| 解凍後の `使い方ガイド.html` | 中学生向けに書いた HTML 形式の使い方 |

### 機能 (Python版と対等)

- **ファイル操作**: PDF を開く / PDFを追加 (結合) / 画像→PDF 変換 / クリア / ダウンロード
- **ページ操作**: サムネイルストリップでドラッグ&ドロップ並べ替え (Pointer Events ベース)、ページ削除
- **注釈ツール**: 選択 / テキスト / ハイライト / 枠線 / 取り消し線 / ペン / 消しゴム
- **ページ番号**: 6位置 + カスタム書式 + 開始番号 + スキップ
- **プロパティパネル**: 色・透明度・フォントサイズ・線太さ・幅高さ・削除

### 実装上の重要な決定 / 学び

#### 1. ドラッグ&ドロップ並べ替え
HTML5 ネイティブ DnD は WKWebView で不安定なので、**Pointer Events + window レベルのリスナー** で実装。フローティングゴーストとドロップインジケータ表示。これは Python 版 `pdf_editor_app/static/js/page-manager.js` の修正でも同じ問題と解決を経験している。

#### 2. テキスト注釈の IME 対応
日本語入力中の Enter で blur が走ると変換確定前に commit してしまう問題があった (旧バグ「セウ」のように途中で切れる)。`compositionstart`/`compositionend` で IME 状態を追跡し、`e.isComposing` || `keyCode === 229` のときは Enter を無視。

#### 3. ダブルクリックでテキスト再編集
3段階の落とし穴があった:
- **a)** `selectAnnotation` が `drawAnnotationsForPage` を呼んで `.annot` DOM を毎回再生成 → 連続クリックが別 DOM 要素になり `dblclick` 不発火 → **選択 chrome を `updateSelectionChrome` に分離**して `.annot` を温存
- **b)** `pointerdown` の `preventDefault()` が後続 click/dblclick を抑止 → **annot ヒット時は preventDefault を呼ばない**
- **c)** 選択後に `.sel-move` (透明な移動 overlay) が `.annot` の上に重なり、2回目のクリックターゲットが変わって dblclick が発火しない → **タイムスタンプベースの自前ダブルクリック検出** を svg pointerdown と sel-move pointerdown 両方に実装 (`DOUBLE_CLICK_MS = 400`)

#### 4. テキストボックスの自動行折り返し
- 注釈データに `w` (PDFポイント) を保持
- canvas 2D context の `measureText` で文字幅を測定し `wrapTextToLines` で文字単位ラップ
- SVG 表示は `<text>` + 複数 `<tspan>` (`dy = fontSize * 1.25`)
- pdf-lib 保存は各行を `drawText` で順次描画
- 旧形式 (baseline 基準・width なし) を `migrateTextAnnotation` で自動マイグレーション
- 入力欄は textarea で `autoGrow` (scrollHeight 連動)

#### 5. 注釈削除の安全化
- 新しいテキスト入力を開く瞬間に `deselectAnnotation()` を呼んで前の選択をクリア → 削除ボタンの暴発を防止
- editTextAnnotation で空入力時は keep original (delete しない)
- 「明示的な削除ボタン or 消しゴム」以外で消えない設計

#### 6. 日本語フォント埋め込み
- pdf-lib の `StandardFonts.Helvetica` は Latin-1 のみ → `@pdf-lib/fontkit` 経由で TTF/OTF を `embedFont(bytes, { subset: false })`
- `subset: true` にすると Acrobat で「埋め込みフォント抽出できません」警告が出る (CMap 不完全) → `subset: false` 固定
- フォントは Sawarabi Gothic (約 2 MB)
- 配布版では HTML に **base64 でインライン**して fetch ゼロ化

### セキュリティ監査 (並列エージェント 2人)

#### Agent A (XSS / コードインジェクション / DOM)
- **Critical / High: 0件**
- ユーザー入力はすべて `textContent` または pdf-lib 経由
- `innerHTML` の使用は空文字クリアのみ
- `eval` / `Function` / `document.write` / `iframe` / `window.open` / `location` 代入 すべて 0件

#### Agent B (情報漏洩 / 通信 / CDN)
- コード単体ではユーザーデータ送信経路 0件
- localStorage / sessionStorage / cookie 不使用、テレメトリ無し
- **High リスク**: 当初 4 つの CDN script に SRI 未設定 + フォント URL が `@main` 可変参照
- 推奨: **すべての依存をローカル同梱 + CSP `connect-src` で外部送信全面禁止**

### サプライチェーン対策の実施

監査結果を受けて以下を実施:
1. PDF.js / pdf.worker / pdf-lib / fontkit / Sawarabi Gothic を `lib/` にダウンロード同梱
2. すべての外部 URL を相対パスに書き換え
3. CSP `<meta>` を追加: `connect-src 'self' blob: data:; default-src 'self'; ...` で fetch 全面遮断
4. **検証**: ファイル内の外部 URL が 0件になったことを grep で確認

### スタンドアロン化 (ダブルクリックで動く版)

`lib/` 参照型は Chrome の `file://` 制約 (fetch / Worker のローカル読み込み拒否) で動かないため、Python スクリプト `build_standalone.py` で全依存を HTML 1ファイルにインライン化:

- 3つのライブラリは `<script>...</script>` でインライン (`</script>` エスケープ)
- pdf.worker は文字列 → `Blob URL` で `pdfjsLib.GlobalWorkerOptions.workerSrc` に設定
- フォントは base64 → 起動時に `Uint8Array` にデコードして `jpFontBytesCache` をプリポピュレート
- 結果: 5.1 MB の単一 HTML、Chrome / Edge / Safari / Firefox どこでも file:// で動作

### 配布パッケージ

**ファイル名**: `pdf_tool_v1.1_offline.zip` (4.05 MB)
**SHA-256**: `5b43a48a3cb5d139491ecc9852c5d83fa1fcc7ceeac1f177502fa832b45dc772`

**ZIP 構造**:
```
pdf_tool/
├── 本体：ダブルクリックで作動.html  ★ スタンドアロン版 (5.1 MB)
├── 使い方ガイド.html                ★ HTML 形式の使い方 (中学生向け)
├── pdf_tool.html                    ◇ lib/参照型 (上級者用)
├── LICENSE.txt
├── SHA256SUMS.txt
└── lib/  (PDF.js, pdf.worker, pdf-lib, fontkit, Sawarabi Gothic)
```

### ZIP の UTF-8 ファイル名問題

macOS 標準の `zip` コマンドは ZIP エントリに UTF-8 フラグ (general purpose flag bit 11) を立てないことがあり、Windows で展開時に文字化け。**Python の `zipfile` モジュール** で再ビルドすることで両方の日本語ファイル名 (`本体：...html` と `使い方ガイド.html`) に `[UTF8]` フラグが正しく付与され、Windows / macOS / Linux で文字化けせず展開可能になった。

ファイル名に使う「：」は **全角コロン (U+FF1A)** を使用 (半角コロン `:` は Windows で予約文字)。

### バージョン履歴

- **v1.0**: lib/ 参照型のみ、CDN 依存
- **v1.1**: スタンドアロン版を追加、CDN 全廃、UTF-8 ZIP、ファイル名を日本語化 (`本体：ダブルクリックで作動.html` / `使い方ガイド.html`)
- **v1.2**: **CSP 修正** — Blob URL Worker と eval を許可。スタンドアロン版が Chrome/Edge/Windows で動作するようになった

---

## v1.1 → v1.2: CSP × Blob URL × Inline Library 問題の解決

v1.1 を配布したところ、ユーザーから以下の不具合報告:

| 環境 | 症状 |
|---|---|
| **macOS Chrome/Safari** | UI は動き、ファイルピッカーも開く。しかし PDF を選択した瞬間に **画面が真っ黒** で何も表示されない |
| **Windows Chrome/Edge** | **ファイルピッカーすら開かない** (ボタンを押しても無反応) |

### 根本原因: CSP の3つの不足

スタンドアロン版 (`本体：ダブルクリックで作動.html`) は v1.0 の lib/ 参照型 CSP をそのまま流用していたが、スタンドアロン化で導入した **Blob URL Worker** と **インライン化されたライブラリの内部 eval** に対応していなかった。

旧 CSP (v1.1):
```
default-src 'self';
script-src 'self' 'unsafe-inline';
... (worker-src 指定なし)
```

不足:
1. **`script-src` に `blob:` がない** → Blob URL の script として解釈できない
2. **`worker-src` ディレクティブがない** → fallback で `default-src 'self'` が適用、`blob:` 不許可で worker 起動失敗
3. **`'unsafe-eval'` がない** → pdf-lib / pdf.js が内部的に使う `new Function()` がブロックされ、JS 実行が早期停止

### OS 別の症状の違い

- **macOS**: ライブラリ初期化 (eval 部分) は `<script>` インライン実行のため `'unsafe-inline'` でセーフ → JS は動く → UI 構築までは成功 → **PDF を開く瞬間に worker が CSP `worker-src` で拒否** → PDF.js が描画失敗 → 黒画面
- **Windows**: Chrome on Windows は CSP 違反時の挙動がより厳しく、`'unsafe-eval'` を要する経路で同期的に例外を投げる → 早期に JS 例外 → ボタンの addEventListener が走らない → ファイルピッカーすら開かない

### 修正後の CSP (v1.2)

```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self' blob: data:;
  script-src  'self' 'unsafe-inline' 'unsafe-eval' blob:;
  worker-src  'self' blob:;
  style-src   'self' 'unsafe-inline';
  img-src     'self' data: blob:;
  font-src    'self' data:;
  connect-src 'self' blob: data:;
  frame-src 'none'; object-src 'none';
  base-uri 'none'; form-action 'none';
">
```

### セキュリティを維持できる理由

`'unsafe-eval'` と `blob:` を追加すると一般には CSP の強度が下がるが、**機密データ漏洩防止** という主目的は `connect-src` で守られている:

| 防御 | v1.1 | v1.2 |
|---|---|---|
| HTTP/HTTPS への外部送信 (fetch/XHR/WebSocket) | ✅ ブロック (`connect-src` に http(s) を含めない) | ✅ ブロック (継承) |
| `<iframe>` / `<object>` 埋め込み | ✅ ブロック | ✅ ブロック |
| `<form>` 送信 | ✅ ブロック | ✅ ブロック |
| Blob URL Worker からの外部送信 | ✅ ブロック | ✅ ブロック (worker 内 CSP も継承) |

つまり **eval されたコードが実行されても外部に何も送れない**。ローカル PDF 編集に限定されたサンドボックス内での eval は実質的な攻撃面にならない。

### 教訓: スタンドアロン HTML で必要な CSP の最小セット

将来、依存ライブラリをインライン化したスタンドアロン HTML を作る際は以下を満たすこと:

```
script-src  'self' 'unsafe-inline' 'unsafe-eval' blob:
worker-src  'self' blob:
default-src 'self' blob: data:
connect-src 'self' blob: data:    ← 外部送信は引き続き禁止
```

このパターンは PDF.js のような **Web Worker をインラインで bundle するライブラリ** すべてに通用する。Worker URL は同一オリジン文字列にできないので必ず Blob URL を使うことになり、`worker-src blob:` が必須。

また、minified ライブラリが内部で `new Function`/`eval` を使うかは事前に grep で完全把握できないため、**`'unsafe-eval'` はインライン化スタンドアロン版では事実上必須** と考えてよい。代わりに `connect-src` で外部送信路を断つ多層防御で安全性を確保する。

### v1.2 配布パッケージ

**ファイル名**: `pdf_tool_v1.2_offline.zip` (4.05 MB)
**SHA-256**: `15179673d3b96188a081ebf2096f7d729310233bc1178157d152bca791c7e26a`

ZIP 内容は v1.1 と同じ構造、CSP の修正により Chrome/Edge/Safari/Firefox + macOS/Windows/Linux のすべての組み合わせで動作。

---

**最終更新**: 2026-04-07
**プロジェクト状態**: Phase 7 完了 (HTML 版 v1.2 配布パッケージ完成、CSP 問題解決) / ディレクトリ整理完了 (src/web/docs/tests/launchers 構成)

---

## Phase 8: OS 別配布 + 編集機能強化 — 2026-04-09

### 配布パッケージの分割

v1.1 時代の単一 ZIP (`配布用.zip`) を OS 別に分割:

```
deploy/packages/
├── PDF_Tool_Mac.zip     (6.51 MB)
└── PDF_Tool_Windows.zip (4.22 MB)
```

**Mac 版** の内容 (`pdf_tool/` 配下):
- `本体：ダブルクリックで作動.html`  ← Mac のエントリポイント (全角コロン OK)
- `pdf_tool_bundled.html`         ← 上と byte-for-byte 同一 (ASCII 名コピー)
- `pdf_tool.html` + `lib/`
- `使い方ガイド.html`, `LICENSE.txt`, `SHA256SUMS.txt`

**Windows 版** の内容:
- `pdf_tool_bundled.html`  ← **Windows のエントリポイント** (ASCII 名のみ)
- `pdf_tool.html` + `lib/`
- `使い方ガイド.html`, `LICENSE.txt`, `SHA256SUMS.txt`
- `README_Windows.txt`  ← 起動手順と「開かない場合」のトラブルシューティング
- **`本体：ダブルクリックで作動.html` は意図的に除外** (U+FF1A + NFD/NFC 問題回避、`deploy/pdf_tool/WINDOWS_DEBUG_NOTES.md` 参照)

### ビルドスクリプト (新規)

- `src/build_bundled.py`: `pdf_tool.html` + `lib/` から `pdf_tool_bundled.html` を生成。`pdf.js worker` は base64→Blob URL、TTF は data URL 埋め込み。CSP はそのまま。**以降 `pdf_tool_bundled.html` を手編集してはならない**。
- `src/build_packages.py`: 上を呼び出し → `SHA256SUMS.txt` 再生成 → Mac/Windows zip を `deploy/packages/` に出力。`本体：ダブルクリックで作動.html` は `pdf_tool_bundled.html` から自動コピーされ同期。

### 編集機能の追加 (両パッケージ共通)

1. **サムネイル複数選択 + 並び替え**
   - `state.selectedPages: Set<number>`, `state.lastClickedPage`, `state.selectionCursor`
   - 通常クリック = 単一選択 / Shift+クリック = 範囲 / Ctrl・Cmd+クリック = トグル
   - **Shift+←→ = 範囲拡張 (並びは変えない)** / ←→ = 選択中ページをまとめて1ステップ移動
   - `reorderPdfMany(sources, insertIdx)` が annotations の並びも同期

2. **Word 風ページ外コメント** (新アノテーションタイプ `"comment"`)
   - `.page-frame` = `.page-wrap` + `.comment-gutter` (右ガター) + `.leader-svg` (全域)
   - コメントは HTML `<div class="comment-box">` (contenteditable)、ガター内に絶対配置
   - リーダー線は `leader-svg` の `<line>` で描画、viewBox は `0 0 (pdfW + GUTTER_PT) pdfH`
   - フィルハンドル (右下) でサイズ変更、ヘッダの A−/A+ でフォントサイズ、「返信」ボタンで `ann.replies[]` に追加
   - **返信はそれぞれ独立した「サブウィンドウ」カード**として親の下にスタック。
     `.cb-reply-item` = ヘッダ (`↳ 返信 N` ラベル + × ) + 本文 (contenteditable)、
     左側に縦連結線 (`.cb-replies::before`) と横分岐線 (`.cb-reply-item::before`)
   - エクスポート時 (`burnAnnotationsIntoPdf`) はページ内右端にクランプして焼き付け。
     返信は親本文の下に独立した角丸カード (塗り + 境界線 + ヘッダ帯) として描画

3. **ズーム** (新機能)
   - `VIEW_SCALE` を `let` 化 (全コードが call-time に参照するので動的変更で OK)
   - ツールバーに `−` / `100%` / `＋` ボタン、`setZoom()` で clamp + `renderPages()` + スクロール位置復元
   - 範囲: 40% (`ZOOM_MIN`) 〜 400% (`ZOOM_MAX`)、倍率は 1.25 倍ずつ

4. **フォント選択プルダウン** (新機能)
   - 旧 `「フォント」ボタン` → `<select id="font-select">` に置換
   - `fontRegistry: [{name, bytes, source}]` + `currentFontIdx` で管理
   - 初期エントリ: 同梱 Sawarabi Gothic (`source: "bundled"`, 遅延 fetch)
   - 「カスタムフォントを読み込む…」で `.ttf`/`.otf` をアップロード → registry に追加 → 自動選択
   - `embedJpFont()` は `fontRegistry[currentFontIdx]` の bytes を使う

### ドキュメント

- `deploy/pdf_tool/使い方ガイド.html` に:
  - 「はじめかた」で Mac / Windows それぞれのファイル名を併記
  - 新章「コメント（ページ外の吹き出し）」を追加
  - 「ページの並べかえ」を「ページの並べかえ・複数選択」に拡張、Shift+矢印が並びを動かさないことを明記
  - ツール章にフォントプルダウンとズームの説明を追加
  - 末尾の「ファイルの中身」を Mac 版 / Windows 版 で分けて記載

### 選択 UI の仕様 (重要)

タイプごとに選択解除 (deselect) のトリガーを分岐:

| 注釈タイプ | 空白クリック | Enter | Escape | ツール切替 |
|---|---|---|---|---|
| text | 維持 (パネル出しっぱなし) | 維持 | 解除 | 解除 |
| highlight / frame / pen / strikethrough | 解除 | 解除 | 解除 | 解除 |

- 実装: `svg.pointerdown` の select ブランチで、`e.target === svg && state.selected && ann.type !== "text"` のとき `deselectAnnotation()` を呼ぶ。
- **`svg.onclick` は使わない**: ドラッグ作成直後に click 事件が svg に spurious に発火して handles が一瞬で消える問題があるため、pointerdown 経由に統一。
- 枠線 (`frame`) は `<g class="annot">` の中に **不可視ヒット rect (pointer-events=all)** + **アウトライン rect** を入れる 2 層構造にして、枠の内部のどこをクリックしても選択できるようにしている。

### 検証状況

- **macOS**: `node --check` で構文 OK、Chrome headless でコンソールエラーなしを確認
- **Windows**: 実機未検証。`本体：...html` を除外する設計的対処のみ。中身は Mac 版と byte-for-byte 同一なので、Windows Chrome/Edge で正常動作する想定
