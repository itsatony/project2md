"""Tests for version extraction functionality."""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
from project2md.cli import get_version


class TestVersionExtraction:
    """Test version extraction from pyproject.toml files."""

    def test_get_version_from_project_section(self):
        """Test version extraction from [project] section."""
        toml_content = """
[project]
name = "test-project"
version = "1.2.3"
description = "Test project"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
        
        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                assert version == "1.2.3"

    def test_get_version_from_poetry_section(self):
        """Test version extraction from [tool.poetry] section."""
        toml_content = """
[tool.poetry]
name = "test-project"
version = "2.4.6"
description = "Test project"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
        
        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                assert version == "2.4.6"

    def test_get_version_prefers_project_over_poetry(self):
        """Test that [project] version is preferred over [tool.poetry] version."""
        toml_content = """
[project]
name = "test-project"
version = "1.0.0"
description = "Test project"

[tool.poetry]
name = "test-project"
version = "2.0.0"
description = "Test project"
"""
        
        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                assert version == "1.0.0"

    def test_get_version_falls_back_to_poetry(self):
        """Test fallback to [tool.poetry] when [project] has no version."""
        toml_content = """
[project]
name = "test-project"
description = "Test project"

[tool.poetry]
name = "test-project"
version = "3.1.4"
description = "Test project"
"""
        
        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                assert version == "3.1.4"

    def test_get_version_no_version_found(self):
        """Test when no version is found in either section."""
        toml_content = """
[project]
name = "test-project"
description = "Test project"

[tool.poetry]
name = "test-project"
description = "Test project"
"""
        
        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                assert version == "unknown"

    def test_get_version_no_pyproject_file(self):
        """Test when no pyproject.toml file exists."""
        with patch("pathlib.Path.exists", return_value=False):
            version = get_version()
            assert version == "unknown"

    def test_get_version_file_read_error(self):
        """Test when file reading raises an exception."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("Cannot read file")):
                version = get_version()
                assert version == "unknown"

    def test_get_version_invalid_toml(self):
        """Test when TOML file is malformed."""
        invalid_toml = """
[project
name = "test-project"
version = "1.0.0
"""
        
        with patch("builtins.open", mock_open(read_data=invalid_toml)):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                assert version == "unknown"

    def test_get_version_empty_file(self):
        """Test when pyproject.toml file is empty."""
        with patch("builtins.open", mock_open(read_data="")):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                assert version == "unknown"

    def test_get_version_searches_multiple_paths(self):
        """Test that the function searches multiple directory levels."""
        toml_content = """
[project]
version = "4.5.6"
"""
        
        # Mock to simulate finding pyproject.toml in the parent.parent directory (third search location)
        def mock_exists(self):
            path_str = str(self)
            # Return True only for the third path that would be checked (parent.parent)
            return path_str.endswith("pyproject.toml") and "parent.parent" in path_str
        
        call_count = 0
        original_exists = Path.exists
        
        def mock_exists_with_counter(self):
            nonlocal call_count
            call_count += 1
            # First two calls return False, third returns True
            if call_count <= 2:
                return False
            return True
        
        with patch.object(Path, 'exists', mock_exists_with_counter):
            with patch("builtins.open", mock_open(read_data=toml_content)):
                version = get_version()
                assert version == "4.5.6"

    def test_get_version_with_real_pyproject_toml(self):
        """Test with the actual pyproject.toml file from the project."""
        # This test uses the real pyproject.toml file to ensure it works correctly
        version = get_version()
        
        # The version should not be "unknown" if the real file exists and is readable
        assert version != "unknown"
        assert isinstance(version, str)
        assert len(version) > 0
        
        # Check that it matches semantic versioning pattern (x.y.z)
        import re
        semver_pattern = r'^\d+\.\d+\.\d+.*$'
        assert re.match(semver_pattern, version), f"Version '{version}' doesn't match semantic versioning pattern"

    def test_get_version_complex_toml_structure(self):
        """Test with a more complex TOML structure."""
        toml_content = """
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[project]
name = "complex-project"
version = "1.2.3-alpha.1"
description = "A complex project with pre-release version"
authors = [
    {name = "Test Author", email = "test@example.com"}
]
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0"
]

[project.optional-dependencies]
dev = ["pytest>=6.0.0"]

[tool.poetry]
name = "complex-project"
version = "0.9.9"  # Different version in poetry section
description = "A complex project"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.25.0"

[tool.black]
line-length = 88
"""
        
        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                # Should prefer [project] version over [tool.poetry] version
                assert version == "1.2.3-alpha.1"

    def test_get_version_nested_dict_access(self):
        """Test that nested dictionary access works correctly."""
        toml_content = """
[tool]
poetry = {name = "test", version = "5.6.7"}

[project]
name = "test-project"
"""
        
        with patch("builtins.open", mock_open(read_data=toml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                version = get_version()
                assert version == "5.6.7"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
