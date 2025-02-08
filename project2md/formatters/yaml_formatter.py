from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import yaml

from .base import BaseFormatter, FormatterError
from ..config import Config

class YAMLFormatter(BaseFormatter):
    """YAML output formatter with safe encoding."""

    def __init__(self, config: Config):
        super().__init__(config)  # Call parent init
    
    def generate_output(
        self,
        repo_path: Path,
        files: List[Tuple[Path, Optional[str]]],
        stats: Dict,
        output_path: Path
    ) -> None:
        """Generate YAML formatted output."""
        try:
            output = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "generator": "project2md",
                    "version": "1.2.0"
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

            # Use safe_dump to prevent arbitrary code execution
            output_path.write_text(
                yaml.safe_dump(
                    output,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                ),
                encoding='utf-8'
            )

        except Exception as e:
            raise FormatterError(f"Failed to generate YAML output: {str(e)}")

    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension."""
        return file_path.suffix.lower().lstrip('.') or 'unknown'

    def _find_readme_content(self, files: List[Tuple[Path, Optional[str]]]) -> Optional[str]:
        """Find README.md content."""
        for file_path, content in files:
            if file_path.name.lower() == "readme.md" and content:
                return content
        return None
