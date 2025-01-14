# tests/test_walker.py
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from rich.progress import Progress

from reposcribe.walker import FileSystemWalker, WalkerError
from reposcribe.config import Config, PathPatterns

@pytest.fixture
def mock_progress():
    return Mock(spec=Progress)
    
@pytest.fixture
def basic_config():
    config = Config()
    config.include = PathPatterns(
        files=["*.py", "*.md"],
        dirs=["src/", "docs/"]
    )
    config.exclude = PathPatterns(
        files=["*.pyc", "test_*"],
        dirs=["__pycache__/", "tests/"]
    )
    return config

@pytest.fixture
def walker(basic_config, mock_progress):
    mock_progress.task_ids = [1]  # Mock task IDs
    return FileSystemWalker(basic_config, mock_progress)

@pytest.fixture
def sample_repo(tmp_path):
    """Create a sample repository structure."""
    # Create directories
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "__pycache__").mkdir()
    
    # Create files
    (tmp_path / "README.md").write_text("# Test Project")
    (tmp_path / "src/main.py").write_text("print('Hello')")
    (tmp_path / "src/test.pyc").write_bytes(b'\x00\x00\x00')
    (tmp_path / "docs/index.md").write_text("Documentation")
    (tmp_path / "tests/test_main.py").write_text("def test_main(): pass")
    
    return tmp_path

def test_collect_files_basic(walker, sample_repo):
    files = walker.collect_files(sample_repo)
    
    # Should include README.md, src/main.py, docs/index.md
    # Should exclude test_main.py, test.pyc
    assert len(files) == 3
    assert sample_repo / "README.md" in files
    assert sample_repo / "src/main.py" in files
    assert sample_repo / "docs/index.md" in files

def test_collect_files_max_depth(walker, sample_repo):
    walker.config.general.max_depth = 0
    files = walker.collect_files(sample_repo)
    
    # Should only include files in root directory
    assert len(files) == 1
    assert sample_repo / "README.md" in files

def test_collect_files_with_gitignore(walker, sample_repo):
    # Create .gitignore file
    (sample_repo / ".gitignore").write_text("*.pyc\n__pycache__/\n")
    
    files = walker.collect_files(sample_repo)
    assert not any(f.suffix == '.pyc' for f in files)

def test_read_file_text(walker, tmp_path):
    test_file = tmp_path / "test.txt"
    content = "Hello, World!"
    test_file.write_text(content)
    
    assert walker.read_file(test_file) == content

def test_read_file_binary(walker, tmp_path):
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b'\x00\x01\x02\x03')
    
    assert walker.read_file(test_file) is None

def test_read_file_size_limit(walker, tmp_path):
    test_file = tmp_path / "large.txt"
    walker.config.general.max_file_size_bytes = 10
    test_file.write_text("This is a large file that exceeds the limit")
    
    assert walker.read_file(test_file) is None

def test_read_file_encoding_detection(walker, tmp_path):
    test_file = tmp_path / "utf8.txt"
    content = "Hello, 世界!"
    test_file.write_text(content, encoding='utf-8')
    
    assert walker.read_file(test_file) == content

def test_is_binary_detection():
    walker = FileSystemWalker(Config(), Mock())
    
    # Test binary detection
    assert walker._is_binary(b'\x00\x01\x02\x03')
    assert walker._is_binary(b'\xff\xd8\xff')  # JPEG signature
    assert walker._is_binary(b'%PDF')  # PDF signature
    
    # Test text detection
    assert not walker._is_binary(b'Hello, World!')
    assert not walker._is_binary(b'{"key": "value"}')
    assert not walker._is_binary(b'# Python code')

def test_error_handling(walker, tmp_path):
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(WalkerError):
        walker.collect_files(non_existent)

@patch('pathlib.Path.iterdir')
def test_permission_error_handling(mock_iterdir, walker, tmp_path):
    mock_iterdir.side_effect = PermissionError()
    
    # Should not raise an error, just log warning and continue
    files = walker.collect_files(tmp_path)
    assert len(files) == 0