from ..config import Config, OutputFormat
from .base import BaseFormatter
from .json_formatter import JSONFormatter
from .markdown_formatter import MarkdownFormatter
from .yaml_formatter import YAMLFormatter


def get_formatter(config: Config) -> BaseFormatter:
    """Get the appropriate formatter based on configuration."""
    format_map: dict[OutputFormat, type[BaseFormatter]] = {
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
