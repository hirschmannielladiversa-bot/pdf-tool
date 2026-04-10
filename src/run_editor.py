#!/usr/bin/env python3
"""Launch PDF Editor Application."""

import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)   # src/ for pdf_edit, pdf_merger, etc.
sys.path.insert(0, _ROOT)   # project root for pdf_editor_app package

from pdf_editor_app.app import main

if __name__ == "__main__":
    main()
