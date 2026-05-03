# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Best Practices

### Before First Run

1. **Generate a strong SECRET_KEY**:
   ```bash
   python -c 'import secrets; print(secrets.token_hex())'
   ```
   Set this in your environment:
   ```bash
   export SECRET_KEY='your-generated-key-here'
   ```

2. **Set the environment** to production when deploying:
   ```bash
   export FLASK_ENV=production
   export NODE_ENV=production
   ```

### Network Security

- The Flask backend binds to `127.0.0.1` (localhost only) for security
- CORS is restricted to localhost and Electron app origins
- Never expose the backend to `0.0.0.0` in production

### File Access

- The application validates file paths to prevent path traversal attacks
- Only markdown files with approved extensions are processed
- Consider implementing an allowed base directory for additional security

### Electron Security

The Electron app implements critical security settings:
- `nodeIntegration: false` - Node.js APIs not available in renderer
- `contextIsolation: true` - Isolates renderer from Node.js
- `sandbox: true` - Renderer runs in sandboxed process
- Safe IPC communication via preload script

### Content Security

- Mermaid diagrams use `securityLevel: 'strict'` to prevent XSS
- HTML sanitization is performed on rendered content
- CSRF protection is enabled for all state-changing operations

## Reporting a Vulnerability

If you discover a security vulnerability, please [open a private security advisory](https://github.com/dimpletz/markdown-viewer/security/advisories/new).

Do **not** include sensitive details in a public issue.

We will respond within 48 hours and provide a timeline for a fix.

## Security Checklist for Deployment

- [ ] SECRET_KEY environment variable is set
- [ ] FLASK_ENV=production is set
- [ ] NODE_ENV=production is set
- [ ] HTTPS is configured for any web deployment
- [ ] File access is restricted to necessary directories
- [ ] Logs are monitored for suspicious activity
- [ ] Dependencies are up to date
- [ ] Electron is packaged with latest security patches

## Accepted Findings (2026-04-27 Audit)

The following findings were reviewed and accepted for now, with monitoring:

1. Python dependency advisory (`pip-audit`)
- Package: `pip 26.0.1`
- Advisory: `CVE-2026-3219`
- Reason accepted: tool reported no fix version at audit time; this affects local packaging/tooling, not runtime application request handling.
- Mitigation: monitor for patched `pip` release and upgrade promptly.

2. JavaScript dependency advisories (`npm audit --omit=dev`)
- Package chain: `mermaid` -> `uuid <14.0.0`
- Severity: 2 moderate
- Reason accepted: fix path requires breaking dependency changes; current risk is limited to client-side diagram rendering context.
- Mitigation: track upstream mermaid/uuid updates and re-audit on next dependency refresh cycle.

3. Source scan findings (`bandit`)
- Medium findings: `B310` (`urllib.request.urlopen`) in `markdown_viewer/exporters/word_exporter.py`
- Reason accepted: used for remote image retrieval workflow; no high/critical findings remain.
- Mitigation: keep strict input validation on URL sources and re-review during exporter refactor.
