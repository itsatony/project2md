# tests/test_config.py
import pytest
from pathlib import Path
from reposcribe.config import Config, ConfigError, OutputFormat, GeneralConfig

@pytest.fixture
def sample_config_dict():
    return {
        'general': {
            'max_depth': 5,
            'max_file_size': '2MB',
            'stats_in_output': True,
            'collapse_empty_dirs': False
        },
        'output': {
            'format': 'markdown',
            'stats': True
        },
        'include': {
            'files': ['*.py', '*.md'],
            'dirs': ['src/', 'docs/']
        },
        'exclude': {
            'files': ['*.pyc', '*.log'],
            'dirs': ['__pycache__/', 'build/']
        }
    }

def test_config_from_dict(sample_config_dict):
    config = Config.from_dict(sample_config_dict)
    assert config.general.max_depth == 5
    assert config.general.max_file_size == '2MB'
    assert config.general.max_file_size_bytes == 2 * 1024 * 1024
    assert config.include.files == ['*.py', '*.md']
    assert config.exclude.dirs == ['__pycache__/', 'build/']

def test_config_defaults():
    config = Config()
    assert config.general.max_depth == 10
    assert config.general.max_file_size == '1MB'
    assert config.output.format == OutputFormat.MARKDOWN

def test_merge_cli_args():
    config = Config()
    cli_args = {
        'repo_url': 'https://github.com/user/repo',
        'target_dir': '/tmp/target',
        'output_file': 'output.md',
        'include': ['*.txt'],
        'exclude': ['*.tmp']
    }
    config.merge_cli_args(cli_args)
    assert config.repo_url == 'https://github.com/user/repo'
    assert config.target_dir == Path('/tmp/target')
    assert config.output_file == Path('output.md')
    assert '*.txt' in config.include.files
    assert '*.tmp' in config.exclude.files

def test_invalid_file_size():
    with pytest.raises(ValueError):
        GeneralConfig(max_file_size='invalid')

def test_invalid_patterns():
    config = Config()
    config.include.files = ['[']  # Invalid glob pattern
    with pytest.raises(ConfigError):
        config.validate()

@pytest.fixture
def temp_config_file(tmp_path):
    config_path = tmp_path / '.reposcribe.yml'
    return config_path

def test_save_and_load_config(temp_config_file, sample_config_dict):
    config = Config.from_dict(sample_config_dict)
    config.save(temp_config_file)
    
    loaded_config = Config.from_yaml(temp_config_file)
    assert loaded_config.general.max_depth == config.general.max_depth
    assert loaded_config.include.files == config.include.files
    assert loaded_config.exclude.dirs == config.exclude.dirs