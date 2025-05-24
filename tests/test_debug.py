"""Debug test to identify the exact issue."""
import pytest
from click.testing import CliRunner
from project2md.cli import cli
from pathlib import Path


def test_debug_version_command():
    """Test just the version command to see if basic CLI works."""
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    
    print(f"Version command exit code: {result.exit_code}")
    print(f"Version output: {result.output}")
    if result.exception:
        print(f"Version exception: {result.exception}")
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    # This will pass if version command works
    assert result.exit_code == 0


def test_debug_minimal_process(tmp_path):
    """Minimal test to debug the process command issue."""
    # Create a simple test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")
    
    # Create minimal config
    config_file = tmp_path / ".project2md.yml"
    config_file.write_text("""
general:
  max_depth: 5
  stats_in_output: false
include:
  files:
    - "**/*.txt"
exclude:
  files: []
  dirs: []
""")
    
    runner = CliRunner()
    
    # Try the process command with minimal arguments
    result = runner.invoke(cli, [
        'process',
        '--root-dir', str(tmp_path),
        '--config', str(config_file),
        '--output', str(tmp_path / 'output.md'),
        '--force'
    ])
    
    print(f"Process command exit code: {result.exit_code}")
    print(f"Process output: {result.output}")
    if result.exception:
        print(f"Process exception: {result.exception}")
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    # Don't assert - just print debug info
    print("Debug test completed - check output above for errors")
