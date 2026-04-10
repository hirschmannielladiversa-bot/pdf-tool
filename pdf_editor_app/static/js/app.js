/**
 * PDF Editor - Main Application Controller (ES module)
 * Wires together all modules and manages global state.
 */

import { PdfViewer } from './pdf-viewer.js';
import { Toolbar } from './toolbar.js';

// These modules will be provided by another agent.
// We import them dynamically so the app still boots if they are missing.
let AnnotationLayer, CommentPanel, PageManager;

try {
    ({ AnnotationLayer } = await import('./annotation-layer.js'));
} catch (_) {
    AnnotationLayer = null;
}
try {
    ({ CommentPanel } = await import('./comment-panel.js'));
} catch (_) {
    CommentPanel = null;
}
try {
    ({ PageManager } = await import('./page-manager.js'));
} catch (_) {
    PageManager = null;
}

class App {
    constructor() {
        this.currentFile = null;
        this.currentTool = 'select';
        this.currentColor = '#FF0000';
        this.scale = 1.5;
        this.annotations = {};   // { pageNum: [annotation, ...] }
        this.undoStack = [];
        this.redoStack = [];

        this.viewer = new PdfViewer(this);
        this.toolbar = new Toolbar(this);

        // Optional modules — gracefully handle if not yet available
        this.annotationLayer = AnnotationLayer ? new AnnotationLayer(this) : null;
        this.commentPanel = CommentPanel ? new CommentPanel(this) : null;
        this.pageManager = PageManager ? new PageManager(this) : null;
    }

    // ------------------------------------------------------------------
    // Initialization
    // ------------------------------------------------------------------

    async init() {
        console.log('[App] init started');

        // Set up UI immediately (before waiting for API)
        this.toolbar.init();
        if (this.commentPanel) this.commentPanel.init();
        if (this.pageManager) this.pageManager.init();
        this.setupKeyboardShortcuts();
        this.setupWelcomeButton();
        this.setupMenuBar();
        this.setupCommentToggle();

        console.log('[App] UI setup complete, waiting for API...');
        await this.waitForApi();
        console.log('[App] API ready');

        this.apiReady = true;
    }

    /** Wait until the pywebview bridge is ready (with timeout fallback). */
    waitForApi() {
        return new Promise((resolve) => {
            const check = () => {
                if (window.pywebview && window.pywebview.api) {
                    console.log('[App] pywebview.api found');
                    resolve();
                    return true;
                }
                return false;
            };
            if (check()) return;

            // Listen for the event
            window.addEventListener('pywebviewready', () => {
                console.log('[App] pywebviewready event received');
                resolve();
            });

            // Also poll as fallback (event may have already fired)
            let attempts = 0;
            const interval = setInterval(() => {
                attempts++;
                if (check()) {
                    clearInterval(interval);
                } else if (attempts > 100) {
                    console.warn('[App] API not available after 10s, continuing anyway');
                    clearInterval(interval);
                    resolve();
                }
            }, 100);
        });
    }

    // ------------------------------------------------------------------
    // File operations
    // ------------------------------------------------------------------

    async openFile() {
        console.log('[App] openFile called');
        if (!window.pywebview || !window.pywebview.api) {
            console.error('[App] pywebview API not available');
            this.showToast('APIが初期化されていません。少しお待ちください。');
            return;
        }
        try {
            console.log('[App] calling select_file...');
            const path = await window.pywebview.api.select_file();
            console.log('[App] select_file returned:', path);
            if (!path) return;

            this.currentFile = path;
            document.getElementById('file-name').textContent = path.split('/').pop();

            // Load PDF via base64 from Python backend
            const base64 = await window.pywebview.api.get_pdf_base64(path);
            if (!base64) {
                this.showToast('PDFの読み込みに失敗しました');
                return;
            }
            await this.viewer.loadPdf(base64);

            // Load saved annotations if any
            try {
                const saved = await window.pywebview.api.load_annotations(path);
                if (saved) {
                    this.annotations = JSON.parse(saved);
                    if (this.annotationLayer) this.annotationLayer.renderAll();
                }
            } catch (e) {
                console.warn('注釈の読み込みをスキップ:', e);
            }

            // Generate thumbnails
            if (this.pageManager) this.pageManager.generateThumbnails();

            // Hide welcome
            const welcome = document.getElementById('welcome-message');
            if (welcome) welcome.style.display = 'none';

            this.showToast('ファイルを開きました');
        } catch (err) {
            console.error('openFile error:', err);
            this.showToast('ファイルを開けませんでした');
        }
    }

