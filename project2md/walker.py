# project2md/walker.py
from pathlib import Path
from typing import List, Set, Optional, Dict
import logging
from rich.progress import Progress
import chardet
import fnmatch
import pathspec

logger = logging.getLogger(__name__)

class WalkerError(Exception):
    """Custom exception for file system walker errors."""
    pass

class FileSystemWalker:
    """Handles repository traversal, file filtering, and content reading."""
    
    BINARY_EXTENSIONS = {
        '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe', 
        '.obj', '.bin', '.pdf', '.jpg', '.jpeg', '.png', 
        '.gif', '.bmp', '.ico', '.db', '.sqlite', '.zip',
        '.tar', '.gz', '.7z', '.rar', '.jar', '.war',
        '.ear', '.class', '.mo', '.pkl', '.pyd'
    }

    def __init__(self, config, progress: Progress):
        self.config = config
        self.progress = progress
        self._gitignore_spec = None
        self._include_spec = None
        self._exclude_spec = None

    def collect_files(self, root_path: Path) -> List[Path]:
        """
        Walk through the repository and collect files based on configuration.
        """
        try:
            root_path = Path(root_path).resolve()
            
            if not root_path.exists():
                error_msg = f"Directory does not exist: {root_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
                
            if not root_path.is_dir():
                error_msg = f"Path is not a directory: {root_path}"
                logger.error(error_msg)
                raise NotADirectoryError(error_msg)

            # Initialize pattern matching
            self._setup_patterns(root_path)
            
            # Debug log patterns
            logger.debug(f"Include patterns: {self.config.include.files + self.config.include.dirs}")
            logger.debug(f"Exclude patterns: {self.config.exclude.files + self.config.exclude.dirs}")
            
            files = []
            for path in self._collect_files_recursive(root_path):
                if self._should_process_path(path, root_path):
                    logger.debug(f"Including file: {path}")
                    files.append(path)
                else:
                    logger.debug(f"Excluding file: {path}")
            
            logger.info(f"Collected {len(files)} files to process")
            return sorted(files)
            
        except FileNotFoundError as e:
            raise WalkerError(f"Error collecting files: {str(e)}")
        except NotADirectoryError as e:
            raise WalkerError(f"Error collecting files: {str(e)}")
        except Exception as e:
            raise WalkerError(f"Error collecting files: Unexpected error - {str(e)}")

    def _collect_files_recursive(self, current_path: Path, depth: int = 0) -> List[Path]:
        """Recursively collect all files from directory."""
        if depth > self.config.general.max_depth:
            return []

        files = []
        try:
            for item in current_path.iterdir():
                if item.is_file():
                    files.append(item)
                elif item.is_dir() and not item.is_symlink():
                    files.extend(self._collect_files_recursive(item, depth + 1))
            return files
        except Exception as e:
            logger.warning(f"Error accessing {current_path}: {e}")
            return files

    def _should_process_path(self, path: Path, root_path: Path) -> bool:
        """Determine if a path should be processed based on patterns and rules."""
        try:
            rel_path = str(path.relative_to(root_path))
            
            # Always exclude .git directory
            if '.git' in path.parts:
                return False

            # Check if path matches exclude patterns
            if self._exclude_spec and self._exclude_spec.match_file(rel_path):
                return False

            # Check if path matches include patterns (if any are specified)
            if self._include_spec:
                return bool(self._include_spec.match_file(rel_path))

            return True
            
        except Exception as e:
            logger.error(f"Error checking path {path}: {e}")
            return False

    @staticmethod
    def _is_binary(chunk: bytes) -> bool:
        """Detect if content appears to be binary."""
        # First check for null bytes
        if b'\x00' in chunk:
            return True

        # Then check other binary signatures
        signatures = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF89a',  # GIF
            b'BM',  # BMP
            b'%PDF',  # PDF
            b'PK\x03\x04',  # ZIP
        ]
        
        if any(chunk.startswith(sig) for sig in signatures):
            return True

        # Count control characters and high ASCII
        control_chars = sum(1 for byte in chunk if byte < 32 and byte not in [9, 10, 13])  # tab, LF, CR
        high_chars = sum(1 for byte in chunk if byte > 127)
        
        # If more than 30% non-printable characters, consider it binary
        size = len(chunk)
        if size == 0:
            return False
            
        return (control_chars + high_chars) / size > 0.3

    def _setup_patterns(self, root_path: Path) -> None:
        """Set up pattern matching for includes/excludes and gitignore."""
        # Set up gitignore patterns
        gitignore_path = root_path / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path) as f:
                self._gitignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
        
        # Set up include/exclude patterns
        if self.config.include.files or self.config.include.dirs:
            self._include_spec = pathspec.PathSpec.from_lines('gitwildmatch', 
                self.config.include.files + self.config.include.dirs)
        
        if self.config.exclude.files or self.config.exclude.dirs:
            self._exclude_spec = pathspec.PathSpec.from_lines('gitwildmatch', 
                self.config.exclude.files + self.config.exclude.dirs)

    def read_file(self, file_path: Path) -> Optional[str]:
        """Read and return file content if it's a text file."""
        try:
            if not self._should_read_file(file_path):
                return None

            # Check file size before reading
            if file_path.stat().st_size > self.config.general.max_file_size_bytes:
                logger.warning(f"Skipping {file_path}: exceeds size limit")
                return None

            # Try reading as text
            try:
                return file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Fall back to detection
                content = file_path.read_bytes()
                detection = chardet.detect(content)
                if detection['confidence'] >= 0.7:
                    try:
                        return content.decode(detection['encoding'])
                    except UnicodeDecodeError:
                        pass
            return None
                
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            return None

    def _should_read_file(self, path: Path) -> bool:
        """Determine if a file should be read."""
        try:
            return (
                path.exists() and
                path.is_file() and
                path.suffix.lower() not in self.BINARY_EXTENSIONS and
                path.stat().st_size > 0
            )
        except Exception:
            return False