# Publishing Checklist for v1.3.6

**Date**: 2026-05-04  
**Version**: 1.3.6  
**Author**: Ofelia B Webb  
**Status**: 🚀 READY TO PUBLISH

---

## 📋 Pre-Publish Validation

### Code Quality
- [x] **Audit Complete**: All steps GREEN (see [AUDIT_REPORT.md](AUDIT_REPORT.md))
- [x] **Tests Passing**: 468/468 tests (100%)
- [x] **Coverage**: 84% (exceeds 80% threshold)
- [x] **Code Quality**: Pylint 9.81/10 (excellent)
- [x] **Formatting**: Black clean, flake8 passing (25 E501 acceptable - URLs/HTML)

### Security
- [x] **Vulnerabilities**: 0 High/Critical
- [x] **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options ✅
- [x] **Input Validation**: Path traversal protection, CSRF tokens ✅
- [x] **Dependencies**: All security patches applied

### Version Management
- [x] **Version Bumped**: 1.3.5 → 1.3.6
  - [x] `pyproject.toml`: 1.3.6 ✅
  - [x] `package.json`: 1.3.6 ✅
  - [x] `markdown_viewer/__init__.py`: 1.3.6 ✅
- [x] **CHANGELOG Updated**: v1.3.6 entry complete with all features
- [x] **dist/ Cleaned**: Empty (ready for fresh build)
- [x] **Author Verified**: Ofelia B Webb in all files ✅

### Documentation
- [x] **README.md**: Installation guide with troubleshooting section ✅
- [x] **Examples**: Comprehensive demos including TABLE_BEFORE_TOC.md ✅
- [x] **Docs**: CLI usage, export features, installation guides ✅
- [x] **SECURITY.md**: Security practices documented ✅

### Key Features in v1.3.6
- [x] **Version Display**: UI shows app version next to Translate button
- [x] **Playwright Info Banner**: Helpful installation instructions with dismissible banner
- [x] **Better Error Messages**: Clear guidance for missing Playwright browsers
- [x] **Word Export Performance**: Improved reliability (domcontentloaded wait, 60s timeout)
- [x] **Export Button Visibility**: Both PDF/Word buttons hidden when Playwright unavailable
- [x] **TOC Rendering**: Fixed table of contents styling with bold title
- [x] **Badge Spacing**: Improved image/badge layout spacing
- [x] **Documentation**: Enhanced guides for non-technical users

### Git Status
- [x] **Working Directory**: Clean (no uncommitted changes)
- [x] **All Changes Committed**: Ready for tagging
- [x] **Remote Synced**: All commits pushed to origin/main

## 📦 Build & Publish Commands

### 1. Clean Build Directory
```bash
# CRITICAL: Delete all content in dist/ before building
Remove-Item -Recurse -Force dist\* -ErrorAction SilentlyContinue
```

### 2. Build Python Package
```bash
# Build wheel and source distribution
poetry build

# Expected output:
# Building markdown-viewer-app (1.3.6)
#  - Building sdist
#  - Built markdown_viewer_app-1.3.6.tar.gz
#  - Building wheel
#  - Built markdown_viewer_app-1.3.6-py3-none-any.whl
```

### 3. Verify Build
```bash
# Check dist/ contents
ls dist/

# Expected files:
# markdown_viewer_app-1.3.6-py3-none-any.whl (~2.3 MB)
# markdown_viewer_app-1.3.6.tar.gz (~2.3 MB)

# Verify wheel contents include vendor files
python -m zipfile -l dist/markdown_viewer_app-1.3.6-py3-none-any.whl | Select-String "mermaid.min.js"
# Should show: markdown_viewer/electron/renderer/vendor/mermaid/mermaid.min.js
```

### 4. Test Installation (Local)
```bash
# Create fresh test environment
python -m venv test-env-1.3.6
test-env-1.3.6\Scripts\activate

# Install from wheel
pip install dist/markdown_viewer_app-1.3.6-py3-none-any.whl

# Test CLI
mdview --version  # Should show: Markdown Viewer v1.3.6
mdview --help

# Test with example file
mdview examples/COMPREHENSIVE_DEMO.md
# Verify: Version badge shows "v1.3.6" in UI
# Verify: All vendor scripts load (check browser console)
# Verify: Export buttons visible if Playwright installed

# Test export (if Playwright installed)
# Word export should complete in 15-30s

# Cleanup
deactivate
Remove-Item -Recurse -Force test-env-1.3.6
```

