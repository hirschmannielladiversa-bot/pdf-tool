#!/usr/bin/env python3
"""
PDF Page Number Tool
Add page numbers to PDF files with customizable position and format.
"""

import argparse
import sys
from pathlib import Path
from io import BytesIO
from typing import NoReturn, Optional, Union

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Error: pypdf not installed. Run: pip install pypdf", file=sys.stderr)
    sys.exit(1)

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    print("Error: reportlab not installed. Run: pip install reportlab", file=sys.stderr)
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import filedialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


def fail(message: str) -> NoReturn:
    """Print a user-friendly error and exit."""
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def calculate_position(position: str, width: float, height: float, font_size: int) -> tuple[float, float]:
    """Calculate x, y coordinates for page number based on position."""
    margin = 30
    
    # Adjust for text centering
    x_offset = 0
    if "center" in position:
        # This is approximate - actual centering would need text width
        x_offset = -20
    elif "right" in position:
        x_offset = -40
    
    positions = {
        "top-left": (margin, height - margin),
        "top-center": (width / 2 + x_offset, height - margin),
        "top-right": (width - margin, height - margin),
        "bottom-left": (margin, margin),
        "bottom-center": (width / 2 + x_offset, margin),
        "bottom-right": (width - margin, margin),
    }
    
    return positions.get(position, positions["bottom-center"])


def add_page_numbers(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    position: str = "bottom-center",
    format_str: str = "{page}",
    font_size: int = 10,
    start_number: int = 1,
    skip_pages: Optional[list[int]] = None,
    verbose: bool = False
) -> None:
    """Add page numbers to PDF."""

    # Convert to Path objects
    input_path = Path(input_file) if isinstance(input_file, str) else input_file
    output_path = Path(output_file) if isinstance(output_file, str) else output_file

    # Validate input file
    if not input_path.exists():
        fail(f"File not found: {input_path}")

    if not input_path.suffix.lower() == '.pdf':
        fail(f"Input file must be PDF: {input_path}")

    # Validate position
    valid_positions = [
        "top-left", "top-center", "top-right",
        "bottom-left", "bottom-center", "bottom-right"
    ]
    if position not in valid_positions:
        fail(f"Invalid position: {position}. Must be one of {valid_positions}")

    # Initialize skip_pages
    if skip_pages is None:
        skip_pages = []

    # Validate skip_pages
    for page_num in skip_pages:
        if page_num < 1:
            fail(f"Invalid skip page number: {page_num}. Page numbers must be >= 1")
    
    if verbose:
        print(f"Reading PDF: {input_path}")

    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    # Validate skip_pages against total_pages
    for page_num in skip_pages:
        if page_num > total_pages:
            fail(f"Invalid skip page number: {page_num}. PDF only has {total_pages} pages")

    if verbose:
        print(f"Total pages: {total_pages}")
        if skip_pages:
            print(f"Skipping pages: {skip_pages}")
    
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        
        if page_num in skip_pages:
            if verbose:
                print(f"Page {page_num}: skipped")
            writer.add_page(page)
            continue
        
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        x, y = calculate_position(position, page_width, page_height, font_size)
        
        display_number = page_num + start_number - 1
        text = format_str.format(page=display_number, total=total_pages)
        
        can.setFont("Helvetica", font_size)
        can.drawString(x, y, text)
        can.save()
        
        packet.seek(0)
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        
        writer.add_page(page)
        
        if verbose:
            print(f"Page {page_num}: added '{text}' at {position}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        writer.write(f)

    if verbose:
        print(f"Saved to: {output_path}")


def select_files_gui() -> Optional[tuple[Path, Path]]:
    """GUI file selection dialog."""
    if not GUI_AVAILABLE:
        print("Error: tkinter not available for GUI mode", file=sys.stderr)
        return None
    
    root = tk.Tk()
    root.withdraw()
    
    input_path = filedialog.askopenfilename(
        title="Select PDF file to add page numbers",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    
    if not input_path:
        return None
    
    input_file = Path(input_path)
    suggested_name = f"{input_file.stem}_numbered.pdf"
    
    output_path = filedialog.asksaveasfilename(
        title="Save numbered PDF as",
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile=suggested_name
    )
    
    if not output_path:
        return None
    
    return input_file, Path(output_path)


def parse_skip_pages(skip_str: str) -> list[int]:
    """Parse comma-separated page numbers."""
    if not skip_str:
        return []
    
    pages = []
    for part in skip_str.split(','):
        part = part.strip()
        if part:
            try:
                pages.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid page number: {part}")
    
    return pages


def main():
    parser = argparse.ArgumentParser(
        description="Add page numbers to PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.pdf -o output.pdf
  %(prog)s input.pdf -o output.pdf --position bottom-right
  %(prog)s input.pdf -o output.pdf --format "Page {page} of {total}"
  %(prog)s input.pdf -o output.pdf --skip-pages "1,2"
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
    
    parser.add_argument(
        '--position',
        choices=['top-left', 'top-center', 'top-right', 
                 'bottom-left', 'bottom-center', 'bottom-right'],
        default='bottom-center',
        help='Page number position (default: bottom-center)'
    )
    
    parser.add_argument(
        '--format',
        default='{page}',
        help='Page number format. Use {page} and {total} placeholders (default: {page})'
    )
    
    parser.add_argument(
        '--font-size',
        type=int,
        default=10,
        help='Font size for page numbers (default: 10)'
    )
    
    parser.add_argument(
        '--start-number',
        type=int,
        default=1,
        help='Starting page number (default: 1)'
    )
    
    parser.add_argument(
        '--skip-pages',
        type=str,
        help='Comma-separated page numbers to skip (e.g., "1,2,3")'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--select-files',
        action='store_true',
        help='Use GUI to select files'
    )
    
    args = parser.parse_args()
    
    try:
        if args.select_files:
            result = select_files_gui()
            if result is None:
                print("File selection cancelled")
                return
            input_file, output_file = result
        else:
            if not args.input or not args.output:
                parser.error("input and --output are required (or use --select-files)")
            input_file = args.input
            output_file = args.output
        
        skip_pages = parse_skip_pages(args.skip_pages) if args.skip_pages else []
        
        add_page_numbers(
            input_file=input_file,
            output_file=output_file,
            position=args.position,
            format_str=args.format,
            font_size=args.font_size,
            start_number=args.start_number,
            skip_pages=skip_pages,
            verbose=args.verbose
        )
        
        print(f"Success: Page numbers added to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
