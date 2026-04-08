"""
Markdown processor with support for extensions, code highlighting, and diagrams.
"""

import markdown
from markdown.extensions import tables, fenced_code, codehilite, toc
from pymdownx import superfences, emoji, highlight
import pygments
from pygments.formatters import HtmlFormatter
from typing import Dict, List, Any, Optional


class MarkdownProcessor:
    """Process markdown content with various extensions."""
    
    def __init__(self, custom_extensions: Optional[List[str]] = None, 
                 custom_config: Optional[Dict[str, Any]] = None):
        """Initialize the markdown processor with extensions.
        
        Args:
            custom_extensions: Optional list of markdown extensions
            custom_config: Optional dictionary of extension configurations
        """
        self.extensions = custom_extensions or self._default_extensions()
        self.extension_configs = custom_config or self._default_config()
    
    def _default_extensions(self) -> List[str]:
        """Get default markdown extensions."""
        return [
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
            'markdown.extensions.md_in_html',
            'pymdownx.superfences',
            'pymdownx.highlight',
            'pymdownx.emoji',
            'pymdownx.tasklist',
            'pymdownx.arithmatex',
            'pymdownx.mark',
            'pymdownx.tilde',
            'pymdownx.caret',
            'pymdownx.keys',
            'pymdownx.magiclink',
        ]
    
    def _default_config(self) -> Dict[str, Any]:
        """Get default extension configurations."""
        return {
            'pymdownx.highlight': {
                'use_pygments': True,
                'linenums': True,
                'linenums_style': 'pymdownx-inline',
            },
            'pymdownx.superfences': {
                'custom_fences': [
                    {
                        'name': 'mermaid',
                        'class': 'mermaid',
                        'format': self._mermaid_formatter
                    }
                ]
            },
            'pymdownx.emoji': {
                'emoji_index': emoji.gemoji,
                'emoji_generator': emoji.to_svg,
                'options': {
                    'attributes': {
                        'align': 'absmiddle',
                        'height': '20px',
                        'width': '20px'
                    },
                    'image_path': 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/',
                    'non_standard_image_path': 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/'
                }
            },
            'pymdownx.arithmatex': {
                'generic': True
            },
            'markdown.extensions.toc': {
                'permalink': True,
                'permalink_title': 'Permalink to this heading',
                'toc_depth': '1-6',
                'title': 'Table of Contents'
            },
            'codehilite': {
                'css_class': 'highlight',
                'linenums': False
            }
        }
    
    def _mermaid_formatter(self, source, language, css_class, options, md, **kwargs):
        """Custom formatter for Mermaid diagrams."""
        return f'<div class="mermaid">\n{source}\n</div>'
    
    def process(self, content: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Process markdown content to HTML.
        
        Args:
            content: Markdown content string
            options: Optional dictionary of processing options
            
        Returns:
            HTML string
        """
        if options is None:
            options = {}
        
        # Create markdown instance with extensions
        md = markdown.Markdown(
            extensions=self.extensions,
            extension_configs=self.extension_configs,
            output_format='html5'
        )
        
        # Process the markdown
        html = md.convert(content)
        
        # Get CSS for syntax highlighting
        css = self._get_highlight_css()
        
        # Wrap in a complete HTML document if requested
        if options.get('full_html', False):
            html = self._wrap_html(html, css, options)
        
        return html
    
    def _get_highlight_css(self):
        """Get CSS for syntax highlighting."""
        formatter = HtmlFormatter(style='monokai')
        return formatter.get_style_defs('.highlight')
    
    def _wrap_html(self, content, css, options):
        """Wrap content in a complete HTML document."""
        title = options.get('title', 'Markdown Document')
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        
        pre {{
            background-color: #272822;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        
        code {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        
        blockquote {{
            border-left: 4px solid #ccc;
            margin: 20px 0;
            padding-left: 20px;
            color: #666;
        }}
        
        {css}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
</head>
<body>
    {content}
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>"""
