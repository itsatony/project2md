"""
Signature processor for extracting function signatures and markdown headers.
"""
import re
from pathlib import Path
from typing import Optional, List, Tuple
import ast


class SignatureProcessor:
    """Processes files to extract signatures based on file type."""
    
    def __init__(self):
        self.code_extensions = {
            '.py': self._process_python,
            '.js': self._process_javascript,
            '.ts': self._process_typescript,
            '.java': self._process_java,
            '.cpp': self._process_cpp,
            '.c': self._process_cpp,
            '.hpp': self._process_cpp,
            '.h': self._process_cpp,
            '.cs': self._process_csharp,
            '.go': self._process_go,
            '.rs': self._process_rust,
            '.php': self._process_php,
            '.rb': self._process_ruby,
        }
    
    def process_file(self, file_path: Path, content: str) -> str:
        """Process a file and return its signature version."""
        if not content:
            return content
            
        suffix = file_path.suffix.lower()
        
        # Handle markdown files
        if suffix == '.md':
            return self._process_markdown(content)
        
        # Handle code files
        if suffix in self.code_extensions:
            return self.code_extensions[suffix](content)
        
        # For other file types, return original content
        return content
    
    def _process_markdown(self, content: str) -> str:
        """Extract headers from markdown and count section lines."""
        lines = content.split('\n')
        result = []
        current_header_level = 0
        section_start = 0
        
        for i, line in enumerate(lines):
            if line.startswith('#'):
                # If we have a previous section, add line count
                if current_header_level > 0:
                    section_lines = i - section_start
                    if result and not result[-1].endswith(']'):
                        result[-1] += f" [lines:{section_lines}]"
                
                # Add the current header
                header_level = len(line) - len(line.lstrip('#'))
                result.append(line)
                current_header_level = header_level
                section_start = i + 1
        
        # Handle the last section
        if current_header_level > 0 and result:
            section_lines = len(lines) - section_start
            if not result[-1].endswith(']'):
                result[-1] += f" [lines:{section_lines}]"
        
        return '\n'.join(result)
    
    def _process_python(self, content: str) -> str:
        """Extract Python function and class signatures."""
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            result = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    signature = self._get_python_function_signature(node, lines)
                    line_count = self._count_function_lines(node, lines)
                    result.append(f"{signature} [lines:{line_count}]")
                elif isinstance(node, ast.ClassDef):
                    signature = self._get_python_class_signature(node, lines)
                    line_count = self._count_class_lines(node, lines)
                    result.append(f"{signature} [lines:{line_count}]")
            
            return '\n'.join(result)
        except SyntaxError:
            # If parsing fails, use regex fallback
            return self._process_python_regex(content)
    
    def _get_python_function_signature(self, node, lines) -> str:
        """Get Python function signature from AST node."""
        line_num = node.lineno - 1
        signature_lines = []
        
        # Get the function definition line(s)
        for i in range(line_num, min(line_num + 10, len(lines))):
            line = lines[i].strip()
            signature_lines.append(line)
            if line.endswith(':'):
                break
        
        return ' '.join(signature_lines)
    
    def _get_python_class_signature(self, node, lines) -> str:
        """Get Python class signature from AST node."""
        line_num = node.lineno - 1
        return lines[line_num].strip()
    
    def _count_function_lines(self, node, lines) -> int:
        """Count lines in a Python function."""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        
        # Fallback: estimate based on indentation
        start_line = node.lineno
        for i in range(start_line, len(lines)):
            line = lines[i]
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                return i - start_line + 1
        
        return len(lines) - start_line + 1
    
    def _count_class_lines(self, node, lines) -> int:
        """Count lines in a Python class."""
        return self._count_function_lines(node, lines)
    
    def _process_python_regex(self, content: str) -> str:
        """Fallback Python processing using regex."""
        lines = content.split('\n')
        result = []
        
        func_pattern = re.compile(r'^(\s*)(def|async def)\s+([^:]+):')
        class_pattern = re.compile(r'^(\s*)class\s+([^:]+):')
        
        for i, line in enumerate(lines):
            func_match = func_pattern.match(line)
            class_match = class_pattern.match(line)
            
            if func_match or class_match:
                # Count lines for this function/class
                indent_level = len(func_match.group(1)) if func_match else len(class_match.group(1))
                line_count = self._count_lines_by_indent(lines, i, indent_level)
                result.append(f"{line.strip()} [lines:{line_count}]")
        
        return '\n'.join(result)
    
    def _process_javascript(self, content: str) -> str:
        """Extract JavaScript function signatures."""
        lines = content.split('\n')
        result = []
        
        patterns = [
            re.compile(r'^(\s*)(function\s+\w+\s*\([^)]*\))'),
            re.compile(r'^(\s*)(\w+\s*:\s*function\s*\([^)]*\))'),
            re.compile(r'^(\s*)(const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>'),
            re.compile(r'^(\s*)(async\s+function\s+\w+\s*\([^)]*\))'),
            re.compile(r'^(\s*)(\w+\s*\([^)]*\))\s*{'),
        ]
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                match = pattern.match(line)
                if match:
                    indent_level = len(match.group(1))
                    line_count = self._count_lines_by_braces(lines, i)
                    result.append(f"{line.strip()} [lines:{line_count}]")
                    break
        
        return '\n'.join(result)
    
    def _process_typescript(self, content: str) -> str:
        """Extract TypeScript function signatures."""
        # TypeScript is similar to JavaScript with type annotations
        return self._process_javascript(content)
    
    def _process_java(self, content: str) -> str:
        """Extract Java method signatures."""
        lines = content.split('\n')
        result = []
        
        method_pattern = re.compile(r'^(\s*)(public|private|protected|static|\s).*\s+\w+\s*\([^)]*\)\s*{?')
        
        for i, line in enumerate(lines):
            if method_pattern.match(line) and '{' in line:
                indent_level = len(line) - len(line.lstrip())
                line_count = self._count_lines_by_braces(lines, i)
                result.append(f"{line.strip()} [lines:{line_count}]")
        
        return '\n'.join(result)
    
    def _process_cpp(self, content: str) -> str:
        """Extract C++ function signatures."""
        lines = content.split('\n')
        result = []
        
        func_pattern = re.compile(r'^(\s*)[\w\s\*&:<>]+\s+\w+\s*\([^)]*\)\s*{')
        
        for i, line in enumerate(lines):
            if func_pattern.match(line):
                indent_level = len(line) - len(line.lstrip())
                line_count = self._count_lines_by_braces(lines, i)
                result.append(f"{line.strip()} [lines:{line_count}]")
        
        return '\n'.join(result)
    
    def _process_csharp(self, content: str) -> str:
        """Extract C# method signatures."""
        return self._process_java(content)  # Similar structure to Java
    
    def _process_go(self, content: str) -> str:
        """Extract Go function signatures."""
        lines = content.split('\n')
        result = []
        
        func_pattern = re.compile(r'^(\s*)func\s+(\([^)]*\)\s*)?\w+\s*\([^)]*\).*{')
        
        for i, line in enumerate(lines):
            if func_pattern.match(line):
                indent_level = len(line) - len(line.lstrip())
                line_count = self._count_lines_by_braces(lines, i)
                result.append(f"{line.strip()} [lines:{line_count}]")
        
        return '\n'.join(result)
    
    def _process_rust(self, content: str) -> str:
        """Extract Rust function signatures."""
        lines = content.split('\n')
        result = []
        
        func_pattern = re.compile(r'^(\s*)(pub\s+)?fn\s+\w+.*{')
        
        for i, line in enumerate(lines):
            if func_pattern.match(line):
                indent_level = len(line) - len(line.lstrip())
                line_count = self._count_lines_by_braces(lines, i)
                result.append(f"{line.strip()} [lines:{line_count}]")
        
        return '\n'.join(result)
    
    def _process_php(self, content: str) -> str:
        """Extract PHP function signatures."""
        lines = content.split('\n')
        result = []
        
        func_pattern = re.compile(r'^(\s*)(public|private|protected|\s)*function\s+\w+\s*\([^)]*\)')
        
        for i, line in enumerate(lines):
            if func_pattern.match(line):
                indent_level = len(line) - len(line.lstrip())
                line_count = self._count_lines_by_braces(lines, i)
                result.append(f"{line.strip()} [lines:{line_count}]")
        
        return '\n'.join(result)
    
    def _process_ruby(self, content: str) -> str:
        """Extract Ruby method signatures."""
        lines = content.split('\n')
        result = []
        
        func_pattern = re.compile(r'^(\s*)def\s+\w+.*')
        
        for i, line in enumerate(lines):
            if func_pattern.match(line):
                indent_level = len(line) - len(line.lstrip())
                line_count = self._count_lines_by_indent(lines, i, indent_level)
                result.append(f"{line.strip()} [lines:{line_count}]")
        
        return '\n'.join(result)
    
    def _count_lines_by_braces(self, lines: List[str], start_line: int) -> int:
        """Count lines until matching closing brace."""
        brace_count = 0
        line_count = 0
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            line_count += 1
            
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0 and i > start_line:
                break
        
        return line_count
    
    def _count_lines_by_indent(self, lines: List[str], start_line: int, base_indent: int) -> int:
        """Count lines until indentation returns to base level or less."""
        line_count = 1
        
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            
            if line.strip() == '':
                line_count += 1
                continue
            
            current_indent = len(line) - len(line.lstrip())
            
            if current_indent <= base_indent:
                break
            
            line_count += 1
        
        return line_count