### 5. Publish to PyPI
```bash
# ⚠️ FINAL CHECK BEFORE PUBLISHING ⚠️
# - All tests passing? ✅
# - dist/ cleaned before build? ✅
# - Version correct in all files? ✅
# - CHANGELOG updated? ✅
# - Local test successful? ✅

# Publish to PyPI (requires PyPI credentials)
poetry publish

# Expected output:
# Publishing markdown-viewer-app (1.3.6) to PyPI
#  - Uploading markdown_viewer_app-1.3.6-py3-none-any.whl 100%
#  - Uploading markdown_viewer_app-1.3.6.tar.gz 100%
```

### 6. Create Git Tag and GitHub Release
```bash
# Commit checklist update (if modified)
git add PUBLISH_CHECKLIST.md
git commit -m "docs: Update publish checklist for v1.3.6"
git push origin main

# Tag the release
git tag -a v1.3.6 -m "Release v1.3.6: Version display, Playwright UX improvements, TOC fixes"
git push origin v1.3.6

# Create release on GitHub:
# 1. Go to https://github.com/dimpletz/markdown-viewer/releases/new
# 2. Tag: v1.3.6
# 3. Title: "v1.3.6 - Version Display & UX Improvements"
# 4. Description: Copy from CHANGELOG.md v1.3.6 section
# 5. Attach: dist/markdown_viewer_app-1.3.6-py3-none-any.whl
# 6. Attach: dist/markdown_viewer_app-1.3.6.tar.gz
# 7. Publish release
```

### 7. Post-Publish Verification
```bash
# Wait 5-10 minutes for PyPI to propagate

# Install from PyPI in clean environment
python -m venv test-pypi-1.3.6
test-pypi-1.3.6\Scripts\activate

pip install --upgrade markdown-viewer-app

# Verify version
mdview --version  # Should show: Markdown Viewer v1.3.6

# Test functionality
mdview examples/TABLE_BEFORE_TOC.md
# ✅ Version badge shows v1.3.6
# ✅ TOC renders with bold title
# ✅ Table before TOC displays correctly

# Cleanup
deactivate
Remove-Item -Recurse -Force test-pypi-1.3.6

# Verify PyPI page
# https://pypi.org/project/markdown-viewer-app/
# Should show version 1.3.6 with updated description
```

## 🔍 Final Checklist

Before running `poetry publish`:

- [x] All tests pass (`pytest tests/ -v`) - 468/468 ✅
- [x] Audit report complete - 84% coverage ✅
- [x] Version numbers aligned (pyproject.toml + package.json + __init__.py) - 1.3.6 ✅
- [x] CHANGELOG.md updated - v1.3.6 section complete ✅
- [x] Author name verified - Ofelia B Webb ✅
- [ ] dist/ cleaned before build - **DO THIS FIRST**
- [ ] Poetry build successful
- [ ] Wheel integrity verified (vendor files included)
- [ ] Local installation test passed
- [ ] Git committed and pushed
- [ ] Git tag created (v1.3.6)

After publishing:

