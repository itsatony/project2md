# project2md/stats.py
from pathlib import Path
from typing import Dict, Optional, Set
import logging
from collections import Counter
import humanize

logger = logging.getLogger(__name__)

class StatsCollector:
    """Collects and manages repository statistics."""

    def __init__(self):
        self._total_files = 0
        self._text_files = 0
        self._binary_files = 0
        self._total_size = 0
        self._file_types = Counter()
        self._languages = Counter()
        self._processed_paths: Set[Path] = set()
        
        # Track largest files
        self._largest_files: Dict[Path, int] = {}
        self._max_largest_files = 5

    def process_file(self, file_path: Path, content: Optional[str]) -> None:
        """
        Process a file and update statistics.
        
        Args:
            file_path: Path to the file
            content: File content if text file, None if binary
        """
        if file_path in self._processed_paths:
            return
            
        self._processed_paths.add(file_path)
        self._total_files += 1
        
        # Get file size
        size = file_path.stat().st_size
        self._total_size += size
        
        # Track largest files
        self._update_largest_files(file_path, size)
        
        # Update file type statistics
        extension = file_path.suffix.lower()
        self._file_types[extension] += 1
        
        # Determine if text or binary
        if content is not None:
            self._text_files += 1
            self._update_language_stats(file_path, content)
        else:
            self._binary_files += 1

    def get_stats(self, branch: str = "unknown") -> Dict:
        """
        Get collected statistics.
        
        Args:
            branch: Current git branch name
            
        Returns:
            Dictionary containing all collected statistics
        """
        stats = {
            "total_files": self._total_files,
            "text_files": self._text_files,
            "binary_files": self._binary_files,
            "repo_size": humanize.naturalsize(self._total_size),
            "branch": branch,
            "file_types": dict(self._file_types.most_common()),
            "languages": dict(self._languages.most_common(10)),  # Top 10 languages
            "largest_files": {
                str(path): humanize.naturalsize(size)
                for path, size in sorted(
                    self._largest_files.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            }
        }
        
        # Add percentage calculations
        if self._total_files > 0:
            stats.update({
                "text_files_percentage": round(self._text_files / self._total_files * 100, 1),
                "binary_files_percentage": round(self._binary_files / self._total_files * 100, 1)
            })
            
        # Add file type percentages
        total_by_type = sum(stats["file_types"].values())
        if total_by_type > 0:
            stats["file_types_percentage"] = {
                ext: round(count / total_by_type * 100, 1)
                for ext, count in stats["file_types"].items()
            }
            
        return stats

    def _update_largest_files(self, file_path: Path, size: int) -> None:
        """Update tracking of largest files."""
        self._largest_files[file_path] = size
        if len(self._largest_files) > self._max_largest_files:
            # Remove smallest file from tracking
            smallest = min(self._largest_files.items(), key=lambda x: x[1])[0]
            del self._largest_files[smallest]

    def _update_language_stats(self, file_path: Path, content: str) -> None:
        """Update programming language statistics based on file content."""
        extension = file_path.suffix.lower()
        
        # Map extensions to languages
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.sh': 'Shell',
            '.pl': 'Perl',
            '.lua': 'Lua'
        }
        
        if extension in language_map:
            self._languages[language_map[extension]] += 1
            return
            
        # Special cases
        if extension == '.md':
            self._languages['Markdown'] += 1
        elif extension == '.json':
            self._languages['JSON'] += 1
        elif extension == '.xml':
            self._languages['XML'] += 1
        elif extension == '.yml' or extension == '.yaml':
            self._languages['YAML'] += 1
        elif extension == '.html':
            self._languages['HTML'] += 1
        elif extension == '.css':
            self._languages['CSS'] += 1

    def merge(self, other: 'StatsCollector') -> None:
        """Merge statistics from another collector."""
        self._total_files += other._total_files
        self._text_files += other._text_files
        self._binary_files += other._binary_files
        self._total_size += other._total_size
        self._file_types.update(other._file_types)
        self._languages.update(other._languages)
        self._processed_paths.update(other._processed_paths)
        
        # Merge largest files
        for path, size in other._largest_files.items():
            self._update_largest_files(path, size)