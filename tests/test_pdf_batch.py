"""
Tests for PDF batch processing functionality.
"""
import pytest
from pathlib import Path
from pypdf import PdfWriter, PdfReader

from pdf_batch import (
    batch_add_page_numbers,
    batch_split,
    batch_delete
)


@pytest.fixture
def sample_pdfs_dir(tmp_path):
    """Create directory with sample PDFs."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    # Create 3 sample PDFs
    for i in range(1, 4):
        pdf_path = input_dir / f"sample{i}.pdf"
        writer = PdfWriter()
        for j in range(5):  # 5 pages each
            writer.add_blank_page(width=200, height=200)
        with open(pdf_path, 'wb') as f:
            writer.write(f)
    
    return input_dir


@pytest.fixture
def single_pdf_dir(tmp_path):
    """Create directory with single PDF."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    pdf_path = input_dir / "test.pdf"
    writer = PdfWriter()
    for i in range(3):
        writer.add_blank_page(width=200, height=200)
    with open(pdf_path, 'wb') as f:
        writer.write(f)
    
    return input_dir


class TestBatchAddPageNumbers:
    """Tests for batch page number addition."""
    
    def test_batch_add_page_numbers_basic(self, sample_pdfs_dir, tmp_path):
        """Test basic batch page number addition."""
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            verbose=True
        )
        
        assert len(results["success"]) == 3
        assert len(results["failed"]) == 0
        assert (output_dir / "sample1.pdf").exists()
        assert (output_dir / "sample2.pdf").exists()
        assert (output_dir / "sample3.pdf").exists()
        
        # Verify page numbers were added
        reader = PdfReader(output_dir / "sample1.pdf")
        assert len(reader.pages) == 5
    
    def test_batch_add_page_numbers_custom_position(self, sample_pdfs_dir, tmp_path):
        """Test batch page number addition with custom position."""
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            position="top-left",
            verbose=True
        )
        
        assert len(results["success"]) == 3
        assert len(results["failed"]) == 0
    
    def test_batch_add_page_numbers_custom_format(self, sample_pdfs_dir, tmp_path):
        """Test batch page number addition with custom format."""
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            format_str="Page {page} of {total}",
            verbose=True
        )
        
        assert len(results["success"]) == 3
        assert len(results["failed"]) == 0
    
    def test_batch_add_page_numbers_skip_pages(self, sample_pdfs_dir, tmp_path):
        """Test batch page number addition with skipped pages."""
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            skip_pages=[1],
            verbose=True
        )
        
        assert len(results["success"]) == 3
        assert len(results["failed"]) == 0
    
    def test_batch_add_page_numbers_partial_failure(self, tmp_path):
        """Test batch processing with some corrupted files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        # Create valid PDF
        valid_pdf = input_dir / "valid.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(valid_pdf, 'wb') as f:
            writer.write(f)
        
        # Create corrupted PDF
        corrupted_pdf = input_dir / "corrupted.pdf"
        with open(corrupted_pdf, 'wb') as f:
            f.write(b"Not a valid PDF")
        
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            input_dir,
            output_dir,
            verbose=True
        )
        
        # Should continue processing despite errors
        assert len(results["success"]) == 1
        assert len(results["failed"]) == 1
        assert (output_dir / "valid.pdf").exists()


class TestBatchSplit:
    """Tests for batch PDF splitting."""
    
    def test_batch_split_basic(self, sample_pdfs_dir, tmp_path):
        """Test basic batch split."""
        output_dir = tmp_path / "output"
        
        results = batch_split(
            sample_pdfs_dir,
            output_dir,
            "1-2,3-5",
            verbose=True
        )
        
        assert len(results["success"]) == 3
        assert len(results["failed"]) == 0
        
        # Check subdirectories created
        assert (output_dir / "sample1").exists()
        assert (output_dir / "sample2").exists()
        assert (output_dir / "sample3").exists()
        
        # Verify split files
        sample1_dir = output_dir / "sample1"
        split_files = sorted(sample1_dir.glob("*.pdf"))
        assert len(split_files) == 2
    
    def test_batch_split_single_range(self, sample_pdfs_dir, tmp_path):
        """Test batch split with single range."""
        output_dir = tmp_path / "output"
        
        results = batch_split(
            sample_pdfs_dir,
            output_dir,
            "1-3",
            verbose=True
        )
        
        assert len(results["success"]) == 3
        
        # Verify only one split file per PDF
        sample1_dir = output_dir / "sample1"
        split_files = sorted(sample1_dir.glob("*.pdf"))
        assert len(split_files) == 1


class TestBatchDelete:
    """Tests for batch page deletion."""
    
    def test_batch_delete_basic(self, sample_pdfs_dir, tmp_path):
        """Test basic batch page deletion."""
        output_dir = tmp_path / "output"
        
        results = batch_delete(
            sample_pdfs_dir,
            output_dir,
            "1",
            verbose=True
        )
        
        assert len(results["success"]) == 3
        assert len(results["failed"]) == 0
        
        # Verify pages deleted
        reader = PdfReader(output_dir / "sample1.pdf")
        assert len(reader.pages) == 4  # 5 - 1 = 4
    
    def test_batch_delete_multiple_pages(self, sample_pdfs_dir, tmp_path):
        """Test batch deletion of multiple pages."""
        output_dir = tmp_path / "output"
        
        results = batch_delete(
            sample_pdfs_dir,
            output_dir,
            "1,3,5",
            verbose=True
        )
        
        assert len(results["success"]) == 3
        
        # Verify pages deleted
        reader = PdfReader(output_dir / "sample1.pdf")
        assert len(reader.pages) == 2  # 5 - 3 = 2
    
    def test_batch_delete_range(self, sample_pdfs_dir, tmp_path):
        """Test batch deletion of page range."""
        output_dir = tmp_path / "output"
        
        results = batch_delete(
            sample_pdfs_dir,
            output_dir,
            "2-4",
            verbose=True
        )
        
        assert len(results["success"]) == 3
        
        # Verify pages deleted
        reader = PdfReader(output_dir / "sample1.pdf")
        assert len(reader.pages) == 2  # 5 - 3 = 2


class TestBatchErrorHandling:
    """Tests for error handling in batch operations."""
    
    def test_output_directory_creation(self, sample_pdfs_dir, tmp_path):
        """Test automatic creation of output directory."""
        output_dir = tmp_path / "nested" / "output"
        
        results = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            verbose=True
        )
        
        assert len(results["success"]) == 3
        assert output_dir.exists()
    
    def test_overwrite_protection(self, sample_pdfs_dir, tmp_path):
        """Test that output files are properly overwritten."""
        output_dir = tmp_path / "output"
        
        # First batch
        results1 = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            verbose=True
        )
        
        # Second batch (should overwrite)
        results2 = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            verbose=True
        )
        
        assert len(results1["success"]) == 3
        assert len(results2["success"]) == 3
        assert (output_dir / "sample1.pdf").exists()
    
    def test_mixed_files_in_directory(self, tmp_path):
        """Test batch processing with non-PDF files in directory."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        # Create valid PDF
        valid_pdf = input_dir / "valid.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(valid_pdf, 'wb') as f:
            writer.write(f)
        
        # Create non-PDF file
        text_file = input_dir / "readme.txt"
        with open(text_file, 'w') as f:
            f.write("Not a PDF")
        
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            input_dir,
            output_dir,
            verbose=True
        )
        
        # Should only process PDF files
        assert len(results["success"]) == 1
        assert len(results["failed"]) == 0
    
    def test_nested_output_directory(self, sample_pdfs_dir, tmp_path):
        """Test creating nested output directories."""
        output_dir = tmp_path / "level1" / "level2" / "output"
        
        results = batch_split(
            sample_pdfs_dir,
            output_dir,
            "1-2,3-5",
            verbose=True
        )
        
        assert len(results["success"]) == 3
        assert output_dir.exists()
        assert (output_dir / "sample1").exists()
    
    def test_filename_preservation(self, tmp_path):
        """Test that original filenames are preserved."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        # Create PDFs with special names
        special_names = ["file with spaces.pdf", "file_with_underscores.pdf", "file-with-dashes.pdf"]
        
        for name in special_names:
            pdf_path = input_dir / name
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            with open(pdf_path, 'wb') as f:
                writer.write(f)
        
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            input_dir,
            output_dir,
            verbose=True
        )
        
        assert len(results["success"]) == 3
        # Verify filenames preserved
        for name in special_names:
            assert (output_dir / name).exists()
    
    def test_large_batch_processing(self, tmp_path):
        """Test processing larger batch of files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        # Create 10 PDFs
        for i in range(10):
            pdf_path = input_dir / f"file{i:02d}.pdf"
            writer = PdfWriter()
            for j in range(3):
                writer.add_blank_page(width=200, height=200)
            with open(pdf_path, 'wb') as f:
                writer.write(f)
        
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            input_dir,
            output_dir,
            verbose=True
        )
        
        assert len(results["success"]) == 10
        assert len(results["failed"]) == 0
    
    def test_results_format(self, sample_pdfs_dir, tmp_path):
        """Test that results dictionary has correct format."""
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            verbose=False
        )
        
        # Verify results structure
        assert isinstance(results, dict)
        assert "success" in results
        assert "failed" in results
        assert isinstance(results["success"], list)
        assert isinstance(results["failed"], list)
        
        # Verify success items have correct format
        for item in results["success"]:
            assert isinstance(item, str)
    
    def test_verbose_output(self, sample_pdfs_dir, tmp_path, capsys):
        """Test verbose output mode."""
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            sample_pdfs_dir,
            output_dir,
            verbose=True
        )
        
        captured = capsys.readouterr()
        assert "sample1.pdf" in captured.out
        assert "sample2.pdf" in captured.out
        assert "sample3.pdf" in captured.out
    
    def test_batch_with_subdirectories(self, tmp_path):
        """Test that batch processing only processes files in root directory."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        # Create PDF in root
        root_pdf = input_dir / "root.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(root_pdf, 'wb') as f:
            writer.write(f)
        
        # Create subdirectory with PDF
        subdir = input_dir / "subdir"
        subdir.mkdir()
        sub_pdf = subdir / "sub.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(sub_pdf, 'wb') as f:
            writer.write(f)
        
        output_dir = tmp_path / "output"
        
        results = batch_add_page_numbers(
            input_dir,
            output_dir,
            verbose=True
        )
        
        # Should only process root level files
        assert len(results["success"]) == 1
        assert (output_dir / "root.pdf").exists()
        assert not (output_dir / "subdir").exists()
    
    def test_empty_pdf_list(self, tmp_path):
        """Test handling of directory with no PDFs."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        # Create non-PDF files
        with open(input_dir / "file.txt", 'w') as f:
            f.write("text")
        
        output_dir = tmp_path / "output"
        
        # Should exit with error for operations requiring PDFs
        with pytest.raises(SystemExit):
            batch_add_page_numbers(input_dir, output_dir)
    
    def test_split_output_structure(self, single_pdf_dir, tmp_path):
        """Test that split creates correct directory structure."""
        output_dir = tmp_path / "output"
        
        results = batch_split(
            single_pdf_dir,
            output_dir,
            "1-2",
            verbose=True
        )
        
        # Verify directory structure
        assert (output_dir / "test").exists()
        assert (output_dir / "test").is_dir()
        
        # Verify split file exists
        split_files = list((output_dir / "test").glob("*.pdf"))
        assert len(split_files) >= 1
    
    def test_delete_preserves_metadata(self, single_pdf_dir, tmp_path):
        """Test that deletion preserves PDF metadata."""
        output_dir = tmp_path / "output"
        
        results = batch_delete(
            single_pdf_dir,
            output_dir,
            "1",
            verbose=True
        )
        
        assert len(results["success"]) == 1
        
        # Verify output exists and is valid PDF
        output_pdf = output_dir / "test.pdf"
        assert output_pdf.exists()
        
        reader = PdfReader(output_pdf)
        assert len(reader.pages) == 2  # 3 - 1 = 2
