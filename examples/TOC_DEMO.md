# Complete Documentation Guide 📚

[TOC]

## Introduction

This document demonstrates the Table of Contents feature. The `[TOC]` marker above automatically generates a clickable table of contents based on all headings in the document.

## Features

### Core Capabilities

The TOC feature provides:

- **Automatic Generation**: Simply add `[TOC]` anywhere in your document
- **Multi-level Support**: Supports all heading levels (H1-H6)
- **Clickable Links**: Every TOC entry is a clickable anchor
- **Permalink Support**: Each heading gets a permalink icon on hover

### Styling Features

The TOC comes with beautiful styling:

- GitHub-inspired design with subtle borders
- Hover effects for better UX
- Proper indentation for nested headings
- Responsive design

## Installation

### Prerequisites

Before installing, ensure you have:

1. Python 3.9 or higher
2. Poetry package manager
3. A modern web browser

### Installation Steps

#### Using pip

```bash
pip install markdown-viewer
```

#### Using Poetry

```bash
poetry add markdown-viewer
```

## Usage

### Basic Usage

The simplest way to use the viewer:

```bash
mdview README.md
```

### Advanced Options

#### Output to File

Save the HTML instead of opening in browser:

```bash
mdview document.md -o output.html --no-browser
```

#### Keep Temporary Files

Preserve the generated HTML:

```bash
mdview document.md --keep
```

## Configuration

### Environment Variables

You can configure the viewer using environment variables:

- `MDVIEW_THEME`: Set the color theme (default: light)
- `MDVIEW_PORT`: Set the server port (for full app mode)

### Custom Styling

To customize the appearance, you can:

1. Fork the repository
2. Modify the CSS in `cli.py`
3. Rebuild the package

## API Reference

### MarkdownProcessor Class

The core processing class:

#### Methods

##### process()

Process markdown content to HTML.

**Parameters:**
- `content` (str): The markdown content
- `options` (dict, optional): Processing options

**Returns:**
- `str`: The rendered HTML

##### get_toc()

Extract table of contents from markdown.

**Returns:**
- `list`: List of TOC entries

## Examples

### Example 1: Simple Document

A basic markdown file:

```markdown
# My Document

[TOC]

## Section 1
Content here...

## Section 2
More content...
```

### Example 2: Technical Documentation

Complex documentation with code:

```markdown
# API Documentation

[TOC]

## Authentication

### OAuth 2.0

Details...

### API Keys

More details...
```

### Example 3: Multi-level Structure

Deep nesting example:

```markdown
# Project

[TOC]

## Backend

### Database

#### PostgreSQL

##### Configuration

##### Optimization
```

## Troubleshooting

### Common Issues

#### TOC Not Appearing

If the TOC doesn't appear:

1. Ensure you have `[TOC]` in your document
2. Check that you have headings after the TOC marker
3. Verify the markdown is properly formatted

#### Links Not Working

If TOC links don't work:

1. Check for duplicate heading IDs
2. Ensure JavaScript is enabled
3. Try regenerating the document

### Debug Mode

Enable debug logging:

```bash
mdview --verbose document.md
```

## Best Practices

### Document Structure

Follow these guidelines:

1. **Use Logical Hierarchy**: H1 for title, H2 for main sections, H3 for subsections
2. **Unique Headings**: Avoid duplicate heading text
3. **TOC Placement**: Put `[TOC]` near the top, after the main title
4. **Descriptive Headers**: Use clear, descriptive heading text

### Performance

For optimal performance:

- Keep documents under 10,000 lines
- Use code fences for code blocks
- Optimize embedded images

### Accessibility

Make your documents accessible:

- Use semantic heading levels
- Provide alt text for images
- Ensure good color contrast

## Advanced Topics

### Custom Renderers

You can create custom renderers for special content types:

```python
from markdown_viewer.processors import MarkdownProcessor

processor = MarkdownProcessor()
html = processor.process(content)
```

### Plugin System

Extend functionality with plugins:

1. Create a Python module
2. Register your extension
3. Configure in `pyproject.toml`

### Integration

Integrate with other tools:

#### CI/CD Pipelines

```yaml
- name: Generate Docs
  run: mdview README.md -o docs/index.html --no-browser
```

#### Pre-commit Hooks

```yaml
- repo: local
  hooks:
    - id: markdown-viewer
      name: Validate Markdown
      entry: mdview
      language: system
```

## Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `poetry install`
3. Run tests: `poetry run pytest`
4. Make your changes
5. Submit a pull request

### Code Style

Follow the project conventions:

- PEP 8 for Python code
- ESLint for JavaScript
- Prettier for formatting

### Testing

Write tests for new features:

```python
def test_toc_generation():
    content = "# Title\n[TOC]\n## Section"
    html = processor.process(content)
    assert '<div class="toc">' in html
```

## Frequently Asked Questions

### General Questions

#### Q: Is this free?

A: Yes, this project is open source under the MIT license.

#### Q: What markdown flavors are supported?

A: We support GitHub Flavored Markdown (GFM) with extensions.

### Technical Questions

#### Q: Can I use custom CSS?

A: Yes, you can modify the template or use custom stylesheets.

#### Q: Does it work offline?

A: The CLI works offline, but CDN resources (math, diagrams) require internet.

### Feature Requests

#### Q: Will you add dark mode?

A: This is planned for a future release.

#### Q: Can it export to PDF?

A: Yes, using the full app mode with the export feature.

## Changelog

### Version 1.0.0

- Initial release
- TOC support
- Emoji rendering
- Math equations
- Mermaid diagrams

### Version 0.9.0

- Beta release
- Core features
- CLI tool

## License

This project is licensed under the MIT License.

## Acknowledgments

Special thanks to:

- The Python Markdown team
- PyMdown Extensions developers
- All contributors

## Contact

For questions or support:

- GitHub Issues: [github.com/dimpletz/markdown-viewer/issues](https://github.com/dimpletz/markdown-viewer/issues)
- Discord: Join our community

---

**Generated with** 💖 **by markdown-viewer**
