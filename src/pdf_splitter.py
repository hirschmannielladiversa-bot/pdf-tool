#!/usr/bin/env python3
"""
PDF Splitter CLI Tool
Split a PDF file into multiple files by page ranges.
"""

import argparse
import os
import re
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from typing import NoReturn

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Error: pypdf is not installed. Run: pip install pypdf", file=sys.stderr)
    raise SystemExit(1)


def fail(message: str) -> NoReturn:
    """Print a user-friendly error and exit."""
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_page_ranges(ranges_str: str, total_pages: int) -> list[tuple[int, int]]:
    """
    Parse page ranges from string like "1-3,4-7,8-10" or "1:3 4:7 8:10".

    Returns list of (start, end) tuples (1-indexed, inclusive).
    Validates that all page numbers are within valid range.
    """
    if not ranges_str or not ranges_str.strip():
        fail("Page ranges cannot be empty")

    # Split by comma or space
    range_parts = re.split(r'[,\s]+', ranges_str.strip())
    parsed_ranges: list[tuple[int, int]] = []

    for part in range_parts:
        part = part.strip()
        if not part:
            continue

        # Check for range separator (- or :)
        if '-' in part or ':' in part:
            separator = '-' if '-' in part else ':'
            parts = part.split(separator, 1)
            if len(parts) != 2:
                fail(f"Invalid range format: {part}")

            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except ValueError:
                fail(f"Invalid page numbers in range: {part}")

            if start < 1 or end < 1:
                fail(f"Page numbers must be >= 1: {part}")
            if start > total_pages or end > total_pages:
                fail(f"Page numbers must be <= {total_pages}: {part}")
            if start > end:
                fail(f"Start page must be <= end page: {part}")

            parsed_ranges.append((start, end))
        else:
            # Single page
            try:
                page = int(part.strip())
            except ValueError:
                fail(f"Invalid page number: {part}")

            if page < 1:
                fail(f"Page number must be >= 1: {part}")
            if page > total_pages:
                fail(f"Page number must be <= {total_pages}: {part}")

            parsed_ranges.append((page, page))

    if not parsed_ranges:
        fail("No valid page ranges found")

    # Sort ranges by start page
    parsed_ranges.sort(key=lambda x: x[0])

    # Check for overlaps (optional warning, but allow it for now)
    for i in range(len(parsed_ranges) - 1):
        current_end = parsed_ranges[i][1]
        next_start = parsed_ranges[i + 1][0]
        if current_end >= next_start:
            print(f"Warning: Ranges overlap: {parsed_ranges[i]} and {parsed_ranges[i+1]}",
                  file=sys.stderr)

    return parsed_ranges


