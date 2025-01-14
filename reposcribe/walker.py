# reposcribe/walker.py
from pathlib import Path
from typing import List, Tuple, Optional, Set
import logging
import pathspec
import chardet
from rich.progress import Progress
import os

from .config import Config

logger = logging.getLogger(__name__)

class WalkerError(Exception):
    """Custom exception for file system walker errors."""
    pass

class FileSystemWalker:
    """Handles repository traversal, file filtering, and content reading."""
    
    # Common binary file extensions
    BINARY_EXTENSIONS = {
        '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe', 
        '.obj', '.bin', '.pdf', '.jpg', '.jpeg', '.png', 
        '.gif', '.bmp', '.ico', '.db', '.sqlite', '.zip',
        '.tar', '.gz', '.7z', '.rar', '.jar', '.war',
        '.ear', '.class', '.mo', '.pkl', '.pyd'
    }

    def __init__(self, config: Config, progress: Progress):
        self.config = config
        self.progress = progress
        self._gitignore_spec = None
        self._include_spec = None
        self._exclude_spec = None

    def collect_files(self, root_path: Path) -> List[Path]:
        """
        Walk through the repository and collect files based on configuration.
        
        Args:
            root_path: Root directory to start traversal
            
        Returns:
            List of paths to process
            
        Raises:
            WalkerError: If there are issues during traversal
        """
        try:
            self._setup_patterns(root_path)
            
            files: List[Path] = []
            visited_dirs: Set[Path] = set()
            
            self.progress.update(self.progress.task_ids[1], description="Collecting files...")
            
            for current_path, depth in self._walk_directory(root_path):
                if depth > self.config.general.max_depth:
                    logger.debug(f"Skipping {current_path}: max depth exceeded")
                    continue
                
                # Skip if already visited (handles symlinks)
                if current_path in visited_dirs:
                    continue
                    
                visited_dirs.add(current_path)
                
                # Apply filters
                if not self._should_process_path(current_path, root_path):
                    continue
                
                if current_path.is_file():
                    files.append(current_path)
            
            logger.info(f"Collected {len(files)} files to process")
            return sorted(files)  # Sort for consistent output
            
        except Exception as e:
            raise WalkerError(f"Error collecting files: {str(e)}")

    def read_file(self, file_path: Path) -> Optional[str]:
        """
        Read and return file content if it's a text file and meets size requirements.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string or None if file should be skipped
        """
        try:
            if not self._should_read_file(file_path):
                return None
                
            # Read file content
            content = file_path.read_bytes()
            
            # Check file size
            if len(content) > self.config.general.max_file_size_bytes:
                logger.warning(f"Skipping {file_path}: exceeds size limit")
                return None
            
            # Detect encoding
            detection = chardet.detect(content)
            if detection['confidence'] < 0.7:
                logger.warning(f"Unreliable encoding detection for {file_path}")
                return None
            
            try:
                return content.decode(detection['encoding'])
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode {file_path} as text")
                return None
                
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {str(e)}")
            return None

    def _setup_patterns(self, root_path: Path) -> None:
        """Set up pattern matching for includes/excludes and gitignore."""
        # Setup gitignore patterns
        gitignore_path = root_path / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                self._gitignore_spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern,
                    f.readlines()
                )
        
        # Setup include patterns
        if self.config.include.files or self.config.include.dirs:
            patterns = self.config.include.files + self.config.include.dirs
            self._include_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern,
                patterns
            )
        
        # Setup exclude patterns
        if self.config.exclude.files or self.config.exclude.dirs:
            patterns = self.config.exclude.files + self.config.exclude.dirs
            self._exclude_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern,
                patterns
            )

    def _walk_directory(self, path: Path, depth: int = 0) -> List[Tuple[Path, int]]:
        """Walk directory recursively, yielding paths and their depths."""
        try:
            for item in path.iterdir():
                yield item, depth
                if item.is_dir() and not item.is_symlink():
                    yield from self._walk_directory(item, depth + 1)
        except PermissionError:
            logger.warning(f"Permission denied: {path}")
        except Exception as e:
            logger.warning(f"Error accessing {path}: {str(e)}")

    def _should_process_path(self, path: Path, root_path: Path) -> bool:
        """Determine if a path should be processed based on patterns and rules."""
        # Get relative path for pattern matching
        rel_path = str(path.relative_to(root_path))
        
        # Check gitignore
        if self._gitignore_spec and self._gitignore_spec.match_file(rel_path):
            return False
        
        # Check excludes
        if self._exclude_spec and self._exclude_spec.match_file(rel_path):
            return False
        
        # Check includes
        if self._include_spec:
            return self._include_spec.match_file(rel_path)
        
        return True

    def _should_read_file(self, path: Path) -> bool:
        """Determine if a file should be read based on type and extension."""
        # Skip binary files based on extension
        if path.suffix.lower() in self.BINARY_EXTENSIONS:
            return False
            
        # Skip empty files
        if path.stat().st_size == 0:
            return False
            
        # Try to read first few bytes to detect if binary
        try:
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                return not self._is_binary(chunk)
        except Exception:
            return False

    @staticmethod
    def _is_binary(chunk: bytes) -> bool:
        """Detect if content appears to be binary."""
        # Check for common binary signatures
        signatures = [
            b'\x00',  # Null bytes
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF89a',  # GIF
            b'BM',  # BMP
            b'%PDF',  # PDF
            b'PK\x03\x04',  # ZIP
        ]
        
        for sig in signatures:
            if chunk.startswith(sig):
                return True
        
        # Count null bytes and high ASCII characters
        null_count = chunk.count(b'\x00')
        high_ascii_count = len([b for b in chunk if b > 0x7f])
        
        # If more than 30% non-text characters, consider it binary
        suspicious_chars = null_count + high_ascii_count
        return suspicious_chars > (len(chunk) * 0.3)