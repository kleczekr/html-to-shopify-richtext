"""shopify_richtext_converter
============================
A tiny helper library that converts HTML fragments into Shopify-compatible
Rich Text JSON.

>>> from shopify_richtext_converter import html_to_richtext
>>> html_to_richtext('<p><strong>Hello</strong> <em>world</em></p>')
{"type": "root", "children": [...]}  # trimmed for brevity
"""

from .converter import html_to_richtext  # noqa: F401 re-export

__all__ = ["html_to_richtext"] 