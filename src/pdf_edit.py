#!/usr/bin/env python3
"""
PDF Page Editor CLI Tool
Delete, reorder, and insert pages in PDF files.
"""

import argparse
import os
import re
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
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


def parse_page_spec(spec: str, total_pages: int) -> list[int]:
    """
    Parse page specification (e.g., "1,3,5-7") into list of page numbers.
    
    Args:
        spec: Page specification string
        total_pages: Total number of pages in PDF
        
    Returns:
        List of page numbers (1-based)
    """
    if not spec or not spec.strip():
        fail("Empty page specification")

    parts = spec.split(',')
    page_numbers: list[int] = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check if it's a range (e.g., "5-7")
        if '-' in part:
            range_parts = part.split('-', 1)
            if len(range_parts) != 2:
                fail(f"Invalid range format: {part}")

            try:
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
            except ValueError:
                fail(f"Invalid page numbers in range: {part}")

            if start < 1 or end < 1:
                fail(f"Page numbers must be >= 1: {part}")
            if start > total_pages or end > total_pages:
                fail(f"Page numbers must be <= {total_pages}: {part}")
            if start > end:
                fail(f"Start page must be <= end page: {part}")

            page_numbers.extend(range(start, end + 1))
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

            page_numbers.append(page)

    if not page_numbers:
        fail("No valid page numbers found in specification")

    return page_numbers


def delete_pages(
    input_file: Path,
    output_file: Path,
    delete_spec: str,
    verbose: bool = False
) -> None:
    """
    Delete specified pages from a PDF file.
    
    Args:
        input_file: Input PDF file path
        output_file: Output PDF file path
        delete_spec: Page specification (e.g., "1,3,5-7")
        verbose: Enable verbose output
    """
    input_path = validate_input_file(input_file)
    output_path = validate_output_path(output_file)

    try:
        with open(input_path, 'rb') as f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)

            if verbose:
                print(f"Input PDF: {input_path}")
                print(f"Total pages: {total_pages}")
                print(f"Delete specification: {delete_spec}")

            # Parse pages to delete
            pages_to_delete = set(parse_page_spec(delete_spec, total_pages))

            if verbose:
                print(f"Pages to delete: {sorted(pages_to_delete)}")

            # Create output PDF with remaining pages
            writer = PdfWriter()
            kept_pages = 0

            for page_num in range(1, total_pages + 1):
                if page_num not in pages_to_delete:
                    writer.add_page(reader.pages[page_num - 1])
                    kept_pages += 1

            if kept_pages == 0:
                fail("All pages would be deleted. Output PDF must have at least 1 page")

            # Write output file
            with open(output_path, 'wb') as out_f:
                writer.write(out_f)

            if verbose:
                print(f"Deleted {len(pages_to_delete)} page(s)")
                print(f"Kept {kept_pages} page(s)")
                print(f"Output: {output_path}")

    except Exception as e:
        fail(f"Failed to delete pages: {e}")


def reorder_pages(
    input_file: Path,
    output_file: Path,
    reorder_spec: str,
    verbose: bool = False
) -> None:
    """
    Reorder pages in a PDF file.
    
    Args:
        input_file: Input PDF file path
        output_file: Output PDF file path
        reorder_spec: Page order specification (e.g., "3,1,2,4-10")
        verbose: Enable verbose output
    """
    input_path = validate_input_file(input_file)
    output_path = validate_output_path(output_file)

    try:
        with open(input_path, 'rb') as f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)

            if verbose:
                print(f"Input PDF: {input_path}")
                print(f"Total pages: {total_pages}")
                print(f"Reorder specification: {reorder_spec}")

            # Parse new page order
            new_order = parse_page_spec(reorder_spec, total_pages)

            if verbose:
                print(f"New page order: {new_order}")

            # Create output PDF with reordered pages
            writer = PdfWriter()

            for page_num in new_order:
                writer.add_page(reader.pages[page_num - 1])

            # Write output file
            with open(output_path, 'wb') as out_f:
                writer.write(out_f)

            if verbose:
                print(f"Reordered {len(new_order)} page(s)")
                print(f"Output: {output_path}")

    except Exception as e:
        fail(f"Failed to reorder pages: {e}")


