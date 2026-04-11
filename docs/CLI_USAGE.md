# Markdown Viewer CLI

Beautiful markdown renderer with GitHub emoji support, Mermaid diagrams, KaTeX math, and syntax highlighting.

## Installation

### From PyPI (Recommended)

```bash
pip install markdown-viewer-app
```

### From Source

```bash
git clone https://github.com/dimpletz/markdown-viewer.git
cd markdown-viewer
pip install .
```

## Usage

### Basic Usage

```bash
# Render and open in browser
mdview README.md

# Render without opening browser
mdview README.md --no-browser

# Save to specific file
mdview README.md -o output.html

# Keep output as README.html
mdview README.md --keep
```

### CI/CD Usage

Perfect for automated documentation generation:

```bash
# Generate HTML for deployment
mdview docs/report.md --no-browser --keep

# Or save to specific location
mdview docs/report.md -o dist/report.html --no-browser
```

### GitHub Actions Example

```yaml
name: Generate Docs

on: [push]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install markdown-viewer-app
        run: pip install markdown-viewer-app
      
      - name: Generate HTML
        run: mdview README.md -o docs/index.html --no-browser
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

## Features

✅ **GitHub Flavored Markdown** - Full GFM support  
✅ **GitHub Emojis** - `:rocket:` :rocket: `:heart:` :heart:  
✅ **Mermaid Diagrams** - Flowcharts, sequence diagrams, etc.  
✅ **KaTeX Math** - Beautiful mathematical equations  
✅ **Syntax Highlighting** - 200+ languages via Pygments  
✅ **Tables, Task Lists** - All standard markdown extensions  
✅ **Beautiful Styling** - GitHub-like rendering  
✅ **No Server Required** - Pure HTML output  

## Advanced Usage

### Show Help

```bash
mdview --help
```

### Version

```bash
mdview --version
```

## Full Application

For the full desktop application with export (PDF/Word) and translation features:

```bash
# Install with full dependencies
pip install markdown-viewer-app
```

## Development

```bash
# Clone repository
git clone https://github.com/dimpletz/markdown-viewer.git
cd markdown-viewer

# Install in development mode
pip install -e .

# Run tests
pytest
```

## Publishing to PyPI

```bash
# Build the package
poetry build

# Publish to PyPI
poetry publish
```

Or use twine:

```bash
python -m build
twine upload dist/*
```

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or pull request.
