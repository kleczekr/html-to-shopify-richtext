from __future__ import annotations

"""shopify_richtext_converter.converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Core conversion utilities used by the public API exposed in the top-level
package.  At the moment this single module contains the main helper
`html_to_richtext` which converts a fragment of HTML into a Python dict that
adheres to Shopify's Rich Text metafield JSON schema.
"""

from typing import Dict, List, Union, Optional
from bs4 import BeautifulSoup, NavigableString, Tag

RichTextNode = Dict[str, Union[str, int, bool, List["RichTextNode"], None]]

__all__ = ["html_to_richtext"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _text_node(value: str, *, bold: bool = False, italic: bool = False) -> RichTextNode:
    """Return a Shopify text node, removing surrounding whitespace."""

    node: RichTextNode = {
        "type": "text",
        "value": value.strip("\n"),
    }
    if bold:
        node["bold"] = True
    if italic:
        node["italic"] = True
    return node


def _parse_inline(
    element: Union[Tag, NavigableString],
    *,
    bold: bool = False,
    italic: bool = False,
) -> List[RichTextNode]:
    """Recursively parse inline-level *element* into Rich Text child nodes.

    The *bold* and *italic* flags track inherited formatting when nested
    `<strong>`/`<b>` or `<em>`/`<i>` tags appear.
    """

    # NavigableString (raw text) ------------------------------------------------
    if isinstance(element, NavigableString):
        text = str(element)
        if not text.strip():
            return []  # Skip pure whitespace
        return [_text_node(text, bold=bold, italic=italic)]

    # If the element itself is a formatting tag, merge context ---------------
    tag_name = element.name.lower()

    if tag_name in {"strong", "b"}:
        bold = True
    elif tag_name in {"em", "i"}:
        italic = True

    # <a> ---------------------------------------------------------------------
    if tag_name == "a":
        # Collect children first so we don't lose nested formatting inside link
        children: List[RichTextNode] = []
        for child in element.contents:
            children.extend(_parse_inline(child, bold=bold, italic=italic))

        return [
            {
                "type": "link",
                "url": element.get("href"),
                "title": element.get("title"),
                "target": element.get("target"),
                "children": children if children else [_text_node(element.get_text(), bold=bold, italic=italic)],
            }
        ]

    # Generic inline container ------------------------------------------------
    children: List[RichTextNode] = []
    for child in element.contents:
        children.extend(_parse_inline(child, bold=bold, italic=italic))
    return children


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def html_to_richtext(html_content: str) -> RichTextNode:
    """Convert an HTML fragment to Shopify Rich Text JSON represented as dict.

    The conversion follows Shopify's *exact* schema. Block-level elements
    supported:

    • Paragraphs      (<p>)
    • Headings        (<h1> … <h6>)
    • Lists           (<ul>, <ol>)
    • List items      (<li>)
    • Block quotes    (<blockquote>)

    Inline-level formatting recognised:

    • Bold            (<strong>, <b>)
    • Italic          (<em>, <i>)
    • Hyperlinks      (<a href="…">)

    If *html_content* is empty or contains no recognised blocks an empty root
    with no children is returned.
    """

    if not html_content:
        return {"type": "root", "children": []}

    soup = BeautifulSoup(html_content, "html.parser")

    # Determine the top-level iterable (inside <body> if present) -------------
    top_level = soup.body.contents if soup.body else soup.contents

    root_children: List[RichTextNode] = []

    for node in top_level:
        # ------------------------------------------------------------------
        # Skip whitespace / comments etc.
        # ------------------------------------------------------------------
        if isinstance(node, NavigableString):
            if node.strip():
                # Stray text at top level gets wrapped in <p>
                paragraph_children = _parse_inline(node)
                root_children.append({"type": "paragraph", "children": paragraph_children})
            continue

        tag_name = node.name.lower()

        # -------------------------- Headings ------------------------------
        if tag_name in {f"h{i}" for i in range(1, 7)}:
            level = int(tag_name[1])
            children = _parse_inline(node)
            root_children.append({"type": "heading", "level": level, "children": children})
            continue

        # ------------------------- Paragraphs -----------------------------
        if tag_name == "p":
            children = _parse_inline(node)
            root_children.append({"type": "paragraph", "children": children})
            continue

        # ----------------------------- Lists ------------------------------
        if tag_name in {"ul", "ol"}:
            list_type = "unordered" if tag_name == "ul" else "ordered"
            items: List[RichTextNode] = []
            for li in node.find_all("li", recursive=False):
                li_children = _parse_inline(li)
                if li_children:
                    items.append({"type": "list-item", "children": li_children})
            if items:
                root_children.append({"type": "list", "listType": list_type, "children": items})
            continue

        # -------------------------- Block quote ---------------------------
        if tag_name == "blockquote":
            quote_children = _parse_inline(node)
            root_children.append({"type": "quote", "children": [{"type": "paragraph", "children": quote_children}]})
            continue

        # ------------------ Fallback: treat as paragraph ------------------
        children = _parse_inline(node)
        root_children.append({"type": "paragraph", "children": children})

    return {"type": "root", "children": root_children} 