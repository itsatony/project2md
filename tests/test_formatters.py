import pytest
from pathlib import Path
import json
import yaml
from project2md.formatters.base import BaseFormatter, FormatterError
from project2md.formatters.json_formatter import JSONFormatter
from project2md.formatters.yaml_formatter import YAMLFormatter
from project2md.config import Config

@pytest.fixture
def config():
    return Config()

@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing."""
    root = tmp_path / "repo"
    root.mkdir()
    
    # Create test files
    readme = root / "README.md"
    readme.write_text("# Test Project\nThis is a test.")
    
    src = root / "src"
    src.mkdir()
    
    # File with JSON content
    json_file = src / "config.json"
    json_file.write_text('{"key": "value"}')
    
    # File with YAML content
    yaml_file = src / "config.yaml"
    yaml_file.write_text('key: value\nlist:\n  - item1\n  - item2')
    
    return [
        (readme, readme.read_text()),
        (json_file, json_file.read_text()),
        (yaml_file, yaml_file.read_text())
    ]

@pytest.fixture
def sample_stats():
    return {
        "total_files": 3,
        "text_files": 3,
        "binary_files": 0,
        "repo_size": "1.2KB",
        "branch": "main",
        "file_types": {
            ".md": 1,
            ".json": 1,
            ".yaml": 1
        }
    }

class TestJSONFormatter:
    def test_json_output_structure(self, config, sample_files, sample_stats, tmp_path):
        formatter = JSONFormatter(config)
        output_file = tmp_path / "output.json"
        
        formatter.generate_output(tmp_path / "repo", sample_files, sample_stats, output_file)
        
        with open(output_file) as f:
            data = json.load(f)
        
        # Check structure
        assert "metadata" in data
        assert "project" in data
        assert "files" in data
        assert isinstance(data["files"], list)
        
        # Check metadata
        assert "generated_at" in data["metadata"]
        assert data["metadata"]["generator"] == "project2md"
        
        # Check project data
        assert data["project"]["readme"] == "# Test Project\nThis is a test."
        assert data["project"]["statistics"] == sample_stats
        
        # Check file entries
        file_paths = [f["path"] for f in data["files"]]
        assert "README.md" in file_paths
        assert "src/config.json" in file_paths
        assert "src/config.yaml" in file_paths

    def test_json_special_content_handling(self, config, tmp_path):
        """Test handling of files containing JSON content."""
        files = [(
            tmp_path / "test.json",
            '{"nested": {"json": true, "array": [1,2,3]}}'
        )]
        
        formatter = JSONFormatter(config)
        output_file = tmp_path / "output.json"
        
        formatter.generate_output(tmp_path, files, {}, output_file)
        
        # Verify output can be parsed as valid JSON
        with open(output_file) as f:
            data = json.load(f)
            
        # Check the nested JSON content is properly escaped
        file_content = next(f["content"] for f in data["files"] if f["path"] == "test.json")
        assert json.loads(file_content) == {"nested": {"json": True, "array": [1,2,3]}}

class TestYAMLFormatter:
    def test_yaml_output_structure(self, config, sample_files, sample_stats, tmp_path):
        formatter = YAMLFormatter(config)
        output_file = tmp_path / "output.yaml"
        
        formatter.generate_output(tmp_path / "repo", sample_files, sample_stats, output_file)
        
        with open(output_file) as f:
            data = yaml.safe_load(f)
        
        # Check structure
        assert "metadata" in data
        assert "project" in data
        assert "files" in data
        assert isinstance(data["files"], list)
        
        # Check metadata
        assert "generated_at" in data["metadata"]
        assert data["metadata"]["generator"] == "project2md"
        
        # Check project data
        assert data["project"]["readme"] == "# Test Project\nThis is a test."
        assert data["project"]["statistics"] == sample_stats
        
        # Check file entries
        file_paths = [f["path"] for f in data["files"]]
        assert "README.md" in file_paths
        assert "src/config.json" in file_paths
        assert "src/config.yaml" in file_paths

    def test_yaml_special_content_handling(self, config, tmp_path):
        """Test handling of files containing YAML content."""
        files = [(
            tmp_path / "test.yaml",
            'nested:\n  key: value\n  list:\n    - item1\n    - item2'
        )]
        
        formatter = YAMLFormatter(config)
        output_file = tmp_path / "output.yaml"
        
        formatter.generate_output(tmp_path, files, {}, output_file)
        
        # Verify output can be parsed as valid YAML
        with open(output_file) as f:
            data = yaml.safe_load(f)
            
        # Check the nested YAML content is properly handled
        file_content = next(f["content"] for f in data["files"] if f["path"] == "test.yaml")
        assert yaml.safe_load(file_content) == {
            "nested": {
                "key": "value",
                "list": ["item1", "item2"]
            }
        }

def test_formatter_error_handling():
    """Test error handling in formatters."""
    config = Config()
    
    # Test JSON formatter
    json_formatter = JSONFormatter(config)
    with pytest.raises(FormatterError):
        json_formatter.generate_output(
            Path("/nonexistent"),
            [],
            {},
            Path("/nonexistent/output.json")
        )
    
    # Test YAML formatter
    yaml_formatter = YAMLFormatter(config)
    with pytest.raises(FormatterError):
        yaml_formatter.generate_output(
            Path("/nonexistent"),
            [],
            {},
            Path("/nonexistent/output.yaml")
        )
