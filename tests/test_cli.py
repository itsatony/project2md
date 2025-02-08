from click.testing import CliRunner
from project2md.cli import cli
import json
import yaml
from pathlib import Path

def test_process_json_format(tmp_path):
    """Test CLI with JSON output format."""
    # Create a test file to process
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--format', 'json',
        '--output', str(tmp_path / 'output.json'),
        '--force'  # Add force flag to process non-git directory
    ])
    
    if result.exit_code != 0:
        print(f"Error output: {result.output}")  # Debug output
    
    assert result.exit_code == 0
    
    # Verify output file exists and is valid JSON
    output_file = tmp_path / 'output.json'
    assert output_file.exists()
    with open(output_file) as f:
        data = json.load(f)
        assert "metadata" in data
        assert "project" in data
        # Verify the test file was processed
        assert any(f["path"] == "test.txt" for f in data.get("files", []))

def test_process_yaml_format(tmp_path):
    """Test CLI with YAML output format."""
    # Create a test file to process
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--format', 'yaml',
        '--output', str(tmp_path / 'output.yaml'),
        '--force'  # Add force flag to process non-git directory
    ])
    
    if result.exit_code != 0:
        print(f"Error output: {result.output}")  # Debug output
    
    assert result.exit_code == 0
    
    # Verify output file exists and is valid YAML
    output_file = tmp_path / 'output.yaml'
    assert output_file.exists()
    with open(output_file) as f:
        data = yaml.safe_load(f)
        assert "metadata" in data
        assert "project" in data
        # Verify the test file was processed
        assert any(f["path"] == "test.txt" for f in data.get("files", []))

def test_invalid_format(tmp_path):
    """Test CLI with invalid format option."""
    runner = CliRunner()
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--format', 'invalid'
    ])
    
    assert result.exit_code != 0
    assert "Invalid value for '--format'" in result.output

def test_process_git_repo(tmp_path):
    """Test CLI with an actual Git repository."""
    from git import Repo
    
    # Initialize a test git repository
    repo = Repo.init(tmp_path)
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    # Add and commit the file
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit")
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--format', 'json',
        '--output', str(tmp_path / 'output.json')
    ])
    
    assert result.exit_code == 0
    assert (tmp_path / 'output.json').exists()
