#!/usr/bin/env python3
"""
Safe wrappers around existing PDF CLI tools.

Catches SystemExit raised by the fail() helper in each tool
and converts it into a dict result: {"success": True/False, "error": "..."}.
"""

import sys
from pathlib import Path

# Add parent directory so we can import existing CLI tools
_parent_dir = str(Path(__file__).resolve().parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from pdf_edit import delete_pages as _delete_pages
from pdf_edit import reorder_pages as _reorder_pages
from pdf_edit import insert_pages as _insert_pages
from pdf_merger import merge_pdfs as _merge_pdfs
from pdf_splitter import split_pdf_by_ranges as _split_pdf_by_ranges
from pdf_splitter import parse_page_ranges as _parse_page_ranges
from pdf_page_number import add_page_numbers as _add_page_numbers


def safe_delete_pages(input_file, output_file, delete_spec, verbose=False):
    """Delete pages from a PDF, returning a result dict."""
    try:
        _delete_pages(Path(input_file), Path(output_file), delete_spec, verbose)
        return {"success": True}
    except SystemExit as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def safe_reorder_pages(input_file, output_file, reorder_spec, verbose=False):
    """Reorder pages in a PDF, returning a result dict."""
    try:
        _reorder_pages(Path(input_file), Path(output_file), reorder_spec, verbose)
        return {"success": True}
    except SystemExit as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def safe_insert_pages(input_file, output_file, insert_spec, verbose=False):
    """Insert pages from one PDF into another, returning a result dict."""
    try:
        _insert_pages(Path(input_file), Path(output_file), insert_spec, verbose)
        return {"success": True}
    except SystemExit as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def safe_merge_pdfs(input_files, output_file, verbose=False):
    """Merge multiple PDFs into one, returning a result dict."""
    try:
        paths = [Path(f) for f in input_files]
        _merge_pdfs(paths, Path(output_file), verbose)
        return {"success": True}
    except SystemExit as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def safe_split_pdf(input_file, output_dir, ranges_str, verbose=False):
    """Split a PDF by page ranges, returning a result dict with created files."""
    try:
        input_path = Path(input_file)
        from pypdf import PdfReader
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        ranges = _parse_page_ranges(ranges_str, total_pages)
        created = _split_pdf_by_ranges(input_path, Path(output_dir), ranges, verbose)
        return {"success": True, "files": [str(f) for f in created]}
    except SystemExit as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def safe_add_page_numbers(
    input_file, output_file,
    position="bottom-center",
    format_str="{page}",
    font_size=10,
    start_number=1,
    skip_pages=None,
    verbose=False,
):
    """Add page numbers to a PDF, returning a result dict."""
    try:
        _add_page_numbers(
            input_file=str(input_file),
            output_file=str(output_file),
            position=position,
            format_str=format_str,
            font_size=font_size,
            start_number=start_number,
            skip_pages=skip_pages or [],
            verbose=verbose,
        )
        return {"success": True}
    except SystemExit as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}
