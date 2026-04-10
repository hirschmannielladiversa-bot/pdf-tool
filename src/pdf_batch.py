#!/usr/bin/env python3
"""
PDF Batch Processing Tool

Batch process multiple PDF files using existing PDF tools:
- Batch add page numbers
- Batch split PDFs
- Batch delete pages

Usage:
    # Batch add page numbers
    python3 pdf_batch.py add-page-numbers --input-dir ./pdfs --output-dir ./numbered

    # Batch split
    python3 pdf_batch.py split --input-dir ./pdfs --output-dir ./split --ranges "1-5,6-10"

    # Batch delete pages
    python3 pdf_batch.py delete --input-dir ./pdfs --output-dir ./edited --delete-pages "1"

    # GUI mode
    python3 pdf_batch.py --select-dir
"""

import argparse
import sys
from pathlib import Path
from typing import NoReturn, List, Optional
import tkinter as tk
from tkinter import filedialog, messagebox

# Import functions from existing tools
from pdf_page_number import add_page_numbers
from pdf_splitter import split_pdf_by_ranges, parse_page_ranges, get_num_pages
from pdf_edit import delete_pages


def fail(message: str) -> NoReturn:
    """Print error message and exit."""
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def batch_add_page_numbers(
    input_dir: Path,
    output_dir: Path,
    position: str = "bottom-center",
    format_str: str = "{page}",
    font_size: int = 10,
    skip_pages: Optional[List[int]] = None,
    verbose: bool = False
) -> dict:
    """Batch add page numbers to all PDFs in directory.
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Output directory for processed PDFs
        position: Page number position
        format_str: Page number format string
        font_size: Font size for page numbers
        skip_pages: Pages to skip (optional)
        verbose: Enable verbose output
        
    Returns:
        Dictionary with 'success' and 'failed' lists
    """
    if not input_dir.exists():
        fail(f"Input directory does not exist: {input_dir}")
    
    if not input_dir.is_dir():
        fail(f"Input path is not a directory: {input_dir}")
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        fail(f"No PDF files found in {input_dir}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {"success": [], "failed": []}
    
    if verbose:
        print(f"Found {len(pdf_files)} PDF file(s)")
        print(f"Output directory: {output_dir}")
        print(f"Position: {position}")
        print(f"Format: {format_str}")
        print(f"Font size: {font_size}")
        print()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        output_file = output_dir / pdf_file.name
        
        if verbose:
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        try:
            add_page_numbers(
                pdf_file,
                output_file,
                position=position,
                format_str=format_str,
                font_size=font_size,
                skip_pages=skip_pages,
                verbose=False
            )
            results["success"].append(pdf_file.name)
            if verbose:
                print(f"  ✓ Success: {output_file}")
        except Exception as e:
            results["failed"].append((pdf_file.name, str(e)))
            if verbose:
                print(f"  ✗ Failed: {e}")
    
    return results


def batch_split(
    input_dir: Path,
    output_dir: Path,
    ranges_str: str,
    verbose: bool = False
) -> dict:
    """Batch split all PDFs in directory.
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Output directory for split PDFs
        ranges_str: Page ranges specification
        verbose: Enable verbose output
        
    Returns:
        Dictionary with 'success' and 'failed' lists
    """
    if not input_dir.exists():
        fail(f"Input directory does not exist: {input_dir}")
    
    if not input_dir.is_dir():
        fail(f"Input path is not a directory: {input_dir}")
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        fail(f"No PDF files found in {input_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {"success": [], "failed": []}
    
    if verbose:
        print(f"Found {len(pdf_files)} PDF file(s)")
        print(f"Output directory: {output_dir}")
        print(f"Ranges: {ranges_str}")
        print()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        if verbose:
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        try:
            # Create subdirectory for each PDF
            pdf_output_dir = output_dir / pdf_file.stem
            pdf_output_dir.mkdir(exist_ok=True)
            
            # Parse ranges
            total_pages = get_num_pages(pdf_file)
            ranges = parse_page_ranges(ranges_str, total_pages)
            
            # Split
            created_files = split_pdf_by_ranges(
                pdf_file,
                pdf_output_dir,
                ranges,
                verbose=False
            )
            
            results["success"].append(pdf_file.name)
            if verbose:
                print(f"  ✓ Success: {len(created_files)} file(s) created in {pdf_output_dir}")
        except Exception as e:
            results["failed"].append((pdf_file.name, str(e)))
            if verbose:
                print(f"  ✗ Failed: {e}")
    
    return results


def batch_delete(
    input_dir: Path,
    output_dir: Path,
    delete_spec: str,
    verbose: bool = False
) -> dict:
    """Batch delete pages from all PDFs in directory.
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Output directory for processed PDFs
        delete_spec: Pages to delete specification
        verbose: Enable verbose output
        
    Returns:
        Dictionary with 'success' and 'failed' lists
    """
    if not input_dir.exists():
        fail(f"Input directory does not exist: {input_dir}")
    
    if not input_dir.is_dir():
        fail(f"Input path is not a directory: {input_dir}")
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        fail(f"No PDF files found in {input_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {"success": [], "failed": []}
    
    if verbose:
        print(f"Found {len(pdf_files)} PDF file(s)")
        print(f"Output directory: {output_dir}")
        print(f"Delete pages: {delete_spec}")
        print()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        output_file = output_dir / pdf_file.name
        
        if verbose:
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        try:
            delete_pages(
                pdf_file,
                output_file,
                delete_spec,
                verbose=False
            )
            results["success"].append(pdf_file.name)
            if verbose:
                print(f"  ✓ Success: {output_file}")
        except Exception as e:
            results["failed"].append((pdf_file.name, str(e)))
            if verbose:
                print(f"  ✗ Failed: {e}")
    
    return results


def print_summary(results: dict, operation: str):
    """Print batch operation summary.
    
    Args:
        results: Dictionary with 'success' and 'failed' lists
        operation: Operation name
    """
    total = len(results["success"]) + len(results["failed"])
    print(f"\n{'='*60}")
    print(f"Batch {operation} Summary")
    print(f"{'='*60}")
    print(f"Total files: {total}")
    print(f"Success: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    
    if results["failed"]:
        print(f"\nFailed files:")
        for filename, error in results["failed"]:
            print(f"  - {filename}: {error}")
    
    if results["success"]:
        print(f"\nSuccessful files:")
        for filename in results["success"]:
            print(f"  - {filename}")


def gui_mode():
    """Launch GUI mode for batch processing."""
    root = tk.Tk()
    root.title("PDF Batch Processing")
    root.geometry("500x400")
    
    # Variables
    input_dir_var = tk.StringVar()
    output_dir_var = tk.StringVar()
    operation_var = tk.StringVar(value="add-page-numbers")
    
    # Operation-specific variables
    position_var = tk.StringVar(value="bottom-center")
    format_var = tk.StringVar(value="{page}")
    font_size_var = tk.IntVar(value=10)
    ranges_var = tk.StringVar(value="1-5,6-10")
    delete_pages_var = tk.StringVar(value="1")
    
    def select_input_dir():
        dir_path = filedialog.askdirectory(title="Select Input Directory")
        if dir_path:
            input_dir_var.set(dir_path)
    
    def select_output_dir():
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            output_dir_var.set(dir_path)
    
    def process():
        input_dir = input_dir_var.get()
        output_dir = output_dir_var.get()
        operation = operation_var.get()
        
        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Please select input and output directories")
            return
        
        try:
            if operation == "add-page-numbers":
                results = batch_add_page_numbers(
                    Path(input_dir),
                    Path(output_dir),
                    position=position_var.get(),
                    format_str=format_var.get(),
                    font_size=font_size_var.get(),
                    verbose=True
                )
                op_name = "Page Number Addition"
            
            elif operation == "split":
                results = batch_split(
                    Path(input_dir),
                    Path(output_dir),
                    ranges_var.get(),
                    verbose=True
                )
                op_name = "Split"
            
            elif operation == "delete":
                results = batch_delete(
                    Path(input_dir),
                    Path(output_dir),
                    delete_pages_var.get(),
                    verbose=True
                )
                op_name = "Page Deletion"
            
            total = len(results["success"]) + len(results["failed"])
            message = f"Batch {op_name} Complete\n\n"
            message += f"Total: {total}\n"
            message += f"Success: {len(results['success'])}\n"
            message += f"Failed: {len(results['failed'])}"
            
            if results["failed"]:
                message += f"\n\nFailed files:\n"
                for filename, error in results["failed"][:5]:
                    message += f"- {filename}\n"
                if len(results["failed"]) > 5:
                    message += f"... and {len(results['failed']) - 5} more"
            
            messagebox.showinfo("Success", message)
        
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # Layout
    row = 0
    
    # Input directory
    tk.Label(root, text="Input Directory:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    tk.Entry(root, textvariable=input_dir_var, width=40).grid(row=row, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=select_input_dir).grid(row=row, column=2, padx=5, pady=5)
    row += 1
    
    # Output directory
    tk.Label(root, text="Output Directory:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    tk.Entry(root, textvariable=output_dir_var, width=40).grid(row=row, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=select_output_dir).grid(row=row, column=2, padx=5, pady=5)
    row += 1
    
    # Operation selection
    tk.Label(root, text="Operation:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    operations_frame = tk.Frame(root)
    operations_frame.grid(row=row, column=1, sticky="w", padx=5, pady=5)
    tk.Radiobutton(operations_frame, text="Add Page Numbers", variable=operation_var, value="add-page-numbers").pack(anchor="w")
    tk.Radiobutton(operations_frame, text="Split", variable=operation_var, value="split").pack(anchor="w")
    tk.Radiobutton(operations_frame, text="Delete Pages", variable=operation_var, value="delete").pack(anchor="w")
    row += 1
    
    # Operation-specific options
    options_frame = tk.LabelFrame(root, text="Options", padx=10, pady=10)
    options_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
    
    # Page numbers options
    tk.Label(options_frame, text="Position:").grid(row=0, column=0, sticky="w")
    tk.Entry(options_frame, textvariable=position_var, width=20).grid(row=0, column=1, sticky="w")
    
    tk.Label(options_frame, text="Format:").grid(row=1, column=0, sticky="w")
    tk.Entry(options_frame, textvariable=format_var, width=20).grid(row=1, column=1, sticky="w")
    
    tk.Label(options_frame, text="Font Size:").grid(row=2, column=0, sticky="w")
    tk.Entry(options_frame, textvariable=font_size_var, width=20).grid(row=2, column=1, sticky="w")
    
    # Split options
    tk.Label(options_frame, text="Ranges:").grid(row=3, column=0, sticky="w")
    tk.Entry(options_frame, textvariable=ranges_var, width=20).grid(row=3, column=1, sticky="w")
    
    # Delete options
    tk.Label(options_frame, text="Delete Pages:").grid(row=4, column=0, sticky="w")
    tk.Entry(options_frame, textvariable=delete_pages_var, width=20).grid(row=4, column=1, sticky="w")
    
    row += 1
    
    # Process button
    tk.Button(root, text="Process", command=process, bg="green", fg="white", padx=20, pady=10).grid(row=row, column=0, columnspan=3, pady=20)
    
    root.mainloop()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch process PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Batch add page numbers
  python3 pdf_batch.py add-page-numbers --input-dir ./pdfs --output-dir ./numbered

  # Batch split
  python3 pdf_batch.py split --input-dir ./pdfs --output-dir ./split --ranges "1-5,6-10"

  # Batch delete pages
  python3 pdf_batch.py delete --input-dir ./pdfs --output-dir ./edited --delete-pages "1"

  # GUI mode
  python3 pdf_batch.py --select-dir
"""
    )
    
    # GUI mode flag
    parser.add_argument("--select-dir", action="store_true", help="Launch GUI mode")
    
    subparsers = parser.add_subparsers(dest="command", help="Batch operation")
    
    # add-page-numbers subcommand
    page_num_parser = subparsers.add_parser("add-page-numbers", help="Batch add page numbers")
    page_num_parser.add_argument("--input-dir", type=Path, required=True, help="Input directory containing PDFs")
    page_num_parser.add_argument("--output-dir", type=Path, required=True, help="Output directory")
    page_num_parser.add_argument("--position", default="bottom-center", help="Position (default: bottom-center)")
    page_num_parser.add_argument("--format", dest="format_str", default="{page}", help="Format string (default: {page})")
    page_num_parser.add_argument("--font-size", type=int, default=10, help="Font size (default: 10)")
    page_num_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    # split subcommand
    split_parser = subparsers.add_parser("split", help="Batch split PDFs")
    split_parser.add_argument("--input-dir", type=Path, required=True, help="Input directory containing PDFs")
    split_parser.add_argument("--output-dir", type=Path, required=True, help="Output directory")
    split_parser.add_argument("--ranges", required=True, help="Page ranges (e.g., '1-5,6-10')")
    split_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    # delete subcommand
    delete_parser = subparsers.add_parser("delete", help="Batch delete pages")
    delete_parser.add_argument("--input-dir", type=Path, required=True, help="Input directory containing PDFs")
    delete_parser.add_argument("--output-dir", type=Path, required=True, help="Output directory")
    delete_parser.add_argument("--delete-pages", required=True, help="Pages to delete (e.g., '1,3,5' or '1-3')")
    delete_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # GUI mode
    if args.select_dir:
        gui_mode()
        return
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == "add-page-numbers":
        results = batch_add_page_numbers(
            args.input_dir,
            args.output_dir,
            position=args.position,
            format_str=args.format_str,
            font_size=args.font_size,
            verbose=args.verbose
        )
        print_summary(results, "Page Number Addition")
    
    elif args.command == "split":
        results = batch_split(
            args.input_dir,
            args.output_dir,
            args.ranges,
            verbose=args.verbose
        )
        print_summary(results, "Split")
    
    elif args.command == "delete":
        results = batch_delete(
            args.input_dir,
            args.output_dir,
            args.delete_pages,
            verbose=args.verbose
        )
        print_summary(results, "Page Deletion")


if __name__ == "__main__":
    main()
