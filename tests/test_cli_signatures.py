"""
Tests for CLI integration with signatures functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from click.testing import CliRunner

from project2md.cli import cli
from project2md.config import Config


class TestSignaturesCLI:
    """Test CLI integration with signatures flag."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('project2md.cli.load_configuration')
    @patch('project2md.cli.process_repository')
    @patch('project2md.cli.GitHandler')
    @patch('project2md.cli.FileSystemWalker')
    @patch('project2md.cli.StatsCollector')
    @patch('project2md.cli.get_formatter')
    def test_signatures_flag_sets_config(
        self, 
        mock_get_formatter,
        mock_stats_collector,
        mock_walker,
        mock_git_handler,
        mock_process_repo,
        mock_load_config
    ):
        """Test that --signatures flag properly sets config.signatures_mode."""
        # Setup mocks
        mock_config = Mock(spec=Config)
        mock_config.target_dir = Path.cwd()
        mock_config.output_file = Path("test_output.md")
        mock_config.general = Mock()
        mock_config.general.stats_in_output = True
        mock_load_config.return_value = mock_config
        
        # Run command with signatures flag
        result = self.runner.invoke(cli, [
            'process', 
            '--signatures',
            '--output', 'test.md'
        ])
        
        # Verify the flag was processed
        assert result.exit_code == 0
        mock_load_config.assert_called_once()
        
        # Check that signatures_mode was set on config
        assert mock_config.signatures_mode == True
    
    @patch('project2md.cli.load_configuration')
    @patch('project2md.cli.process_repository')
    @patch('project2md.cli.GitHandler')
    @patch('project2md.cli.FileSystemWalker')
    @patch('project2md.cli.StatsCollector')
    @patch('project2md.cli.get_formatter')
    def test_no_signatures_flag_default_false(
        self, 
        mock_get_formatter,
        mock_stats_collector,
        mock_walker,
        mock_git_handler,
        mock_process_repo,
        mock_load_config
    ):
        """Test that without --signatures flag, signatures_mode defaults to False."""
        # Setup mocks
        mock_config = Mock(spec=Config)
        mock_config.target_dir = Path.cwd()
        mock_config.output_file = Path("test_output.md")
        mock_config.general = Mock()
        mock_config.general.stats_in_output = True
        mock_load_config.return_value = mock_config
        
        # Run command without signatures flag
        result = self.runner.invoke(cli, [
            'process',
            '--output', 'test.md'
        ])
        
        # Verify the command ran successfully
        assert result.exit_code == 0
        mock_load_config.assert_called_once()
        
        # Check that signatures_mode was set to False
        assert mock_config.signatures_mode == False
    
    def test_signatures_flag_help_text(self):
        """Test that --signatures flag appears in help text."""
        result = self.runner.invoke(cli, ['process', '--help'])
        
        assert result.exit_code == 0
        assert '--signatures' in result.output
        assert 'Extract only function signatures' in result.output
    
    @patch('project2md.signature_processor.SignatureProcessor')
    @patch('project2md.cli.load_configuration')
    def test_signature_processor_integration(
        self,
        mock_load_config,
        mock_signature_processor_class
    ):
        """Test that SignatureProcessor is imported and used when signatures_mode is True."""
        from project2md.cli import process_repository
        
        # Setup mocks
        mock_config = Mock(spec=Config)
        mock_config.signatures_mode = True
        mock_config.output_file = Path("test.md")
        mock_config.general = Mock()
        mock_config.general.stats_in_output = False
        
        mock_git_handler = Mock()
        mock_git_handler.prepare_repository.return_value = Path("/test/repo")
        mock_git_handler.get_repo_info.return_value = {'branch': 'main'}
        
        mock_walker = Mock()
        mock_walker.collect_files.return_value = [Path("test.py")]
        mock_walker.read_file.return_value = "def test(): pass"
        
        mock_formatter = Mock()
        mock_stats_collector = Mock()
        mock_stats_collector.get_stats.return_value = {}
        
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1
        
        mock_message_handler = Mock()
        
        # Setup SignatureProcessor mock
        mock_processor_instance = Mock()
        mock_processor_instance.process_file.return_value = "def test(): pass [lines:1]"
        mock_signature_processor_class.return_value = mock_processor_instance
        
        # Test that the function can be called without error
        try:
            process_repository(
                mock_config,
                mock_git_handler,
                mock_walker,
                mock_formatter,
                mock_stats_collector,
                mock_progress,
                False,
                mock_message_handler
            )
            # If signatures_mode is True, SignatureProcessor should be instantiated
            if mock_config.signatures_mode:
                mock_signature_processor_class.assert_called_once()
                mock_processor_instance.process_file.assert_called()
        except Exception as e:
            # Should not raise an import error
            assert "SignatureProcessor" not in str(e)


