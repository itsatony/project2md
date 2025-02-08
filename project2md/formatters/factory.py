from typing import Type
from .base import BaseFormatter
from .json_formatter import JSONFormatter
from .yaml_formatter import YAMLFormatter
from .markdown_formatter import MarkdownFormatter
from ..config import Config, OutputFormat

def get_formatter(config: Config) -> BaseFormatter:
    """Get the appropriate formatter based on config."""
    formatters = {
        OutputFormat.JSON: JSONFormatter,
        OutputFormat.YAML: YAMLFormatter,
        OutputFormat.MARKDOWN: MarkdownFormatter
    }
    
    formatter_class = formatters.get(config.output.format)
    if not formatter_class:
        raise ValueError(f"No formatter available for format: {config.output.format}")
        
    return formatter_class(config)
