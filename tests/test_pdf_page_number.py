"""Tests for PDF page number insertion functionality."""

import pytest
from pathlib import Path
from pypdf import PdfReader, PdfWriter


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


@pytest.fixture
def sample_pdf_1page(tmp_path):
    """Create a sample PDF with 1 page."""
    pdf_path = tmp_path / "sample_1page.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with open(pdf_path, 'wb') as f:
        writer.write(f)
    return pdf_path


class TestAddPageNumbers:
    """Test suite for add_page_numbers function."""

    def test_basic_page_numbers(self, sample_pdf_5pages, tmp_path):
        """Test adding basic page numbers with default settings."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output)
        
        assert output.exists()
        reader = PdfReader(output)
        assert len(reader.pages) == 5

    def test_position_bottom_center(self, sample_pdf_5pages, tmp_path):
        """Test bottom-center position."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, position="bottom-center")
        
        assert output.exists()
        reader = PdfReader(output)
        assert len(reader.pages) == 5

    def test_position_bottom_left(self, sample_pdf_5pages, tmp_path):
        """Test bottom-left position."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, position="bottom-left")
        
        assert output.exists()

    def test_position_bottom_right(self, sample_pdf_5pages, tmp_path):
        """Test bottom-right position."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, position="bottom-right")
        
        assert output.exists()

    def test_position_top_center(self, sample_pdf_5pages, tmp_path):
        """Test top-center position."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, position="top-center")
        
        assert output.exists()

    def test_position_top_left(self, sample_pdf_5pages, tmp_path):
        """Test top-left position."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, position="top-left")
        
        assert output.exists()

    def test_position_top_right(self, sample_pdf_5pages, tmp_path):
        """Test top-right position."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, position="top-right")
        
        assert output.exists()

    def test_format_simple_page(self, sample_pdf_5pages, tmp_path):
        """Test simple page number format."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, format_str="{page}")
        
        assert output.exists()

    def test_format_with_text(self, sample_pdf_5pages, tmp_path):
        """Test format with text prefix."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, format_str="Page {page}")
        
        assert output.exists()

    def test_format_page_total(self, sample_pdf_5pages, tmp_path):
        """Test format with page/total."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, format_str="{page}/{total}")
        
        assert output.exists()

    def test_format_custom_decorators(self, sample_pdf_5pages, tmp_path):
        """Test custom format with decorators."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, format_str="- {page} -")
        
        assert output.exists()

    def test_skip_single_page(self, sample_pdf_5pages, tmp_path):
        """Test skipping first page."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, skip_pages=[1])
        
        assert output.exists()
        reader = PdfReader(output)
        assert len(reader.pages) == 5

    def test_skip_multiple_pages(self, sample_pdf_5pages, tmp_path):
        """Test skipping multiple pages."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, skip_pages=[1, 2, 5])
        
        assert output.exists()

    def test_skip_middle_pages(self, sample_pdf_5pages, tmp_path):
        """Test skipping middle pages."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, skip_pages=[2, 3, 4])
        
        assert output.exists()

    def test_start_number_zero(self, sample_pdf_5pages, tmp_path):
        """Test starting from page 0."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, start_number=0)
        
        assert output.exists()

    def test_start_number_five(self, sample_pdf_5pages, tmp_path):
        """Test starting from page 5."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, start_number=5)
        
        assert output.exists()

    def test_start_number_ten(self, sample_pdf_5pages, tmp_path):
        """Test starting from page 10."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, start_number=10)
        
        assert output.exists()

    def test_font_size_small(self, sample_pdf_5pages, tmp_path):
        """Test small font size."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, font_size=8)
        
        assert output.exists()

    def test_font_size_medium(self, sample_pdf_5pages, tmp_path):
        """Test medium font size."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, font_size=12)
        
        assert output.exists()

    def test_font_size_large(self, sample_pdf_5pages, tmp_path):
        """Test large font size."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output, font_size=18)
        
        assert output.exists()

    def test_single_page_pdf(self, sample_pdf_1page, tmp_path):
        """Test with single page PDF."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(sample_pdf_1page, output)
        
        assert output.exists()
        reader = PdfReader(output)
        assert len(reader.pages) == 1

    def test_combined_options(self, sample_pdf_5pages, tmp_path):
        """Test multiple options combined."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(
            sample_pdf_5pages,
            output,
            position="top-right",
            format_str="Page {page}/{total}",
            skip_pages=[1],
            start_number=0,
            font_size=14
        )
        
        assert output.exists()

    def test_invalid_position_error(self, sample_pdf_5pages, tmp_path):
        """Test error with invalid position."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        with pytest.raises(SystemExit):
            add_page_numbers(sample_pdf_5pages, output, position="invalid-position")

    def test_nonexistent_file_error(self, tmp_path):
        """Test error with nonexistent file."""
        from pdf_page_number import add_page_numbers
        
        nonexistent = tmp_path / "nonexistent.pdf"
        output = tmp_path / "output.pdf"
        with pytest.raises(SystemExit):
            add_page_numbers(nonexistent, output)

    def test_invalid_skip_pages_negative(self, sample_pdf_5pages, tmp_path):
        """Test error with negative skip page number."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        with pytest.raises(SystemExit):
            add_page_numbers(sample_pdf_5pages, output, skip_pages=[-1])

    def test_invalid_skip_pages_out_of_range(self, sample_pdf_5pages, tmp_path):
        """Test error with skip page number out of range."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        with pytest.raises(SystemExit):
            add_page_numbers(sample_pdf_5pages, output, skip_pages=[10])

    def test_output_directory_created(self, sample_pdf_5pages, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "subdir" / "output.pdf"
        add_page_numbers(sample_pdf_5pages, output)
        
        assert output.exists()
        assert output.parent.exists()

    def test_overwrite_existing_file(self, sample_pdf_5pages, tmp_path):
        """Test overwriting existing output file."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        
        # Create initial file
        add_page_numbers(sample_pdf_5pages, output)
        assert output.exists()
        
        # Overwrite
        add_page_numbers(sample_pdf_5pages, output, format_str="Page {page}")
        assert output.exists()

    def test_path_objects(self, sample_pdf_5pages, tmp_path):
        """Test that Path objects are handled correctly."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(Path(sample_pdf_5pages), Path(output))
        
        assert output.exists()

    def test_string_paths(self, sample_pdf_5pages, tmp_path):
        """Test that string paths are handled correctly."""
        from pdf_page_number import add_page_numbers
        
        output = tmp_path / "output.pdf"
        add_page_numbers(str(sample_pdf_5pages), str(output))
        
        assert output.exists()