    /** Auto-save annotations to JSON sidecar (for editing session). */
    async _autoSave() {
        if (!this.currentFile) return;
        try {
            await window.pywebview.api.save_annotations(
                this.currentFile,
                JSON.stringify(this.annotations)
            );
        } catch (err) {
            console.warn('自動保存エラー:', err);
        }
    }

    /** Alias for backward compatibility — called on annotation add/remove. */
    async saveAnnotations() {
        await this._autoSave();
    }

    /** 上書き保存: 注釈をPDFに直接書き込む */
    async savePdf() {
        if (!this.currentFile) {
            this.showToast('PDFが開かれていません');
            return;
        }
        try {
            // Force-commit any in-progress text edits (blur contenteditable)
            if (document.activeElement && document.activeElement.isContentEditable) {
                document.activeElement.blur();
                // Give time for blur handler to save
                await new Promise(r => setTimeout(r, 50));
            }
            this.showToast('保存中...');
            // Ensure sidecar JSON is synced before PDF export
            await window.pywebview.api.save_annotations(
                this.currentFile,
                JSON.stringify(this.annotations)
            );
            const result = await window.pywebview.api.export_with_annotations(
                this.currentFile,
                this.currentFile,
                JSON.stringify(this.annotations)
            );
            if (result && result.success) {
                // 注釈はクリアしない — 元PDFバックアップから常に再生成するため再編集可能
                // プレビューを更新（保存済みPDFを表示）
                const base64 = await window.pywebview.api.get_pdf_base64(this.currentFile);
                await this.viewer.loadPdf(base64);
                if (this.annotationLayer) this.annotationLayer.renderAll();
                if (this.pageManager) this.pageManager.generateThumbnails();
                this.showToast('PDFに保存しました（注釈は引き続き編集可能）');
            } else {
                this.showToast('保存に失敗しました: ' + (result?.error || ''));
            }
        } catch (err) {
            console.error('savePdf error:', err);
            this.showToast('保存に失敗しました');
        }
    }

    /** 名前を付けて保存: 別ファイルとして注釈埋め込みPDFを保存 */
    async saveAsPdf() {
        if (!this.currentFile) {
            this.showToast('PDFが開かれていません');
            return;
        }
        try {
            // Force-commit any in-progress text edits
            if (document.activeElement && document.activeElement.isContentEditable) {
                document.activeElement.blur();
                await new Promise(r => setTimeout(r, 50));
            }
            const outputPath = await window.pywebview.api.save_file_dialog();
            if (!outputPath) return;
            this.showToast('保存中...');
            // Ensure sidecar JSON is synced first
            await window.pywebview.api.save_annotations(
                this.currentFile,
                JSON.stringify(this.annotations)
            );
            const result = await window.pywebview.api.export_with_annotations(
                this.currentFile,
                outputPath,
                JSON.stringify(this.annotations)
            );
            if (result && result.success) {
                this.showToast('PDFを保存しました: ' + outputPath.split('/').pop());
            } else {
                this.showToast('保存に失敗しました: ' + (result?.error || ''));
            }
        } catch (err) {
            console.error('saveAsPdf error:', err);
            this.showToast('保存に失敗しました');
        }
    }

    // ------------------------------------------------------------------
    // Tool management
    // ------------------------------------------------------------------

    setTool(toolName) {
        this.currentTool = toolName;
        this.toolbar.updateActiveState(toolName);

        const cursors = {
            select: 'default',
            highlight: 'crosshair',
            text: 'text',
            pen: 'crosshair',
            rectangle: 'crosshair',
            comment: 'pointer',
            eraser: 'pointer',
        };
        document.getElementById('pdf-container').style.cursor = cursors[toolName] || 'default';

        // Toggle body class for text selection
        document.body.classList.toggle('tool-text', toolName === 'text');

        // When using drawing tools, disable pointer events on HTML annotation
        // boxes so the underlying canvas receives mouse events.
        const disablePtr = ['eraser', 'highlight', 'rectangle', 'pen', 'text', 'comment'].includes(toolName);
        document.querySelectorAll('.anno-box').forEach(el => {
            el.style.pointerEvents = disablePtr ? 'none' : 'auto';
        });
    }

