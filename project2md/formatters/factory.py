from typing import Union
from .base import BaseFormatter
from .markdown_formatter import MarkdownFormatter
from .json_formatter import JSONFormatter
from .yaml_formatter import YAMLFormatter
from ..config import Config, OutputFormat

def get_formatter(config: Config) -> BaseFormatter:
    """Get the appropriate formatter based on configuration."""
    format_map = {
        OutputFormat.MARKDOWN: MarkdownFormatter,
        OutputFormat.JSON: JSONFormatter,
        OutputFormat.YAML: YAMLFormatter,
    }
    
    # Convert string format to enum if necessary
    if isinstance(config.output.format, str):
        format_enum = OutputFormat(config.output.format.lower())
    else:
        format_enum = config.output.format
        
    formatter_class = format_map.get(format_enum, MarkdownFormatter)
    return formatter_class(config)
