# project2md/config.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Union
import yaml
from enum import Enum
import logging
import re
import pathspec

logger = logging.getLogger(__name__)

class OutputFormat(Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"

    @classmethod
    def from_string(cls, value: str) -> 'OutputFormat':
        try:
            return cls(value.lower())
        except ValueError:
            raise ConfigError(f"Invalid output format: {value}")

DEFAULT_INCLUDE_PATTERNS = {
    'files': [
        '**/*.py',         # Python
        '**/*.js',         # JavaScript
        '**/*.ts',         # TypeScript
        '**/*.java',       # Java
        '**/*.c',          # C
        '**/*.h',          # C header
        '**/*.cpp',        # C++
        '**/*.hpp',        # C++ header
        '**/*.cs',         # C#
        '**/*.rb',         # Ruby
        '**/*.php',        # PHP
        '**/*.go',         # Go
        '**/*.rs',         # Rust
        '**/*.swift',      # Swift
        '**/*.kt',         # Kotlin
        '**/*.m',          # Objective-C
        '**/*.mm',         # Objective-C++
        '**/*.scala',      # Scala
        '**/*.hs',         # Haskell
        '**/*.erl',        # Erlang
        '**/*.ex',         # Elixir
        '**/*.exs',        # Elixir script
        '**/*.sh',         # Shell script
        '**/*.bash',       # Bash script
        '**/*.zsh',        # Zsh script
        '**/*.ps1',        # PowerShell
        '**/*.r',          # R
        '**/*.jl',         # Julia
        '**/*.clj',        # Clojure
        '**/*.cljs',       # ClojureScript
        '**/*.cljc',       # Clojure common/shared
        '**/*.sql',        # SQL
        '**/*.pl',         # Perl
        '**/*.pm',         # Perl module
        '**/*.asm',        # Assembly
        '**/*.s',          # Assembly
        '**/*.v',          # Verilog
        '**/*.sv',         # SystemVerilog
        '**/*.vhd',        # VHDL
        '**/*.dart',       # Dart
        '**/*.coffee',     # CoffeeScript
        '**/*.lisp',       # Lisp
        '**/*.scm',        # Scheme
        '**/*.rkt',        # Racket
        '**/*.ml',         # OCaml
        '**/*.fs',         # F#
        '**/*.vb',         # Visual Basic
        '**/*.vba',        # Visual Basic for Applications
        '**/*.fsx',        # F# script
        '**/*.tex',        # LaTeX
        '**/*.bib',        # BibTeX
        '**/*.md',         # Markdown
        '**/*.rst',        # reStructuredText
        '**/*.txt',        # Plain text
        '**/*.json',       # JSON
        '**/*.yml',        # YAML
        '**/*.yaml',       # YAML
        '**/*.xml',        # XML
        '**/*.html',       # HTML
        '**/*.htm',        # HTML
        '**/*.css',        # CSS
        '**/*.scss',       # SCSS/Sass
        '**/*.less',       # Less
        '**/*.ini',        # INI configuration
        '**/*.conf',       # Config file
        '**/*.cfg',        # Config file
        '**/*.toml',       # TOML
        '**/*.properties', # Java properties
        '**/*.gradle',     # Gradle
        '**/*.gradle.kts', # Gradle Kotlin DSL
        '**/*.mk',         # Makefile fragment
        '**/Makefile',     # Makefile
        '**/*.bat',        # Batch file (Windows)
        '**/*.cmd',        # Batch file (Windows)
        '**/*.cmake',      # CMake
        '**/*.rake',       # Rake (Ruby)
        '**/*.gemspec',    # Ruby gemspec
        '**/Dockerfile',   # Dockerfile
        '**/*.dockerfile', # Alternative Dockerfile pattern
        '**/*.psd1',       # PowerShell data file
        '**/*.nuspec',     # NuGet specification
        '**/*.csproj',     # C# project file
        '**/*.vbproj',     # VB.NET project file
        '**/*.fsproj',     # F# project file
        '**/*.xproj',      # .NET project file (legacy)
        '**/*.sln',        # Visual Studio solution
        '**/*.cabal',      # Haskell Cabal
        '**/*.opam',       # OCaml OPAM
        '**/*.d',          # D language
        '**/*.nim',        # Nim
        '**/*.elm',        # Elm
        '**/*.sbt',        # SBT (Scala build tool)
        '**/*.proto',      # Protocol Buffers
        '**/*.hbs',        # Handlebars template
        '**/*.ejs',        # Embedded JavaScript template
        '**/*.mjs',        # JavaScript module (ESM)
        '**/*.cjs',        # CommonJS module
        '**/.editorconfig',# EditorConfig file
        '**/.gitignore',   # Git ignore file
        '**/.dockerignore',# Docker ignore file

        # Additional entries:
        '**/*.ipynb',          # Jupyter Notebook (JSON-based)
        '**/*.lua',            # Lua scripts
        '**/*.f',              # Fortran fixed-format source
        '**/*.for',            # Fortran source (fixed/free)
        '**/*.f90',            # Fortran free-format source
        '**/CMakeLists.txt',   # CMake build scripts (no extension)
        '**/Vagrantfile',      # Vagrant configuration
        '**/Rakefile',         # Rake build file (no extension)
        '**/Gemfile',          # Ruby Gemfile
        '**/Gemfile.lock',     # Ruby Gemfile lock
        '**/Pipfile',          # Python Pipfile for pipenv
        '**/Pipfile.lock',     # Python Pipfile lock
        '**/requirements.txt', # Python dependencies list
        '**/Jenkinsfile',      # Jenkins pipeline
        '**/Procfile',         # Procfile for deployment (e.g., Heroku)
        '**/BUILD',            # Bazel build file (no extension)
        '**/BUILD.bazel',      # Bazel build file (alternative naming)
        '**/WORKSPACE',        # Bazel workspace file
        '**/*.csx',            # C# script files
        '**/*.tsx',            # TypeScript React files
        '**/*.jsx',            # React JavaScript files
        '**/.npmignore',       # npm ignore file
        '**/Docker-compose.yml' # Docker Compose file
    ],
    'dirs': []
}

DEFAULT_EXCLUDE_PATTERNS = {
    'files': [
        # Output and config files
        'project_summary.md',  # Default output file
        '.project2md.yml',     # Default config file
        # Draft files
        '**/__*.md',          # Draft markdown files
        # Version control metadata
        '.git/**',
        '.gitignore',
        '.gitmodules',
        '.gitattributes',
        '.hg/**',
        '.hgignore',
        '.bzr/**',
        '.bzrignore',
        '.svn/**',

        # Build artifacts and output directories (also in dirs)
        '**/dist/**',
        '**/build/**',
        '**/target/**',
        '**/coverage/**',

        # Python cache and compiled files
        '**/__pycache__/**',
        '**/*.pyc',
        '**/*.pyo',
        '**/*.pyd',

        # Node.js artifacts
        '**/node_modules/**',

        # IDE and editor files
        '**/.idea/**',
        '**/.vscode/**',
        '**/.vs/**',
        '**/*.sublime-workspace',
        '**/*.sublime-project',

        # Operating system and miscellaneous files
        '**/.DS_Store',
        '**/desktop.ini',
        '**/Thumbs.db',
        '**/ehthumbs.db',

        # Temporary and backup files
        '**/*.tmp',
        '**/*.temp',
        '**/*.swp',
        '**/*~',
        '**/*.bak',
        '**/*.old',
        '**/*.orig',

        # Jupyter Notebook checkpoints
        '**/.ipynb_checkpoints/**',

        # Cache directories and files
        '**/.cache/**',
        '**/.sass-cache/**',

        # Log files and error dumps
        '**/logs/**',
        '**/*.log',
        '**/npm-debug.log',
        '**/yarn-debug.log',
        '**/yarn-error.log',

        # Compiled binaries and libraries
        '**/*.exe',
        '**/*.dll',
        '**/*.so',
        '**/*.dylib',
        '**/*.obj',
        '**/*.o',
        '**/*.a',
        '**/*.lib',
        '**/*.bin',
        '**/*.class',
        '**/*.mo',

        # Archives and compressed files
        '**/*.zip',
        '**/*.tar.gz',
        '**/*.7z',
        '**/*.rar',
        '**/*.gz',
        '**/*.bz2',
        '**/*.xz',
        '**/*.lzma',
        '**/*.zst',
        '**/*.lz4',

        # Media files (often large; may be part of docs but typically excluded)
        '**/*.jpg',
        '**/*.jpeg',
        '**/*.png',
        '**/*.gif',
        '**/*.bmp',
        '**/*.ico',
        '**/*.mp4',
        '**/*.mov',
        '**/*.avi',
        '**/*.flv',
        '**/*.mkv',
        '**/*.wmv',
        '**/*.mp3',
        '**/*.wav',
        '**/*.ogg',
        '**/*.flac',
        '**/*.aac',
        '**/*.wma',

        # Documents (binary formats that are usually not source)
        '**/*.pdf',
        '**/*.doc',
        '**/*.docx',
        '**/*.xls',
        '**/*.xlsx',
        '**/*.ppt',
        '**/*.pptx',
        '**/*.odt',
        '**/*.ods',
        '**/*.odp',
        '**/*.rtf',

        # Databases and GIS files
        '**/*.db',
        '**/*.sqlite',
        '**/*.sql',
        '**/*.dbf',
        '**/*.mdb',
        '**/*.accdb',
        '**/*.shp',
    ],
    'dirs': [
        # Version control directories
        '.git',
        '.hg',
        '.bzr',
        '.svn',

        # IDE and editor directories
        '.idea',
        '.vscode',
        '.vs',

        # Python and Node artifacts
        'venv',
        'env',
        '.venv',
        '.env',
        'node_modules',

        # Build and cache directories
        '__pycache__',
        'dist',
        'build',
        'target',
        'coverage',
        'vendor',
        'bower_components',
        '.cache',
        '.sass-cache',
        '.ipynb_checkpoints',

        # Temporary directories
        'tmp',
        'temp',
    ]
}


@dataclass
class GeneralConfig:
    max_depth: int = 10
    max_file_size: str = "1MB"
    stats_in_output: bool = True
    collapse_empty_dirs: bool = True
    max_file_size_bytes: int = field(init=False)

    def __post_init__(self):
        self.max_file_size_bytes = self._parse_size(self.max_file_size)

    @staticmethod
    def _parse_size(size_str: str) -> int:
        """Convert size string (e.g., '1MB') to bytes."""
        units = {'B': 1, 'KB': 1024, 'MB': 1024*1024, 'GB': 1024*1024*1024}
        match = re.match(r'^(\d+)\s*([A-Za-z]+)$', size_str.strip())
        if not match:
            raise ValueError(f"Invalid size format: {size_str}")
        number, unit = match.groups()
        unit = unit.upper()
        if unit not in units:
            raise ValueError(f"Invalid size unit: {unit}")
        return int(number) * units[unit]

@dataclass
class OutputConfig:
    format: OutputFormat = OutputFormat.MARKDOWN
    stats: bool = True

    def validate(self):
        if not isinstance(self.format, OutputFormat):
            raise ConfigError("Invalid output format")

    @classmethod
    def from_dict(cls, data: dict) -> 'OutputConfig':
        config = cls()
        if 'format' in data:
            config.format = OutputFormat.from_string(data['format'])
        return config

    def merge_cli_args(self, args: dict):
        if 'format' in args:
            self.format = OutputFormat.from_string(args['format'])

@dataclass
class PathPatterns:
    files: List[str] = field(default_factory=list)
    dirs: List[str] = field(default_factory=list)

@dataclass
class Config:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    include: PathPatterns = field(default_factory=PathPatterns)
    exclude: PathPatterns = field(default_factory=PathPatterns)
    repo_url: Optional[str] = None
    target_dir: Path = Path.cwd()
    output_file: Path = Path('project_summary.md')
    branch: str = "main"  # Add this line
    signatures_mode: bool = False

    DEFAULT_INCLUDES = {
        'files': [
            '*.py', '*.js', '*.ts', '*.java', '*.c', '*.cpp', '*.h', '*.hpp',
            '*.cs', '*.go', '*.rs', '*.rb', '*.php', '*.swift', '*.kt',
            '*.md', '*.txt', '*.json', '*.yaml', '*.yml', '*.xml',
            '*.html', '*.css', '*.scss', '*.sass', '*.less',
            'LICENSE*', 'README*', 'CHANGELOG*', 'CONTRIBUTING*'
        ],
        'dirs': [
            'src/', 'lib/', 'app/', 'tests/', 'docs/'
        ]
    }

    DEFAULT_EXCLUDES = {
        'files': [
            '*.min.js', '*.min.css', '*.map',
            '*.pyc', '*.pyo', '*.pyd', '__pycache__/*',
            '*.o', '*.obj', '*.a', '*.lib', '*.so', '*.dll', '*.dylib',
            '*.exe', '*.bin', '*.out',
            '*.zip', '*.tar', '*.gz', '*.rar', '*.7z',
            '*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx',
            '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.svg',
            '*.mo', '*.pot',
            '**/node_modules/**', '**/vendor/**', '**/build/**', '**/dist/**',
            '**/.git/**', '**/.svn/**', '**/.hg/**',
            '**/.idea/**', '**/.vscode/**', '**/.DS_Store'
        ],
        'dirs': [
            '.git/', '.svn/', '.hg/',
            'node_modules/', 'vendor/', 'venv/', 'env/',
            'build/', 'dist/', 'target/',
            '.idea/', '.vscode/', '__pycache__/',
            'coverage/', '.nyc_output/', '.coverage/'
        ]
    }

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> 'Config':
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            return cls.from_dict(data or {})
        except FileNotFoundError:
            # Try loading default config if custom config not found
            default_config_path = Path(__file__).parent / 'default_config.yml'
            try:
                with open(default_config_path, 'r') as f:
                    data = yaml.safe_load(f)
                logger.info(f"Using default config from {default_config_path}")
                return cls.from_dict(data or {})
            except FileNotFoundError:
                logger.warning("No config file found, using hardcoded defaults")
                return cls()
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading config: {e}")

    @classmethod
    def from_dict(cls, data: Dict) -> 'Config':
        """Create configuration from dictionary."""
        try:
            general_data = data.get('general', {})
            output_data = data.get('output', {})
            include_data = data.get('include', {})
            exclude_data = data.get('exclude', {})

            general = GeneralConfig(
                max_depth=general_data.get('max_depth', 10),
                max_file_size=general_data.get('max_file_size', '1MB'),
                stats_in_output=general_data.get('stats_in_output', True),
                collapse_empty_dirs=general_data.get('collapse_empty_dirs', True)
            )

            output = OutputConfig.from_dict(output_data)

            include = PathPatterns(
                files=include_data.get('files', []),
                dirs=include_data.get('dirs', [])
            )

            exclude = PathPatterns(
                files=exclude_data.get('files', []),
                dirs=exclude_data.get('dirs', [])
            )

            return cls(
                general=general,
                output=output,
                include=include,
                exclude=exclude
            )
        except Exception as e:
            raise ConfigError(f"Error parsing config data: {e}")

    @classmethod
    def create_default_config(cls, path: Path) -> None:
        """Create a default configuration file if none exists."""
        if path.exists():
            return
            
        config_dict = {
            'general': {
                'max_depth': 10,
                'max_file_size': '1MB',
                'stats_in_output': True,
                'collapse_empty_dirs': True
            },
            'output': {
                'format': 'markdown',
                'stats': True
            },
            'exclude': DEFAULT_EXCLUDE_PATTERNS,
            'include': {
                'files': ['**/*.md', '**/*.py', '**/*.js', '**/*.ts', '**/*.java', '**/*.c', '**/*.cpp', '**/*.h'],
                'dirs': []
            }
        }
        
        with open(path, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)
            
    def _load_gitignore_patterns(self, repo_path: Path) -> None:
        """Load patterns from .gitignore file if it exists."""
        gitignore_path = repo_path / '.gitignore'
        if not gitignore_path.exists():
            return
            
        with open(gitignore_path) as f:
            gitignore_patterns = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    gitignore_patterns.append(line)
                    
        # Add patterns from .gitignore to exclude patterns
        self.exclude.files.extend(gitignore_patterns)
        
    def apply_smart_defaults(self) -> None:
        """Apply smart defaults if no patterns are configured."""
        if not self.exclude.files and not self.exclude.dirs:
            self.exclude.files.extend(DEFAULT_EXCLUDE_PATTERNS['files'])
            self.exclude.dirs.extend(DEFAULT_EXCLUDE_PATTERNS['dirs'])

    def merge_cli_args(self, cli_args: Dict) -> None:
        """Merge CLI arguments into config with CLI taking precedence."""
        if cli_args.get('repo_url'):
            self.repo_url = cli_args['repo_url']
        if cli_args.get('target_dir'):
            self.target_dir = Path(cli_args['target_dir'])
        if cli_args.get('output_file'):
            self.output_file = Path(cli_args['output_file'])
        
        # Merge include/exclude patterns
        if cli_args.get('include'):
            self.include.files.extend(cli_args['include'])
        if cli_args.get('exclude'):
            self.exclude.files.extend(cli_args['exclude'])
        if cli_args.get('include_extra'):
            self.include.files.extend(cli_args['include_extra'])
        if cli_args.get('exclude_extra'):
            self.exclude.files.extend(cli_args['exclude_extra'])

        if cli_args.get('branch'):
            self.branch = cli_args['branch']

        if 'format' in cli_args:
            # Ensure format is properly set as enum
            self.output.format = OutputFormat(cli_args['format'].lower())

        if 'signatures' in cli_args:
            self.signatures_mode = cli_args['signatures']

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.general.max_depth < 1:
            raise ConfigError("max_depth must be greater than 0")
        
        if self.general.max_file_size_bytes < 1:
            raise ConfigError("max_file_size must be greater than 0")

        # Validate target directory
        if not self.target_dir.exists() and self.repo_url:
            self.target_dir.mkdir(parents=True, exist_ok=True)
        elif not self.target_dir.exists():
            raise ConfigError(f"Target directory does not exist: {self.target_dir}")

        # Validate patterns
        self._validate_patterns(self.include.files, "include files")
        self._validate_patterns(self.include.dirs, "include dirs")
        self._validate_patterns(self.exclude.files, "exclude files")
        self._validate_patterns(self.exclude.dirs, "exclude dirs")

    @staticmethod
    def _validate_patterns(patterns: List[str], context: str) -> None:
        """Validate glob patterns."""
        for pattern in patterns:
            # Basic syntax validation
            if pattern.count('[') != pattern.count(']'):
                raise ConfigError(f"Invalid pattern in {context}: {pattern} (Unmatched brackets)")
            if pattern.count('{') != pattern.count('}'):
                raise ConfigError(f"Invalid pattern in {context}: {pattern} (Unmatched braces)")
            if '\\' in pattern and not any(c in pattern for c in '*?[]{}'):
                raise ConfigError(f"Invalid pattern in {context}: {pattern} (Invalid escape character)")

            try:
                # Additional validation using pathspec
                pathspec.PathSpec.from_lines('gitwildmatch', [pattern])
            except Exception as e:
                raise ConfigError(f"Invalid pattern in {context}: {pattern} ({e})")

    def save(self, path: Union[str, Path]) -> None:
        """Save current configuration to YAML file."""
        config_dict = {
            'general': {
                'max_depth': self.general.max_depth,
                'max_file_size': self.general.max_file_size,
                'stats_in_output': self.general.stats_in_output,
                'collapse_empty_dirs': self.general.collapse_empty_dirs
            },
            'output': {
                'format': self.output.format.value,
                'stats': self.output.stats
            },
            'include': {
                'files': self.include.files,
                'dirs': self.include.dirs
            },
            'exclude': {
                'files': self.exclude.files,
                'dirs': self.exclude.dirs
            }
        }
        
        try:
            with open(path, 'w') as f:
                yaml.safe_dump(config_dict, f, default_flow_style=False)
        except Exception as e:
            raise ConfigError(f"Error saving config to {path}: {e}")


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass