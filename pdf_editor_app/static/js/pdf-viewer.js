/**
 * PDF Editor - PDF Viewer Module (ES module)
 * Handles pdf.js document loading, page rendering, and viewport management.
 */

import * as pdfjsLib from '../lib/pdf.min.mjs';

// Configure pdf.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'lib/pdf.worker.min.mjs';

export class PdfViewer {
    constructor(app) {
        this.app = app;
        this.pdfDoc = null;
        this.pages = [];       // Array of { pageNum, canvas, overlay, viewport, pageDiv }
        this.container = null;
        this._renderTask = null;
    }

    /**
     * Load a PDF from a base64-encoded string.
     * @param {string} base64Data - The PDF file content as base64.
     */
    async loadPdf(base64Data) {
        // Decode base64 to Uint8Array
        const binaryStr = atob(base64Data);
        const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) {
            bytes[i] = binaryStr.charCodeAt(i);
        }

        try {
            // Destroy previous document if any
            if (this.pdfDoc) {
                this.pdfDoc.destroy();
                this.pdfDoc = null;
            }

            this.pdfDoc = await pdfjsLib.getDocument({ data: bytes }).promise;
            this.container = document.getElementById('pdf-container');
            await this.renderAllPages();
        } catch (err) {
            console.error('PDF loading error:', err);
            this.container = document.getElementById('pdf-container');
            this.container.innerHTML =
                '<div class="error-message">PDFの読み込みに失敗しました。ファイルが破損している可能性があります。</div>';
        }
    }

    /**
     * Render all pages sequentially into the container.
     */
    async renderAllPages() {
        if (!this.pdfDoc || !this.container) return;

        // Clear existing content (but keep welcome message reference)
        this.container.innerHTML = '';
        this.pages = [];

        const numPages = this.pdfDoc.numPages;

        for (let i = 1; i <= numPages; i++) {
            await this.renderPage(i);
        }
    }

    /**
     * Render a single page and append it to the container.
     * @param {number} pageNum - 1-based page number.
     */
    async renderPage(pageNum) {
        const page = await this.pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: this.app.scale });

        // Page wrapper
        const pageDiv = document.createElement('div');
        pageDiv.className = 'pdf-page';
        pageDiv.dataset.pageNum = pageNum;
        pageDiv.style.width = viewport.width + 'px';
        pageDiv.style.height = viewport.height + 'px';

        // PDF rendering canvas
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-canvas';
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        // Annotation overlay canvas (positioned absolutely on top)
        const overlay = document.createElement('canvas');
        overlay.className = 'annotation-overlay';
        overlay.width = viewport.width;
        overlay.height = viewport.height;
        overlay.dataset.pageNum = pageNum;

        pageDiv.appendChild(canvas);
        pageDiv.appendChild(overlay);
        this.container.appendChild(pageDiv);

        // Render the PDF page onto the canvas
        const ctx = canvas.getContext('2d');
        try {
            await page.render({ canvasContext: ctx, viewport: viewport }).promise;
        } catch (err) {
            console.error(`Page ${pageNum} render error:`, err);
        }

        // Store page info
        this.pages.push({ pageNum, canvas, overlay, viewport, pageDiv });

        // Wire up annotation layer events on the overlay
        if (this.app.annotationLayer) {
            this.app.annotationLayer.setupOverlay(overlay, pageNum, viewport);
        }
    }

    /**
     * Re-render all pages (e.g. after zoom change).
     */
    async rerender() {
        if (!this.pdfDoc) return;
        await this.renderAllPages();

        // Re-render annotations on new canvases
        if (this.app.annotationLayer) {
            this.app.annotationLayer.renderAll();
        }

        // Regenerate thumbnails
        if (this.app.pageManager) {
            this.app.pageManager.generateThumbnails();
        }
    }

    /**
     * Get info for a specific page.
     * @param {number} pageNum - 1-based page number.
     * @returns {{ pageNum, canvas, overlay, viewport, pageDiv } | undefined}
     */
    getPageInfo(pageNum) {
        return this.pages.find(p => p.pageNum === pageNum);
    }

    /**
     * Get total number of pages.
     * @returns {number}
     */
    get numPages() {
        return this.pdfDoc ? this.pdfDoc.numPages : 0;
    }

    /**
     * Scroll to a specific page in the viewer.
     * @param {number} pageNum - 1-based page number.
     */
    scrollToPage(pageNum) {
        const info = this.getPageInfo(pageNum);
        if (info && info.pageDiv) {
            info.pageDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    /**
     * Render a page to a thumbnail canvas.
     * @param {number} pageNum - 1-based page number.
     * @param {HTMLCanvasElement} thumbCanvas - Target canvas for the thumbnail.
     * @param {number} maxWidth - Maximum width in pixels.
     * @param {number} maxHeight - Maximum height in pixels.
     */
    async renderThumbnail(pageNum, thumbCanvas, maxWidth, maxHeight) {
        if (!this.pdfDoc) return;

        const page = await this.pdfDoc.getPage(pageNum);
        const unscaledViewport = page.getViewport({ scale: 1.0 });

        // Compute scale to fit within maxWidth x maxHeight
        const scaleX = maxWidth / unscaledViewport.width;
        const scaleY = maxHeight / unscaledViewport.height;
        const thumbScale = Math.min(scaleX, scaleY);

        const viewport = page.getViewport({ scale: thumbScale });

        thumbCanvas.width = viewport.width;
        thumbCanvas.height = viewport.height;

        const ctx = thumbCanvas.getContext('2d');
        try {
            await page.render({ canvasContext: ctx, viewport: viewport }).promise;
        } catch (err) {
            console.error(`Thumbnail render error (page ${pageNum}):`, err);
        }
    }
}
