# Plans.md

**PDFproject - Task Management and Progress Tracking**

---

## Current Status

**Last Updated**: 2026-03-21 (24:15)
**Mode**: 2-Agent (Cursor PM + Claude Code Worker)
**Active Sprint**: 全6フェーズ完了

---

## ✅ フェーズ1: プロジェクトセットアップ `cc:完了`

**完了日**: 2026-03-21
- 2-Agent ワークフロー基盤構築、環境診断（Python 3.13.5、pypdf、tkinter利用可能）

---

## ✅ フェーズ2: PDF分割機能 `cc:完了`

**完了日**: 2026-03-21
- **pdf_splitter.py**: ページ範囲指定でPDF分割（`1-3,4-7`形式）、CLI/GUI両対応

---

## ✅ フェーズ3: PDF結合機能 `cc:完了`

**完了日**: 2026-03-21
- **pdf_merger.py**: 複数PDFを1つに結合（2ファイル以上必須）、ファイル順序保持

---

## ✅ フェーズ4: PDFページ操作機能 `cc:完了`

**完了日**: 2026-03-21
- **pdf_edit.py**: ページ削除（`--delete`）、並べ替え（`--reorder`）、挿入（`--insert`）

---

## ✅ フェーズ5: PDFページ番号挿入機能 `cc:完了`

**完了日**: 2026-03-21
- **pdf_page_number.py**: 6つの位置指定、カスタムフォーマット、ページスキップ機能

---

## ✅ フェーズ6: PDFバッチ処理機能 `cc:完了`

**完了日**: 2026-03-21
- **pdf_batch.py**: 複数PDFへの一括処理（ページ番号追加、分割、ページ削除）、処理サマリー表示

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

---

## 🔵 バックログ

- [ ] PDF圧縮機能
- [ ] PDF暗号化・パスワード保護
- [ ] PDF透かし追加
- [ ] プレビュー機能

---

## 技術スタック

### 開発環境
- **言語**: Python 3.13.5
- **PDFライブラリ**: pypdf（PyPDF2の後継）
- **PDF生成**: reportlab（ページ番号オーバーレイ）
- **テスト**: pytest
- **GUI**: tkinter（macOS標準）

### プロジェクト構造

```
PDFproject/
├── img2pdf.py              # 画像→PDF変換
├── pdf_splitter.py         # PDF分割
├── pdf_merger.py           # PDF結合
├── pdf_edit.py             # PDFページ操作
├── pdf_page_number.py      # PDFページ番号挿入
├── tests/
│   ├── test_pdf_splitter.py (21テスト)
│   ├── test_pdf_merger.py (19テスト)
│   ├── test_pdf_edit.py (23テスト)
│   └── test_pdf_page_number.py (30テスト)
├── requirements.txt
└── README.md
```

### 設計パターン
- CLI優先、GUIはラッパー
- 1機能=1ファイル
- 既存のimg2pdf.pyパターンを踏襲
- 関数ベースの実装（クラス不使用）
- `--select-files`フラグでGUIモード

---

## マーカー凡例

| マーカー | 意味 |
|---------|------|
| `[PM]` | Cursor PMが担当 |
| `[Impl]` | Claude Codeが担当 |
| `cc:TODO` | 未着手 |
| `cc:WIP` | 作業中 |
| `cc:完了` | 完了 |

---

## Quick Reference

### Cursor PM コマンド

```bash
/start-session          # セッション開始
/project-overview       # プロジェクト概要確認
/plan-with-cc [要件]    # 実装計画作成
/handoff-to-claude      # 実装依頼
/review-cc-work         # 成果レビュー
```

### Claude Code コマンド

```bash
/work                   # タスク実装
/review                 # セルフレビュー
/verify                 # ビルド・テスト検証
/handoff-to-cursor      # 完了報告
```

---

**最終更新**: 2026-03-21 (24:00)
**バックアップ**: Plans.md.backup-phase5
