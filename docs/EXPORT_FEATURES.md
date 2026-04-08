# 📤 Export & Share Features

## 🌐 Browser Toolbar

When viewing markdown files in your browser, you'll see a simple toolbar with:

**📄 Export PDF**
- Click the button or press **Ctrl+P**
- Browser print dialog opens
- Select "Save as PDF" or "Microsoft Print to PDF"
- Choose location and save
- ✅ Works perfectly, no installation needed!

## 💻 Command Line (Full Features)

For maximum flexibility, use the CLI commands:

### Export to PDF
```bash
# Export to file.pdf in same directory
mdview document.md --export-pdf

# Export to specific path
mdview document.md --export-pdf reports/output.pdf
```

### Export to Word
```bash
# Export to file.docx in same directory  
mdview document.md --export-word

# Export to specific path
mdview document.md --export-word reports/output.docx
```

### Share via Email

Share commands export the file and open your email client with pre-filled details:

```bash
# Share as PDF
mdview document.md --share-pdf
# → Exports PDF
# → Opens email client
# → Shows file path to attach

# Share as Word
mdview document.md --share-word  
# → Exports Word document
# → Opens email client
# → Shows file path to attach
```

## 📊 Feature Comparison

| Feature | Browser Toolbar | CLI Command | Notes |
|---------|-----------------|-------------|-------|
| **Export PDF** | ✅ One-click (Ctrl+P) | ✅ `--export-pdf` | Browser method works great! |
| **Export Word** | ❌ | ✅ `--export-word` | Requires python-docx library |
| **Share PDF** | ❌ | ✅ `--share-pdf` | CLI exports + opens email |
| **Share Word** | ❌ | ✅ `--share-word` | CLI exports + opens email |

## 🎯 Best Practices

### Quick Viewing
- Use browser: `mdview file.md`
- Click Export PDF button when needed
- Simple and fast!

### Document Production
- Use CLI for Word exports: `mdview file.md --export-word`
- Use CLI for email sharing: `mdview file.md --share-pdf`
- Scriptable and repeatable!

### CI/CD & Automation
```bash
# Generate docs
mdview README.md --export-pdf docs.pdf --no-browser

# Multiple formats
mdview report.md --export-pdf --export-word --no-browser
```

## 🔧 Setup for Export/Share

### Install Chromium (for PDF via CLI)
```bash
poetry run playwright install chromium
```

### Dependencies
All export dependencies are already in `pyproject.toml`:
- `playwright` - PDF export
- `python-docx` - Word export
- `beautifulsoup4` - HTML parsing

## 💡 Tips

1. **For quick PDF exports**: Just use the browser button (Ctrl+P)
2. **For Word documents**: Use CLI `--export-word`
3. **For sharing**: Use CLI share commands (exports + email in one step)
4. **For automation**: CLI commands work in scripts and CI/CD
5. **For offline use**: Browser PDF export works without internet

## 📝 Examples

### Example 1: Quick PDF Export
```bash
mdview README.md
# Browser opens → Click Export PDF → Save
```

### Example 2: Generate Word Document
```bash
mdview specification.md --export-word spec.docx
# ✅ spec.docx created
```

### Example 3: Share Report via Email
```bash
mdview monthly-report.md --share-pdf
# ✅ Exports monthly-report.pdf
# ✅ Opens email with pre-filled subject
# ✅ Shows path to attach the PDF
# ✅ You attach and send
```

### Example 4: Build Documentation Pipeline
```bash
#!/bin/bash
# Generate all documentation formats

for file in docs/*.md; do
  mdview "$file" --export-pdf --export-word --no-browser
done

echo "✅ All documentation generated!"
```

## 🎊 Summary

**Browser:** Simple, one-button PDF export. Perfect for quick viewing and exporting.

**CLI:** Full power - PDF, Word, sharing, automation. Perfect for documentation workflows.

Choose the right tool for your task! 🚀
