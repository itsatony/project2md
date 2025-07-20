"""Tests for improved signature processor functionality."""
import pytest
from pathlib import Path
from project2md.signature_processor import SignatureProcessor


class TestSignatureProcessorImprovements:
    """Test improvements to signature processor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SignatureProcessor()

    def test_yaml_files_show_line_count_only(self):
        """Test that YAML files show only line count in signatures mode."""
        yaml_content = """version: 1.0
name: test-project
dependencies:
  - requests
  - click
config:
  debug: true
  port: 8080"""
        
        result = self.processor.process_file(Path("config.yml"), yaml_content)
        assert result == "[lines:8]"

    def test_json_files_show_line_count_only(self):
        """Test that JSON files show only line count in signatures mode."""
        json_content = """{
  "name": "test-project",
  "version": "1.0.0",
  "dependencies": {
    "requests": "^2.25.0",
    "click": "^8.0.0"
  }
}"""
        
        result = self.processor.process_file(Path("package.json"), json_content)
        assert result == "[lines:8]"

    def test_toml_files_show_line_count_only(self):
        """Test that TOML files show only line count in signatures mode."""
        toml_content = """[project]
name = "test-project"
version = "1.0.0"

[tool.poetry]
name = "test-project"
version = "1.0.0"

[build-system]
requires = ["poetry-core"]"""
        
        result = self.processor.process_file(Path("pyproject.toml"), toml_content)
        assert result == "[lines:10]"

    def test_txt_files_show_line_count_only(self):
        """Test that text files show only line count in signatures mode."""
        txt_content = """This is a text file
with multiple lines
of content
for testing purposes"""
        
        result = self.processor.process_file(Path("notes.txt"), txt_content)
        assert result == "[lines:4]"

    def test_empty_code_file_shows_empty(self):
        """Test that empty code files show 'empty' instead of empty code block."""
        empty_content = ""
        
        result = self.processor.process_file(Path("empty.py"), empty_content)
        assert result == ""

    def test_code_file_with_only_whitespace_shows_empty(self):
        """Test that code files with only whitespace/comments show 'empty'."""
        whitespace_content = """   
# Just a comment
    
"""
        
        result = self.processor.process_file(Path("whitespace.py"), whitespace_content)
        assert result == "empty"

    def test_code_file_with_only_imports_shows_empty(self):
        """Test that code files with only imports show 'empty'."""
        imports_only_content = """import sys
import os
from pathlib import Path
"""
        
        result = self.processor.process_file(Path("imports_only.py"), imports_only_content)
        assert result == "empty"

    def test_code_file_with_functions_shows_signatures(self):
        """Test that code files with actual functions show signatures."""
        code_content = """import sys

def hello_world():
    print("Hello, World!")
    return True

class MyClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
"""
        
        result = self.processor.process_file(Path("code.py"), code_content)
        assert "def hello_world():" in result
        assert "class MyClass:" in result
        assert "[lines:" in result

    def test_unknown_file_type_returns_original_content(self):
        """Test that unknown file types return original content."""
        unknown_content = """This is some unknown file content
with multiple lines"""
        
        result = self.processor.process_file(Path("unknown.xyz"), unknown_content)
        assert result == unknown_content

    def test_markdown_files_still_process_headers(self):
        """Test that markdown files still process headers correctly."""
        md_content = """# Main Title
Some content here

## Section 1
More content

### Subsection
Even more content

## Section 2
Final content"""
        
        result = self.processor.process_file(Path("test.md"), md_content)
        assert "# Main Title [lines:2]" in result
        assert "## Section 1 [lines:2]" in result
        assert "### Subsection [lines:2]" in result
        assert "## Section 2 [lines:1]" in result

    def test_all_config_extensions_supported(self):
        """Test that all config file extensions show line count only."""
        extensions_and_content = [
            (".yml", "key: value\nother: data"),
            (".yaml", "key: value\nother: data"),
            (".json", '{"key": "value"}'),
            (".toml", "[section]\nkey = 'value'"),
            (".ini", "[section]\nkey=value"),
            (".cfg", "[section]\nkey=value"),
            (".conf", "key=value\nother=data"),
            (".config", "key=value"),
            (".txt", "plain text\ncontent"),
            (".log", "log entry 1\nlog entry 2"),
            (".csv", "col1,col2\nval1,val2"),
            (".xml", "<root><item>value</item></root>"),
            (".properties", "key=value\nother=data"),
        ]
        
        for ext, content in extensions_and_content:
            file_path = Path(f"test{ext}")
            result = self.processor.process_file(file_path, content)
            expected_lines = len(content.split('\n'))
            assert result == f"[lines:{expected_lines}]", f"Failed for {ext}"

    def test_empty_line_count_only_file(self):
        """Test empty files that should show line count only."""
        result = self.processor.process_file(Path("empty.yml"), "")
        assert result == ""  # Empty files return as-is

    def test_single_line_config_file(self):
        """Test single-line config files."""
        single_line_content = "key=value"
        result = self.processor.process_file(Path("config.ini"), single_line_content)
        assert result == "[lines:1]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
