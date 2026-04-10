#!/usr/bin/env python3
"""
JS-Python bridge for the PDF Editor.

All public methods of the Api class are automatically exposed to the
frontend via ``window.pywebview.api.<method>(...)``.
"""

import base64
import json
import os
import shutil
import tempfile
import traceback

from pypdf import PdfReader

from . import annotation_engine
from .pdf_operations import (
    safe_add_page_numbers,
    safe_delete_pages,
    safe_insert_pages,
    safe_merge_pdfs,
    safe_reorder_pages,
    safe_split_pdf,
)


import subprocess


def _osascript_open_file(file_type="pdf", multiple=False):
    """Open a file dialog using macOS osascript (works from any thread)."""
    if multiple:
        script = '''
        set theFiles to choose file of type {"%s"} with multiple selections allowed
        set pathList to ""
        repeat with f in theFiles
            set pathList to pathList & POSIX path of f & linefeed
        end repeat
        return pathList
        ''' % file_type
    else:
        script = 'return POSIX path of (choose file of type {"%s"})' % file_type
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return None
        paths = result.stdout.strip()
        if not paths:
            return None
        if multiple:
            return [p for p in paths.split("\n") if p]
        return paths
    except Exception:
        return None


def _osascript_save_file(default_name="output.pdf"):
    """Save file dialog using macOS osascript."""
    script = '''
    set savePath to choose file name with prompt "保存先を選択" default name "%s"
    return POSIX path of savePath
    ''' % default_name
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return None
        path = result.stdout.strip()
        if path and not path.endswith(".pdf"):
            path += ".pdf"
        return path if path else None
    except Exception:
        return None


def _osascript_select_directory():
    """Directory selection dialog using macOS osascript."""
    script = 'return POSIX path of (choose folder)'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None
    except Exception:
        return None


