#!/usr/bin/env python3
"""
PDF Merger CLI Tool
Merge multiple PDF files into a single file.
"""

import argparse
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
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


def validate_input_file(path: Path) -> Path:
    """Validate that input file exists and is a readable PDF."""
    if not path.exists():
        fail(f"File not found: {path}")

    if not path.is_file():
        fail(f"Not a file: {path}")

    if path.suffix.lower() != '.pdf':
        fail(f"Input file must be a PDF: {path}")

    if not os.access(path, os.R_OK):
        fail(f"File is not readable: {path}")

    return path


def validate_output_path(path: Path) -> Path:
    """Validate that output path can be written as a PDF."""
    resolved = path.expanduser()

    if resolved.suffix.lower() != '.pdf':
        fail(f"Output file must use the .pdf extension: {resolved}")

    if resolved.exists() and resolved.is_dir():
        fail(f"Output path is a directory: {resolved}")

    parent = resolved.parent
    if not parent.exists():
        fail(f"Output directory does not exist: {parent}")

    if not os.access(parent, os.W_OK):
        fail(f"Output directory is not writable: {parent}")

    return resolved


def merge_pdfs(
    input_files: list[Path],
    output_file: Path,
    verbose: bool = False
) -> None:
    """
    Merge multiple PDF files into a single file.

    Args:
        input_files: List of PDF files to merge (in order)
        output_file: Output PDF file path
        verbose: Enable verbose output
    """
    if not input_files:
        fail("No input files provided")

    if len(input_files) < 2:
        fail("At least 2 PDF files are required for merging")

    # Validate all input files
    validated_files: list[Path] = []
    for file in input_files:
        validated_files.append(validate_input_file(file))

    # Validate output path
    output_path = validate_output_path(output_file)

    if verbose:
        print(f"Merging {len(validated_files)} PDF file(s):")
        for i, file in enumerate(validated_files, 1):
            print(f"  {i}. {file.name}")
        print(f"Output: {output_path}")

    # Create PDF writer
    writer = PdfWriter()
    total_pages = 0

    try:
        # Read and merge all PDFs
        for file in validated_files:
            if verbose:
                print(f"Reading: {file.name}")

            with open(file, 'rb') as f:
                reader = PdfReader(f)
                num_pages = len(reader.pages)
                total_pages += num_pages

                if verbose:
                    print(f"  Pages: {num_pages}")

                # Add all pages from this PDF
                for page in reader.pages:
                    writer.add_page(page)

        # Write merged PDF
        with open(output_path, 'wb') as output:
            writer.write(output)

        if verbose:
            print(f"\n✅ Merged {len(validated_files)} file(s) ({total_pages} pages) → {output_path}")
        else:
            print(f"Created: {output_path} ({total_pages} pages)")

    except PermissionError as e:
        fail(f"Permission denied: {e}")
    except Exception as e:
        fail(f"Failed to merge PDFs: {e}")


def select_input_files() -> list[Path]:
    """Open a file dialog to select multiple input PDFs."""
    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        selected = filedialog.askopenfilenames(
            title="Select PDF files to merge (in order)",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
    finally:
        root.destroy()

    if not selected:
        fail("No input files selected")

    if len(selected) < 2:
        fail("At least 2 PDF files are required for merging")

    return [Path(path) for path in selected]


def select_output_file() -> Path:
    """Open a save dialog to select output PDF path."""
    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        selected = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
    finally:
        root.destroy()

    if not selected:
        fail("No output file selected")

    return Path(selected)


def run_gui_mode():
    """Run in GUI mode with dialogs."""
    print("Running in GUI mode...")

    # Select input files
    input_files = select_input_files()
    print(f"Selected {len(input_files)} file(s):")
    for i, file in enumerate(input_files, 1):
        print(f"  {i}. {file.name}")

    # Select output file
    output_file = select_output_file()
    print(f"Output: {output_file}")

    # Merge PDFs
    merge_pdfs(input_files, output_file, verbose=True)

    # Show success message
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Success",
        f"Merged {len(input_files)} PDF file(s) into:\n{output_file}"
    )
    root.destroy()


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    return argparse.ArgumentParser(
        description="Merge multiple PDF files into a single file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # GUI mode
  python3 pdf_merger.py --select-files

  # CLI mode
  python3 pdf_merger.py file1.pdf file2.pdf -o merged.pdf
  python3 pdf_merger.py doc1.pdf doc2.pdf doc3.pdf --output combined.pdf --verbose
  python3 pdf_merger.py chapter*.pdf -o book.pdf
        """,
    )


def main() -> None:
    """Main entry point for the CLI tool."""
    parser = build_parser()
    parser.add_argument(
        "input_files",
        nargs="*",
        type=Path,
        help="Input PDF files to merge (in order)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output merged PDF file path"
    )
    parser.add_argument(
        "--select-files",
        action="store_true",
        help="Use GUI dialogs to select files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # GUI mode
    if args.select_files or not args.input_files:
        if args.input_files:
            fail("Do not combine input files with --select-files")
        run_gui_mode()
        return

    # CLI mode validation
    if not args.output:
        fail("Output file is required. Use -o/--output or --select-files for GUI")

    if len(args.input_files) < 2:
        fail("At least 2 PDF files are required for merging")

    # Expand user paths
    input_files = [f.expanduser() for f in args.input_files]
    output_file = args.output.expanduser()

    # Merge PDFs
    merge_pdfs(input_files, output_file, args.verbose)


if __name__ == "__main__":
    main()
