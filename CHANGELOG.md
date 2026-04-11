# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.3] - 2026-04-11

### Security
- Replaced `deep-translator` dependency with a direct call to the MyMemory REST API using Python stdlib `urllib` — eliminates PYSEC-2022-252 (2022 supply-chain advisory that blanket-flagged all `1.x` with no fix version), reducing the attack surface and removing one third-party dependency entirely

### Fixed
- Server no longer shuts down when the browser tab is refreshed or navigates — the `pagehide` event was firing on every refresh, killing the background Flask server after the first reload
- `--export-pdf` and `--export-word` now accept a directory as the output path and automatically append the correct filename (e.g. `mdview readme.md --export-word c:\dev\` saves to `c:\dev\readme.docx`) instead of crashing with `PermissionError`
- Added `-p`/`--port` flag and CI/CD headless auto-detection to README CLI Reference section
- Test `test_main_opens_browser_by_default` now correctly patches `sys.stdout.isatty` to simulate an interactive terminal

### Changed
- Root `package.json` version aligned to `1.1.3`

## [1.1.2] - 2026-04-11

### Security
- Fixed 22 CVEs across 11 packages: flask (CVE-2026-27205), flask-cors (CVE-2024-6839/6844/6866), werkzeug (CVE-2025-66221, CVE-2026-21860/27199), urllib3 (5 CVEs including decompression bombs and SSRF), requests (CVE-2026-25645), pillow (CVE-2026-25990), markdown (CVE-2025-69534), pymdown-extensions (CVE-2025-68142), marshmallow (CVE-2025-68480), pygments (CVE-2026-4539), black (CVE-2024-21503, CVE-2026-32274)

### Changed
- Upgraded `flask` 2.3.3 → 3.1.3
- Upgraded `flask-cors` 4.0.2 → 6.0.2
- Upgraded `werkzeug` 3.0.6 → 3.1.8
- Upgraded `urllib3` 2.2.3 → 2.6.3
- Upgraded `requests` 2.32.4 → 2.33.1
- Upgraded `pillow` 11.3.0 → 12.2.0 (Python 3.10+); 11.x retained for Python 3.9
- Upgraded `markdown` 3.7 → 3.10.2
- Upgraded `pymdown-extensions` 10.15 → 10.21.2
- Upgraded `marshmallow` 3.22.0 → 4.3.0
- Upgraded `pygments` 2.19.2 → 2.20.0
- Upgraded `black` (dev) 23.12.1 → 26.3.1 (Python 3.10+); 24.3.0+ retained for Python 3.9
- Updated CDN: `katex` 0.16.9 → 0.16.45
- Updated CDN: `highlight.js` 11.9.0 → 11.11.1
- Added Python 3.14 support; updated all classifiers and constraints

### Fixed
- All hardcoded Python 3.8 minimum references updated to 3.9 (setup.py runtime check, docs, examples)

## [1.1.1] - 2026-04-10

### Changed
- Updated development status to Production/Stable
- Added `pytest_out.txt` to `.gitignore`
- Removed stale build artifacts from repository

## [1.1.0] - 2026-04-10

### Added
- `mdview <file>` browser mode: opens the file directly in the browser with a single command
- Detached background server: terminal returns immediately after the browser opens; server keeps running silently for subsequent calls
- Auto-reloader: Flask server watches source files and restarts automatically when code changes (no manual server kill needed during development)

### Fixed
- Emoji and special characters now render correctly — `chardet` was misidentifying UTF-8 files as Windows-1252; UTF-8 is now always tried first
- Welcome screen no longer flashes before the file loads when opening via `mdview <file>`
- Export dialogs no longer show a success popup; the status bar updates silently, alert only shown on failure
- Background server no longer opens a visible console window on Windows (`CREATE_NO_WINDOW` flag)
- CSRF cookie no longer carries the `Secure` flag over plain HTTP, fixing authentication failures in Firefox and other strict browsers
- Files outside the home directory (e.g. `C:\dev\`) are no longer blocked with 403

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
