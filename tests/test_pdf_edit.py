#!/usr/bin/env python3
"""
Tests for pdf_edit.py
"""

import pytest
from pathlib import Path
from pypdf import PdfReader, PdfWriter

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_edit import parse_page_spec, delete_pages, reorder_pages, insert_pages


@pytest.fixture
def sample_pdf_10pages(tmp_path):
    """Create a sample PDF with 10 pages."""
    pdf_path = tmp_path / "sample_10pages.pdf"
    writer = PdfWriter()
    for i in range(10):
        writer.add_blank_page(width=200, height=200)
    with open(pdf_path, 'wb') as f:
        writer.write(f)
    return pdf_path


@pytest.fixture
def sample_pdf_5pages(tmp_path):
    """Create a sample PDF with 5 pages."""
    pdf_path = tmp_path / "sample_5pages.pdf"
    writer = PdfWriter()
    for i in range(5):
        writer.add_blank_page(width=200, height=200)
    with open(pdf_path, 'wb') as f:
        writer.write(f)
    return pdf_path


class TestParsePageSpec:
    """Tests for parse_page_spec function."""

    def test_single_page(self):
        """Test parsing single page."""
        result = parse_page_spec("5", 10)
        assert result == [5]

    def test_multiple_pages(self):
        """Test parsing multiple pages."""
        result = parse_page_spec("1,3,5", 10)
        assert result == [1, 3, 5]

    def test_range(self):
        """Test parsing range."""
        result = parse_page_spec("1-5", 10)
        assert result == [1, 2, 3, 4, 5]

    def test_mixed(self):
        """Test parsing mixed specification."""
        result = parse_page_spec("1,3-5,7", 10)
        assert result == [1, 3, 4, 5, 7]

    def test_invalid_page_zero(self):
        """Test error when page is 0."""
        with pytest.raises(SystemExit):
            parse_page_spec("0", 10)

    def test_invalid_page_exceeds_total(self):
        """Test error when page exceeds total."""
        with pytest.raises(SystemExit):
            parse_page_spec("15", 10)


class TestDeletePages:
    """Tests for delete_pages function."""

    def test_delete_single_page(self, sample_pdf_10pages, tmp_path):
        """Test deleting a single page."""
        output = tmp_path / "output.pdf"
        delete_pages(sample_pdf_10pages, output, "5")

        reader = PdfReader(output)
        assert len(reader.pages) == 9

    def test_delete_multiple_pages(self, sample_pdf_10pages, tmp_path):
        """Test deleting multiple pages."""
        output = tmp_path / "output.pdf"
        delete_pages(sample_pdf_10pages, output, "1,5,10")

        reader = PdfReader(output)
        assert len(reader.pages) == 7

    def test_delete_range(self, sample_pdf_10pages, tmp_path):
        """Test deleting a range of pages."""
        output = tmp_path / "output.pdf"
        delete_pages(sample_pdf_10pages, output, "3-7")

        reader = PdfReader(output)
        assert len(reader.pages) == 5

    def test_delete_first_page(self, sample_pdf_10pages, tmp_path):
        """Test deleting the first page."""
        output = tmp_path / "output.pdf"
        delete_pages(sample_pdf_10pages, output, "1")

        reader = PdfReader(output)
        assert len(reader.pages) == 9

    def test_delete_last_page(self, sample_pdf_10pages, tmp_path):
        """Test deleting the last page."""
        output = tmp_path / "output.pdf"
        delete_pages(sample_pdf_10pages, output, "10")

        reader = PdfReader(output)
        assert len(reader.pages) == 9

    def test_delete_all_pages_error(self, sample_pdf_10pages, tmp_path):
        """Test error when attempting to delete all pages."""
        output = tmp_path / "output.pdf"
        with pytest.raises(SystemExit):
            delete_pages(sample_pdf_10pages, output, "1-10")