class Api:
    """pywebview JS API bridge."""

    def __init__(self):
        self.window = None  # set by app.py after window creation
        self.current_file = None

    # ------------------------------------------------------------------
    # File dialogs (using osascript for reliable macOS thread safety)
    # ------------------------------------------------------------------

    def select_file(self):
        """Open a file-open dialog and return the selected PDF path."""
        result = _osascript_open_file("pdf")
        if result:
            self.current_file = result
        return result

    def select_files(self):
        """Open a file-open dialog for multiple PDFs."""
        return _osascript_open_file("pdf", multiple=True)

    def save_file_dialog(self):
        """Open a save-file dialog and return the chosen path."""
        return _osascript_save_file()

    def select_directory(self):
        """Open a directory selection dialog."""
        return _osascript_select_directory()

    # ------------------------------------------------------------------
    # PDF reading helpers
    # ------------------------------------------------------------------

    def get_pdf_base64(self, path):
        """Read a PDF file and return its contents as a base64 string.

        If a clean original backup exists, return that instead so the
        editor shows the un-annotated PDF and overlays annotations from JSON.
        This prevents visual double-vision of baked-in + overlay annotations.
        """
        try:
            orig = self._original_path(path)
            source = orig if os.path.exists(orig) else path
            with open(source, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            return {"error": str(e)}

    def get_page_count(self, path):
        """Return the total page count of a PDF."""
        try:
            reader = PdfReader(path)
            return len(reader.pages)
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Annotation persistence
    # ------------------------------------------------------------------

    def save_annotations(self, pdf_path, annotations_json):
        """Save annotations to a sidecar JSON file next to the PDF."""
        return annotation_engine.save_annotations(pdf_path, annotations_json)

    def load_annotations(self, pdf_path):
        """Load annotations from the sidecar JSON file. Returns JSON string or None."""
        return annotation_engine.load_annotations(pdf_path)

    @staticmethod
    def _original_path(pdf_path):
        """Return the path for the clean original backup."""
        base, ext = os.path.splitext(pdf_path)
        return base + ".original" + ext

    def ensure_original_backup(self, pdf_path):
        """Create a backup of the original (clean) PDF if it doesn't exist yet."""
        orig = self._original_path(pdf_path)
        if not os.path.exists(orig):
            shutil.copy2(pdf_path, orig)
        return orig

    def export_with_annotations(self, input_path, output_path, annotations_json):
        """Export a PDF with annotations burned in via reportlab overlay.

        Always renders from the original clean PDF so annotations remain editable.
        """
        try:
            raw = json.loads(annotations_json)
            # Frontend sends {pageNum: [annotations]}, flatten to list with "page" key
            flat = []
            if isinstance(raw, dict):
                for page_str, anns in raw.items():
                    for ann in anns:
                        ann["page"] = int(page_str)
                        flat.append(ann)
            elif isinstance(raw, list):
                flat = raw

            # Use original clean PDF as source (not the already-annotated one)
            orig_input = self._original_path(input_path)
            source = orig_input if os.path.exists(orig_input) else input_path

            # Ensure backup exists before first save
            self.ensure_original_backup(input_path)

            # Render to a temp file first, then move to output
            tmp = self._write_to_temp()
            result = annotation_engine.render_to_pdf(source, tmp, flat)
            if result.get("success"):
                shutil.move(tmp, output_path)
                # If save-as (different output path), also copy the original backup
                # and annotations sidecar so the new file remains re-editable.
                if os.path.abspath(output_path) != os.path.abspath(input_path):
                    orig_output = self._original_path(output_path)
                    # Use the clean source as backup for the new file
                    try:
                        shutil.copy2(source, orig_output)
                    except Exception:
                        pass
                    # Copy annotations sidecar
                    try:
                        sidecar_in = input_path + ".annotations.json"
                        sidecar_out = output_path + ".annotations.json"
                        if os.path.exists(sidecar_in):
                            shutil.copy2(sidecar_in, sidecar_out)
                    except Exception:
                        pass
                return {"success": True}
            else:
                self._cleanup_temp(tmp)
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Page operations (modify-in-place via temp file)
    # ------------------------------------------------------------------

    def _write_to_temp(self):
        """Create a temp PDF path that won't be auto-deleted."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        return path

    def reorder_pages(self, input_path, new_order_json):
        """Reorder pages in a PDF. *new_order_json* is a JSON list of 1-based indices."""
        try:
            new_order = json.loads(new_order_json)
            # Build a reorder spec string like "3,1,2"
            reorder_spec = ",".join(str(p) for p in new_order)
            tmp = self._write_to_temp()
            result = safe_reorder_pages(input_path, tmp, reorder_spec)
            if result["success"]:
                shutil.move(tmp, input_path)
                return {"success": True, "path": input_path}
            else:
                self._cleanup_temp(tmp)
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_pages(self, input_path, page_spec):
        """Delete pages specified by *page_spec* (e.g. '1,3,5-7')."""
        try:
            tmp = self._write_to_temp()
            result = safe_delete_pages(input_path, tmp, page_spec)
            if result["success"]:
                shutil.move(tmp, input_path)
                return {"success": True, "path": input_path}
            else:
                self._cleanup_temp(tmp)
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def insert_pages(self, target_path, source_path, page_spec, position):
        """Insert pages from *source_path* into *target_path* at *position*."""
        try:
            # Build insert spec: "source.pdf:page_spec@position"
            insert_spec = f"{source_path}:{page_spec}@{position}"
            tmp = self._write_to_temp()
            result = safe_insert_pages(target_path, tmp, insert_spec)
            if result["success"]:
                shutil.move(tmp, target_path)
                return {"success": True, "path": target_path}
            else:
                self._cleanup_temp(tmp)
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def merge_pdfs(self, paths_json):
        """Merge multiple PDFs. *paths_json* is a JSON list of file paths."""
        try:
            paths = json.loads(paths_json)
            if len(paths) < 2:
                return {"success": False, "error": "結合には2つ以上のPDFが必要です"}
            tmp = self._write_to_temp()
            result = safe_merge_pdfs(paths, tmp)
            if result["success"]:
                return {"success": True, "path": tmp}
            else:
                self._cleanup_temp(tmp)
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def split_pdf(self, input_path, ranges_str, output_dir):
        """Split a PDF by page ranges into *output_dir*."""
        try:
            return safe_split_pdf(input_path, output_dir, ranges_str)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_page_numbers(
        self,
        input_path,
        output_path,
        position="bottom-center",
        format_str="{page}",
        font_size=10,
        start_number=1,
    ):
        """Add page numbers to a PDF. Supports in-place via temp file."""
        try:
            tmp = self._write_to_temp()
            result = safe_add_page_numbers(
                input_file=input_path,
                output_file=tmp,
                position=position,
                format_str=format_str,
                font_size=int(font_size),
                start_number=int(start_number),
            )
            if result.get("success"):
                shutil.move(tmp, output_path)
                # Also update the .original.pdf backup so subsequent
                # annotation re-renders preserve the page numbers.
                if os.path.abspath(input_path) == os.path.abspath(output_path):
                    orig = self._original_path(output_path)
                    try:
                        shutil.copy2(output_path, orig)
                    except Exception:
                        pass
                return {"success": True}
            else:
                self._cleanup_temp(tmp)
                return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _cleanup_temp(path):
        """Silently remove a temp file if it exists."""
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass
