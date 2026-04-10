/**
 * annotation-layer.js - Canvas overlay annotation drawing
 * Handles all annotation tools: select, highlight, text, pen, rectangle, comment, eraser
 */

export class AnnotationLayer {
    constructor(app) {
        this.app = app;
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        this.currentPenPoints = [];
        this.activeTextInput = null;
        this.selectedAnnotationId = null;
    }

    /**
     * Set up mouse event listeners on a page overlay canvas.
     * Called by the viewer when a page is rendered.
     */
    setupOverlay(overlay, pageNum, viewport) {
        overlay.addEventListener('mousedown', (e) => this.onMouseDown(e, overlay, pageNum));
        overlay.addEventListener('mousemove', (e) => this.onMouseMove(e, overlay, pageNum));
        overlay.addEventListener('mouseup', (e) => this.onMouseUp(e, overlay, pageNum));

        // Disable pointer events on HTML annotation elements when using eraser
        // so clicks go through to the canvas overlay for hit testing.
        const updateAnnoPointerEvents = () => {
            const tool = this.app.currentTool;
            const pageDiv = overlay.parentElement;
            if (pageDiv) {
                pageDiv.querySelectorAll('.anno-box').forEach(el => {
                    el.style.pointerEvents = (tool === 'eraser') ? 'none' : 'auto';
                });
            }
        };
        overlay.addEventListener('mouseenter', updateAnnoPointerEvents);

        // Update cursor based on current tool
        const updateCursor = () => {
            const cursors = {
                select: 'default',
                highlight: 'crosshair',
                text: 'text',
                pen: 'crosshair',
                rectangle: 'crosshair',
                comment: 'crosshair',
                eraser: 'pointer'
            };
            overlay.style.cursor = cursors[this.app.currentTool] || 'default';
        };

        // Listen for tool changes via a MutationObserver on toolbar buttons
        // or just update cursor on mousemove as a simple approach
        overlay.addEventListener('mouseenter', updateCursor);
        overlay.addEventListener('mousemove', () => {
            const cursors = {
                select: 'default',
                highlight: 'crosshair',
                text: 'text',
                pen: 'crosshair',
                rectangle: 'crosshair',
                comment: 'crosshair',
                eraser: 'pointer'
            };
            overlay.style.cursor = cursors[this.app.currentTool] || 'default';
        });
    }

    /**
     * Get mouse position relative to canvas element.
     */
    getCanvasPos(e, canvas) {
        const rect = canvas.getBoundingClientRect();
        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    }

    onMouseDown(e, overlay, pageNum) {
        const pos = this.getCanvasPos(e, overlay);
        const tool = this.app.currentTool;

        if (tool === 'select') {
            this.selectAtPosition(pageNum, pos);
            return;
        }

        if (tool === 'eraser') {
            this.eraseAtPosition(pageNum, pos);
            this.renderPage(pageNum);
            return;
        }

        if (tool === 'comment') {
            this.addComment(pageNum, pos);
            return;
        }

        if (tool === 'text') {
            this.addTextInput(pageNum, pos, overlay);
            return;
        }

        // Start drawing for highlight, pen, rectangle
        this.isDrawing = true;
        this.startX = pos.x;
        this.startY = pos.y;

        if (tool === 'pen') {
            this.currentPenPoints = [{ x: pos.x / this.app.scale, y: pos.y / this.app.scale }];
        }
    }

    onMouseMove(e, overlay, pageNum) {
        if (!this.isDrawing) return;
        const pos = this.getCanvasPos(e, overlay);
        const tool = this.app.currentTool;
        const ctx = overlay.getContext('2d');

        // Clear and re-render existing annotations + draw preview
        this.renderPage(pageNum);

        const color = this.app.currentColor || '#FF0000';

        if (tool === 'highlight') {
            ctx.save();
            const hlColor = color === '#FF0000' ? '#FFFF00' : color;
            ctx.fillStyle = hlColor;
            ctx.globalAlpha = 0.4;
            ctx.fillRect(this.startX, this.startY, pos.x - this.startX, pos.y - this.startY);
            ctx.restore();
        }

        if (tool === 'rectangle') {
            ctx.save();
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.strokeRect(this.startX, this.startY, pos.x - this.startX, pos.y - this.startY);
            ctx.restore();
        }

        if (tool === 'pen') {
            this.currentPenPoints.push({ x: pos.x / this.app.scale, y: pos.y / this.app.scale });
            ctx.save();
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.beginPath();
            const pts = this.currentPenPoints;
            ctx.moveTo(pts[0].x * this.app.scale, pts[0].y * this.app.scale);
            for (let i = 1; i < pts.length; i++) {
                ctx.lineTo(pts[i].x * this.app.scale, pts[i].y * this.app.scale);
            }
            ctx.stroke();
            ctx.restore();
        }
    }

