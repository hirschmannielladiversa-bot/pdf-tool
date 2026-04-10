/**
 * comment-panel.js - Comment list panel
 * Displays all comment annotations in a collapsible sidebar list,
 * with click-to-scroll and delete functionality.
 */

export class CommentPanel {
    constructor(app) {
        this.app = app;
        this.isExpanded = true;
    }

    /**
     * Initialize the comment panel.
     * Note: Toggle behavior is handled by app.js setupCommentToggle().
     * This init only sets up comment-specific functionality.
     */
    init() {
        // Initial render of comment list
        this.refresh();
    }

    /**
     * Rebuild the comment list from current annotations.
     */
    refresh() {
        const list = document.getElementById('comment-list');
        if (!list) return;

        list.innerHTML = '';

        // Collect all comment annotations across all pages
        const allComments = [];
        for (const [pageNum, annotations] of Object.entries(this.app.annotations)) {
            for (const a of annotations) {
                if (a.type === 'comment') {
                    allComments.push({ pageNum: parseInt(pageNum), ...a });
                }
            }
        }

        if (allComments.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'comment-empty';
            empty.style.color = 'var(--text-muted)';
            empty.style.textAlign = 'center';
            empty.style.padding = '16px 8px';
            empty.style.fontSize = '12px';
            empty.textContent = 'コメントはありません';
            list.appendChild(empty);
            return;
        }

        // Sort by page number, then by creation time
        allComments.sort((a, b) => {
            if (a.pageNum !== b.pageNum) return a.pageNum - b.pageNum;
            return new Date(a.created) - new Date(b.created);
        });

        for (const comment of allComments) {
            const item = document.createElement('div');
            item.className = 'comment-item';

            // Comment marker dot
            const marker = document.createElement('div');
            marker.className = 'comment-marker';
            marker.style.background = comment.color || '#FFA500';

            // Comment body
            const body = document.createElement('div');
            body.className = 'comment-body';

            // Meta line: page number + time
            const meta = document.createElement('div');
            meta.className = 'comment-meta';

            const pageSpan = document.createElement('span');
            pageSpan.className = 'comment-page';
            pageSpan.textContent = `ページ ${comment.pageNum}`;

            const timeSpan = document.createElement('span');
            timeSpan.className = 'comment-time';
            timeSpan.style.marginLeft = '8px';
            timeSpan.textContent = new Date(comment.created).toLocaleTimeString('ja-JP');

            meta.appendChild(pageSpan);
            meta.appendChild(timeSpan);

            // Comment text
            const textDiv = document.createElement('div');
            textDiv.className = 'comment-text';
            textDiv.textContent = comment.text; // textContent auto-escapes

            body.appendChild(meta);
            body.appendChild(textDiv);

            // Delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'comment-delete';
            deleteBtn.title = '削除';
            deleteBtn.textContent = '\u00D7'; // multiplication sign (x)
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.app.removeAnnotation(comment.pageNum, comment.id);
                // Re-render the annotation overlay for that page
                if (this.app.annotationLayer) {
                    this.app.annotationLayer.renderPage(comment.pageNum);
                }
                this.refresh();
            });

            item.appendChild(marker);
            item.appendChild(body);
            item.appendChild(deleteBtn);

            // Click to scroll to the comment's page
            item.addEventListener('click', () => {
                this.scrollToComment(comment.pageNum, comment);
            });

            list.appendChild(item);
        }
    }

    /**
     * Scroll the viewer to bring the specified page into view.
     */
    scrollToComment(pageNum, comment) {
        if (!this.app.viewer) return;
        const pageInfo = this.app.viewer.getPageInfo(pageNum);
        if (pageInfo && pageInfo.pageDiv) {
            pageInfo.pageDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}
