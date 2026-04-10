/**
 * PDF Editor - Toolbar Module (ES module)
 * Renders the vertical tool column on the right side and handles tool selection.
 */

export class Toolbar {
    constructor(app) {
        this.app = app;
        this.container = null;
    }

    /** Initialize the toolbar by rendering buttons into #toolbar. */
    init() {
        this.container = document.getElementById('toolbar');
        if (!this.container) return;
        this.render();
    }

    /** Build the toolbar HTML and attach event listeners. */
    render() {
        const tools = [
            { id: 'select',    icon: '\u2196', label: '\u9078\u629e' },         // ↖ 選択
            { id: 'highlight', icon: '\u2588', label: '\u30CF\u30A4\u30E9\u30A4\u30C8' },  // █ ハイライト
            { id: 'text',      icon: 'T',      label: '\u30C6\u30AD\u30B9\u30C8' },        // テキスト
            { id: 'pen',       icon: '\u270E', label: '\u30DA\u30F3' },          // ✎ ペン
            { id: 'rectangle', icon: '\u25A1', label: '\u77E9\u5F62' },          // □ 矩形
            { id: 'comment',   icon: '\u{1F4AC}', label: '\u30B3\u30E1\u30F3\u30C8' }, // 💬 コメント
            { id: 'eraser',    icon: '\u232B', label: '\u6D88\u3057\u30B4\u30E0' },     // ⌫ 消しゴム
        ];

        const actions = [
            { id: 'zoom-in',  icon: '+', label: '\u30BA\u30FC\u30E0\u30A4\u30F3',  handler: () => this.app.zoomIn() },
            { id: 'zoom-out', icon: '\u2212', label: '\u30BA\u30FC\u30E0\u30A2\u30A6\u30C8', handler: () => this.app.zoomOut() },
            { id: 'open',     icon: '\u{1F4C2}', label: '\u958B\u304F',       handler: () => this.app.openFile() },
            { id: 'save',     icon: '\u{1F4BE}', label: 'PDF\u306B\u4FDD\u5B58',   handler: () => this.app.savePdf() },
            { id: 'save-as',  icon: '\u{1F4E4}', label: '\u540D\u524D\u3092\u4ED8\u3051\u3066\u4FDD\u5B58', handler: () => this.app.saveAsPdf() },
        ];

        // Build tool buttons
        let html = '<div class="toolbar-section">';
        for (const tool of tools) {
            const activeClass = tool.id === this.app.currentTool ? ' active' : '';
            html += `<button class="tool-btn${activeClass}" data-tool="${tool.id}" title="${tool.label}">` +
                    `<span class="tool-icon">${tool.icon}</span>` +
                    `<span class="tool-label">${tool.label}</span>` +
                    `</button>`;
        }
        html += '</div>';

        // Color picker
        html += '<div class="toolbar-divider"></div>';
        html += '<div class="toolbar-section">';
        html += `<label class="tool-color-label" title="色">
                    <input type="color" id="tool-color" value="${this.app.currentColor || '#FF0000'}" />
                    <span class="tool-label">色</span>
                 </label>`;
        html += '</div>';

        // Divider
        html += '<div class="toolbar-divider"></div>';

        // Build action buttons
        html += '<div class="toolbar-section">';
        for (const action of actions) {
            html += `<button class="tool-btn action-btn" data-action="${action.id}" title="${action.label}">` +
                    `<span class="tool-icon">${action.icon}</span>` +
                    `<span class="tool-label">${action.label}</span>` +
                    `</button>`;
        }
        html += '</div>';

        this.container.innerHTML = html;

        // --- Event listeners ---

        // Tool selection
        this.container.querySelectorAll('[data-tool]').forEach((btn) => {
            btn.addEventListener('click', () => {
                this.app.setTool(btn.dataset.tool);
            });
        });

        // Action buttons
        for (const action of actions) {
            const btn = this.container.querySelector(`[data-action="${action.id}"]`);
            if (btn) {
                btn.addEventListener('click', action.handler);
            }
        }

        // Color picker
        const colorInput = this.container.querySelector('#tool-color');
        if (colorInput) {
            colorInput.addEventListener('input', (e) => {
                this.app.currentColor = e.target.value;
            });
        }
    }

    /**
     * Visually highlight the active tool button.
     * @param {string} toolName - The tool id to mark as active.
     */
    updateActiveState(toolName) {
        if (!this.container) return;
        this.container.querySelectorAll('[data-tool]').forEach((btn) => {
            btn.classList.toggle('active', btn.dataset.tool === toolName);
        });
    }
}
