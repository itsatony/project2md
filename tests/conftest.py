"""
Pytest configuration and shared fixtures.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from project2md.config import Config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    config = Config()
    config.general.max_depth = 5
    config.general.max_file_size = "1MB"
    config.general.stats_in_output = True
    config.signatures_mode = False
    return config


@pytest.fixture
def mock_git_repo(temp_dir):
    """Create a mock git repository structure."""
    # Create git directory
    git_dir = temp_dir / ".git"
    git_dir.mkdir()
    
    # Create some sample files
    (temp_dir / "README.md").write_text("# Test Repository\n\nThis is a test.")
    (temp_dir / "main.py").write_text("def hello():\n    print('Hello')\n")
    (temp_dir / "src").mkdir()
    (temp_dir / "src" / "utils.py").write_text("def util_func():\n    return True\n")
    
    return temp_dir


@pytest.fixture
def sample_python_file():
    """Sample Python code for testing."""
    return '''
def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

class Calculator:
    def __init__(self):
        self.value = 0
    
    def multiply(self, x, y):
        """Multiply two numbers."""
        return x * y
    
    async def async_calculate(self, operation):
        """Perform async calculation."""
        await some_async_operation()
        return operation()

def nested_function():
    def inner():
        return "inner"
    return inner()
'''


@pytest.fixture
def sample_markdown():
    """Sample Markdown content for testing."""
    return '''# Main Title

This is the introduction.

## Section 1

Some content here.

### Subsection 1.1

More detailed content.

## Section 2

Final section content.
'''


@pytest.fixture
def sample_javascript():
    """Sample JavaScript code for testing.""" 
    return '''
function regularFunction(a, b) {
    return a + b;
}

const arrowFunction = (x) => {
    return x * 2;
};

class TestClass {
    constructor() {
        this.value = 0;
    }
    
    method(param) {
        this.value = param;
        return this.value;
    }
}

async function asyncFunction() {
    await someOperation();
    return result;
}
'''