class TestReorderPages:
    """Tests for reorder_pages function."""

    def test_reorder_basic(self, sample_pdf_10pages, tmp_path):
        """Test basic page reordering."""
        output = tmp_path / "output.pdf"
        reorder_pages(sample_pdf_10pages, output, "1,3,2,4-10")

        reader = PdfReader(output)
        assert len(reader.pages) == 10

    def test_reorder_reverse(self, sample_pdf_10pages, tmp_path):
        """Test reversing page order."""
        output = tmp_path / "output.pdf"
        reorder_pages(sample_pdf_10pages, output, "10,9,8,7,6,5,4,3,2,1")

        reader = PdfReader(output)
        assert len(reader.pages) == 10

    def test_reorder_with_range(self, sample_pdf_10pages, tmp_path):
        """Test reordering with range notation."""
        output = tmp_path / "output.pdf"
        reorder_pages(sample_pdf_10pages, output, "6-10,1-5")

        reader = PdfReader(output)
        assert len(reader.pages) == 10

    def test_reorder_with_duplicates(self, sample_pdf_10pages, tmp_path):
        """Test reordering allows duplicate page numbers."""
        output = tmp_path / "output.pdf"
        reorder_pages(sample_pdf_10pages, output, "1,2,2,3")

        reader = PdfReader(output)
        assert len(reader.pages) == 4

    def test_reorder_partial_pages(self, sample_pdf_10pages, tmp_path):
        """Test reordering allows partial page selection."""
        output = tmp_path / "output.pdf"
        reorder_pages(sample_pdf_10pages, output, "1-5")

        reader = PdfReader(output)
        assert len(reader.pages) == 5


class TestInsertPages:
    """Tests for insert_pages function."""

    def test_insert_at_beginning(self, sample_pdf_10pages, sample_pdf_5pages, tmp_path):
        """Test inserting pages at the beginning."""
        output = tmp_path / "output.pdf"
        insert_spec = f"{sample_pdf_5pages}:1-5@1"
        insert_pages(sample_pdf_10pages, output, insert_spec)

        reader = PdfReader(output)
        assert len(reader.pages) == 15

    def test_insert_in_middle(self, sample_pdf_10pages, sample_pdf_5pages, tmp_path):
        """Test inserting pages in the middle."""
        output = tmp_path / "output.pdf"
        insert_spec = f"{sample_pdf_5pages}:1-5@5"
        insert_pages(sample_pdf_10pages, output, insert_spec)

        reader = PdfReader(output)
        assert len(reader.pages) == 15

    def test_insert_at_end(self, sample_pdf_10pages, sample_pdf_5pages, tmp_path):
        """Test inserting pages at the end."""
        output = tmp_path / "output.pdf"
        insert_spec = f"{sample_pdf_5pages}:1-5@10"
        insert_pages(sample_pdf_10pages, output, insert_spec)

        reader = PdfReader(output)
        assert len(reader.pages) == 15

    def test_insert_partial_range(self, sample_pdf_10pages, sample_pdf_5pages, tmp_path):
        """Test inserting a partial range of pages."""
        output = tmp_path / "output.pdf"
        insert_spec = f"{sample_pdf_5pages}:2-4@5"
        insert_pages(sample_pdf_10pages, output, insert_spec)

        reader = PdfReader(output)
        assert len(reader.pages) == 13

    def test_insert_single_page(self, sample_pdf_10pages, sample_pdf_5pages, tmp_path):
        """Test inserting a single page."""
        output = tmp_path / "output.pdf"
        insert_spec = f"{sample_pdf_5pages}:3@5"
        insert_pages(sample_pdf_10pages, output, insert_spec)

        reader = PdfReader(output)
        assert len(reader.pages) == 11

    def test_insert_nonexistent_file_error(self, sample_pdf_10pages, tmp_path):
        """Test error when source file doesn't exist."""
        output = tmp_path / "output.pdf"
        nonexistent = tmp_path / "nonexistent.pdf"
        insert_spec = f"{nonexistent}:1-5@5"
        with pytest.raises(SystemExit):
            insert_pages(sample_pdf_10pages, output, insert_spec)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
