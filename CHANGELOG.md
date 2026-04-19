# Changelog

このプロジェクト (PDF Tool — クライアントサイド PDF エディタ) の主な変更を記録します。
書式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠し、
バージョン番号は [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に従います。

---

## [1.3.0] — 2026-04-19

**注釈サイズのズーム不変化、取り消し線の二重線間隔調整、保存ボタン明示化、回転 UX 改善**

### Added
- 取り消し線に**フィルハンドル**を追加（端点 2 点 + 中点伸縮 + 線脇の二重線間隔調整）
  緑色のハンドルを線に垂直方向にドラッグすると 2 本の平行線の間隔が広がる／狭まる
- プロパティパネルに「**二重線の間隔**」入力欄を追加（取り消し線専用、pt 単位）
- ページ回転をサムネ未選択時に**ビューポート中央のページ 1 枚**へ自動フォールバック
  1 ページずつ向きを直したいときワンクリックで完了する

### Changed
- 「ダウンロード」ボタンを「**保存・ダウンロード**」に改名（保存動作の明示化）
- ツール用サイズ入力 (`tool-size`) を **PDF point として直接解釈**するよう変更
  従来は `state.toolSize / VIEW_SCALE` で都度割っていたためズーム率に依存していた
- 回転ボタンの tooltip / welcome テキストを「未選択時は表示中の 1 枚」に更新
- `使い方ガイド.html` を v1.3 機能に合わせて全面的に更新（章番号再採番、回転章追加、取り消し線サブ章追加）

### Fixed
- **縮小表示で書き込んだ注釈が拡大・印刷時にズレる問題を修正**
  - `pointToPdf` を SVG `getScreenCTM().inverse()` ベースに変更（CSS サブピクセル丸めを排除）
  - `measureTextWidth` を VIEW_SCALE 非依存（固定参照スケール 4×）にしてズーム差で行折り返しが揺れないように
  - フォントサイズ・線の太さがズームに関わらず PDF point として保存される

### Verification
- macOS 上の Chrome / Safari でユーザーによる動作確認完了（縮小表示でハイライト・テキスト挿入 → 100% 表示で位置一致を確認）
- 取り消し線の 4 ハンドル（p1/p2/pm/pg）の動作確認完了
- 回転ボタン: サムネ未選択 / 単一選択 / 複数選択の 3 ケースで挙動確認

---

## [1.2.0] — (過去リリース)

**CSP × Blob URL × Inline Library 問題の解決**

### Fixed
- Standalone HTML (`本体：ダブルクリックで作動.html`) の CSP を修正:
  - `script-src` に `'unsafe-eval'`, `blob:` を追加（pdf-lib / pdf.js 内部 `new Function()` 用）
  - `worker-src 'self' blob:` を追加（PDF.js Worker は Blob URL 経由）
- Chrome / Edge / Safari / Firefox + macOS / Windows / Linux の組み合わせで動作確認

---

## [1.1.0] — (過去リリース)

### Added
- スタンドアロン版（バンドル HTML）追加：lib/ 参照型に加え単一 HTML で配布可能に
- ファイル名を日本語化（`本体：ダブルクリックで作動.html` / `使い方ガイド.html`）

### Changed
- CDN 依存を全廃しオフライン動作可能に
- ZIP を UTF-8 名対応に

---

## [1.0.0] — (過去リリース)

### Added
- 初版リリース: lib/ 参照型 HTML エディタ。CDN 依存版。
