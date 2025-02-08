# tests/test_formatter.py
import pytest
from pathlib import Path
from project2md.formatter import MarkdownFormatter, FormatterError
from project2md.config import Config, OutputFormat
import json

@pytest.fixture
def config():
    config = Config()
    config.output.stats = True
    return config

@pytest.fixture
def formatter(config):
    return MarkdownFormatter(config)

@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing."""
    root = tmp_path / "repo"
    root.mkdir()
    
    # Create README
    readme = root / "README.md"
    readme.write_text("# Test Project\nThis is a test.")
    
    # Create source file
    src_dir = root / "src"
    src_dir.mkdir()
    main_py = src_dir / "main.py"
    main_py.write_text("print('Hello')")
    
    return [
        (readme, readme.read_text()),
        (main_py, main_py.read_text())
    ]

@pytest.fixture
def sample_stats():
    return {
        "total_files": 5,
        "text_files": 4,
        "binary_files": 1,
        "repo_size": "1.2MB",
        "branch": "main",
        "file_types": {
            ".py": 2,
            ".md": 1,
            ".txt": 1
        }
    }

def test_generate_markdown(formatter, sample_files, sample_stats, tmp_path):
    output = tmp_path / "output.md"
    formatter.generate_output(tmp_path / "repo", sample_files, sample_stats, output)
    
    content = output.read_text()
    
    # Check main sections
    assert "# Project Overview" in content
    assert "## README.md Content" in content
    assert "## Project Structure" in content
    assert "## Project Statistics" in content
    assert "## File Contents" in content
    
    # Check specific content
    assert "# Test Project" in content  # README content
    assert "print('Hello')" in content  # Python file content
    assert "Total Files: 5" in content  # Stats
    assert "```tree" in content  # Tree structure

def test_generate_json(formatter, sample_files, sample_stats, tmp_path):
    formatter.config.output.format = OutputFormat.JSON
    output = tmp_path / "output.json"
    
    formatter.generate_output(tmp_path / "repo", sample_files, sample_stats, output)
    
    with open(output) as f:
        data = json.load(f)
    
    assert "project_overview" in data
    assert "statistics" in data
    assert "files" in data
    assert data["statistics"]["total_files"] == 5

def test_tree_generation(formatter, sample_files, tmp_path):
    tree = formatter._generate_tree(tmp_path / "repo", sample_files)
    
    # Check tree structure
    assert "└── repo" in tree
    assert "├── README.md" in tree or "└── README.md" in tree
    assert "src" in tree
    assert "main.py" in tree

def test_language_detection(formatter):
    assert formatter._get_language_tag(Path("test.py")) == "python"
    assert formatter._get_language_tag(Path("test.js")) == "javascript"
    assert formatter._get_language_tag(Path("test.unknown")) == ""

def test_stats_formatting(formatter, sample_stats):
    stats_md = formatter._format_stats(sample_stats)
    
    assert "Total Files: 5" in stats_md
    assert "Text Files: 4" in stats_md
    assert "Binary Files: 1" in stats_md
    assert "Current Branch: main" in stats_md
    assert ".py: 2" in stats_md

def test_error_handling(formatter, sample_files, sample_stats, tmp_path):
    invalid_path = Path('/nonexistent/directory/output.md')
    
    with pytest.raises(FormatterError, match="Failed to generate output"):
        formatter.generate_output(tmp_path, sample_files, sample_stats, invalid_path)

def test_readme_handling(formatter, sample_files, tmp_path):
    readme_content = formatter._find_readme_content(sample_files)
    assert readme_content is not None
    assert "# Test Project" in readme_content

def test_empty_repo(formatter, tmp_path):
    output = tmp_path / "output.md"
    formatter.generate_output(
        tmp_path,
        [],
        {"total_files": 0, "text_files": 0, "binary_files": 0, "repo_size": "0B", "branch": "main", "file_types": {}},
        output
    )
    
    content = output.read_text()
    assert "# Project Overview" in content
    assert "No files found" not in content  # Should handle empty repo gracefully