# project2md/formatters/json.py
from typing import List, Tuple, Optional
from pathlib import Path
import json
from .base import BaseFormatter

class JsonFormatter(BaseFormatter):
    """Formatter that generates JSON output."""
    
    def generate_output(
        self,
        repo_path: Path,
        files: List[Tuple[Path, Optional[str]]],
        stats: dict,
        output_path: Path,
        run_info: dict = None
    ) -> None:
        """Generate JSON output with run information."""
        data = {
            "metadata": {
                "repository_name": repo_path.name,
                "generated_by": "project2md",
                "generator_info": run_info or {},
                "timestamp": run_info.get('timestamp') if run_info else None,
                "signatures_mode": run_info.get('signatures_mode', False) if run_info else False
            },
            "project": {
                "name": repo_path.name,
                "path": str(repo_path)
            },
            "statistics": stats if self.config.general.stats_in_output else None,
            "files": []
        }
        
        # Add files data
        for file_path, content in files:
            relative_path = file_path.relative_to(repo_path)
            file_data = {
                "path": str(relative_path),
                "content": content
            }
            data["files"].append(file_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.console.print(f"[green]JSON output written to {output_path}[/green]")