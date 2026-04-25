## Purpose

Markdown Viewer is a cross-platform desktop + CLI markdown rendering app. **Backend**: Flask 3.1 (Python 3.9–3.14) exposing a 12-endpoint REST API for rendering, file I/O, PDF/Word export (playwright + python-docx), and translation. **Frontend**: Electron 28 + vanilla ES6 (Marked.js, Mermaid, KaTeX, highlight.js, DOMPurify). Stateless — no database; SQLite-style favourites repo lives under `markdown_viewer/db/`. Run locally with `mdview` (CLI) or `python -m markdown_viewer` (server). Test with `pytest`. Format with `black .`. Lint with `flake8` / `pylint`.

## Tree

- markdown_viewer/ — Python package (Flask app, CLI, routes, server)
- markdown_viewer/app.py — Flask factory, CORS, CSRF, security headers
- markdown_viewer/routes.py — main API blueprint (12 endpoints)
- markdown_viewer/favourites_routes.py — favourites API
- markdown_viewer/cli.py — `mdview` CLI entry point
- markdown_viewer/server.py — threaded server + PID management
- markdown_viewer/db/ — SQLite favourites repo
- markdown_viewer/exporters/ — PDF (playwright) + Word (python-docx) exporters
- markdown_viewer/processors/ — markdown processor
- markdown_viewer/translators/ — content translator
- markdown_viewer/utils/ — file_handler + helpers
- markdown_viewer/electron/ — Electron shell (main.js, preload.js, renderer/)
- tests/ — pytest suite (unit + integration); mirrors package layout
- scripts/ — install.bat/install.sh, setup_electron.py
- docs/ — user-facing docs (CLI usage, install, exports)
- examples/ — sample markdown demos
- pyproject.toml — Python build, deps, tool config (black, pytest, coverage)
- package.json — Electron deps + scripts
- htmlcov/ — generated coverage report (do not commit edits)
- logs/ — runtime logs (gitignored content)

## Rules

### General
- Before changing any API endpoint, read `markdown_viewer/routes.py` and update `tests/test_routes.py`.
- Before touching path/file handling, read `markdown_viewer/utils/file_handler.py` — path-traversal protection is enforced via `ALLOWED_DOCUMENTS_DIR`.
- Never bypass DOMPurify, CSRF tokens, or marshmallow schema validation.
- Never hardcode secrets; use env vars (`SECRET_KEY`, `BACKEND_PORT`, `ALLOWED_DOCUMENTS_DIR`).
- Never modify `pyproject.toml` deps, `package.json` deps, or CI workflows without my approval.
- When you create or discover new files/folders, update the Tree above.

### Coding Standards (apply per language)
- **Python**: PEP 8 + Black (line length per `pyproject.toml`). Type hints on public functions. Google-style docstrings. `snake_case` funcs/vars, `PascalCase` classes, `UPPER_SNAKE` constants. Use `pathlib`, f-strings, context managers, dataclasses. No bare `except`.
- **JavaScript (Electron)**: ES6+, `const`/`let` (never `var`), `===`, arrow funcs for callbacks, async/await over `.then` chains, optional chaining. No globals — use modules. Sanitize all rendered HTML via DOMPurify.
- **HTML/CSS**: Semantic HTML5, ARIA where needed, BEM-ish class names, CSS custom properties for theming, mobile-first media queries.
- **SQL** (favourites_repo): Parameterized queries only — never string concat. UPPERCASE keywords.
- **Shell/PowerShell** (scripts/): `set -euo pipefail` for bash; approved verbs + `[CmdletBinding()]` for PowerShell.
- **YAML/JSON**: 2-space indent, no trailing commas in JSON.

### Universal Quality Gates
- SOLID, DRY, KISS, YAGNI. Functions ≤ 50 lines, cyclomatic complexity ≤ 10, nesting ≤ 4, files ≤ 500 lines.
- Validate **all** inputs at system boundaries. Whitelist over blacklist.
- OWASP Top 10: parameterized SQL, escape output, CSRF tokens, secure headers, no secrets in logs.
- Tests required for all new logic; minimum **90% line + branch coverage** (project standard, stricter than the 80% baseline).

## Audit Command

When I say **"audit"**, perform the following sequence in order, stopping only on unrecoverable errors. Report results in a numbered checklist.

