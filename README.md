# Project2MD

Transform Git repositories into comprehensive Markdown documentation with intelligent file filtering and structure preservation.

## Overview

project2md is a command-line tool that creates a single Markdown file containing the complete structure and content of a Git repository. It's designed to prepare repository content for Large Language Model (LLM) analysis while maintaining project structure and context.

## Features

### Core Features (v1.3.0)

- **Signature extraction mode** - Extract only function signatures and headers for high-level code overview
- Multiple output formats (Markdown, JSON, YAML)
- Clone Git repositories using SSH authentication
- Process existing local repositories
- Configuration file support (.project2md.yml)
- Project initialization with default config
- Intelligent file filtering with glob patterns
- Configurable directory depth limits
- Text file content extraction
- Repository structure visualization
- Project statistics
- Progress tracking
- Branch information
- Smart defaults for common file patterns
- Draft file exclusion (`__*.md`)
- Gitignore integration

### Signature Extraction

The new `--signatures` flag transforms how code files are processed:

- **Code files**: Extracts function signatures, class definitions, and method signatures with line counts
- **Markdown files**: Keeps only headers with section line counts
- **Supported languages**: Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, PHP, Ruby

Example output with `--signatures`:

```python
def add_numbers(a, b): [lines:3]
class Calculator: [lines:15]
async def process_async(items: List[str]) -> bool: [lines:8]
```

### Planned Features

- Enhanced tree visualization
- Extended Git metadata support

## Installation

```bash
pip install project2md
```

## Usage

### Initialization

```bash
# Initialize project with default configuration
project2md init

# Initialize in specific directory
project2md init --root-dir /path/to/project

# Force overwrite existing config
project2md init --force
```

### Processing Repositories

```bash
# Process a remote repository
project2md process --repo=https://github.com/user/repo --output=summary.md

# Process current directory
project2md process --output=summary.md

# Extract only signatures for a high-level overview
project2md process --signatures --output=signatures.md

# Use specific configuration
project2md process --repo=https://github.com/user/repo --config=.project2md.yml
```

### Command Line Arguments

#### Global Options

```text
init        Initialize project with default configuration
process     Process a repository or directory
explicit    Generate explicit configuration file
version     Show version information
```

#### Init Command Options

```text
--root-dir  Root directory for initialization (defaults to current directory)
--force     Overwrite existing config file
```

#### Process Command Options

```text
--repo        Repository URL (optional, defaults to current directory)
--target      Clone target directory (optional, defaults to current directory)
--output      Output file path (optional, defaults to project_summary.md)
--config      Configuration file path (optional, defaults to .project2md.yml)
--include     Include patterns (can be specified multiple times)
--exclude     Exclude patterns (can be specified multiple times)
--branch      Specific branch to process (defaults to 'main')
--format      Output format: markdown, json, yaml (default: markdown)
--signatures  Extract only function signatures and headers
```

#### Explicit Command Options

```text
--directory   Directory to analyze (defaults to current directory)
```

### Configuration File (.project2md.yml)

The tool automatically creates this file when you run `project2md init`. It includes:

```yaml
general:
  max_depth: 10
  max_file_size: "1MB"
  stats_in_output: true
  collapse_empty_dirs: true

output:
  format: "markdown"
  stats: true

include:
  files:
    - "**/*.py"         # Python files
    - "**/*.js"         # JavaScript files
    - "**/*.md"         # Markdown files
    # ... many more defaults for common file types
  dirs:
    - "src/"
    - "lib/"
    - "app/"
    - "tests/"
    - "docs/"

exclude:
  files:
    - "project_summary.md"  # Default output file
    - ".project2md.yml"     # Config file
    - "**/__*.md"          # Draft markdown files
    - "**/.git/**"         # Git files
    # ... many more sensible defaults
  dirs:
    - ".git"
    - "node_modules"
    - "venv"
    # ... more excluded directories
```

## Output Format

The generated Markdown file follows this structure:

````markdown
# Project Overview

{README.md content}

# Project Structure

```tree
{project tree}
```

# Statistics

{detailed statistics if enabled}

# File Contents

## filepath: repoRoot/file1

{file1 content}

## filepath: repoRoot/dir/file2

{file2 content}
````

### Signature Mode Output

When using `--signatures`, the output focuses on structure:

