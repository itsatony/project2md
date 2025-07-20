"""
Tests for the signature processor module.
"""
import pytest
from pathlib import Path
from project2md.signature_processor import SignatureProcessor


class TestSignatureProcessor:
    """Test cases for SignatureProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SignatureProcessor()
    
    def test_process_file_unsupported_extension(self):
        """Test processing files with unsupported extensions."""
        content = "Some random content\nWith multiple lines"
        # .xyz extension is not in line_count_only_extensions, so should return original content
        result = self.processor.process_file(Path("test.xyz"), content)
        assert result == content
    
    def test_process_file_txt_extension(self):
        """Test processing .txt files which should show line count only."""
        content = "Some random content\nWith multiple lines"
        result = self.processor.process_file(Path("test.txt"), content)
        assert result == "[lines:2]"
    
    def test_process_file_empty_content(self):
        """Test processing files with empty content."""
        result = self.processor.process_file(Path("test.py"), "")
        assert result == ""
    
    # Markdown tests
    def test_process_markdown_simple_headers(self, sample_markdown):
        """Test markdown processing with simple headers."""
        result = self.processor.process_file(Path("test.md"), sample_markdown)
        lines = result.split('\n')
        
        # Should extract headers with line counts
        assert any("# Main Title" in line and "[lines:" in line for line in lines)
        assert any("## Section 1" in line and "[lines:" in line for line in lines)
        assert any("### Subsection 1.1" in line and "[lines:" in line for line in lines)
        assert any("## Section 2" in line and "[lines:" in line for line in lines)
    
    def test_process_markdown_no_headers(self):
        """Test markdown processing with no headers."""
        content = "Just some content\nWith no headers"
        result = self.processor.process_file(Path("test.md"), content)
        assert result == ""
    
    # Python tests
    def test_process_python_simple_function(self, sample_python_file):
        """Test Python function signature extraction."""
        result = self.processor.process_file(Path("test.py"), sample_python_file)
        lines = result.split('\n')
        
        # Should find function signatures with line counts
        assert any("def add_numbers(a, b):" in line and "[lines:" in line for line in lines)
        assert any("class Calculator:" in line and "[lines:" in line for line in lines)
        assert any("def multiply(self, x, y):" in line and "[lines:" in line for line in lines)
        assert any("async def async_calculate" in line and "[lines:" in line for line in lines)
    
    # JavaScript tests  
    def test_process_javascript_functions(self, sample_javascript):
        """Test JavaScript function signature extraction."""
        result = self.processor.process_file(Path("test.js"), sample_javascript)
        lines = result.split('\n')
        
        # Should find function signatures
        assert any("function regularFunction(a, b)" in line and "[lines:" in line for line in lines)
        assert any("const arrowFunction = (x) =>" in line and "[lines:" in line for line in lines)
        assert any("async function asyncFunction()" in line and "[lines:" in line for line in lines)
    
    # Helper method tests
    def test_count_lines_by_braces(self):
        """Test brace-based line counting."""
        lines = [
            "function test() {",
            "    let x = 1;", 
            "    return x;",
            "}"
        ]
        
        count = self.processor._count_lines_by_braces(lines, 0)
        assert count == 4
    
    def test_count_lines_by_indent(self):
        """Test indentation-based line counting.""" 
        lines = [
            "def test():",
            "    x = 1",
            "    return x",
            "",
            "def next_function():"
        ]
        
        count = self.processor._count_lines_by_indent(lines, 0, 0)
        assert count == 4


class TestSignatureProcessorIntegration:
    """Integration tests for signature processor with different file types."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SignatureProcessor()
    
    def test_process_multiple_languages(self):
        """Test processing multiple programming languages."""
        test_cases = [
            (Path("test.py"), "def test(): pass", "def test(): pass [lines:1]"),
            (Path("test.js"), "function test() { return; }", "function test() { return; } [lines:1]"),
        ]
        
        for file_path, content, expected_content in test_cases:
            result = self.processor.process_file(file_path, content)
            assert expected_content in result


# Mark tests appropriately
pytestmark = pytest.mark.unit