def insert_pages(
    input_file: Path,
    output_file: Path,
    insert_spec: str,
    verbose: bool = False
) -> None:
    """
    Insert pages from another PDF into the input PDF.
    
    Args:
        input_file: Input PDF file path
        output_file: Output PDF file path
        insert_spec: Insert specification (e.g., "source.pdf:1-3@5")
        verbose: Enable verbose output
    """
    input_path = validate_input_file(input_file)
    output_path = validate_output_path(output_file)

    # Parse insert specification
    match = re.match(r'^(.+):(.+)@(\d+)$', insert_spec)
    if not match:
        fail("Invalid insert specification format. Expected: 'source.pdf:1-3@5'")

    source_file_str, page_spec, insert_pos_str = match.groups()
    source_file = Path(source_file_str).expanduser()
    
    try:
        insert_position = int(insert_pos_str)
    except ValueError:
        fail(f"Invalid insert position: {insert_pos_str}")

    # Validate source file
    source_path = validate_input_file(source_file)

    try:
        # Read input PDF
        with open(input_path, 'rb') as f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)

            if verbose:
                print(f"Input PDF: {input_path}")
                print(f"Total pages: {total_pages}")
                print(f"Source PDF: {source_path}")

            # Validate insert position
            if insert_position < 0:
                fail(f"Insert position must be >= 0: {insert_position}")
            if insert_position > total_pages:
                fail(f"Insert position must be <= {total_pages}: {insert_position}")

            # Read source PDF
            with open(source_path, 'rb') as src_f:
                source_reader = PdfReader(src_f)
                source_total_pages = len(source_reader.pages)

                if verbose:
                    print(f"Source total pages: {source_total_pages}")
                    print(f"Page specification: {page_spec}")
                    print(f"Insert position: {insert_position}")

                # Parse pages to insert from source
                pages_to_insert = parse_page_spec(page_spec, source_total_pages)

                if verbose:
                    print(f"Pages to insert: {pages_to_insert}")

                # Create output PDF
                writer = PdfWriter()

                # Add pages before insert position
                for i in range(insert_position):
                    writer.add_page(reader.pages[i])

                # Add pages from source
                for page_num in pages_to_insert:
                    writer.add_page(source_reader.pages[page_num - 1])

                # Add remaining pages from input
                for i in range(insert_position, total_pages):
                    writer.add_page(reader.pages[i])

                # Write output file
                with open(output_path, 'wb') as out_f:
                    writer.write(out_f)

                if verbose:
                    print(f"Inserted {len(pages_to_insert)} page(s)")
                    print(f"Output: {output_path} ({total_pages + len(pages_to_insert)} pages)")

    except Exception as e:
        fail(f"Failed to insert pages: {e}")


