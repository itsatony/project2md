# tests/test_stats.py
import pytest
from pathlib import Path
from reposcribe.stats import StatsCollector

@pytest.fixture
def stats_collector():
    return StatsCollector()

@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing."""
    files = []
    
    # Python file
    py_file = tmp_path / "main.py"
    py_file.write_text("print('Hello')")
    files.append((py_file, py_file.read_text()))
    
    # JavaScript file
    js_file = tmp_path / "script.js"
    js_file.write_text("console.log('Hello');")
    files.append((js_file, js_file.read_text()))
    
    # Binary file
    bin_file = tmp_path / "data.bin"
    bin_file.write_bytes(b'\x00\x01\x02\x03')
    files.append((bin_file, None))
    
    # Markdown file
    md_file = tmp_path / "README.md"
    md_file.write_text("# Hello")
    files.append((md_file, md_file.read_text()))
    
    return files

def test_basic_stats(stats_collector, sample_files):
    for file_path, content in sample_files:
        stats_collector.process_file(file_path, content)
    
    stats = stats_collector.get_stats("main")
    
    assert stats["total_files"] == 4
    assert stats["text_files"] == 3
    assert stats["binary_files"] == 1
    assert stats["branch"] == "main"
    assert isinstance(stats["repo_size"], str)

def test_file_types(stats_collector, sample_files):
    for file_path, content in sample_files:
        stats_collector.process_file(file_path, content)
    
    stats = stats_collector.get_stats()
    file_types = stats["file_types"]
    
    assert file_types[".py"] == 1
    assert file_types[".js"] == 1
    assert file_types[".md"] == 1
    assert file_types[".bin"] == 1

def test_language_detection(stats_collector, tmp_path):
    # Create files with different languages
    files = [
        (tmp_path / "script.py", "def hello(): pass"),
        (tmp_path / "style.css", ".class { color: red; }"),
        (tmp_path / "data.json", '{"key": "value"}'),
        (tmp_path / "config.yml", "key: value")
    ]
    
    for path, content in files:
        path.write_text(content)
        stats_collector.process_file(path, content)
    
    stats = stats_collector.get_stats()
    languages = stats["languages"]
    
    assert "Python" in languages
    assert "CSS" in languages
    assert "JSON" in languages
    assert "YAML" in languages

def test_largest_files(stats_collector, tmp_path):
    # Create files of different sizes
    files = [
        (tmp_path / "small.txt", "x" * 100),
        (tmp_path / "medium.txt", "x" * 1000),
        (tmp_path / "large.txt", "x" * 10000),
    ]
    
    for path, content in files:
        path.write_text(content)
        stats_collector.process_file(path, content)
    
    stats = stats_collector.get_stats()
    largest = stats["largest_files"]
    
    # The largest file should be first
    assert str(tmp_path / "large.txt") in largest

def test_percentages(stats_collector, sample_files):
    for file_path, content in sample_files:
        stats_collector.process_file(file_path, content)
    
    stats = stats_collector.get_stats()
    
    assert "text_files_percentage" in stats
    assert "binary_files_percentage" in stats
    assert "file_types_percentage" in stats
    
    # Verify percentages add up to 100%
    assert abs(stats["text_files_percentage"] + stats["binary_files_percentage"] - 100) < 0.1

def test_duplicate_processing(stats_collector, sample_files):
    # Process files twice
    for _ in range(2):
        for file_path, content in sample_files:
            stats_collector.process_file(file_path, content)
    
    stats = stats_collector.get_stats()
    
    # Numbers should not be doubled
    assert stats["total_files"] == 4

def test_merge_collectors(stats_collector, tmp_path):
    # Create two collectors with different files
    collector2 = StatsCollector()
    
    # Files for first collector
    file1 = tmp_path / "file1.py"
    file1.write_text("print('hello')")
    stats_collector.process_file(file1, file1.read_text())
    
    # Files for second collector
    file2 = tmp_path / "file2.js"
    file2.write_text("console.log('hello')")
    collector2.process_file(file2, file2.read_text())
    
    # Merge collectors
    stats_collector.merge(collector2)
    stats = stats_collector.get_stats()
    
    assert stats["total_files"] == 2
    assert stats["text_files"] == 2
    assert stats["file_types"][".py"] == 1
    assert stats["file_types"][".js"] == 1