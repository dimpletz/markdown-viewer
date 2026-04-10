# Export & Share Quick Reference Card

## ✅ All Features Working!

### 📄 Export to PDF
```bash
# Default output (same name as input)
mdview README.md --export-pdf
# → Creates: README.pdf

# Custom filename  
mdview README.md --export-pdf report.pdf
# → Creates: report.pdf
```

### 📝 Export to Word
```bash
# Default output (same name as input)
mdview README.md --export-word
# → Creates: README.docx

# Custom filename
mdview README.md --export-word document.docx
# → Creates: document.docx
```

### 📧 Share as PDF
```bash
mdview README.md --share-pdf
# → Creates: README.pdf
# → Opens email client
# → Shows attachment path
```

### 📧 Share as Word
```bash
mdview README.md --share-word
# → Creates: README.docx
# → Opens email client
# → Shows attachment path
```

### 🎯 Combined Operations
```bash
# Export to both PDF and Word
mdview README.md --export-pdf --export-word
# → Creates: README.pdf AND README.docx

# Export + Render HTML
mdview README.md --export-pdf --keep
# → Creates: README.pdf AND README.html
# → Opens in browser

# Export all formats
mdview README.md --export-pdf --export-word --keep
# → Creates: README.pdf, README.docx, AND README.html
```

## 📋 Command Summary

| Command | Result |
|---------|--------|
| `mdview file.md` | Render & open in browser |
| `mdview file.md --export-pdf` | Export to PDF |
| `mdview file.md --export-word` | Export to Word |
| `mdview file.md --share-pdf` | Export PDF + open email |
| `mdview file.md --share-word` | Export Word + open email |
| `mdview file.md --export-pdf --export-word` | Export to both formats |
| `mdview file.md --no-browser --keep` | HTML only (for CI/CD) |

## 🎨 What Gets Exported

### PDF Export Includes:
- ✅ Emojis (scaled with text)
- ✅ Mathematical equations (KaTeX)
- ✅ Mermaid diagrams
- ✅ Syntax highlighting
- ✅ Tables & task lists
- ✅ Table of Contents (if `[TOC]` used)
- ✅ GitHub-style formatting

### Word Export Includes:
- ✅ Heading hierarchy (H1-H6)
- ✅ Paragraphs with formatting
- ✅ Bulleted & numbered lists
- ✅ Code blocks (monospace)
- ✅ Tables
- ✅ Blockquotes
- ✅ Table of Contents links (as text)

## 📦 Installation Requirements

### Basic (HTML only)
```bash
pip install markdown-viewer
```

### With Export Support
```bash
# Install with export features
pip install markdown-viewer[export]

# Install Playwright browsers (for PDF)
playwright install chromium
```

### Using Poetry
```bash
# Install export dependencies
poetry install -E export

# Install Playwright browsers
poetry run playwright install chromium
```

## 🚀 Real-World Examples

### Documentation Pipeline
```bash
# Generate docs in all formats for release
mdview API_DOCS.md --export-pdf api-docs.pdf --export-word api-docs.docx --no-browser
mdview USER_GUIDE.md --export-pdf user-guide.pdf --no-browsermdview CHANGELOG.md --share-pdf  # Email to stakeholders
```

### Meeting Notes Workflow
```bash
# Take notes in markdown, then share
nano meeting-notes.md
mdview meeting-notes.md --share-word
# → Creates editable Word doc for team collaboration
```

### Report Generation
```bash
# Create report, export to PDF, keep HTML
mdview quarterly-report.md --export-pdf --keep
# → PDF for printing, HTML for web
```

## 💡 Pro Tips

1. **Use TOC** for long documents: Add `[TOC]` to auto-generate table of contents
2. **Preview first**: Run `mdview file.md` to preview before exporting
3. **Custom filenames**: Use descriptive names: `--export-pdf Q1-2026-Report.pdf`
4. **Batch export**: Combine `--export-pdf --export-word` for multiple formats
5. **CI/CD friendly**: Use `--no-browser` flag in automated scripts

## ⚙️ Tested Configurations

✅ Windows 10/11  
✅ Python 3.9-3.14  
✅ Outlook, Thunderbird, Gmail (desktop)  
✅ Chrome, Firefox, Edge browsers  
✅ Poetry & pip package managers

## 📚 Related Guides

- Full details: [EXPORT_FEATURES.md](EXPORT_FEATURES.md)
- TOC usage: [TOC_USAGE.md](../examples/TOC_USAGE.md)
- Demo files: [COMPREHENSIVE_DEMO.md](../examples/COMPREHENSIVE_DEMO.md), [TOC_DEMO.md](../examples/TOC_DEMO.md)

---

**Ready to share your markdown documents!** 🎉
