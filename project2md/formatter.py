# project2md/formatter.py
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging
from datetime import datetime
import json
from textwrap import dedent

from .config import Config, OutputFormat

logger = logging.getLogger(__name__)

class FormatterError(Exception):
    """Custom exception for formatting errors."""
    pass

class MarkdownFormatter:
    """Handles the generation of the output documentation."""

    def __init__(self, config: Config):
        self.config = config
        self._readme_content: Optional[str] = None
        self._tree_cache: Optional[str] = None

    def generate_output(
        self,
        repo_path: Path,
        files: List[Tuple[Path, Optional[str]]],
        stats: Dict,
        output_path: Path
    ) -> None:
        """
        Generate the output documentation file.
        
        Args:
            repo_path: Root path of the repository
            files: List of tuples containing file paths and their contents
            stats: Dictionary containing repository statistics
            output_path: Path where the output should be written
        """
        try:
            if self.config.output.format == OutputFormat.MARKDOWN:
                content = self._generate_markdown(repo_path, files, stats)
            elif self.config.output.format == OutputFormat.JSON:
                content = self._generate_json(repo_path, files, stats)
            else:
                raise FormatterError(f"Unsupported output format: {self.config.output.format}")

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write output
            output_path.write_text(content, encoding='utf-8')
            logger.info(f"Documentation written to {output_path}")
            
        except Exception as e:
            raise FormatterError(f"Failed to generate output: {str(e)}")

    def _generate_markdown(
        self,
        repo_path: Path,
        files: List[Tuple[Path, Optional[str]]],
        stats: Dict
    ) -> str:
        """Generate Markdown formatted output."""
        sections = []
        
        # Project Overview
        sections.append("# Project Overview\n")

        # Add README content if available
        readme_content = self._find_readme_content(files)
        if readme_content:
            sections.append("## README.md Content\n\n````markdown\n{}\n````\n".format(readme_content))

        # Add project tree
        tree = self._generate_tree(repo_path, files)
        sections.append("## Project Structure\n\n```tree\n{}\n```\n".format(tree))

        # Add statistics if enabled
        if self.config.output.stats:
            sections.append(self._format_stats(stats))

        # Add file contents
        sections.append("## File Contents\n")
        for file_path, content in files:
            if content is not None and file_path.name != "README.md":  # Skip README as it's already included
                rel_path = file_path.relative_to(repo_path)
                lang_tag = self._get_language_tag(file_path)
                
                # Use four backticks for markdown files to handle nested markdown content
                if lang_tag == 'markdown':
                    sections.append(f"### filepath {rel_path}\n\n````{lang_tag}\n{content}\n````\n")
                else:
                    sections.append(f"### filepath {rel_path}\n\n```{lang_tag}\n{content}\n```\n")

        # Add generation metadata
        sections.append("---\nGenerated by project2md on {}\n".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        return "\n".join(sections)

    def _generate_json(
        self,
        repo_path: Path,
        files: List[Tuple[Path, Optional[str]]],
        stats: Dict
    ) -> str:
        """Generate JSON formatted output."""
        output = {
            "project_overview": {
                "readme": self._find_readme_content(files),
                "tree": self._generate_tree(repo_path, files)
            },
            "statistics": stats,
            "files": [
                {
                    "path": str(f.relative_to(repo_path)),
                    "content": content
                }
                for f, content in files
                if content is not None
            ],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "project2md"
            }
        }
        return json.dumps(output, indent=2)

    def _find_readme_content(self, files: List[Tuple[Path, Optional[str]]]) -> Optional[str]:
        """Find and return README content from files."""
        if self._readme_content is None:
            for file_path, content in files:
                if file_path.name.lower() == "readme.md" and content:
                    self._readme_content = content
                    break
        return self._readme_content

    def _generate_tree(self, repo_path: Path, files: List[Tuple[Path, Optional[str]]]) -> str:
        """Generate a tree representation of the repository structure."""
        if self._tree_cache is not None:
            return self._tree_cache

        class Node:
            def __init__(self, name: str):
                self.name = name
                self.children: Dict[str, Node] = {}
                self.is_file = False

        # Build tree structure
        root = Node(repo_path.name)
        for file_path, _ in files:
            current = root
            parts = file_path.relative_to(repo_path).parts
            
            for part in parts[:-1]:
                if part not in current.children:
                    current.children[part] = Node(part)
                current = current.children[part]
            
            # Add file
            file_name = parts[-1]
            current.children[file_name] = Node(file_name)
            current.children[file_name].is_file = True

        # Generate tree string
        lines = []
        def _add_node(node: Node, prefix: str = "", is_last: bool = True) -> None:
            lines.append(f"{prefix}{'└── ' if is_last else '├── '}{node.name}")
            children = sorted(node.children.values(), key=lambda x: (not x.is_file, x.name))
            for i, child in enumerate(children):
                new_prefix = prefix + ("    " if is_last else "│   ")
                _add_node(child, new_prefix, i == len(children) - 1)

        _add_node(root)
        self._tree_cache = "\n".join(lines)
        return self._tree_cache

    def _format_stats(self, stats: Dict) -> str:
        """Format statistics as Markdown."""
        # Format file types separately
        file_types_str = "\n  ".join(
            f"- {ext}: {count}" for ext, count in stats.get('file_types', {}).items()
        )
        
        # Create stats dict without file_types to avoid format conflicts
        format_stats = stats.copy()
        format_stats.pop('file_types', None)
        format_stats['file_types_list'] = file_types_str
        
        return dedent("""
            ## Project Statistics

            - Total Files: {total_files}
            - Text Files: {text_files}
            - Binary Files: {binary_files}
            - Repository Size: {repo_size}
            - Current Branch: {branch}
            - Most Common File Types:
              {file_types_list}
            """).format(**format_stats)

    @staticmethod
    def _get_language_tag(file_path: Path) -> str:
        """Determine the language tag for syntax highlighting."""
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'jsx',
            '.ts': 'typescript',
            '.tsx': 'tsx',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql',
            '.sh': 'bash',
            '.bash': 'bash',
            '.md': 'markdown',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
        }
        return extensions.get(file_path.suffix.lower(), '')