    onMouseUp(e, overlay, pageNum) {
        if (!this.isDrawing) return;
        this.isDrawing = false;
        const pos = this.getCanvasPos(e, overlay);
        const tool = this.app.currentTool;
        const scale = this.app.scale;

        if (tool === 'highlight') {
            const annotation = {
                id: crypto.randomUUID(),
                type: 'highlight',
                x: Math.min(this.startX, pos.x) / scale,
                y: Math.min(this.startY, pos.y) / scale,
                width: Math.abs(pos.x - this.startX) / scale,
                height: Math.abs(pos.y - this.startY) / scale,
                color: this.app.currentColor === '#FF0000' ? '#FFFF00' : this.app.currentColor,
                opacity: 0.4,
                created: new Date().toISOString()
            };
            // Only create if the area is large enough (avoid accidental clicks)
            if (annotation.width > 2 && annotation.height > 2) {
                this.app.addAnnotation(pageNum, annotation);
                this.renderPage(pageNum);
            }
        }

        if (tool === 'rectangle') {
            const annotation = {
                id: crypto.randomUUID(),
                type: 'rectangle',
                x: Math.min(this.startX, pos.x) / scale,
                y: Math.min(this.startY, pos.y) / scale,
                width: Math.abs(pos.x - this.startX) / scale,
                height: Math.abs(pos.y - this.startY) / scale,
                color: this.app.currentColor,
                strokeWidth: 2,
                created: new Date().toISOString()
            };
            if (annotation.width > 2 && annotation.height > 2) {
                this.app.addAnnotation(pageNum, annotation);
                this.renderPage(pageNum);
            }
        }

        if (tool === 'pen' && this.currentPenPoints.length > 1) {
            const annotation = {
                id: crypto.randomUUID(),
                type: 'pen',
                points: [...this.currentPenPoints],
                color: this.app.currentColor,
                strokeWidth: 2,
                opacity: 1,
                created: new Date().toISOString()
            };
            this.app.addAnnotation(pageNum, annotation);
            this.currentPenPoints = [];
            this.renderPage(pageNum);
        }
    }

    /**
     * Select (highlight) an annotation at the given screen position.
     */
    selectAtPosition(pageNum, pos) {
        const scale = this.app.scale;
        const annotations = this.app.annotations[pageNum] || [];
        this.selectedAnnotationId = null;

        for (let i = annotations.length - 1; i >= 0; i--) {
            const a = annotations[i];
            if (this.hitTest(a, pos, scale)) {
                this.selectedAnnotationId = a.id;
                break;
            }
        }
        this.renderPage(pageNum);
    }

