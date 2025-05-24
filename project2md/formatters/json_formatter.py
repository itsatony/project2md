import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from .base import BaseFormatter, FormatterError
from ..config import Config

class JSONFormatter(BaseFormatter):
    """JSON output formatter with safe encoding."""

    def __init__(self, config: Config):
        super().__init__(config)  # Call parent init
    
    def generate_output(
        self,
        repo_path: Path,
        files: List[Tuple[Path, Optional[str]]],
        stats: Dict,
        output_path: Path,
        run_info: dict = None
    ) -> None:
        """Generate JSON formatted output."""
        try:
            output = {
                "metadata": {
                    "generated_at": run_info.get('timestamp') if run_info else datetime.now().isoformat(),
                    "generator": "project2md",
                    "version": run_info.get('version', '1.2.0') if run_info else '1.2.0',
                    "signatures_mode": run_info.get('signatures_mode', False) if run_info else False,
                    "output_format": run_info.get('output_format', 'json') if run_info else 'json',
                    "pypi_url": run_info.get('pypi_url', 'https://pypi.org/project/project2md') if run_info else 'https://pypi.org/project/project2md',
                    "github_url": run_info.get('github_url', 'https://github.com/itsatony/project2md') if run_info else 'https://github.com/itsatony/project2md'
                },
                "project": {
                    "readme": self._find_readme_content(files),
                    "structure": self._generate_tree(repo_path, files),
                    "statistics": stats
                },
                "files": [
                    {
                        "path": str(f.relative_to(repo_path)),
                        "content": content,
                        "type": self._get_file_type(f)
                    }
                    for f, content in files
                    if content is not None
                ]
            }

            # Validate JSON before writing
            json.dumps(output)  # Test serialization
            
            # Write with proper formatting
            output_path.write_text(
                json.dumps(output, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )

        except Exception as e:
            raise FormatterError(f"Failed to generate JSON output: {str(e)}")

    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension."""
        return file_path.suffix.lower().lstrip('.') or 'unknown'

    def _find_readme_content(self, files: List[Tuple[Path, Optional[str]]]) -> Optional[str]:
        """Find README.md content."""
        for file_path, content in files:
            if file_path.name.lower() == "readme.md" and content:
                return content
        return None
