# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-07

### Added
- Initial release of Markdown Viewer
- Rich markdown rendering with GFM support
- Mermaid diagram rendering (flowcharts, sequence diagrams, pie charts, Gantt charts)
- Math equation support with KaTeX
- Syntax highlighting for 180+ programming languages
- PDF export using Playwright
- Microsoft Word (.docx) export
- Content translation to 15+ languages
- Copy all content feature
- Share via email functionality
- Electron-based cross-platform desktop UI
- Flask backend API
- Poetry-based dependency management
- Keyboard shortcuts (Ctrl+O, Ctrl+Shift+C, etc.)
- Comprehensive documentation
- Example markdown files
- Installation scripts

### Features
- **Markdown Processing**
  - Tables support
  - Task lists
  - Blockquotes
  - Code blocks with syntax highlighting
  - Footnotes
  - Definition lists
  - Emoji support

- **Export Capabilities**
  - High-quality PDF generation
  - Word document with preserved formatting
  - Automatic diagram and math rendering in exports

- **Translation**
  - Auto-detect source language
  - Preserve markdown formatting
  - Support for code blocks during translation

- **User Interface**
  - Clean, modern design
  - Responsive layout
  - Loading indicators
  - Status bar with file info
  - Modal dialogs
  - Welcome screen

### Technical Details
- Python backend with Flask
- Electron frontend
- Poetry for Python dependency management
- npm for JavaScript dependencies
- Cross-platform support (Windows, macOS, Linux)

### Documentation
- README with full feature description
- Installation guide
- Quick start guide
- Comprehensive example document
- API reference
- Contributing guidelines

## [Unreleased]

### Planned Features
- Dark mode theme
- Custom CSS themes
- Live preview while editing
- Plugin system
- Cloud sync
- Collaborative editing
- PlantUML support
- More diagram types
- Custom export templates
- Browser extension
- Mobile app (iOS/Android)
- WebDAV support
- Git integration
- Search functionality
- Recent files list
- Drag and drop file support
- Multiple file tabs
- Split view
- Auto-save
- Version history

### Known Issues
- PDF export requires Playwright browsers to be installed separately
- Translation requires internet connection
- Some complex Mermaid diagrams may need syntax adjustment
- Large files (>10MB) may take longer to process
- Image paths must be absolute or URLs for export

### Improvements Needed
- Optimize loading time for large files
- Add progress indicators for long operations
- Improve error messages
- Add more language support for translation
- Better handling of relative image paths
- Add undo/redo functionality
- Improve accessibility

---

For upgrade instructions, see [INSTALLATION.md](docs/INSTALLATION.md).

For full documentation, see [README.md](README.md).
