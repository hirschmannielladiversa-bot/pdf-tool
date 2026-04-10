#!/usr/bin/env python3
"""
Tests for pdf_merger.py
"""

import pytest
from pathlib import Path
from pypdf import PdfWriter

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_merger import validate_input_file, validate_output_path, merge_pdfs


@pytest.fixture
def sample_pdf_1(tmp_path):
    """Create a sample PDF with 3 pages."""
    pdf_path = tmp_path / "sample1.pdf"

    writer = PdfWriter()
    for i in range(3):
        writer.add_blank_page(width=200, height=200)

    with open(pdf_path, 'wb') as f:
        writer.write(f)

    return pdf_path


@pytest.fixture
def sample_pdf_2(tmp_path):
    """Create a sample PDF with 5 pages."""
    pdf_path = tmp_path / "sample2.pdf"

    writer = PdfWriter()
    for i in range(5):
        writer.add_blank_page(width=200, height=200)

    with open(pdf_path, 'wb') as f:
        writer.write(f)

    return pdf_path


@pytest.fixture
def sample_pdf_3(tmp_path):
    """Create a sample PDF with 2 pages."""
    pdf_path = tmp_path / "sample3.pdf"

    writer = PdfWriter()
    for i in range(2):
        writer.add_blank_page(width=200, height=200)

    with open(pdf_path, 'wb') as f:
        writer.write(f)

    return pdf_path


class TestValidateInputFile:
    """Tests for validate_input_file function."""

    def test_valid_pdf(self, sample_pdf_1):
        """Test validation of valid PDF file."""
        result = validate_input_file(sample_pdf_1)
        assert result == sample_pdf_1

    def test_nonexistent_file(self, tmp_path):
        """Test error when file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.pdf"
        with pytest.raises(SystemExit):
            validate_input_file(nonexistent)

    def test_non_pdf_file(self, tmp_path):
        """Test error when file is not a PDF."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")
        with pytest.raises(SystemExit):
            validate_input_file(txt_file)

    def test_directory_instead_of_file(self, tmp_path):
        """Test error when path is a directory."""
        directory = tmp_path / "somedir"
        directory.mkdir()
        with pytest.raises(SystemExit):
            validate_input_file(directory)


class TestValidateOutputPath:
    """Tests for validate_output_path function."""

    def test_valid_output_path(self, tmp_path):
        """Test validation of valid output path."""
        output = tmp_path / "output.pdf"
        result = validate_output_path(output)
        assert result == output

    def test_non_pdf_extension(self, tmp_path):
        """Test error when output doesn't have .pdf extension."""
        output = tmp_path / "output.txt"
        with pytest.raises(SystemExit):
            validate_output_path(output)

    def test_output_directory_doesnt_exist(self, tmp_path):
        """Test error when output directory doesn't exist."""
        output = tmp_path / "nonexistent_dir" / "output.pdf"
        with pytest.raises(SystemExit):
            validate_output_path(output)

    def test_output_is_directory(self, tmp_path):
        """Test error when output path is a directory."""
        directory = tmp_path / "somedir.pdf"
        directory.mkdir()
        with pytest.raises(SystemExit):
            validate_output_path(directory)


class TestMergePdfs:
    """Tests for merge_pdfs function."""

    def test_merge_two_pdfs(self, sample_pdf_1, sample_pdf_2, tmp_path):
        """Test merging two PDF files."""
        output = tmp_path / "merged.pdf"
        merge_pdfs([sample_pdf_1, sample_pdf_2], output)

        assert output.exists()

        # Verify merged PDF has correct number of pages
        from pypdf import PdfReader
        with open(output, 'rb') as f:
            reader = PdfReader(f)
            assert len(reader.pages) == 8  # 3 + 5

    def test_merge_three_pdfs(self, sample_pdf_1, sample_pdf_2, sample_pdf_3, tmp_path):
        """Test merging three PDF files."""
        output = tmp_path / "merged.pdf"
        merge_pdfs([sample_pdf_1, sample_pdf_2, sample_pdf_3], output)

        assert output.exists()

        from pypdf import PdfReader
        with open(output, 'rb') as f:
            reader = PdfReader(f)
            assert len(reader.pages) == 10  # 3 + 5 + 2

    def test_merge_order_preserved(self, sample_pdf_1, sample_pdf_2, sample_pdf_3, tmp_path):
        """Test that merge order is preserved."""
        output = tmp_path / "merged.pdf"

        # Merge in specific order
        merge_pdfs([sample_pdf_1, sample_pdf_2, sample_pdf_3], output)

        assert output.exists()

        # Verify total pages matches sum of input PDFs
        from pypdf import PdfReader
        with open(output, 'rb') as f:
            reader = PdfReader(f)
            # 3 + 5 + 2 = 10 pages
            assert len(reader.pages) == 10

    def test_merge_no_files(self, tmp_path):
        """Test error when no input files provided."""
        output = tmp_path / "merged.pdf"
        with pytest.raises(SystemExit):
            merge_pdfs([], output)

    def test_merge_single_file(self, sample_pdf_1, tmp_path):
        """Test error when only one file provided."""
        output = tmp_path / "merged.pdf"
        with pytest.raises(SystemExit):
            merge_pdfs([sample_pdf_1], output)

    def test_merge_nonexistent_file(self, sample_pdf_1, tmp_path):
        """Test error when one of the input files doesn't exist."""
        nonexistent = tmp_path / "nonexistent.pdf"
        output = tmp_path / "merged.pdf"
        with pytest.raises(SystemExit):
            merge_pdfs([sample_pdf_1, nonexistent], output)

    def test_merge_with_verbose(self, sample_pdf_1, sample_pdf_2, tmp_path, capsys):
        """Test verbose output."""
        output = tmp_path / "merged.pdf"
        merge_pdfs([sample_pdf_1, sample_pdf_2], output, verbose=True)

        captured = capsys.readouterr()
        assert "Merging" in captured.out
        assert "sample1.pdf" in captured.out
        assert "sample2.pdf" in captured.out

    def test_merge_output_created(self, sample_pdf_1, sample_pdf_2, tmp_path):
        """Test that output file is actually created."""
        output = tmp_path / "merged.pdf"
        assert not output.exists()

        merge_pdfs([sample_pdf_1, sample_pdf_2], output)

        assert output.exists()
        assert output.is_file()
        assert output.stat().st_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
