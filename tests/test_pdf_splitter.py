#!/usr/bin/env python3
"""
Tests for pdf_splitter.py
"""

import pytest
from pathlib import Path
from pypdf import PdfWriter

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_splitter import parse_page_ranges, get_num_pages, split_pdf_by_ranges


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF with 10 pages for testing."""
    pdf_path = tmp_path / "sample.pdf"

    writer = PdfWriter()
    for i in range(10):
        writer.add_blank_page(width=200, height=200)

    with open(pdf_path, 'wb') as f:
        writer.write(f)

    return pdf_path


class TestParsePageRanges:
    """Tests for parse_page_ranges function."""

    def test_simple_range(self):
        """Test parsing simple range like '1-3'."""
        result = parse_page_ranges("1-3", 10)
        assert result == [(1, 3)]

    def test_multiple_ranges(self):
        """Test parsing multiple ranges."""
        result = parse_page_ranges("1-3,4-7,8-10", 10)
        assert result == [(1, 3), (4, 7), (8, 10)]

    def test_colon_separator(self):
        """Test parsing with colon separator."""
        result = parse_page_ranges("1:3 4:7", 10)
        assert result == [(1, 3), (4, 7)]

    def test_single_page(self):
        """Test parsing single page."""
        result = parse_page_ranges("5", 10)
        assert result == [(5, 5)]

    def test_mixed_single_and_range(self):
        """Test parsing mixed single pages and ranges."""
        result = parse_page_ranges("1-3,5,7-9", 10)
        assert result == [(1, 3), (5, 5), (7, 9)]

    def test_unsorted_ranges(self):
        """Test that ranges are sorted by start page."""
        result = parse_page_ranges("7-9,1-3,4-6", 10)
        assert result == [(1, 3), (4, 6), (7, 9)]

    def test_invalid_range_start_greater_than_end(self):
        """Test that start > end raises error."""
        with pytest.raises(SystemExit):
            parse_page_ranges("5-2", 10)

    def test_invalid_page_zero(self):
        """Test that page 0 raises error."""
        with pytest.raises(SystemExit):
            parse_page_ranges("0-5", 10)

    def test_invalid_page_negative(self):
        """Test that negative page raises error."""
        with pytest.raises(SystemExit):
            parse_page_ranges("-1-5", 10)

    def test_invalid_page_exceeds_total(self):
        """Test that page > total raises error."""
        with pytest.raises(SystemExit):
            parse_page_ranges("1-15", 10)

    def test_empty_ranges(self):
        """Test that empty ranges raise error."""
        with pytest.raises(SystemExit):
            parse_page_ranges("", 10)

    def test_invalid_format(self):
        """Test that invalid format raises error."""
        with pytest.raises(SystemExit):
            parse_page_ranges("abc", 10)


class TestGetNumPages:
    """Tests for get_num_pages function."""

    def test_get_num_pages(self, sample_pdf):
        """Test getting number of pages from PDF."""
        num_pages = get_num_pages(sample_pdf)
        assert num_pages == 10

    def test_get_num_pages_nonexistent_file(self, tmp_path):
        """Test error when file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.pdf"
        with pytest.raises(SystemExit):
            get_num_pages(nonexistent)


class TestSplitPdfByRanges:
    """Tests for split_pdf_by_ranges function."""

    def test_split_single_range(self, sample_pdf, tmp_path):
        """Test splitting PDF into single range."""
        output_dir = tmp_path / "output"
        ranges = [(1, 3)]

        created_files = split_pdf_by_ranges(sample_pdf, output_dir, ranges)

        assert len(created_files) == 1
        assert created_files[0].exists()
        assert get_num_pages(created_files[0]) == 3

    def test_split_multiple_ranges(self, sample_pdf, tmp_path):
        """Test splitting PDF into multiple ranges."""
        output_dir = tmp_path / "output"
        ranges = [(1, 3), (4, 7), (8, 10)]

        created_files = split_pdf_by_ranges(sample_pdf, output_dir, ranges)

        assert len(created_files) == 3
        assert get_num_pages(created_files[0]) == 3
        assert get_num_pages(created_files[1]) == 4
        assert get_num_pages(created_files[2]) == 3

    def test_split_single_page(self, sample_pdf, tmp_path):
        """Test splitting single page."""
        output_dir = tmp_path / "output"
        ranges = [(5, 5)]

        created_files = split_pdf_by_ranges(sample_pdf, output_dir, ranges)

        assert len(created_files) == 1
        assert get_num_pages(created_files[0]) == 1
        assert created_files[0].name == "sample_p5.pdf"

    def test_output_directory_created(self, sample_pdf, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "new_output_dir"
        ranges = [(1, 3)]

        assert not output_dir.exists()
        split_pdf_by_ranges(sample_pdf, output_dir, ranges)
        assert output_dir.exists()

    def test_output_filenames(self, sample_pdf, tmp_path):
        """Test that output filenames follow correct pattern."""
        output_dir = tmp_path / "output"
        ranges = [(1, 3), (5, 5)]

        created_files = split_pdf_by_ranges(sample_pdf, output_dir, ranges)

        assert created_files[0].name == "sample_p1-3.pdf"
        assert created_files[1].name == "sample_p5.pdf"

    def test_nonexistent_input_file(self, tmp_path):
        """Test error when input file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.pdf"
        output_dir = tmp_path / "output"
        ranges = [(1, 3)]

        with pytest.raises(SystemExit):
            split_pdf_by_ranges(nonexistent, output_dir, ranges)

    def test_non_pdf_input(self, tmp_path):
        """Test error when input is not a PDF."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")
        output_dir = tmp_path / "output"
        ranges = [(1, 3)]

        with pytest.raises(SystemExit):
            split_pdf_by_ranges(txt_file, output_dir, ranges)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