def get_num_pages(pdf_path: Path) -> int:
    """Get the number of pages in a PDF file."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            return len(reader.pages)
    except Exception as e:
        fail(f"Failed to read PDF file: {e}")


def split_pdf_by_ranges(
    input_path: Path,
    output_dir: Path,
    ranges: list[tuple[int, int]],
    verbose: bool = False
) -> list[Path]:
    """
    Split PDF into multiple files based on page ranges.

    Returns list of created file paths.
    """
    if not input_path.exists():
        fail(f"Input file not found: {input_path}")

    if not input_path.is_file():
        fail(f"Not a file: {input_path}")

    if input_path.suffix.lower() != '.pdf':
        fail(f"Input file must be a PDF: {input_path}")

    if not os.access(input_path, os.R_OK):
        fail(f"Input file is not readable: {input_path}")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    if not os.access(output_dir, os.W_OK):
        fail(f"Output directory is not writable: {output_dir}")

    # Read the input PDF
    try:
        with open(input_path, 'rb') as f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)

            if verbose:
                print(f"Input PDF: {input_path}")
                print(f"Total pages: {total_pages}")
                print(f"Splitting into {len(ranges)} file(s)")

            created_files: list[Path] = []
            base_name = input_path.stem

            for start, end in ranges:
                # Create output filename
                if start == end:
                    output_filename = f"{base_name}_p{start}.pdf"
                else:
                    output_filename = f"{base_name}_p{start}-{end}.pdf"

                output_path = output_dir / output_filename

                # Create new PDF with specified pages
                writer = PdfWriter()
                for page_num in range(start - 1, end):  # Convert to 0-indexed
                    writer.add_page(reader.pages[page_num])

                # Write to file
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

                created_files.append(output_path)

                if verbose:
                    print(f"  Created: {output_filename} (pages {start}-{end})")

            return created_files

    except PermissionError as e:
        fail(f"Permission denied: {e}")
    except Exception as e:
        fail(f"Failed to split PDF: {e}")


def select_input_file() -> Path:
    """Open a file dialog to select input PDF."""
    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        selected = filedialog.askopenfilename(
            title="Select PDF file to split",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
    finally:
        root.destroy()

    if not selected:
        fail("No input file selected")

    return Path(selected)


def select_output_directory() -> Path:
    """Open a directory dialog to select output location."""
    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        selected = filedialog.askdirectory(
            title="Select output directory for split PDFs",
        )
    finally:
        root.destroy()

    if not selected:
        fail("No output directory selected")

    return Path(selected)


def ask_page_ranges(total_pages: int) -> str:
    """Show dialog to input page ranges."""
    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        ranges = simpledialog.askstring(
            "Page Ranges",
            f"Enter page ranges (total: {total_pages} pages)\n\n"
            f"Examples:\n"
            f"  1-3,4-7,8-10\n"
            f"  1:3 4:7 8:10\n"
            f"  5 (single page)\n"
            f"  1-5,10-15",
            parent=root
        )
    finally:
        root.destroy()

    if not ranges:
        fail("No page ranges specified")

    return ranges


def run_gui_mode():
    """Run in GUI mode with dialogs."""
    print("Running in GUI mode...")

    # Select input file
    input_file = select_input_file()
    print(f"Selected input: {input_file}")

    # Get total pages
    total_pages = get_num_pages(input_file)
    print(f"Total pages: {total_pages}")

    # Ask for page ranges
    ranges_str = ask_page_ranges(total_pages)
    print(f"Page ranges: {ranges_str}")

    # Parse ranges
    ranges = parse_page_ranges(ranges_str, total_pages)

    # Select output directory
    output_dir = select_output_directory()
    print(f"Output directory: {output_dir}")

    # Split PDF
    created_files = split_pdf_by_ranges(input_file, output_dir, ranges, verbose=True)

    # Show success message
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Success",
        f"Created {len(created_files)} file(s) in:\n{output_dir}"
    )
    root.destroy()


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    return argparse.ArgumentParser(
        description="Split a PDF file into multiple files by page ranges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # GUI mode
  python3 pdf_splitter.py --select-files

  # CLI mode
  python3 pdf_splitter.py input.pdf --ranges "1-3,4-7,8-10" --output-dir ./out
  python3 pdf_splitter.py report.pdf --ranges "1:5 10:15" -o ./split
  python3 pdf_splitter.py document.pdf --ranges "1-10" --output-dir ./pages --verbose
        """,
    )


def main() -> None:
    """Main entry point for the CLI tool."""
    parser = build_parser()
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="Input PDF file to split"
    )
    parser.add_argument(
        "--ranges",
        type=str,
        help='Page ranges to split (e.g., "1-3,4-7,8-10" or "1:3 4:7 8:10")'
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        help="Output directory for split PDF files (default: same as input)"
    )
    parser.add_argument(
        "--select-files",
        action="store_true",
        help="Use GUI dialogs to select files and ranges"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # GUI mode
    if args.select_files or not args.input_file:
        if args.input_file:
            fail("Do not combine input file with --select-files")
        run_gui_mode()
        return

    # CLI mode validation
    if not args.ranges:
        fail("Page ranges are required. Use --ranges or --select-files for GUI")

    input_file = args.input_file.expanduser()

    # Get total pages to validate ranges
    total_pages = get_num_pages(input_file)

    # Parse and validate ranges
    ranges = parse_page_ranges(args.ranges, total_pages)

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir.expanduser()
    else:
        output_dir = input_file.parent

    # Split PDF
    created_files = split_pdf_by_ranges(input_file, output_dir, ranges, args.verbose)

    if not args.verbose:
        print(f"Created {len(created_files)} file(s) in: {output_dir}")


if __name__ == "__main__":
    main()
