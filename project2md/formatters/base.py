from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Dict, Optional

class FormatterError(Exception):
    """Custom exception for formatting errors."""
    pass

class BaseFormatter(ABC):
    """Base class for all formatters."""
    
    def __init__(self, config):
        self.config = config
        self._readme_content = None
        self._tree_cache = None
    
    @abstractmethod
    def generate_output(
        self,
        repo_path: Path,
        files: List[Tuple[Path, Optional[str]]],
        stats: dict,
        output_path: Path,
        run_info: dict = None
    ) -> None:
        """
        Generate output file.
        
        Args:
            repo_path: Path to the repository root
            files: List of (file_path, content) tuples
            stats: Statistics dictionary
            output_path: Path where to save the output
            run_info: Information about the current run
        """
        raise NotImplementedError("Subclasses must implement generate_output")

    def _find_readme_content(self, files: List[Tuple[Path, Optional[str]]]) -> Optional[str]:
        """Find README content in files."""
        for file_path, content in files:
            if file_path.name.lower() == "readme.md" and content:
                return content
        return None

    def _generate_tree(self, repo_path: Path, files: List[Tuple[Path, Optional[str]]]) -> str:
        """Generate tree structure."""
        if self._tree_cache is not None:
            return self._tree_cache

        class Node:
            def __init__(self, name: str):
                self.name = name
                self.children: Dict[str, 'Node'] = {}
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
