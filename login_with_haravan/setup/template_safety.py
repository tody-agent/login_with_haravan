from __future__ import annotations

from html import escape


def escape_template_context(value):
    """Recursively HTML-escape dynamic values for safe template rendering."""
    if isinstance(value, dict):
        return {key: escape_template_context(item) for key, item in value.items()}
    if isinstance(value, list):
        return [escape_template_context(item) for item in value]
    if isinstance(value, tuple):
        return tuple(escape_template_context(item) for item in value)
    if isinstance(value, str):
        return escape(value, quote=True)
    return value