    /**
     * Check if a screen position hits an annotation.
     */
    hitTest(a, pos, scale) {
        const ax = a.x * scale;
        const ay = a.y * scale;

        if (a.type === 'highlight' || a.type === 'rectangle') {
            return pos.x >= ax && pos.x <= ax + a.width * scale &&
                   pos.y >= ay && pos.y <= ay + a.height * scale;
        }

        if (a.type === 'text' || a.type === 'comment') {
            return Math.abs(pos.x - ax) < 30 && Math.abs(pos.y - ay) < 30;
        }

        if (a.type === 'pen' && a.points) {
            for (const pt of a.points) {
                if (Math.abs(pos.x - pt.x * scale) < 10 && Math.abs(pos.y - pt.y * scale) < 10) {
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * Create an inline text input over the canvas for adding text annotations.
     */
    async addTextInput(pageNum, pos, overlay) {
        const result = await this.app.showInputDialog('テキストを追加', 'テキストを入力...', {
            showFontSize: true, showColor: true, defaultFontSize: 12, defaultColor: this.app.currentColor
        });
        if (result) {
            const annotation = {
                id: crypto.randomUUID(),
                type: 'text',
                x: pos.x / this.app.scale,
                y: pos.y / this.app.scale,
                width: 150,
                height: Math.max(30, result.fontSize * 2),
                text: result.text,
                fontSize: result.fontSize,
                color: result.color,
                created: new Date().toISOString()
            };
            this.app.addAnnotation(pageNum, annotation);
            this.renderPage(pageNum);
        }
    }

    /**
     * Create a movable/resizable HTML text box element for a text annotation.
     */
    createTextBox(pageDiv, annotation, pageNum, scale) {
        const box = document.createElement('div');
        box.className = 'anno-box text-box-annotation';
        box.dataset.annotationId = annotation.id;
        box.style.left = (annotation.x * scale) + 'px';
        box.style.top = (annotation.y * scale) + 'px';
        box.style.width = ((annotation.width || 150) * scale) + 'px';
        box.style.height = ((annotation.height || 30) * scale) + 'px';
        box.style.fontSize = ((annotation.fontSize || 12) * scale) + 'px';
        box.style.color = annotation.color || '#FF0000';
        box.style.overflow = 'hidden';

        // Text content in a dedicated span (to avoid mixing with toolbar text)
        const textSpan = document.createElement('span');
        textSpan.className = 'text-box-content';
        textSpan.innerText = annotation.text;
        box.appendChild(textSpan);

        // Font size selector (shown on hover)
        const sizeBar = document.createElement('div');
        sizeBar.className = 'text-box-toolbar';
        const sizeSelect = document.createElement('select');
        sizeSelect.className = 'text-box-size-select';
        [8,10,12,14,16,18,20,24,28,32,36,48].forEach(s => {
            const opt = document.createElement('option');
            opt.value = s; opt.textContent = s + 'pt';
            if (s === (annotation.fontSize || 12)) opt.selected = true;
            sizeSelect.appendChild(opt);
        });
        sizeSelect.addEventListener('change', (e) => {
            e.stopPropagation();
            const newSize = parseInt(sizeSelect.value);
            annotation.fontSize = newSize;
            box.style.fontSize = (newSize * scale) + 'px';
            this.app.saveAnnotations();
        });
        sizeSelect.addEventListener('mousedown', (e) => e.stopPropagation());
        sizeBar.appendChild(sizeSelect);

        // Color picker
        const colorInput = document.createElement('input');
        colorInput.type = 'color';
        colorInput.className = 'text-box-color-picker';
        colorInput.value = annotation.color || '#FF0000';
        colorInput.title = '文字色';
        colorInput.addEventListener('input', (e) => {
            e.stopPropagation();
            annotation.color = colorInput.value;
            box.style.color = colorInput.value;
            this.app.saveAnnotations();
        });
        colorInput.addEventListener('mousedown', (e) => e.stopPropagation());
        colorInput.addEventListener('click', (e) => e.stopPropagation());
        sizeBar.appendChild(colorInput);
        box.appendChild(sizeBar);

        // Delete button
        this._addDeleteButton(box, annotation, pageNum);

        // Resize handle
        const handle = document.createElement('div');
        handle.className = 'text-box-resize-handle';
        box.appendChild(handle);

        // -- Drag to move --
        let isDragging = false, dragStartX, dragStartY, origLeft, origTop;
        box.addEventListener('mousedown', (e) => {
            if (e.target === handle) return; // let resize handle its own event
            if (textSpan.isContentEditable) return; // don't drag while editing
            e.stopPropagation();
            isDragging = true;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            origLeft = parseFloat(box.style.left);
            origTop = parseFloat(box.style.top);
            box.style.cursor = 'grabbing';
        });
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = e.clientX - dragStartX;
            const dy = e.clientY - dragStartY;
            box.style.left = (origLeft + dx) + 'px';
            box.style.top = (origTop + dy) + 'px';
        });
        document.addEventListener('mouseup', () => {
            if (!isDragging) return;
            isDragging = false;
            box.style.cursor = 'grab';
            // Update annotation position
            annotation.x = parseFloat(box.style.left) / scale;
            annotation.y = parseFloat(box.style.top) / scale;
            this.app.saveAnnotations();
        });

        // -- Resize handle --
        let isResizing = false, resizeStartX, resizeStartY, origW, origH;
        handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            isResizing = true;
            resizeStartX = e.clientX;
            resizeStartY = e.clientY;
            origW = box.offsetWidth;
            origH = box.offsetHeight;
        });
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const dw = e.clientX - resizeStartX;
            const dh = e.clientY - resizeStartY;
            box.style.width = Math.max(60, origW + dw) + 'px';
            box.style.height = Math.max(24, origH + dh) + 'px';
        });
        document.addEventListener('mouseup', () => {
            if (!isResizing) return;
            isResizing = false;
            annotation.width = box.offsetWidth / scale;
            annotation.height = box.offsetHeight / scale;
            this.app.saveAnnotations();
        });

        // -- Double-click to edit (on textSpan only) --
        box.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            textSpan.contentEditable = 'true';
            textSpan.style.cursor = 'text';
            textSpan.focus();
        });
        textSpan.addEventListener('blur', () => {
            textSpan.contentEditable = 'false';
            textSpan.style.cursor = 'inherit';
            // Use innerText to preserve line breaks entered via Enter
            annotation.text = (textSpan.innerText || '').replace(/\n+$/, '') || annotation.text;
            this.app.saveAnnotations();
        });
        textSpan.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                textSpan.contentEditable = 'false';
                textSpan.blur();
            }
            e.stopPropagation();
        });

        pageDiv.appendChild(box);
        return box;
    }

    /**
     * Create a movable/resizable HTML element for highlight or rectangle annotations.
     */
    createShapeBox(pageDiv, annotation, pageNum, scale) {
        const box = document.createElement('div');
        box.className = 'anno-box shape-box-annotation';
        box.dataset.annotationId = annotation.id;
        box.style.left = (annotation.x * scale) + 'px';
        box.style.top = (annotation.y * scale) + 'px';
        box.style.width = (annotation.width * scale) + 'px';
        box.style.height = (annotation.height * scale) + 'px';

        if (annotation.type === 'highlight') {
            box.style.background = annotation.color || '#FFFF00';
            box.style.opacity = annotation.opacity || 0.4;
            box.classList.add('shape-highlight');
        } else if (annotation.type === 'rectangle') {
            box.style.border = `${annotation.strokeWidth || 2}px solid ${annotation.color || '#FF0000'}`;
            box.style.background = 'transparent';
            box.classList.add('shape-rectangle');
        }

        // Delete button
        this._addDeleteButton(box, annotation, pageNum);

        // Resize handle
        const handle = document.createElement('div');
        handle.className = 'shape-box-resize-handle';
        box.appendChild(handle);

        // -- Drag to move --
        let isDragging = false, dragStartX, dragStartY, origLeft, origTop;
        box.addEventListener('mousedown', (e) => {
            if (e.target === handle) return;
            e.stopPropagation();
            isDragging = true;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            origLeft = parseFloat(box.style.left);
            origTop = parseFloat(box.style.top);
            box.style.cursor = 'grabbing';
        });
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            box.style.left = (origLeft + e.clientX - dragStartX) + 'px';
            box.style.top = (origTop + e.clientY - dragStartY) + 'px';
        });
        document.addEventListener('mouseup', () => {
            if (!isDragging) return;
            isDragging = false;
            box.style.cursor = 'grab';
            annotation.x = parseFloat(box.style.left) / scale;
            annotation.y = parseFloat(box.style.top) / scale;
            this.app.saveAnnotations();
        });

        // -- Resize handle --
        let isResizing = false, rsX, rsY, origW, origH;
        handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            isResizing = true;
            rsX = e.clientX; rsY = e.clientY;
            origW = box.offsetWidth; origH = box.offsetHeight;
        });
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            box.style.width = Math.max(20, origW + e.clientX - rsX) + 'px';
            box.style.height = Math.max(10, origH + e.clientY - rsY) + 'px';
        });
        document.addEventListener('mouseup', () => {
            if (!isResizing) return;
            isResizing = false;
            annotation.width = box.offsetWidth / scale;
            annotation.height = box.offsetHeight / scale;
            this.app.saveAnnotations();
        });

        pageDiv.appendChild(box);
        return box;
    }

    /**
     * Add a delete button (×) to an annotation HTML element.
     */
    _addDeleteButton(box, annotation, pageNum) {
        const btn = document.createElement('button');
        btn.className = 'anno-delete-btn';
        btn.textContent = '\u00D7';
        btn.title = '削除';
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.app.removeAnnotation(pageNum, annotation.id);
            this.renderPage(pageNum);
            if (annotation.type === 'comment' && this.app.commentPanel) {
                this.app.commentPanel.refresh();
            }
        });
        box.appendChild(btn);
    }

    /**
     * Add a comment annotation via prompt dialog.
     */
    async addComment(pageNum, pos) {
        const result = await this.app.showInputDialog('コメントを入力', 'ここにコメントを入力...');
        const text = result ? (result.text || result) : null;
        if (text) {
            const annotation = {
                id: crypto.randomUUID(),
                type: 'comment',
                x: pos.x / this.app.scale,
                y: pos.y / this.app.scale,
                text: text,
                color: '#FFA500',
                created: new Date().toISOString()
            };
            this.app.addAnnotation(pageNum, annotation);
            this.renderPage(pageNum);
            // Refresh comment panel if it exists
            if (this.app.commentPanel) {
                this.app.commentPanel.refresh();
            }
        }
    }

    /**
     * Find and remove annotation at the given screen position (eraser tool).
     * Checks annotations in reverse order (top-most first).
     */
    eraseAtPosition(pageNum, pos) {
        const scale = this.app.scale;
        const annotations = this.app.annotations[pageNum] || [];

        for (let i = annotations.length - 1; i >= 0; i--) {
            const a = annotations[i];
            if (this.hitTest(a, pos, scale)) {
                this.app.removeAnnotation(pageNum, a.id);
                // Refresh comment panel if a comment was deleted
                if (a.type === 'comment' && this.app.commentPanel) {
                    this.app.commentPanel.refresh();
                }
                return;
            }
        }
    }

    /**
     * Render all annotations for a given page onto its overlay canvas.
     */
    renderPage(pageNum) {
        const pageInfo = this.app.viewer.getPageInfo(pageNum);
        if (!pageInfo) return;

        const overlay = pageInfo.overlay;
        const ctx = overlay.getContext('2d');
        const scale = this.app.scale;
        const pageDiv = pageInfo.pageDiv;

        ctx.clearRect(0, 0, overlay.width, overlay.height);

        // Remove existing interactive annotation elements for this page
        pageDiv.querySelectorAll('.anno-box').forEach(el => el.remove());

        const annotations = this.app.annotations[pageNum] || [];
        for (const a of annotations) {
            if (a.type === 'text') {
                this.createTextBox(pageDiv, a, pageNum, scale);
            } else if (a.type === 'highlight' || a.type === 'rectangle') {
                this.createShapeBox(pageDiv, a, pageNum, scale);
            } else {
                this.drawAnnotation(ctx, a, scale);
            }
        }
    }

    /**
     * Draw a single annotation on the given canvas context.
     */
    drawAnnotation(ctx, a, scale) {
        const isSelected = (a.id === this.selectedAnnotationId);

        ctx.save();

        if (a.type === 'highlight') {
            ctx.globalAlpha = a.opacity || 0.4;
            ctx.fillStyle = a.color || '#FFFF00';
            ctx.fillRect(a.x * scale, a.y * scale, a.width * scale, a.height * scale);
            ctx.globalAlpha = 1;
            if (isSelected) {
                ctx.strokeStyle = '#4a9eff';
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 4]);
                ctx.strokeRect(a.x * scale, a.y * scale, a.width * scale, a.height * scale);
                ctx.setLineDash([]);
            }
        }

        if (a.type === 'rectangle') {
            ctx.strokeStyle = a.color || '#FF0000';
            ctx.lineWidth = a.strokeWidth || 2;
            ctx.strokeRect(a.x * scale, a.y * scale, a.width * scale, a.height * scale);
            if (isSelected) {
                ctx.strokeStyle = '#4a9eff';
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.strokeRect(
                    a.x * scale - 3, a.y * scale - 3,
                    a.width * scale + 6, a.height * scale + 6
                );
                ctx.setLineDash([]);
            }
        }

        if (a.type === 'text') {
            const fontSize = (a.fontSize || 12) * scale;
            ctx.font = `${fontSize}px "Hiragino Sans", sans-serif`;
            ctx.fillStyle = a.color || '#FF0000';
            ctx.textBaseline = 'top';
            ctx.fillText(a.text, a.x * scale, a.y * scale);
            if (isSelected) {
                const metrics = ctx.measureText(a.text);
                ctx.strokeStyle = '#4a9eff';
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.strokeRect(
                    a.x * scale - 2, a.y * scale - 2,
                    metrics.width + 4, fontSize + 4
                );
                ctx.setLineDash([]);
            }
        }

        if (a.type === 'comment') {
            const x = a.x * scale;
            const y = a.y * scale;
            const radius = 12;

            // Orange circle background
            ctx.fillStyle = a.color || '#FFA500';
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();

            // White speech bubble icon (drawn manually for reliability)
            ctx.fillStyle = '#FFFFFF';
            ctx.beginPath();
            // Speech bubble body
            const bx = x - 5;
            const by = y - 5;
            const bw = 10;
            const bh = 7;
            const br = 2;
            ctx.moveTo(bx + br, by);
            ctx.lineTo(bx + bw - br, by);
            ctx.quadraticCurveTo(bx + bw, by, bx + bw, by + br);
            ctx.lineTo(bx + bw, by + bh - br);
            ctx.quadraticCurveTo(bx + bw, by + bh, bx + bw - br, by + bh);
            // Tail
            ctx.lineTo(bx + 4, by + bh);
            ctx.lineTo(bx + 2, by + bh + 3);
            ctx.lineTo(bx + 3, by + bh);
            ctx.lineTo(bx + br, by + bh);
            ctx.quadraticCurveTo(bx, by + bh, bx, by + bh - br);
            ctx.lineTo(bx, by + br);
            ctx.quadraticCurveTo(bx, by, bx + br, by);
            ctx.closePath();
            ctx.fill();

            if (isSelected) {
                ctx.strokeStyle = '#4a9eff';
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.arc(x, y, radius + 4, 0, Math.PI * 2);
                ctx.stroke();
                ctx.setLineDash([]);
            }
        }

        if (a.type === 'pen' && a.points && a.points.length > 1) {
            ctx.strokeStyle = a.color || '#FF0000';
            ctx.lineWidth = a.strokeWidth || 2;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.globalAlpha = a.opacity !== undefined ? a.opacity : 1;
            ctx.beginPath();
            ctx.moveTo(a.points[0].x * scale, a.points[0].y * scale);
            for (let i = 1; i < a.points.length; i++) {
                ctx.lineTo(a.points[i].x * scale, a.points[i].y * scale);
            }
            ctx.stroke();

            if (isSelected) {
                ctx.strokeStyle = '#4a9eff';
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.globalAlpha = 1;
                // Draw selection outline around bounding box
                let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                for (const pt of a.points) {
                    minX = Math.min(minX, pt.x * scale);
                    minY = Math.min(minY, pt.y * scale);
                    maxX = Math.max(maxX, pt.x * scale);
                    maxY = Math.max(maxY, pt.y * scale);
                }
                ctx.strokeRect(minX - 4, minY - 4, maxX - minX + 8, maxY - minY + 8);
                ctx.setLineDash([]);
            }
        }

        ctx.restore();
    }

    /**
     * Re-render annotations on all visible pages.
     */
    renderAll() {
        if (!this.app.viewer || !this.app.viewer.pages) return;
        for (const pageInfo of this.app.viewer.pages) {
            this.renderPage(pageInfo.pageNum);
        }
    }
}