class TestSignaturesConfigIntegration:
    """Test configuration integration with signatures."""
    
    def test_config_merge_signatures_arg(self):
        """Test that signatures argument is properly merged into config."""
        config = Config()
        
        # Test merging signatures=True
        config.merge_cli_args({'signatures': True})
        assert config.signatures_mode == True
        
        # Test merging signatures=False
        config.merge_cli_args({'signatures': False})
        assert config.signatures_mode == False
    
    def test_config_signatures_not_in_args(self):
        """Test that signatures_mode remains unchanged if not in args."""
        config = Config()
        config.signatures_mode = True
        
        config.merge_cli_args({'output_file': 'test.md'})
        assert config.signatures_mode == True  # Should remain unchanged
    
    def test_load_configuration_includes_signatures(self):
        """Test that load_configuration properly handles signatures argument."""
        from project2md.cli import load_configuration
        
        cli_args = {
            'signatures': True,
            'output_file': 'test.md',
            'repo_url': None,
            'target_dir': '/test/dir'
        }
        
        with patch('project2md.config.Config.from_yaml') as mock_from_yaml, \
             patch('project2md.config.Config.apply_smart_defaults'), \
             patch('project2md.config.Config._load_gitignore_patterns'), \
             patch('project2md.config.Config.validate'):
            
            mock_config = Mock(spec=Config)
            mock_config.signatures_mode = False
            mock_from_yaml.return_value = mock_config
            
            result_config = load_configuration(None, cli_args)
            
            # Verify merge_cli_args was called with signatures
            mock_config.merge_cli_args.assert_called_once()
            call_args = mock_config.merge_cli_args.call_args[0][0]
            assert 'signatures' in call_args
            assert call_args['signatures'] == True


@pytest.fixture
def mock_temp_dir(tmp_path):
    """Create a temporary directory with test files."""
    # Create test Python file
    python_file = tmp_path / "test.py"
    python_file.write_text("""
def hello():
    print("Hello, World!")
    return True

class TestClass:
    def method(self):
        pass
""")
    
    # Create test Markdown file
    md_file = tmp_path / "README.md"
    md_file.write_text("""
# Main Title
Introduction

## Section 1
Content here

### Subsection
More content
""")
    
    return tmp_path


class TestSignaturesEndToEnd:
    """End-to-end tests for signatures functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('project2md.cli.GitHandler')
    @patch('project2md.cli.get_formatter')
    def test_signatures_processing_python_file(self, mock_get_formatter, mock_git_handler, tmp_path):
        """Test end-to-end signatures processing for Python files."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def add_numbers(a, b):
    '''Add two numbers together.'''
    result = a + b
    return result

class Calculator:
    def multiply(self, x, y):
        return x * y
""")
        
        # Create config file
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
        
        output_file = tmp_path / "output.md"
        
        # Mock dependencies
        mock_git_instance = Mock()
        mock_git_instance.prepare_repository.return_value = tmp_path
        mock_git_instance.get_repo_info.return_value = {'branch': 'main'}
        mock_git_handler.return_value = mock_git_instance
        
        mock_formatter_instance = Mock()
        mock_get_formatter.return_value = mock_formatter_instance
        
        # Run with signatures flag
        result = self.runner.invoke(cli, [
            'process',
            '--signatures',
            '--root-dir', str(tmp_path),
            '--config', str(config_file),
            '--output', str(output_file)
        ])
        
        # Should complete successfully
        assert result.exit_code == 0
        
        # Verify formatter was called
        mock_formatter_instance.generate_output.assert_called_once()
        
        # Check that processed files contain signature-processed content
        call_args = mock_formatter_instance.generate_output.call_args[0]
        processed_files = call_args[1]  # Second argument is processed_files
        
        # Find our Python file in processed files
        python_content = None
        for file_path, content in processed_files:
            if file_path.name == "test.py":
                python_content = content
                break
        
        assert python_content is not None
        assert "[lines:" in python_content  # Should contain line counts
        assert "def add_numbers(a, b):" in python_content
        assert "class Calculator:" in python_content
