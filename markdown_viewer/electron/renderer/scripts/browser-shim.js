/**
 * Browser compatibility shim.
 * When running in a regular browser (not Electron), window.electronAPI and
 * window.path are undefined. This shim provides equivalent functionality using
 * standard Web APIs so the app works in both environments.
 */

(function () {
  'use strict';

  // ── path shim ──────────────────────────────────────────────────────────────
  if (!window.path) {
    window.path = {
      basename(p, ext) {
        const base = String(p).replace(/\\/g, '/').split('/').pop() || p;
        if (ext && base.endsWith(ext)) return base.slice(0, -ext.length);
        return base;
      },
      dirname(p) {
        const s = String(p).replace(/\\/g, '/');
        const idx = s.lastIndexOf('/');
        return idx >= 0 ? s.slice(0, idx) || '/' : '.';
      },
      extname(p) {
        const m = String(p).match(/\.[^./\\]*$/);
        return m ? m[0] : '';
      },
      join(...args) {
        return args.join('/').replace(/\/+/g, '/');
      }
    };
  }

  // ── electronAPI shim ───────────────────────────────────────────────────────
  if (window.electronAPI) return; // already provided by Electron preload

  // Cache for file content keyed by filename (populated when user picks a file)
  const _fileCache = new Map();

  // Hidden file input used as the "open file" dialog replacement
  const _fileInput = document.createElement('input');
  _fileInput.type = 'file';
  _fileInput.accept = '.md,.markdown,.mdown,text/markdown,text/plain';
  _fileInput.style.display = 'none';
  document.body.appendChild(_fileInput);

  // Helper: trigger a browser download from a Uint8Array/string
  function _download(filename, data, mimeType) {
    const blob = data instanceof Uint8Array
      ? new Blob([data], { type: mimeType || 'application/octet-stream' })
      : new Blob([data], { type: mimeType || 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = window.path.basename(filename);
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }

  window.electronAPI = {
    // IPC event listeners — no-op in browser (menus don't exist)
    on(channel, callback) {
      // nothing to listen to in browser mode
    },

    async invoke(channel, ...args) {
      // ── show-open-dialog ──────────────────────────────────────────────────
      if (channel === 'show-open-dialog') {
        return new Promise((resolve) => {
          _fileInput.onchange = async (e) => {
            const file = e.target.files && e.target.files[0];
            _fileInput.value = ''; // reset so the same file can be picked again
            if (!file) {
              resolve({ canceled: true, filePaths: [] });
              return;
            }
            const content = await file.text();
            _fileCache.set(file.name, content);
            resolve({ canceled: false, filePaths: [file.name] });
          };
          _fileInput.click();
        });
      }

      // ── read-file ─────────────────────────────────────────────────────────
      if (channel === 'read-file') {
        const name = window.path.basename(args[0]);
        if (_fileCache.has(name)) {
          return { success: true, content: _fileCache.get(name) };
        }
        return { success: false, error: 'File not available in browser mode — please reopen the file.' };
      }

      // ── show-save-dialog ──────────────────────────────────────────────────
      if (channel === 'show-save-dialog') {
        const opts = args[0] || {};
        // In browser we never get a real path — return a placeholder
        return { canceled: false, filePath: opts.defaultPath || 'download' };
      }

      // ── save-export-file ──────────────────────────────────────────────────
      if (channel === 'save-export-file') {
        const [filePath, data] = args;
        _download(filePath, data);
        return { success: true };
      }

      // ── save-file ─────────────────────────────────────────────────────────
      if (channel === 'save-file') {
        const [filePath, content] = args;
        _download(window.path.basename(filePath), content, 'text/plain');
        return { success: true };
      }

      return { success: false, error: `IPC channel '${channel}' is not supported in browser mode.` };
    },

    clipboard: {
      writeText(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).catch(() => _fallbackCopy(text));
        } else {
          _fallbackCopy(text);
        }
      }
    },

    shell: {
      openExternal(url) {
        window.open(url, '_blank', 'noopener,noreferrer');
        return Promise.resolve();
      }
    },

    getEnv(key) { return undefined; },
    platform: navigator.platform
  };

  function _fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (_) { /* best effort */ }
    document.body.removeChild(ta);
  }
})();