1. **Cleanup**
   - Delete unused/temporary files (scratch scripts, `*_investigation.py`, `tmp_*`, ad-hoc debug notebooks).
   - Remove dead code, unreachable branches, unused imports, unused variables, commented-out blocks.
   - Drop helper functions/methods that exist only for one-shot debugging.
   - Clear stale entries from `markdown_viewer/temp/` and `markdown_viewer/uploads/` if they are not fixtures.

2. **Format & Lint**
   - Run `black .` (Python).
   - Run `flake8 markdown_viewer tests` and `pylint markdown_viewer` (or whichever is configured); fix all reported issues.
   - Run `prettier --write` on JS/CSS/HTML if available; otherwise apply equivalent style fixes manually.

3. **Coverage Check**
   - Run `pytest --cov=markdown_viewer --cov-branch --cov-report=term-missing --cov-report=html`.
   - **Target**: ≥90% line + branch coverage for business logic modules; ≥80% overall.
   - **Acceptance criteria**: Integration-heavy modules (cli.py, word_exporter.py with OS-specific browser/subprocess code) may fall below 90% if:
     * All business logic modules (CRUD, rendering, translation, routing, file handling) are ≥88%
     * Uncovered code is primarily OS-specific integration (browser launching, Playwright initialization, subprocess spawning)
     * Manual E2E testing validates uncovered paths
   - If overall coverage < **80%**, generate additional unit tests for the uncovered code paths and re-run until ≥ 80%.

4. **Run Unit Tests**
   - Execute `pytest tests/ -v` and ensure all pass.

5. **Integration / Regression / Other Tests**
   - Add or extend integration tests under `tests/integration/` (create folder if missing) covering: end-to-end render → export PDF, render → export Word, file open with path-traversal attempts, favourites CRUD, translate workflow.
   - Add regression tests for any bug fixed since the last audit.
   - Add applicable smoke, contract, and security tests (e.g., CSRF enforcement, oversized payload rejection).
   - Run the full test suite and ensure all pass.

6. **Non-Functional Requirements (NFRs)** — verify and document:
   - **Performance**: render of 1MB markdown < 2s; profile hot paths if regressed.
   - **Security**: CSRF, CSP/security headers, path traversal blocked, DOMPurify active, no secrets in logs.
   - **Availability**: `/health` endpoint returns 200; graceful shutdown works.
   - **Usability**: CLI `--help` accurate; UI keyboard accessible.
   - **Scalability**: stateless design preserved; no per-request global state.
   - **Maintainability**: function/file size limits respected; cyclomatic complexity ≤ 10.
   - **Portability**: tests pass on Python 3.9–3.14; Electron builds for Win/macOS/Linux.
   - **Compatibility**: API request/response schemas unchanged or versioned.
   - **Manageability**: structured logs with request IDs; log rotation configured.
   - **Capacity**: file-size limits enforced (50MB content / 10MB markdown).
   - **Reliability**: error paths tested; no silent exception swallowing.
   - **Compliance**: license headers intact; third-party licenses compatible.
   - **Environment**: env-var driven config; dev vs. production behaviour clear.

7. **Vulnerability Scan**
   - Run `pip-audit` (or `safety check`) on Python deps.
   - Run `npm audit --omit=dev` inside `markdown_viewer/electron/`.
   - Run `bandit -r markdown_viewer` for Python source.
   - Resolve every High/Critical finding; document accepted Mediums in `SECURITY.md`.

8. **Dependency Health**
   - Run `pip check` for conflicts.
   - Run `pip list --outdated` and `npm outdated`; flag risky majors.
   - Verify license compatibility of any new dep.
   - Document conflicts, restrictions, and risks in the audit report section of `AUDIT_REPORT.md`.

9. **Final Report**
   - Append a dated summary to `AUDIT_REPORT.md`: what was cleaned, coverage %, tests added, NFR results, vulns fixed, dep risks.

## Note-taking (Auto-Learn)

- After **every** task, log any correction, preference, pattern, or gotcha learned.
- Write one dated line in plain language to the matching context file's "Session learnings" section. If no file fits, append to the **Rules** section above.
  Example: `Use playwright sync API in exporters; async API leaks Chromium handles (learned 4/24)`
- When **3+ related notes** accumulate on a topic, create a new file under `docs/` (e.g., `docs/testing-strategy.md`, `docs/security-conventions.md`), move the notes there with a `## Session learnings` section, and update the Tree.
- Keep this file under ~150 lines; trim or graduate stale rules.
