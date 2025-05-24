from click.testing import CliRunner
from project2md.cli import cli
import json
import yaml
from pathlib import Path
import pytest

def test_process_json_format(tmp_path):
    """Test CLI with JSON output format."""
    # Create a test file to process
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    # Create a minimal config to avoid validation issues
    config_file = tmp_path / ".project2md.yml"
    config_file.write_text("""
general:
  max_depth: 10
  stats_in_output: false
include:
  files:
    - "**/*.txt"
exclude:
  files: []
  dirs: []
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--config', str(config_file),
        '--format', 'json',
        '--output', str(tmp_path / 'output.json'),
        '--force'  # Add force flag to process non-git directory
    ])
    
    if result.exit_code != 0:
        print(f"Error output: {result.output}")  # Debug output
        print(f"Exception: {result.exception}")  # Debug exception
        if result.exception:
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    
    # Verify output file exists and is valid JSON
    output_file = tmp_path / 'output.json'
    assert output_file.exists()
    with open(output_file) as f:
        data = json.load(f)
        assert "metadata" in data
        assert "project" in data
        # Check for run info in metadata
        assert "version" in data["metadata"]
        assert "signatures_mode" in data["metadata"]
        assert "output_format" in data["metadata"]

def test_process_yaml_format(tmp_path):
    """Test CLI with YAML output format."""
    # Create a test file to process
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    # Create a minimal config to avoid validation issues
    config_file = tmp_path / ".project2md.yml"
    config_file.write_text("""
general:
  max_depth: 10
  stats_in_output: false
include:
  files:
    - "**/*.txt"
exclude:
  files: []
  dirs: []
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--config', str(config_file),
        '--format', 'yaml',
        '--output', str(tmp_path / 'output.yaml'),
        '--force'  # Add force flag to process non-git directory
    ])
    
    if result.exit_code != 0:
        print(f"Error output: {result.output}")  # Debug output
        print(f"Exception: {result.exception}")  # Debug exception
        if result.exception:
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    
    # Verify output file exists and is valid YAML
    output_file = tmp_path / 'output.yaml'
    assert output_file.exists()
    with open(output_file) as f:
        data = yaml.safe_load(f)
        assert "metadata" in data
        assert "project" in data
        # Check for run info in metadata
        assert "version" in data["metadata"]
        assert "signatures_mode" in data["metadata"]
        assert "output_format" in data["metadata"]

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
    
    # Create a minimal config
    config_file = tmp_path / ".project2md.yml"
    config_file.write_text("""
general:
  max_depth: 10
  stats_in_output: false
include:
  files:
    - "**/*.txt"
exclude:
  files: []
  dirs: []
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--config', str(config_file),
        '--format', 'json',
        '--output', str(tmp_path / 'output.json')
    ])
    
    if result.exit_code != 0:
        print(f"Error output: {result.output}")  # Debug output
        print(f"Exception: {result.exception}")  # Debug exception
        if result.exception:
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    assert (tmp_path / 'output.json').exists()

def test_explicit_command(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["explicit", "--directory", str(tmp_path)])
    assert result.exit_code == 0
    config_file = tmp_path / "explicit.config.project2md.yml"
    assert config_file.exists()

def test_explicit_command_with_files(tmp_path):
    # Create sample files
    (tmp_path / "include_me.py").write_text("print('test')")
    (tmp_path / ".gitignore").write_text("exclude_me.bin")

    runner = CliRunner()
    result = runner.invoke(cli, ["explicit", "--directory", str(tmp_path)])
    assert result.exit_code == 0

    config_file = tmp_path / "explicit.config.project2md.yml"
    assert config_file.exists(), "Expected config file not found."

    with config_file.open() as f:
        data = yaml.safe_load(f)

    # Check high-level keys
    assert "tree" in data, "Expected 'tree' field missing in output."
    assert "files" in data, "Expected 'files' list missing in output."
    assert any("include_me.py" in x["path"] for x in data["files"]), \
        "Expected 'include_me.py' not listed in output."

    # Check that includes/excludes are reflected
    bin_file_entry = next((x for x in data["files"] if "exclude_me.bin" in x["path"]), None)
    if bin_file_entry:
        # If the bin file was present, ensure it's excluded
        assert bin_file_entry["include"] is False, "Binary file should be excluded."

def test_signatures_flag(tmp_path):
    """Test CLI with signatures flag."""
    # Create a test Python file
    test_file = tmp_path / "test.py"
    test_file.write_text("""def test_function():
    print("Hello World")
    return True

class TestClass:
    def method(self):
        pass
""")
    
    # Create a minimal config
    config_file = tmp_path / ".project2md.yml"
    config_file.write_text("""
general:
  max_depth: 10
  stats_in_output: false
include:
  files:
    - "**/*.py"
exclude:
  files: []
  dirs: []
""")
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--config', str(config_file),
        '--signatures',
        '--output', str(tmp_path / 'output.md'),
        '--force'
    ])
    
    if result.exit_code != 0:
        print(f"Error output: {result.output}")  # Debug output
        print(f"Exception: {result.exception}")  # Debug exception
        if result.exception:
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    assert result.exit_code == 0
    
    # Verify signatures mode indicator in output
    output_file = tmp_path / 'output.md'
    assert output_file.exists()
    content = output_file.read_text()
    assert "Signatures Mode" in content
    assert "[lines:" in content  # Should contain line counts
