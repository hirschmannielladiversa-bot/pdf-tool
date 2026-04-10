#!/usr/bin/env python3
"""
Image to PDF Converter CLI Tool
Converts multiple PNG/JPEG images into a single PDF file.
"""

import argparse
import os
import re
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from typing import NoReturn

from PIL import Image, ImageOps

SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg"}
FILE_DIALOG_TYPES = [
    ("Image files", "*.png *.jpg *.jpeg"),
    ("PNG files", "*.png"),
    ("JPEG files", "*.jpg *.jpeg"),
    ("All files", "*.*"),
]


def fail(message: str) -> NoReturn:
    """Print a user-friendly error and exit."""
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def natural_sort_key(path: Path) -> list[object]:
    """Sort file names like page2 before page10."""
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def collect_image_files(paths: list[Path], recursive: bool) -> list[Path]:
    """Expand files and directories into a flat list of candidate image files."""
    collected: list[Path] = []

    for path in paths:
        resolved = path.expanduser()

        if not resolved.exists():
            fail(f"File or directory not found: {resolved}")

        if resolved.is_dir():
            iterator = resolved.rglob("*") if recursive else resolved.iterdir()
            image_files = [
                child
                for child in iterator
                if child.is_file() and child.suffix.lower() in SUPPORTED_FORMATS
            ]
            if not image_files:
                fail(f"No supported images found in directory: {resolved}")
            collected.extend(sorted(image_files, key=natural_sort_key))
            continue

        collected.append(resolved)

    return collected


def select_image_files() -> list[Path]:
    """Open a file dialog so the user can pick one or more images."""
    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        selected = filedialog.askopenfilenames(
            title="Select images to convert to PDF",
            filetypes=FILE_DIALOG_TYPES,
        )
    finally:
        root.destroy()

    if not selected:
        fail("No images were selected")

    return [Path(path) for path in selected]


def select_output_path() -> Path:
    """Open a save dialog so the user can choose the output PDF path."""
    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        selected = filedialog.asksaveasfilename(
            title="Save PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
    finally:
        root.destroy()

    if not selected:
        fail("No output file was selected")

    return Path(selected)


def validate_image_files(paths: list[Path]) -> list[Path]:
    """Validate image files for format and readability."""
    valid_paths: list[Path] = []

    for path in paths:
        if not path.is_file():
            fail(f"Not a file: {path}")
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            supported = ", ".join(sorted(SUPPORTED_FORMATS))
            fail(f"Unsupported format: {path.suffix} (expected: {supported})")
        if not os.access(path, os.R_OK):
            fail(f"File is not readable: {path}")

        valid_paths.append(path)

    return valid_paths


def validate_output_path(output_path: Path) -> Path:
    """Validate that the output path can be written as a PDF."""
    resolved = output_path.expanduser()

    if resolved.suffix.lower() != ".pdf":
        fail(f"Output file must use the .pdf extension: {resolved}")
    if resolved.exists() and resolved.is_dir():
        fail(f"Output path is a directory: {resolved}")

    parent = resolved.parent
    if not parent.exists():
        fail(f"Output directory does not exist: {parent}")
    if not os.access(parent, os.W_OK):
        fail(f"Output directory is not writable: {parent}")

    return resolved


def prepare_image_for_pdf(path: Path) -> Image.Image:
    """Open an image and convert it to an RGB image suitable for PDF output."""
    with Image.open(path) as img:
        normalized = ImageOps.exif_transpose(img)

        # PDF output requires RGB, so transparency is flattened onto white.
        if "A" in normalized.getbands():
            background = Image.new("RGB", normalized.size, (255, 255, 255))
            background.paste(normalized, mask=normalized.getchannel("A"))
            return background

        if normalized.mode != "RGB":
            return normalized.convert("RGB")

        return normalized.copy()


def convert_images_to_pdf(
    image_paths: list[Path], output_path: Path, quality: int, verbose: bool
) -> None:
    """Convert multiple images to a single PDF file."""
    images: list[Image.Image] = []

    try:
        for path in image_paths:
            if verbose:
                print(f"Reading: {path}")
            images.append(prepare_image_for_pdf(path))

        first_image, remaining_images = images[0], images[1:]
        save_kwargs = {"quality": quality}
        if remaining_images:
            save_kwargs["save_all"] = True
            save_kwargs["append_images"] = remaining_images

        first_image.save(output_path, "PDF", **save_kwargs)

        if verbose:
            print(f"Created PDF with {len(images)} page(s): {output_path}")
        else:
            print(f"Created: {output_path}")
    except PermissionError as exc:
        fail(f"Permission denied: {exc}")
    except OSError as exc:
        fail(f"Failed to read or write file: {exc}")
    finally:
        for image in images:
            image.close()


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    return argparse.ArgumentParser(
        description="Convert multiple images (PNG/JPEG) to a single PDF file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 img2pdf.py --select-files
  python3 img2pdf.py img1.png img2.jpg -o output.pdf
  python3 img2pdf.py *.png -o report.pdf
  python3 img2pdf.py ./screenshots -o report.pdf
  python3 img2pdf.py ./pages --recursive -o book.pdf
  python3 img2pdf.py photo*.jpg -o album.pdf --verbose
        """,
    )


def main() -> None:
    """Main entry point for the CLI tool."""
    parser = build_parser()
    parser.add_argument(
        "images",
        nargs="*",
        type=Path,
        help="Input image files or directories (PNG, JPEG)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output PDF file path"
    )
    parser.add_argument(
        "--select-files",
        action="store_true",
        help="Choose input images and output PDF using file dialogs",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively collect images when a directory is provided",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=95,
        choices=range(1, 101),
        metavar="1-100",
        help="JPEG quality for embedded images (default: 95)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()
    if args.select_files or not args.images:
        if args.images:
            fail("Do not combine image arguments with --select-files")
        candidate_paths = select_image_files()
        output_source = args.output if args.output else select_output_path()
    else:
        candidate_paths = collect_image_files(args.images, args.recursive)
        output_source = args.output

    if output_source is None:
        fail("Output PDF path is required. Use -o/--output or --select-files.")

    valid_paths = validate_image_files(candidate_paths)
    output_path = validate_output_path(output_source)
    convert_images_to_pdf(valid_paths, output_path, args.quality, args.verbose)


if __name__ == "__main__":
    main()