    // ------------------------------------------------------------------
    // Annotation CRUD
    // ------------------------------------------------------------------

    addAnnotation(pageNum, annotation) {
        if (!this.annotations[pageNum]) this.annotations[pageNum] = [];
        this.annotations[pageNum].push(annotation);

        this.undoStack.push({ action: 'add', pageNum, annotation });
        this.redoStack = [];

        this.saveAnnotations();

        // Update comment panel if this is a comment annotation
        if (annotation.type === 'comment' && this.commentPanel) {
            this.commentPanel.refresh();
            // Auto-expand comment panel when adding a comment
            const panel = document.getElementById('comment-panel');
            if (panel) panel.classList.remove('collapsed');
        }
    }

    removeAnnotation(pageNum, annotationId) {
        if (!this.annotations[pageNum]) return;
        const idx = this.annotations[pageNum].findIndex(a => a.id === annotationId);
        if (idx === -1) return;

        const removed = this.annotations[pageNum].splice(idx, 1)[0];
        this.undoStack.push({ action: 'remove', pageNum, annotation: removed });
        this.redoStack = [];

        if (this.annotationLayer) this.annotationLayer.renderPage(pageNum);
        this.saveAnnotations();

        if (removed.type === 'comment' && this.commentPanel) {
            this.commentPanel.refresh();
        }
    }

    // ------------------------------------------------------------------
    // Undo / Redo
    // ------------------------------------------------------------------

    undo() {
        if (this.undoStack.length === 0) return;
        const entry = this.undoStack.pop();

        if (entry.action === 'add') {
            // Reverse an add → remove the annotation
            const list = this.annotations[entry.pageNum];
            if (list) {
                const idx = list.findIndex(a => a.id === entry.annotation.id);
                if (idx !== -1) list.splice(idx, 1);
            }
        } else if (entry.action === 'remove') {
            // Reverse a remove → re-add
            if (!this.annotations[entry.pageNum]) this.annotations[entry.pageNum] = [];
            this.annotations[entry.pageNum].push(entry.annotation);
        }

        this.redoStack.push(entry);

        if (this.annotationLayer) this.annotationLayer.renderPage(entry.pageNum);
        if (this.commentPanel) this.commentPanel.refresh();
        this.saveAnnotations();
    }

    redo() {
        if (this.redoStack.length === 0) return;
        const entry = this.redoStack.pop();

        if (entry.action === 'add') {
            // Re-apply the add
            if (!this.annotations[entry.pageNum]) this.annotations[entry.pageNum] = [];
            this.annotations[entry.pageNum].push(entry.annotation);
        } else if (entry.action === 'remove') {
            // Re-apply the remove
            const list = this.annotations[entry.pageNum];
            if (list) {
                const idx = list.findIndex(a => a.id === entry.annotation.id);
                if (idx !== -1) list.splice(idx, 1);
            }
        }

        this.undoStack.push(entry);

        if (this.annotationLayer) this.annotationLayer.renderPage(entry.pageNum);
        if (this.commentPanel) this.commentPanel.refresh();
        this.saveAnnotations();
    }

    // ------------------------------------------------------------------
    // Zoom
    // ------------------------------------------------------------------

    zoomIn() {
        this.scale = Math.min(this.scale + 0.25, 4.0);
        this.viewer.rerender();
        this.showToast(`ズーム: ${Math.round(this.scale * 100)}%`);
    }

    zoomOut() {
        this.scale = Math.max(this.scale - 0.25, 0.5);
        this.viewer.rerender();
        this.showToast(`ズーム: ${Math.round(this.scale * 100)}%`);
    }

    // ------------------------------------------------------------------
    // Keyboard shortcuts
    // ------------------------------------------------------------------

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            const mod = e.metaKey || e.ctrlKey;
            if (!mod) return;

