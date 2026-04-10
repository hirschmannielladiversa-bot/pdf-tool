/**
 * page-manager.js - Thumbnail strip with drag-and-drop reorder
 *
 * Generates page thumbnails, handles page reorder (via Pointer Events),
 * delete, and insert operations.
 *
 * NOTE on drag implementation:
 *   The previous version used HTML5 native drag-and-drop (dragstart/dragover/drop).
 *   This is unreliable inside pywebview's WKWebView on macOS — events do not
 *   fire consistently. We now use Pointer Events (pointerdown/move/up) with
 *   setPointerCapture, which works reliably across WKWebView, Chromium and Gecko.
 */

export class PageManager {
    constructor(app) {
        this.app = app;
        this.container = null;
    }

    /**
     * Initialize the page manager by locating the thumbnail strip container.
     */
    init() {
        this.container = document.getElementById('thumbnail-strip');
        if (this.container) {
            // Ensure indicator can be positioned absolutely inside the strip.
            const computed = getComputedStyle(this.container);
            if (computed.position === 'static') {
                this.container.style.position = 'relative';
            }
        }
    }

    /**
     * Generate thumbnail images for all pages in the current PDF.
     */
    async generateThumbnails() {
        if (!this.app.viewer || !this.app.viewer.pdfDoc) return;
        if (!this.container) return;

        this.container.innerHTML = '';
        const pdfDoc = this.app.viewer.pdfDoc;

        const thumbMaxWidth = 60;
        const thumbMaxHeight = 70;

        for (let i = 1; i <= pdfDoc.numPages; i++) {
            const wrapper = document.createElement('div');
            wrapper.className = 'thumbnail-item';
            wrapper.dataset.pageNum = String(i);
            // Disable native HTML5 drag — we use Pointer Events instead.
            wrapper.draggable = false;
            // Prevent the browser's image-drag default on the inner canvas
            wrapper.style.touchAction = 'none';
            wrapper.style.userSelect = 'none';
            wrapper.style.webkitUserSelect = 'none';

            const canvas = document.createElement('canvas');
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.objectFit = 'contain';
            canvas.style.display = 'block';
            canvas.style.pointerEvents = 'none'; // let pointer events hit wrapper

            const label = document.createElement('div');
            label.className = 'thumbnail-label';
            label.textContent = String(i);

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'comment-delete thumb-delete-btn';
            deleteBtn.style.position = 'absolute';
            deleteBtn.style.top = '2px';
            deleteBtn.style.right = '2px';
            deleteBtn.style.fontSize = '12px';
            deleteBtn.style.lineHeight = '1';
            deleteBtn.style.padding = '0 3px';
            deleteBtn.style.background = 'rgba(0,0,0,0.5)';
            deleteBtn.style.color = '#e0e0e0';
            deleteBtn.style.border = 'none';
            deleteBtn.style.borderRadius = '3px';
            deleteBtn.style.cursor = 'pointer';
            deleteBtn.style.display = 'none';
            deleteBtn.style.zIndex = '5';
            deleteBtn.textContent = '\u00D7';
            deleteBtn.title = 'ページ削除';

            wrapper.addEventListener('mouseenter', () => {
                deleteBtn.style.display = 'block';
            });
            wrapper.addEventListener('mouseleave', () => {
                deleteBtn.style.display = 'none';
            });

            const pageNum = i;
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deletePage(pageNum);
            });
            // Stop drag-detection from starting when clicking the delete button.
            deleteBtn.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
            });

            wrapper.appendChild(canvas);
            wrapper.appendChild(label);
            wrapper.appendChild(deleteBtn);
            this.container.appendChild(wrapper);

            await this.app.viewer.renderThumbnail(i, canvas, thumbMaxWidth, thumbMaxHeight);

            // Click to scroll to page (suppressed when a drag has just occurred).
            wrapper.addEventListener('click', (e) => {
                if (wrapper._suppressClick) {
                    wrapper._suppressClick = false;
                    e.stopPropagation();
                    e.preventDefault();
                    return;
                }
                const pageInfo = this.app.viewer.getPageInfo(parseInt(wrapper.dataset.pageNum));
                if (pageInfo && pageInfo.pageDiv) {
                    pageInfo.pageDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });

            this.attachPointerDrag(wrapper);
        }

        // Insert button at the end
        const insertBtn = document.createElement('div');
        insertBtn.className = 'thumbnail-insert-btn';
        insertBtn.innerHTML = '+';
        insertBtn.title = 'ページを挿入';
        insertBtn.addEventListener('click', () => this.insertPages());
        this.container.appendChild(insertBtn);
    }

    // ------------------------------------------------------------------
    // Pointer-based drag-and-drop reorder
    // ------------------------------------------------------------------

    /**
     * Attach Pointer Events drag handling to a thumbnail wrapper.
     * - Click (no movement) still scrolls to the page.
     * - Movement beyond a small threshold begins a drag with a floating ghost
     *   and a vertical drop indicator showing the insertion point.
     */
    attachPointerDrag(wrapper) {
        const DRAG_THRESHOLD = 5; // px
        let startX = 0, startY = 0;
        let dragging = false;
        let pointerId = null;
        let ghost = null;
        let indicator = null;

        const onPointerDown = (e) => {
            if (e.button !== 0 && e.pointerType === 'mouse') return;
            // Ignore drags initiated on the delete button itself.
            if (e.target && e.target.closest('.thumb-delete-btn')) return;

            startX = e.clientX;
            startY = e.clientY;
            pointerId = e.pointerId;

            try {
                wrapper.setPointerCapture(pointerId);
            } catch (_) { /* not all targets allow capture */ }

            wrapper.addEventListener('pointermove', onPointerMove);
            wrapper.addEventListener('pointerup', onPointerUp);
            wrapper.addEventListener('pointercancel', onPointerUp);
        };

        const startDrag = (e) => {
            dragging = true;
            wrapper.classList.add('dragging');

            // Build a floating ghost that follows the cursor.
            ghost = wrapper.cloneNode(true);
            ghost.classList.add('thumbnail-ghost');
            // Strip the delete button from the ghost.
            const ghostBtn = ghost.querySelector('.thumb-delete-btn');
            if (ghostBtn) ghostBtn.remove();
            ghost.style.position = 'fixed';
            ghost.style.left = (e.clientX - 30) + 'px';
            ghost.style.top = (e.clientY - 40) + 'px';
            ghost.style.width = '60px';
            ghost.style.height = '80px';
            ghost.style.pointerEvents = 'none';
            ghost.style.opacity = '0.9';
            ghost.style.zIndex = '9999';
            document.body.appendChild(ghost);

            // Drop position indicator inside the strip.
            indicator = document.createElement('div');
            indicator.className = 'thumbnail-drop-indicator';
            this.container.appendChild(indicator);
        };

        const onPointerMove = (e) => {
            if (!dragging) {
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                if (Math.abs(dx) + Math.abs(dy) < DRAG_THRESHOLD) return;
                startDrag(e);
            }
            ghost.style.left = (e.clientX - 30) + 'px';
            ghost.style.top = (e.clientY - 40) + 'px';

            // Auto-scroll the strip horizontally near edges.
            const stripRect = this.container.getBoundingClientRect();
            const edge = 40;
            if (e.clientX < stripRect.left + edge) {
                this.container.scrollLeft -= 12;
            } else if (e.clientX > stripRect.right - edge) {
                this.container.scrollLeft += 12;
            }

            const target = this.computeDropTarget(e.clientX);
            this.updateIndicator(indicator, target);
        };

        const onPointerUp = (e) => {
            wrapper.removeEventListener('pointermove', onPointerMove);
            wrapper.removeEventListener('pointerup', onPointerUp);
            wrapper.removeEventListener('pointercancel', onPointerUp);
            if (pointerId !== null) {
                try { wrapper.releasePointerCapture(pointerId); } catch (_) {}
            }

            if (!dragging) {
                // Treat as a plain click — handler will run normally.
                return;
            }

            const sourceIdx = this.getDomIndex(wrapper);
            const target = this.computeDropTarget(e.clientX);
            const insertIdx = target.insertIndex;

            // Cleanup visual state.
            wrapper.classList.remove('dragging');
            if (ghost) { ghost.remove(); ghost = null; }
            if (indicator) { indicator.remove(); indicator = null; }
            dragging = false;

            // Suppress the click that fires after pointerup.
            wrapper._suppressClick = true;

            // No-op cases: dropped onto the same slot or onto its own right edge.
            if (insertIdx === sourceIdx || insertIdx === sourceIdx + 1) {
                return;
            }

            this.performReorder(sourceIdx, insertIdx);
        };

        wrapper.addEventListener('pointerdown', onPointerDown);
    }

    /**
     * Return the position (0-based) of *wrapper* among the .thumbnail-item siblings.
     */
    getDomIndex(wrapper) {
        const items = Array.from(this.container.querySelectorAll('.thumbnail-item'));
        return items.indexOf(wrapper);
    }

    /**
     * Compute the insertion gap nearest the cursor X coordinate.
     * Returns { insertIndex, items } where insertIndex is 0..items.length.
     */
    computeDropTarget(clientX) {
        const items = Array.from(this.container.querySelectorAll('.thumbnail-item'));
        let insertIndex = items.length;
        for (let i = 0; i < items.length; i++) {
            const rect = items[i].getBoundingClientRect();
            const center = rect.left + rect.width / 2;
            if (clientX < center) {
                insertIndex = i;
                break;
            }
        }
        return { insertIndex, items };
    }

    /**
     * Position the drop indicator at the insertion gap.
     */
    updateIndicator(indicator, target) {
        const items = target.items;
        if (items.length === 0) return;

        const containerRect = this.container.getBoundingClientRect();
        let xViewport;
        if (target.insertIndex >= items.length) {
            const last = items[items.length - 1].getBoundingClientRect();
            xViewport = last.right + 4;
        } else {
            const item = items[target.insertIndex].getBoundingClientRect();
            xViewport = item.left - 4;
        }
        const x = xViewport - containerRect.left + this.container.scrollLeft;
        indicator.style.left = x + 'px';
    }

    /**
     * Reorder the PDF by moving the page at sourceDomIndex into insertIndex.
     * Calls the Python backend and reloads the PDF on success.
     */
    async performReorder(sourceDomIndex, insertIndex) {
        if (!this.app.currentFile) return;
        const totalPages = this.app.viewer.pdfDoc.numPages;
        if (totalPages <= 1) return;

        // Build the current order from DOM dataset (1-based PDF page numbers).
        const items = Array.from(this.container.querySelectorAll('.thumbnail-item'));
        const order = items.map(el => parseInt(el.dataset.pageNum));

        if (sourceDomIndex < 0 || sourceDomIndex >= order.length) return;

        // Move source into insertIndex. After splice removal, indices >= source shift down.
        const [moved] = order.splice(sourceDomIndex, 1);
        let target = insertIndex;
        if (target > sourceDomIndex) target -= 1;
        if (target < 0) target = 0;
        if (target > order.length) target = order.length;
        order.splice(target, 0, moved);

        // Sanity check: must be a permutation of 1..totalPages
        if (order.length !== totalPages) {
            alert(`内部エラー: ページ数が一致しません (${order.length} vs ${totalPages})`);
            return;
        }

        try {
            const newOrderJson = JSON.stringify(order);
            const result = await window.pywebview.api.reorder_pages(
                this.app.currentFile, newOrderJson
            );
            if (result && result.success) {
                await this.reloadAfterChange();
            } else {
                alert('ページの並べ替えに失敗しました: ' + (result?.error || '不明なエラー'));
            }
        } catch (err) {
            alert('ページの並べ替えに失敗しました: ' + err.message);
        }
    }

    // ------------------------------------------------------------------
    // Page delete / insert (unchanged behavior)
    // ------------------------------------------------------------------

    async deletePage(pageNum) {
        if (!this.app.currentFile) return;

        const totalPages = this.app.viewer.pdfDoc.numPages;
        if (totalPages <= 1) {
            alert('最後のページは削除できません。');
            return;
        }

        if (!confirm(`ページ ${pageNum} を削除しますか？`)) return;

        try {
            const result = await window.pywebview.api.delete_pages(this.app.currentFile, String(pageNum));
            if (result && result.success) {
                delete this.app.annotations[pageNum];
                const newAnnotations = {};
                for (const [pn, annots] of Object.entries(this.app.annotations)) {
                    const num = parseInt(pn);
                    if (num < pageNum) {
                        newAnnotations[num] = annots;
                    } else if (num > pageNum) {
                        newAnnotations[num - 1] = annots;
                    }
                }
                this.app.annotations = newAnnotations;
                await this.reloadAfterChange();
            } else {
                alert('ページの削除に失敗しました: ' + (result?.error || '不明なエラー'));
            }
        } catch (err) {
            alert('ページの削除に失敗しました: ' + err.message);
        }
    }

    async insertPages() {
        if (!this.app.currentFile) return;

        try {
            const sourcePath = await window.pywebview.api.select_file();
            if (!sourcePath) return;

            const sourceCount = await window.pywebview.api.get_page_count(sourcePath);
            if (!sourceCount || sourceCount < 1) {
                alert('選択されたファイルのページ数を取得できませんでした。');
                return;
            }

            const pageSpec = prompt(
                `挿入するページを指定してください (1-${sourceCount}):\n` +
                '例: 1-3, 5, 7-10'
            );
            if (!pageSpec || !pageSpec.trim()) return;

            const totalPages = this.app.viewer.pdfDoc.numPages;
            const position = prompt(
                `挿入位置を指定してください (0-${totalPages}):\n` +
                `0 = 先頭に挿入\n${totalPages} = 末尾に挿入`
            );
            if (position === null || position.trim() === '') return;

            const posNum = parseInt(position);
            if (isNaN(posNum) || posNum < 0 || posNum > totalPages) {
                alert(`挿入位置は 0 から ${totalPages} の範囲で指定してください。`);
                return;
            }

            const result = await window.pywebview.api.insert_pages(
                this.app.currentFile, sourcePath, pageSpec.trim(), posNum
            );

            if (result && result.success) {
                await this.reloadAfterChange();
            } else {
                alert('ページの挿入に失敗しました: ' + (result?.error || '不明なエラー'));
            }
        } catch (err) {
            alert('ページの挿入に失敗しました: ' + err.message);
        }
    }

    /**
     * Reload the PDF and regenerate thumbnails after a page operation.
     */
    async reloadAfterChange() {
        try {
            const base64 = await window.pywebview.api.get_pdf_base64(this.app.currentFile);
            await this.app.viewer.loadPdf(base64);
            await this.generateThumbnails();
            if (this.app.annotationLayer) {
                this.app.annotationLayer.renderAll();
            }
            if (this.app.commentPanel) {
                this.app.commentPanel.refresh();
            }
        } catch (err) {
            alert('PDFの再読み込みに失敗しました: ' + err.message);
        }
    }
}
