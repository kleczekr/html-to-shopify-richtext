# Shopify-RichText-Converter

Convert small fragments of HTML (e.g. taken from a CMS or WYSIWYG editor) into a JSON document that follows **Shopify's Rich Text metafield** schema _exactly_.

```bash
pip install shopify-richtext-converter
```

## Quick-start

```python
from shopify_richtext_converter import html_to_richtext

html = """
<h1>Title</h1>
<p>This is <strong>bold</strong>, <em>italic</em> and <a href='https://example.com'>a link</a>.</p>
<ul>
  <li>First item</li>
  <li>Second item</li>
</ul>
"""

richtext_json = html_to_richtext(html)
print(richtext_json)
```

The output is a Python `dict` ready to be *json-encoded* and sent to Shopify's Admin API.

## Features

* Paragraphs `<p>`
* Headings `<h1>` → `<h6>`
* Block quotes `<blockquote>`
* Ordered / unordered lists `<ol>`, `<ul>` with list-items `<li>`
* Inline markup: **bold**, *italic*, links

## License

MIT © You 