            switch (e.key) {
                case 'o':
                    e.preventDefault();
                    this.openFile();
                    break;
                case 's':
                    e.preventDefault();
                    e.shiftKey ? this.saveAsPdf() : this.savePdf();
                    break;
                case 'z':
                    e.preventDefault();
                    e.shiftKey ? this.redo() : this.undo();
                    break;
                case '=':
                case '+':
                    e.preventDefault();
                    this.zoomIn();
                    break;
                case '-':
                    e.preventDefault();
                    this.zoomOut();
                    break;
            }
        });
    }

    // ------------------------------------------------------------------
    // UI helpers
    // ------------------------------------------------------------------

    setupWelcomeButton() {
        const btn = document.getElementById('welcome-open-btn');
        if (btn) btn.addEventListener('click', () => this.openFile());
    }

    setupMenuBar() {
        const menuItems = document.querySelectorAll('.menu-item');
        const dropdowns = document.querySelectorAll('.dropdown-menu');

        // Menu item click toggles dropdown
        menuItems.forEach((item) => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const menuId = 'menu-' + item.dataset.menu;
                const dd = document.getElementById(menuId);
                const wasVisible = dd.classList.contains('visible');

                // Close all
                dropdowns.forEach(d => d.classList.remove('visible'));
                menuItems.forEach(m => m.classList.remove('active'));

                if (!wasVisible) {
                    // Position and show
                    const rect = item.getBoundingClientRect();
                    dd.style.left = rect.left + 'px';
                    dd.classList.add('visible');
                    item.classList.add('active');
                }
            });
        });

        // Close menus on outside click
        document.addEventListener('click', () => {
            dropdowns.forEach(d => d.classList.remove('visible'));
            menuItems.forEach(m => m.classList.remove('active'));
        });

        // Dropdown actions
        document.querySelectorAll('.dropdown-item').forEach((item) => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdowns.forEach(d => d.classList.remove('visible'));
                menuItems.forEach(m => m.classList.remove('active'));

                const action = item.dataset.action;
                switch (action) {
                    case 'open': this.openFile(); break;
                    case 'save': this.savePdf(); break;
                    case 'save-as': this.saveAsPdf(); break;
                    case 'page-numbers': this.addPageNumbers(); break;
                    case 'undo': this.undo(); break;
                    case 'redo': this.redo(); break;
                    case 'zoom-in': this.zoomIn(); break;
                    case 'zoom-out': this.zoomOut(); break;
                    case 'fit-width': this.fitWidth(); break;
                }
            });
        });
    }

    setupCommentToggle() {
        const panel = document.getElementById('comment-panel');
        const header = document.getElementById('comment-panel-header');
        if (!panel || !header) return;

        // Start collapsed
        panel.classList.add('collapsed');

        header.addEventListener('click', () => {
            panel.classList.toggle('collapsed');
        });
    }

    fitWidth() {
        if (!this.viewer.pdfDoc) return;
        const viewerArea = document.getElementById('viewer-area');
        const availableWidth = viewerArea.clientWidth - 60; // padding
        // Estimate scale from first page
        const pageInfo = this.viewer.getPageInfo(1);
        if (pageInfo) {
            const naturalWidth = pageInfo.viewport.width / this.scale;
            this.scale = Math.max(0.5, Math.min(4.0, availableWidth / naturalWidth));
            this.viewer.rerender();
            this.showToast(`ズーム: ${Math.round(this.scale * 100)}%`);
        }
    }

    /** Show a temporary toast notification. */
    showToast(message, duration = 2000) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('visible');
        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => {
            toast.classList.remove('visible');
        }, duration);
    }

    /** Show page number dialog and add page numbers to PDF. */
    async addPageNumbers() {
        if (!this.currentFile) {
            this.showToast('PDFが開かれていません');
            return;
        }
        const opts = await this.showPageNumberDialog();
        if (!opts) return;
        try {
            this.showToast('ページ番号を追加中...');
            // First save current annotations into the PDF
            await window.pywebview.api.save_annotations(
                this.currentFile,
                JSON.stringify(this.annotations)
            );
            const save = await window.pywebview.api.export_with_annotations(
                this.currentFile,
                this.currentFile,
                JSON.stringify(this.annotations)
            );
            if (!save || !save.success) {
                this.showToast('注釈の保存に失敗しました');
                return;
            }
            // Then add page numbers
            const result = await window.pywebview.api.add_page_numbers(
                this.currentFile,
                this.currentFile,
                opts.position,
                opts.format,
                opts.fontSize,
                opts.startNumber
            );
            if (result && result.success) {
                const base64 = await window.pywebview.api.get_pdf_base64(this.currentFile);
                await this.viewer.loadPdf(base64);
                if (this.annotationLayer) this.annotationLayer.renderAll();
                if (this.pageManager) this.pageManager.generateThumbnails();
                this.showToast('ページ番号を追加しました');
            } else {
                this.showToast('ページ番号の追加に失敗しました: ' + (result?.error || ''));
            }
        } catch (err) {
            console.error('addPageNumbers error:', err);
            this.showToast('ページ番号の追加に失敗しました');
        }
    }

    /** Show page number configuration dialog. */
    showPageNumberDialog() {
        return new Promise((resolve) => {
            const overlay = document.getElementById('pagenum-dialog-overlay');
            const okBtn = document.getElementById('pagenum-dialog-ok');
            const cancelBtn = document.getElementById('pagenum-dialog-cancel');
            const positionEl = document.getElementById('pagenum-position');
            const formatEl = document.getElementById('pagenum-format');
            const fontSizeEl = document.getElementById('pagenum-fontsize');
            const startEl = document.getElementById('pagenum-start');

            overlay.style.display = 'flex';

            const cleanup = () => {
                overlay.style.display = 'none';
                okBtn.removeEventListener('click', onOk);
                cancelBtn.removeEventListener('click', onCancel);
            };
            const onOk = () => {
                cleanup();
                resolve({
                    position: positionEl.value,
                    format: formatEl.value || '{page}',
                    fontSize: parseInt(fontSizeEl.value) || 10,
                    startNumber: parseInt(startEl.value) || 1,
                });
            };
            const onCancel = () => { cleanup(); resolve(null); };

            okBtn.addEventListener('click', onOk);
            cancelBtn.addEventListener('click', onCancel);
        });
    }

    /** Generate a unique ID for annotations. */
    static generateId() {
        return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    }

    /**
     * Show a custom input dialog (replaces prompt() which is blocked in WKWebView).
     * @param {string} title - Dialog title text.
     * @param {string} placeholder - Input placeholder text.
     * @param {object} [options] - Optional settings: { showFontSize, showColor, defaultColor }
     * @returns {Promise<{text,fontSize,color}|null>} Result object, or null if cancelled.
     */
    showInputDialog(title = '入力', placeholder = 'テキストを入力...', options = {}) {
        return new Promise((resolve) => {
            const overlay = document.getElementById('input-dialog-overlay');
            const titleEl = document.getElementById('input-dialog-title');
            const input = document.getElementById('input-dialog-input');
            const okBtn = document.getElementById('input-dialog-ok');
            const cancelBtn = document.getElementById('input-dialog-cancel');
            const optionsDiv = document.getElementById('input-dialog-options');
            const fontSizeEl = document.getElementById('input-dialog-fontsize');
            const colorEl = document.getElementById('input-dialog-color');

            titleEl.textContent = title;
            input.placeholder = placeholder;
            input.value = '';

            // Show/hide options
            if (options.showFontSize || options.showColor) {
                optionsDiv.style.display = 'flex';
            } else {
                optionsDiv.style.display = 'none';
            }
            if (fontSizeEl) fontSizeEl.value = String(options.defaultFontSize || 12);
            if (colorEl) colorEl.value = options.defaultColor || '#FF0000';

            overlay.style.display = 'flex';
            input.focus();

            const cleanup = () => {
                overlay.style.display = 'none';
                okBtn.removeEventListener('click', onOk);
                cancelBtn.removeEventListener('click', onCancel);
                input.removeEventListener('keydown', onKey);
            };
            const onOk = () => {
                cleanup();
                const text = input.value.trim();
                if (!text) { resolve(null); return; }
                resolve({
                    text,
                    fontSize: fontSizeEl ? parseInt(fontSizeEl.value) : 12,
                    color: colorEl ? colorEl.value : '#FF0000',
                });
            };
            const onCancel = () => { cleanup(); resolve(null); };
            const onKey = (e) => {
                if (e.key === 'Enter') onOk();
                if (e.key === 'Escape') onCancel();
            };

            okBtn.addEventListener('click', onOk);
            cancelBtn.addEventListener('click', onCancel);
            input.addEventListener('keydown', onKey);
        });
    }
}

// ------------------------------------------------------------------
// Bootstrap
// ------------------------------------------------------------------

const app = new App();

// Module scripts are deferred, so DOMContentLoaded may have already fired
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => app.init());
} else {
    // DOM already ready
    app.init();
}

// Expose for other modules and debugging
window.app = app;
export default app;
export { App };
