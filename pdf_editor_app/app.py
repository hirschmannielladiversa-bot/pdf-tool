#!/usr/bin/env python3
"""PDF Editor Application - pywebview launcher."""

import os
import webview
from .api import Api


def main():
    """Launch the PDF Editor desktop application."""
    api = Api()

    # Resolve path to static/index.html relative to this file
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    index_path = os.path.join(static_dir, 'index.html')

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"index.html が見つかりません: {index_path}")

    window = webview.create_window(
        'PDF Editor',
        url=index_path,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 600),
    )
    api.window = window
    # http_server=True avoids CORS issues with ES module imports on file:// URLs
    webview.start(http_server=True, debug=False)


if __name__ == '__main__':
    main()