- [ ] PyPI package visible (https://pypi.org/project/markdown-viewer-app/)
- [ ] GitHub release created (https://github.com/dimpletz/markdown-viewer/releases)
- [ ] Installation from PyPI verified
- [ ] Version badge displays correctly in UI
- [ ] Documentation links verified

## 📝 Release Notes Template

```markdown
# Markdown Viewer v1.3.6

**Release Date**: May 4, 2026  
**Author**: Ofelia B Webb

## ✨ New Features

### Version Display
- App version now shown in UI toolbar next to Translate button
- Dynamically fetched from `/api/health` endpoint
- Displays as subtle badge (e.g., "v1.3.6") with tooltip
- Auto-updates when user upgrades package

### Playwright Installation Guide
- Helpful info banner appears when Playwright browsers not installed
- Informs users about PDF & Word export capabilities
- Shows exact command: `playwright install chromium`
- Dismissible with localStorage persistence
- Smooth slide-down animation
- Test mode via `?test-banner` URL parameter

### Better Export Error Messages
- Detects missing Playwright browsers
- Provides clear installation instructions
- Context-aware error messages for timeout issues
- Guides users to exact fix command

## 🐛 Bug Fixes

### Word Export Performance
- Changed wait condition from `networkidle` to `domcontentloaded`
- Increased timeout from 30s to 60s
- Reduced rendering wait from 5s to 2.5s
- Fixes "Page.goto: Timeout 30000ms exceeded" errors

### Table of Contents Rendering
- Fixed TOC marker configuration (`marker: "[TOC]"`)
- Made "Table of Contents" title bold (font-weight: 700)
- Improved TOC placement and styling
- Comprehensive CSS styling for .toc elements

### Badge Spacing
- Reduced image margins from 16px to 4px
- Added inline-block display for badges
- Special styling for shields.io badges (2px 6px margins)
- Reduced excessive vertical gaps

### Export Button Visibility
- Both PDF and Word export buttons hidden when Playwright not installed
- Consistent UX: users only see available features
- Prevents confusion from clicking unavailable features

## 📚 Documentation Improvements

### Non-Technical User Guide
- Step-by-step installation guide with OS-specific instructions
- How to open Terminal/Command Prompt on each platform
- Comprehensive troubleshooting section (10 common issues)
- Clear explanations for Playwright installation

### Examples
- Added `TABLE_BEFORE_TOC.md` demonstrating table before TOC marker
- Validates proper TOC placement and table rendering

## 🔒 Security & Quality

- ✅ 468/468 tests passing (100%)
- ✅ 84% code coverage
- ✅ Pylint 9.81/10 rating
- ✅ 0 High/Critical vulnerabilities
- ✅ All security headers validated
- ✅ No CDN dependencies in renderer

## 📦 Installation

```bash
pip install --upgrade markdown-viewer-app
playwright install chromium  # One-time setup for exports
```

**PyPI**: https://pypi.org/project/markdown-viewer-app/  
**GitHub**: https://github.com/dimpletz/markdown-viewer  
**Changelog**: [CHANGELOG.md](https://github.com/dimpletz/markdown-viewer/blob/main/CHANGELOG.md)
```

## ⚠️ Important Notes

1. **Always delete `dist/` before building** (per AGENTS.md) - prevents stale artifacts
2. **Keep versions in sync**: pyproject.toml, package.json, __init__.py must all be 1.3.6
3. **Test installation before publishing** - PyPI packages cannot be deleted once published
4. **PyPI credentials required** - Configure `~/.pypirc` or use `poetry config`
5. **Wait ~5-10 minutes** after publishing for PyPI CDN to propagate
6. **Verify author name** - Must be "Ofelia B Webb" in all files
7. **Check vendor files** - Ensure mermaid.min.js (5.8MB) is in wheel
8. **Test export features** - Verify Word/PDF export work after installation

## 🎯 Success Criteria

Publish is successful when:

1. ✅ PyPI package page shows version 1.3.6
2. ✅ `pip install markdown-viewer-app` installs 1.3.6
3. ✅ `mdview --version` shows "Markdown Viewer v1.3.6"
4. ✅ UI displays version badge "v1.3.6"
5. ✅ All vendor files load without 404 errors
6. ✅ TOC renders correctly with bold title
7. ✅ Export features work (if Playwright installed)
8. ✅ GitHub release created with wheel and tarball
9. ✅ No security vulnerabilities introduced
10. ✅ Documentation reflects current version

## 📧 Author Information

**Name**: Ofelia B Webb  
**Email**: ofelia.b.webb@gmail.com  
**GitHub**: https://github.com/dimpletz  
**Project**: https://github.com/dimpletz/markdown-viewer  
**PyPI**: https://pypi.org/project/markdown-viewer-app/

---

## 🚀 Quick Publish Commands

```bash
# Complete publish workflow
Remove-Item -Recurse -Force dist\* -ErrorAction SilentlyContinue
poetry build
python -m zipfile -l dist/markdown_viewer_app-1.3.6-py3-none-any.whl | Select-String "mermaid.min.js"
poetry publish
git tag -a v1.3.6 -m "Release v1.3.6: Version display, Playwright UX improvements, TOC fixes"
git push origin v1.3.6
```

Then create GitHub release manually with release notes above.

---

**Status**: 🚀 READY TO PUBLISH  
**Prepared**: 2026-05-04  
**Author**: Ofelia B Webb
- ✅ Package appears on https://pypi.org/project/markdown-viewer-app/
- ✅ `pip install markdown-viewer-app` downloads v1.3.4
- ✅ `mdview --version` shows 1.3.4
- ✅ All functionality works (render, export, UI)

---

**Prepared by**: GitHub Copilot  
**Date**: 2026-05-03  
**Status**: ✅ READY FOR PUBLISH
