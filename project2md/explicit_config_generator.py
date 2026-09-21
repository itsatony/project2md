import os
from pathlib import Path

import yaml

from .walker import FileSystemWalker


def generate_explicit_config(directory: Path, config, output_path: Path):
    # Create a walker with the final config. No progress bar here.
    walker = FileSystemWalker(config, progress=None)  # type: ignore[arg-type]
    # The include/exclude specs are lazily built by the walker's own entry
    # point; this generator bypasses that entry point, so build them here or
    # every path is judged against empty specs.
    walker._setup_patterns(directory)

    # Collect every file in the tree (ignoring internal max_depth)
    all_files = []
    for root, dirs, files in os.walk(directory):
        # .git is never a candidate, and walking it buries the real files.
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            if name.startswith("."):
                continue
            full_path = Path(root) / name
            all_files.append(full_path)

    # Build a textual "tree" overview for convenience
    tree_overview = _build_simple_tree(directory)

    # For each file, decide if included or excluded using walker logic
    entries = []
    for file_path in sorted(all_files):
        rel_path = str(file_path.relative_to(directory))
        # Use the walker's own include/exclude logic. This used to call a
        # method that does not exist (`_matches_include_exclude`) behind a bare
        # `except:`, so every entry was silently reported as excluded.
        try:
            is_included = walker._should_process_path(file_path, directory)
        except Exception:
            is_included = False

        # Get file size in KB and approximate char count
        size_kb = round(file_path.stat().st_size / 1024.0, 2)
        char_count = 0
        try:
            content = file_path.read_text(errors="ignore")
            char_count = len(content)
        except OSError:
            pass

        entries.append(
            {
                "path": rel_path,
                "include": bool(is_included),
                "comment": f"Size: {size_kb}KB, Chars: {char_count}",
            }
        )

    # Final YAML structure
    output_data = {"tree": tree_overview, "files": entries}

    with open(output_path, "w") as f:
        yaml.safe_dump(output_data, f, sort_keys=False)


def _build_simple_tree(directory: Path) -> str:
    """
    Make a minimal text tree of the directory structure.
    (Production code might rely on 'formatter' or a dedicated tree function.)
    """
    lines = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d != ".git"]
        depth = len(root.replace(str(directory), "").strip(os.sep).split(os.sep)) - 1
        indent = "  " * max(depth, 0)
        folder_name = Path(root).name
        if root == str(directory):
            folder_name = directory.name or "/"
        lines.append(f"{indent}{folder_name}/")
        for file in sorted(files):
            lines.append(f"{indent}  {file}")
    return "\n".join(lines)
