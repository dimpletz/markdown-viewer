# Publishing Checklist for v1.3.4

**Date**: 2026-05-03  
**Version**: 1.3.4  
**Status**: ✅ PUBLISHED TO PyPI

## ✅ Publication Complete

**Published**: 2026-05-03 18:33 UTC  
**PyPI Package**: https://pypi.org/project/markdown-viewer-app/  
**GitHub Release**: https://github.com/dimpletz/markdown-viewer/releases/tag/v1.3.4  
**Version**: 1.3.4

### Build Artifacts
- ✅ `markdown_viewer_app-1.3.4-py3-none-any.whl` (2.3 MB)
- ✅ `markdown_viewer_app-1.3.4.tar.gz` (2.3 MB)

### Upload Status
- ✅ Source distribution uploaded to PyPI (100%)
- ✅ Wheel uploaded to PyPI (100%)
- ✅ Package available on PyPI (verified with pip)
- ✅ Code pushed to GitHub (commit 07a0979)
- ✅ Tag v1.3.4 created and pushed to GitHub

### Installation
```bash
pip install --upgrade markdown-viewer-app
# or specific version:
pip install markdown-viewer-app==1.3.4
```

---

## ✅ Pre-Publish Validation

### Code Quality
- [x] **Audit Complete**: 9/9 steps GREEN (see [AUDIT_REPORT.md](AUDIT_REPORT.md))
- [x] **Tests Passing**: 468/468 tests (100%)
- [x] **Coverage**: 85% (exceeds 80% threshold)
- [x] **Code Quality**: Pylint 9.77/10
- [x] **Formatting**: Black clean, 25 E501 warnings (non-critical)

### Security
- [x] **Vulnerabilities**: 0 High/Critical
- [x] **pip-audit**: 1 CVE in pip (build tool, accepted)
- [x] **bandit**: 0 High, 2 Medium (documented safe usage)
- [x] **npm audit**: 2 Moderate in mermaid/uuid (accepted, low-risk)
- [x] **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options ✅

### Version Management
- [x] **Version Bumped**: 1.3.3 → 1.3.4 (both `pyproject.toml` and `package.json`)
- [x] **CHANGELOG Updated**: v1.3.4 entry added with fixes
- [x] **dist/ Cleaned**: All old build artifacts removed

### Critical Fixes in v1.3.4
- [x] Vendor JavaScript loading (404 errors fixed)
- [x] CSP inline script violation (externalized to legacy-check.js)
- [x] Process cleanup (duplicate server detection)

## 📦 Build & Publish Commands

### 1. Build Python Package
```bash
# Build wheel and source distribution
poetry build

# Expected output:
# Building markdown-viewer-app (1.3.4)
#  - Building sdist
#  - Built markdown_viewer_app-1.3.4.tar.gz
#  - Building wheel
#  - Built markdown_viewer_app-1.3.4-py3-none-any.whl
```

### 2. Verify Build
```bash
# Check dist/ contents
ls dist/

# Expected files:
# markdown_viewer_app-1.3.4-py3-none-any.whl
# markdown_viewer_app-1.3.4.tar.gz
```

### 3. Test Installation (Local)
```bash
# Create test environment
python -m venv test-env
test-env\Scripts\activate

# Install from wheel
pip install dist/markdown_viewer_app-1.3.4-py3-none-any.whl

# Test CLI
mdview --version
mdview --help

# Cleanup
deactivate
Remove-Item -Recurse test-env
```

### 4. Publish to PyPI
```bash
# Publish to PyPI (requires PyPI credentials)
poetry publish

# Or use twine:
# pip install twine
# twine upload dist/*
```

### 5. Create GitHub Release
```bash
# Tag the release
git tag -a v1.3.4 -m "Release v1.3.4: Vendor loading and CSP fixes"
git push origin v1.3.4

# Create release on GitHub with:
# - Tag: v1.3.4
# - Title: "v1.3.4 - Vendor Loading and CSP Fixes"
# - Description: Copy from CHANGELOG.md v1.3.4 section
# - Attach: dist/markdown_viewer_app-1.3.4-py3-none-any.whl
# - Attach: dist/markdown_viewer_app-1.3.4.tar.gz
```

### 6. Post-Publish Verification
```bash
# Wait 5-10 minutes for PyPI to update

# Install from PyPI
pip install --upgrade markdown-viewer-app

# Verify version
mdview --version  # Should show 1.3.4
```

## 🔍 Final Checklist

Before running `poetry publish`:

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Audit report complete
- [ ] Version numbers aligned (pyproject.toml + package.json)
- [ ] CHANGELOG.md updated
- [ ] dist/ cleaned before build
- [ ] Poetry build successful
- [ ] Wheel integrity verified
- [ ] Git committed and pushed
- [ ] Git tag created

After publishing:

- [ ] PyPI package visible
- [ ] GitHub release created
- [ ] Installation from PyPI verified
- [ ] Documentation links updated (if needed)
- [ ] Announce release (if applicable)

## 📝 Release Notes Template

```markdown
# Markdown Viewer v1.3.4

**Release Date**: May 3, 2026

## 🐛 Bug Fixes

### Vendor JavaScript Loading
Fixed critical 404 errors preventing vendor libraries from loading. All frontend assets (axios, marked, mermaid, katex, purify) now load correctly from the local vendor directory with proper caching headers.

### Content Security Policy Compliance
Eliminated inline script violations by externalizing legacy browser check to `scripts/legacy-check.js`. Application now fully compliant with strict CSP headers.

## 🔒 Security

Comprehensive audit completed with:
- ✅ 85% test coverage (468/468 tests passing)
- ✅ 0 High/Critical vulnerabilities
- ✅ Code quality: 9.77/10 (Pylint)
- ✅ All security headers validated

## 📊 Quality Metrics

- **Tests**: 468/468 passing (100%)
- **Coverage**: 85% (2400 stmts, 364 missed)
- **Security**: 0 High/Critical vulnerabilities
- **Dependencies**: 0 conflicts

**Upgrade Command**: `pip install --upgrade markdown-viewer-app`

For full details, see [CHANGELOG.md](CHANGELOG.md#134---2026-05-03)
```

## ⚠️ Important Notes

1. **Always delete `dist/` before building** (per AGENTS.md)
2. **Keep pyproject.toml and package.json versions in sync**
3. **Test installation before publishing to PyPI** (no way to delete published versions)
4. **PyPI credentials required** - Set up `~/.pypirc` or use Poetry credentials
5. **Wait ~5-10 minutes** after publishing for PyPI to propagate

## 🎯 Success Criteria

Publish is successful when:
- ✅ Package appears on https://pypi.org/project/markdown-viewer-app/
- ✅ `pip install markdown-viewer-app` downloads v1.3.4
- ✅ `mdview --version` shows 1.3.4
- ✅ All functionality works (render, export, UI)

---

**Prepared by**: GitHub Copilot  
**Date**: 2026-05-03  
**Status**: ✅ READY FOR PUBLISH
