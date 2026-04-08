/**
 * Main Electron process
 */

const { app, BrowserWindow, Menu, dialog, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;
const BACKEND_PORT = process.env.BACKEND_PORT || 5000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

/**
 * Validates that a file path is within the allowed directory.
 * Returns { valid: true, resolvedPath } or { valid: false, error }.
 */
function validateFilePath(filePath) {
  const os = require('os');
  const allowedDir = process.env.ALLOWED_DOCUMENTS_DIR || os.homedir();
  const resolvedPath = path.resolve(filePath);
  const resolvedAllowed = path.resolve(allowedDir);

  const normalizedPath = resolvedPath.toLowerCase();
  const normalizedAllowed = (resolvedAllowed.endsWith(path.sep)
    ? resolvedAllowed
    : resolvedAllowed + path.sep).toLowerCase();

  if (!normalizedPath.startsWith(normalizedAllowed)) {
    return { valid: false, error: 'Access denied: path outside allowed directory' };
  }
  return { valid: true, resolvedPath };
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  // Load the index.html
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // Create application menu
  createMenu();

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            openFile();
          }
        },
        {
          label: 'Export',
          submenu: [
            {
              label: 'Export as PDF',
              click: () => {
                mainWindow.webContents.send('export-pdf');
              }
            },
            {
              label: 'Export as Word',
              click: () => {
                mainWindow.webContents.send('export-word');
              }
            }
          ]
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Tools',
      submenu: [
        {
          label: 'Translate',
          click: () => {
            mainWindow.webContents.send('show-translate');
          }
        },
        {
          label: 'Copy All',
          accelerator: 'CmdOrCtrl+Shift+C',
          click: () => {
            mainWindow.webContents.send('copy-all');
          }
        },
        {
          label: 'Share via Email',
          click: () => {
            mainWindow.webContents.send('share-email');
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => {
            require('electron').shell.openExternal('https://github.com/dimpletz/markdown-viewer');
          }
        },
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Markdown Viewer',
              message: 'Markdown Viewer v1.0.0',
              detail: 'Advanced markdown viewer with translation, diagram rendering, and export capabilities.'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

async function openFile() {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Markdown', extensions: ['md', 'markdown', 'mdown'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });

  if (!result.canceled && result.filePaths.length > 0) {
    const filePath = result.filePaths[0];
    mainWindow.webContents.send('open-file', filePath);
  }
}

// IPC handlers
ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const validation = validateFilePath(filePath);
    if (!validation.valid) {
      return { success: false, error: validation.error };
    }
    const content = fs.readFileSync(validation.resolvedPath, 'utf-8');
    return { success: true, content };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('save-file', async (event, filePath, content) => {
  try {
    const validation = validateFilePath(filePath);
    if (!validation.valid) {
      return { success: false, error: validation.error };
    }
    fs.writeFileSync(validation.resolvedPath, content, 'utf-8');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  return await dialog.showSaveDialog(mainWindow, options);
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  return await dialog.showOpenDialog(mainWindow, options);
});

ipcMain.handle('save-export-file', async (event, filePath, data) => {
  try {
    const validation = validateFilePath(filePath);
    if (!validation.valid) {
      return { success: false, error: validation.error };
    }
    fs.writeFileSync(validation.resolvedPath, Buffer.from(data));
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

app.whenReady().then(() => {
  createWindow();

  // Handle file argument from command line
  if (process.env.MARKDOWN_FILE) {
    setTimeout(() => {
      mainWindow.webContents.send('open-file', process.env.MARKDOWN_FILE);
    }, 1000);
  }

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