```markdown
# File Contents

## filepath: repoRoot/main.py
def main(args): [lines:15]
class Application: [lines:45]
async def startup(): [lines:8]

## filepath: repoRoot/README.md
# Main Title [lines:3]
## Installation [lines:12]
### Prerequisites [lines:5]
## Usage [lines:25]
```

## Development

### Setting Up Development Environment

1. Install Poetry (if not already installed):

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/itsatony/project2md.git
   cd project2md
   ```

3. Install dependencies with Poetry:

   ```bash
   poetry install
   ```

### Running Tests

The project uses pytest for testing. To run the tests:

```bash
# Run all tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=project2md

# Run tests verbosely
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_config.py

# Run tests matching specific pattern
poetry run pytest -k "test_config"
```

### Test Structure

Tests are organized in the `tests/` directory:

- `test_config.py`: Configuration system tests
- `test_git.py`: Git operations tests
- `test_walker.py`: File system traversal tests
- `test_formatter.py`: Output formatting tests
- `test_stats.py`: Statistics collection tests
- `test_signature_processor.py`: Signature extraction tests
- `test_cli_signatures.py`: CLI integration tests for signatures

### Project Structure

```tree
project2md/
├── __init__.py                  # Package initialization
├── cli.py                      # Command-line interface
├── config.py                   # Configuration handling
├── git.py                     # Git operations
├── walker.py                  # File system traversal
├── signature_processor.py     # Signature extraction (NEW)
├── formatters/                # Output formatting
│   ├── base.py               # Base formatter
│   ├── factory.py            # Formatter factory
│   ├── markdown.py           # Markdown formatter
│   ├── json.py               # JSON formatter
│   └── yaml.py               # YAML formatter
├── stats.py                  # Statistics collection
├── messages.py               # User messaging
├── explicit_config_generator.py  # Explicit config generation
└── utils.py                  # Shared utilities
```

### Component Responsibilities

#### CLI (cli.py)

- Parse command-line arguments
- Initialize configuration
- Orchestrate overall process flow
- Handle user interaction (progress bar)

#### Configuration (config.py)

- Parse YAML configuration
- Merge CLI arguments with config file
- Validate configuration
- Provide unified config interface

#### Signature Processor (signature_processor.py)

- Extract function signatures from code files
- Process markdown headers with line counts
- Support multiple programming languages
- Handle syntax errors gracefully

#### Git Operations (git.py)

- Clone repositories
- Validate repository status
- Extract branch information
- Handle SSH authentication

#### File System Walker (walker.py)

- Traverse directory structure
- Apply include/exclude patterns
- Handle file size limits
- Manage directory depth
- Detect binary files

#### Formatters (formatters/)

- Generate output in multiple formats
- Create directory tree visualization
- Format statistics
- Handle file content rendering

#### Statistics (stats.py)

- Collect file and directory statistics
- Calculate size metrics
- Track file types
- Generate statistical summaries

#### Utilities (utils.py)

- Shared helper functions
- Error handling utilities
- Progress tracking
- Logging

### Error Handling

The tool implements comprehensive error handling:

- Clear error messages for configuration issues
- Graceful handling of inaccessible files
- Recovery from non-critical errors
- Detailed logging in verbose mode

### Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## Version History

### v1.3.1 (Latest)

- **NEW**: Signature extraction mode with `--signatures` flag
- **NEW**: Support for extracting function signatures from code files
- **NEW**: Markdown header extraction with line counts
- **NEW**: Multi-language support (Python, JS, TS, Java, C/C++, C#, Go, Rust, PHP, Ruby)
- **NEW**: Comprehensive test suite for signature processing
- Enhanced CLI with signature processing integration
- Improved configuration system for signature mode

### v1.2.2

- Added a dedicated version command
- Updated CLI to show help upon parsing errors without the default "Try ..." message

### v1.2.1

- Added "explicit" CLI command that generates explicit.config.project2md.yml, listing all files/dirs with per-item size info and their default inclusion status

### v1.1.0

- Added `init` command for project initialization
- Improved configuration file handling
- Added draft markdown exclusion (`__*.md`)
- Enhanced default file patterns
- Added config file auto-detection
- Improved documentation
- Better error messages
- Smarter default configurations

## CLI Help

When no command or invalid arguments are provided, project2md now shows usage information by default. Use:

```bash
project2md --help
```

to see all available options.

## License

MIT License - see LICENSE file for details.
