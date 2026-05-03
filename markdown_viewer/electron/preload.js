/**
 * Preload script for Electron with context isolation
 * Exposes safe IPC methods to renderer process
 */

const { contextBridge, ipcRenderer } = require("electron");

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld("electronAPI", {
  // Generic IPC methods
  invoke: (channel, ...args) => {
    // Whitelist allowed channels
    const validChannels = [
      "read-file",
      "save-file",
      "save-export-file",
      "show-save-dialog",
      "show-open-dialog",
      "read-image-as-dataurl",
      "open-new-window",
    ];
    if (validChannels.includes(channel)) {
      return ipcRenderer.invoke(channel, ...args);
    }
    throw new Error(`Invalid IPC channel: ${channel}`);
  },

  on: (channel, callback) => {
    // Whitelist allowed event channels
    const validChannels = [
      "open-file",
      "export-pdf",
      "export-word",
      "show-translate",
      "copy-all",
      "share-email",
    ];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (_event, ...args) => callback(...args));
      return () => ipcRenderer.removeListener(channel, callback);
    }
    throw new Error(`Invalid event channel: ${channel}`);
  },

  // Utilities
  getEnv: (key) => process.env[key],
  platform: process.platform,

  // Clipboard access (safe)
  clipboard: {
    writeText: (text) => {
      const { clipboard } = require("electron");
      clipboard.writeText(text);
    },
  },

  // Shell operations (safe subset)
  shell: {
    openExternal: (url) => {
      // Validate URL before opening
      try {
        const urlObj = new URL(url);
        if (
          urlObj.protocol === "http:" ||
          urlObj.protocol === "https:" ||
          urlObj.protocol === "mailto:"
        ) {
          const { shell } = require("electron");
          return shell.openExternal(url);
        }
        throw new Error("Invalid protocol");
      } catch (e) {
        console.error("Invalid URL:", e);
        return Promise.reject(e);
      }
    },
  },
});

// Expose Node.js path utilities (safe)
contextBridge.exposeInMainWorld("path", {
  basename: (p, ext) => require("path").basename(p, ext),
  dirname: (p) => require("path").dirname(p),
  extname: (p) => require("path").extname(p),
  join: (...args) => require("path").join(...args),
});

// Expose safe fs utilities (read-only; file writes go through validated IPC)
contextBridge.exposeInMainWorld("fs", {
  existsSync: (p) => require("fs").existsSync(p),
});

// Expose Buffer for binary data handling
contextBridge.exposeInMainWorld("Buffer", {
  from: (data) => Buffer.from(data),
});