def run_gui_mode() -> None:
    """Run in GUI mode for interactive page editing."""
    root = tk.Tk()
    root.withdraw()

    # Select input file
    input_file = filedialog.askopenfilename(
        title="Select Input PDF",
        filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
    )

    if not input_file:
        messagebox.showinfo("Cancelled", "No input file selected")
        return

    input_path = Path(input_file)

    try:
        # Get total pages
        with open(input_path, 'rb') as f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read PDF: {e}")
        return

    # Ask for operation type
    operation = None
    while not operation:
        choice = simpledialog.askstring(
            "Select Operation",
            f"PDF: {input_path.name} ({total_pages} pages)\n\n"
            "Choose operation:\n"
            "  d = Delete pages\n"
            "  r = Reorder pages\n"
            "  i = Insert pages\n\n"
            "Enter choice (d/r/i):"
        )

        if not choice:
            messagebox.showinfo("Cancelled", "Operation cancelled")
            return

        choice = choice.lower().strip()
        if choice in ['d', 'r', 'i']:
            operation = choice
        else:
            messagebox.showerror("Error", "Invalid choice. Please enter 'd', 'r', or 'i'")

    # Get operation-specific parameters
    spec = None
    source_file = None

    if operation == 'd':
        spec = simpledialog.askstring(
            "Delete Pages",
            f"Total pages: {total_pages}\n\n"
            "Enter pages to delete (e.g., '1,3,5-7'):"
        )
        if not spec:
            messagebox.showinfo("Cancelled", "Operation cancelled")
            return

    elif operation == 'r':
        spec = simpledialog.askstring(
            "Reorder Pages",
            f"Total pages: {total_pages}\n\n"
            "Enter new page order (e.g., '3,1,2,4-10'):"
        )
        if not spec:
            messagebox.showinfo("Cancelled", "Operation cancelled")
            return

    elif operation == 'i':
        # Select source PDF
        source_file = filedialog.askopenfilename(
            title="Select Source PDF to Insert From",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if not source_file:
            messagebox.showinfo("Cancelled", "No source file selected")
            return

        source_path = Path(source_file)
        try:
            with open(source_path, 'rb') as f:
                source_reader = PdfReader(f)
                source_total_pages = len(source_reader.pages)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read source PDF: {e}")
            return

        page_spec = simpledialog.askstring(
            "Insert Pages - Page Selection",
            f"Source PDF: {source_path.name} ({source_total_pages} pages)\n\n"
            "Enter pages to insert (e.g., '1-3'):"
        )
        if not page_spec:
            messagebox.showinfo("Cancelled", "Operation cancelled")
            return

        insert_pos = simpledialog.askinteger(
            "Insert Pages - Position",
            f"Input PDF: {input_path.name} ({total_pages} pages)\n\n"
            f"Enter insert position (0-{total_pages}):\n"
            f"0 = before all pages\n"
            f"{total_pages} = after all pages",
            minvalue=0,
            maxvalue=total_pages
        )
        if insert_pos is None:
            messagebox.showinfo("Cancelled", "Operation cancelled")
            return

        spec = f"{source_file}:{page_spec}@{insert_pos}"

    # Select output file
    default_output = input_path.parent / f"{input_path.stem}_edited.pdf"
    output_file = filedialog.asksaveasfilename(
        title="Save Output PDF",
        defaultextension=".pdf",
        filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        initialfile=default_output.name,
        initialdir=input_path.parent
    )

    if not output_file:
        messagebox.showinfo("Cancelled", "No output file selected")
        return

    output_path = Path(output_file)

    # Execute operation
    try:
        if operation == 'd':
            delete_pages(input_path, output_path, spec, verbose=False)
            messagebox.showinfo("Success", f"Pages deleted successfully!\n\nOutput: {output_path}")
        elif operation == 'r':
            reorder_pages(input_path, output_path, spec, verbose=False)
            messagebox.showinfo("Success", f"Pages reordered successfully!\n\nOutput: {output_path}")
        elif operation == 'i':
            insert_pages(input_path, output_path, spec, verbose=False)
            messagebox.showinfo("Success", f"Pages inserted successfully!\n\nOutput: {output_path}")
    except SystemExit:
        # Error already displayed by fail()
        pass
    except Exception as e:
        messagebox.showerror("Error", f"Operation failed: {e}")


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="PDF Page Editor - Delete, reorder, and insert pages in PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete pages 1, 3, and 5-7
  %(prog)s input.pdf --delete "1,3,5-7" -o output.pdf

  # Reorder pages (put page 3 first, then 1, 2, and 4-10)
  %(prog)s input.pdf --reorder "3,1,2,4-10" -o output.pdf

  # Insert pages 1-3 from source.pdf at position 5
  %(prog)s input.pdf --insert "source.pdf:1-3@5" -o output.pdf

  # Interactive GUI mode
  %(prog)s --select-files
        """
    )

    parser.add_argument(
        'input',
        nargs='?',
        type=Path,
        help='Input PDF file'
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output PDF file'
    )

    # Operation modes (mutually exclusive)
    operations = parser.add_mutually_exclusive_group()
    operations.add_argument(
        '--delete',
        metavar='SPEC',
        help='Delete pages (e.g., "1,3,5-7")'
    )
    operations.add_argument(
        '--reorder',
        metavar='SPEC',
        help='Reorder pages (e.g., "3,1,2,4-10")'
    )
    operations.add_argument(
        '--insert',
        metavar='SPEC',
        help='Insert pages from another PDF (e.g., "source.pdf:1-3@5")'
    )
    operations.add_argument(
        '--select-files',
        action='store_true',
        help='Use GUI to select files and operation interactively'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser


def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # GUI mode
    if args.select_files:
        run_gui_mode()
        return

    # CLI mode validation
    if not args.input:
        parser.error("input file is required (or use --select-files for GUI mode)")

    if not args.output:
        parser.error("--output is required")

    # Check that exactly one operation is specified
    operations = [args.delete, args.reorder, args.insert]
    if sum(op is not None for op in operations) != 1:
        parser.error("exactly one operation (--delete, --reorder, or --insert) is required")

    # Execute operation
    if args.delete:
        delete_pages(args.input, args.output, args.delete, args.verbose)
    elif args.reorder:
        reorder_pages(args.input, args.output, args.reorder, args.verbose)
    elif args.insert:
        insert_pages(args.input, args.output, args.insert, args.verbose)


if __name__ == '__main__':
    main()
