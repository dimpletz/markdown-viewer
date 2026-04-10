/**
 * Main application logic
 * Uses electronAPI exposed through preload.js for security
 */

class MarkdownViewerApp {
    constructor() {
        this.currentFile = null;
        this.currentMarkdown = '';
        this.currentHTML = '';
        
        this.init();
    }

    init() {
        this.setupUIElements();
        this.setupEventListeners();
        this.checkBackendHealth();
    }

    setupUIElements() {
        // Buttons
        this.btnOpen = document.getElementById('btnOpen');
        this.btnOpenWelcome = document.getElementById('btnOpenWelcome');
        this.btnRefresh = document.getElementById('btnRefresh');
        this.btnExportPdf = document.getElementById('btnExportPdf');
        this.btnExportWord = document.getElementById('btnExportWord');
        this.btnCopyAll = document.getElementById('btnCopyAll');
        this.btnShare = document.getElementById('btnShare');
        this.btnTranslate = document.getElementById('btnTranslate');

        // Containers
        this.welcome = document.getElementById('welcome');
        this.preview = document.getElementById('preview');
        this.statusText = document.getElementById('status-text');
        this.filePath = document.getElementById('file-path');
        this.loadingOverlay = document.getElementById('loading-overlay');

        // Modal
        this.translateModal = document.getElementById('translate-modal');
        this.btnConfirmTranslate = document.getElementById('btnConfirmTranslate');
        this.btnCancelTranslate = document.getElementById('btnCancelTranslate');
        this.sourceLanguage = document.getElementById('sourceLanguage');
        this.targetLanguage = document.getElementById('targetLanguage');
    }

    setupEventListeners() {
        // File operations
        this.btnOpen.addEventListener('click', () => this.openFile());
        this.btnOpenWelcome.addEventListener('click', () => this.openFile());
        this.btnRefresh.addEventListener('click', () => this.refreshPreview());

        // Export operations
        this.btnExportPdf.addEventListener('click', () => this.exportPDF());
        this.btnExportWord.addEventListener('click', () => this.exportWord());

        // Tools
        this.btnCopyAll.addEventListener('click', () => this.copyAll());
        this.btnShare.addEventListener('click', () => this.shareEmail());
        this.btnTranslate.addEventListener('click', () => this.showTranslateDialog());

        // Translate modal
        this.btnConfirmTranslate.addEventListener('click', () => this.performTranslation());
        this.btnCancelTranslate.addEventListener('click', () => this.hideTranslateDialog());
        this.translateModal.querySelector('.close-btn').addEventListener('click', () => this.hideTranslateDialog());

        // IPC listeners
        window.electronAPI.on('open-file', (filePath) => {
            this.loadFile(filePath);
        });

        window.electronAPI.on('export-pdf', () => this.exportPDF());
        window.electronAPI.on('export-word', () => this.exportWord());
        window.electronAPI.on('show-translate', () => this.showTranslateDialog());
        window.electronAPI.on('copy-all', () => this.copyAll());
        window.electronAPI.on('share-email', () => this.shareEmail());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 'o') {
                    e.preventDefault();
                    this.openFile();
                } else if (e.shiftKey && e.key === 'C') {
                    e.preventDefault();
                    this.copyAll();
                }
            }
        });
    }

    async checkBackendHealth() {
        const health = await window.MarkdownViewerAPI.healthCheck();
        if (health.status === 'ok') {
            this.setStatus('Backend connected');
        } else {
            this.setStatus('Backend unavailable - some features may not work', 'warning');
        }
        const pdfAvailable = health.capabilities?.pdf_export !== false;
        if (!pdfAvailable) {
            this.btnExportPdf.style.display = 'none';
        }
    }

    async openFile() {
        // Trigger Electron file dialog
        const result = await window.electronAPI.invoke('show-open-dialog', {
            properties: ['openFile'],
            filters: [
                { name: 'Markdown', extensions: ['md', 'markdown', 'mdown'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });
        
        if (!result.canceled && result.filePaths && result.filePaths.length > 0) {
            this.loadFile(result.filePaths[0]);
        }
    }

    /**
     * Load a file by absolute path via the backend API.
     * Used when the file path is known server-side (CLI ?file= param, or Electron IPC).
     */
    async loadFileFromServer(filePath) {
        try {
            this.showLoading();
            this.setStatus('Loading file...');

            const result = await window.MarkdownViewerAPI.openFile(filePath);

            if (result.success) {
                this.currentFile = filePath;
                this._loadedFromServer = true;
                this.currentMarkdown = result.content;
                this.currentHTML = result.html || '';

                if (result.html) {
                    // Backend already rendered — display directly
                    const sanitized = DOMPurify.sanitize(result.html, {
                        ADD_TAGS: ['mermaid'],
                        ADD_ATTR: ['class', 'id', 'href']
                    });
                    this.currentHTML = sanitized;
                    this.preview.innerHTML = this.currentHTML;
                    await window.MarkdownRenderer.renderMermaidDiagrams(this.preview);
                    window.MarkdownRenderer.renderMath(this.preview);
                } else {
                    await this.renderMarkdown();
                }

                this.setStatus('File loaded successfully');
                this.filePath.textContent = filePath;
                this.welcome.style.display = 'none';
                this.preview.style.display = 'block';
            } else {
                throw new Error(result.error?.message || 'Failed to load file');
            }
        } catch (error) {
            console.error('Error loading file from server:', error);
            this.setStatus(`Error: ${error.message}`, 'error');
            alert(`Failed to load file: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async loadFile(filePath) {
        try {
            this.showLoading();
            this.setStatus('Loading file...');

            // Read file using IPC
            const result = await window.electronAPI.invoke('read-file', filePath);
            
            if (result.success) {
                this.currentFile = filePath;
                this.currentMarkdown = result.content;
                
                await this.renderMarkdown();
                
                this.setStatus('File loaded successfully');
                this.filePath.textContent = filePath;
                
                // Hide welcome, show preview
                this.welcome.style.display = 'none';
                this.preview.style.display = 'block';
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error loading file:', error);
            this.setStatus(`Error: ${error.message}`, 'error');
            alert(`Failed to load file: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async renderMarkdown() {
        try {
            this.showLoading();
            this.setStatus('Rendering markdown...');

            // Use the backend for full-featured rendering (TOC, emojis, diagrams, math)
            let html;
            try {
                const result = await window.MarkdownViewerAPI.renderMarkdown(this.currentMarkdown);
                html = result.html || '';
            } catch (apiError) {
                // Fallback to client-side renderer if backend is unavailable
                console.warn('Backend render failed, falling back to client-side:', apiError);
                html = await window.MarkdownRenderer.render(this.currentMarkdown);
            }

            // SECURITY: Sanitize HTML — allow class/id attrs needed for TOC anchors and diagrams
            const sanitized = DOMPurify.sanitize(html, {
                ADD_TAGS: ['mermaid'],
                ADD_ATTR: ['class', 'id', 'href']
            });

            // Only update the DOM once we have a valid result
            this.currentHTML = sanitized;
            this.preview.innerHTML = this.currentHTML;
            
            // Render mermaid diagrams
            await window.MarkdownRenderer.renderMermaidDiagrams(this.preview);
            
            // Render math
            window.MarkdownRenderer.renderMath(this.preview);
            
            this.setStatus('Render complete');
            return true;
        } catch (error) {
            console.error('Error rendering markdown:', error);
            this.setStatus(`Render error: ${error.message}`, 'error');
            // Preserve whatever was previously displayed — do not blank the preview
            return false;
        } finally {
            this.hideLoading();
        }
    }

    async refreshPreview() {
        if (this.currentFile) {
            // If loaded from server path (absolute path), reload via server
            if (this._loadedFromServer) {
                await this.loadFileFromServer(this.currentFile);
            } else {
                await this.loadFile(this.currentFile);
            }
        }
    }

    async exportPDF() {
        if (!this.currentHTML) {
            alert('No content to export');
            return;
        }

        try {
            this.showLoading();
            this.setStatus('Exporting to PDF...');

            const fileName = window.path.basename(this.currentFile || 'document', '.md') + '.pdf';
            
            const result = await window.electronAPI.invoke('show-save-dialog', {
                defaultPath: fileName,
                filters: [{ name: 'PDF', extensions: ['pdf'] }]
            });

            if (!result.canceled) {
                const blob = await window.MarkdownViewerAPI.exportPDF(this.currentHTML, fileName);
                
                // Save blob to file via validated IPC (path-checked in main process)
                const arrayBuffer = await blob.arrayBuffer();
                const saveResult = await window.electronAPI.invoke('save-export-file', result.filePath, new Uint8Array(arrayBuffer));
                if (!saveResult.success) throw new Error(saveResult.error || 'Failed to save PDF');
                
                this.setStatus('PDF exported successfully');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.setStatus(`Export error: ${error.message}`, 'error');
            alert(`Failed to export PDF: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async exportWord() {
        if (!this.currentHTML || !this.currentMarkdown) {
            alert('No content to export');
            return;
        }

        try {
            this.showLoading();
            this.setStatus('Exporting to Word...');

            const fileName = window.path.basename(this.currentFile || 'document', '.md') + '.docx';
            
            const result = await window.electronAPI.invoke('show-save-dialog', {
                defaultPath: fileName,
                filters: [{ name: 'Word Document', extensions: ['docx'] }]
            });

            if (!result.canceled) {
                const blob = await window.MarkdownViewerAPI.exportWord(
                    this.currentHTML,
                    this.currentMarkdown,
                    fileName
                );
                
                // Save blob to file via validated IPC (path-checked in main process)
                const arrayBuffer = await blob.arrayBuffer();
                const saveResult = await window.electronAPI.invoke('save-export-file', result.filePath, new Uint8Array(arrayBuffer));
                if (!saveResult.success) throw new Error(saveResult.error || 'Failed to save Word document');
                
                this.setStatus('Word document exported successfully');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.setStatus(`Export error: ${error.message}`, 'error');
            alert(`Failed to export Word: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    copyAll() {
        if (!this.currentMarkdown) {
            alert('No content to copy');
            return;
        }

        window.electronAPI.clipboard.writeText(this.currentMarkdown);
        
        this.setStatus('Content copied to clipboard');
        
        // Show temporary notification
        const originalText = this.btnCopyAll.innerHTML;
        this.btnCopyAll.innerHTML = '<span class="icon">✓</span> Copied!';
        setTimeout(() => {
            this.btnCopyAll.innerHTML = originalText;
        }, 2000);
    }

    shareEmail() {
        if (!this.currentMarkdown) {
            alert('No content to share');
            return;
        }

        const filename = window.path.basename(this.currentFile || 'document.md');
        // Ensure filename ends with .md
        const attachmentName = filename.endsWith('.md') ? filename : filename + '.md';

        // Step 1: download the .md file so the user can attach it
        const blob = new Blob([this.currentMarkdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = attachmentName;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 2000);

        // Step 2: open the email client — mailto: cannot carry attachments,
        // so guide the user to attach the just-downloaded file
        const subject = encodeURIComponent(attachmentName);
        const body = encodeURIComponent(
            `Please see the attached markdown document.\n\n` +
            `(The file "${attachmentName}" has been downloaded — please attach it to this email.)`
        );
        const mailtoLink = `mailto:?subject=${subject}&body=${body}`;
        window.electronAPI.shell.openExternal(mailtoLink);

        this.setStatus(`Email client opened — attach "${attachmentName}" from your Downloads folder`);
    }

    showTranslateDialog() {
        if (!this.currentMarkdown) {
            alert('No content to translate');
            return;
        }
        this.translateModal.style.display = 'flex';
    }

    hideTranslateDialog() {
        this.translateModal.style.display = 'none';
    }

    async performTranslation() {
        const previousMarkdown = this.currentMarkdown;
        try {
            this.hideTranslateDialog();
            this.showLoading();
            this.setStatus('Translating content...');

            const sourceLang = this.sourceLanguage.value;
            const targetLang = this.targetLanguage.value;

            const TRANSLATE_TIMEOUT_MS = 60000;
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error(
                    'Translation timed out after 60 seconds. Try a smaller document or check your network.'
                )), TRANSLATE_TIMEOUT_MS)
            );

            const result = await Promise.race([
                window.MarkdownViewerAPI.translate(
                    this.currentMarkdown,
                    sourceLang,
                    targetLang
                ),
                timeoutPromise
            ]);

            if (result.success && result.translated) {
                // Render translated content; only commit if render succeeds
                const savedMarkdown = this.currentMarkdown;
                this.currentMarkdown = result.translated;
                const ok = await this.renderMarkdown();
                if (!ok) {
                    // Render failed — restore original markdown
                    this.currentMarkdown = savedMarkdown;
                } else {
                    this.setStatus('Translation complete');
                }
            } else {
                const msg = (typeof result.error === 'object'
                    ? JSON.stringify(result.error)
                    : result.error) || 'Translation failed';
                throw new Error(msg);
            }
        } catch (error) {
            console.error('Translation error:', error);
            this.currentMarkdown = previousMarkdown; // always restore on exception
            // Try to extract the detailed message from a JSON error response body
            const detail = error.response?.data?.error?.message || error.message;
            this.setStatus(`Translation error: ${detail}`, 'error');
            alert(`Failed to translate: ${detail}`);
        } finally {
            this.hideLoading();
        }
    }

    showLoading() {
        this.loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }

    setStatus(text, type = 'info') {
        this.statusText.textContent = text;
        this.statusText.style.color = type === 'error' ? 'red' : 
                                      type === 'warning' ? 'orange' : 
                                      'inherit';
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize API client (fetch CSRF token)
    await window.MarkdownViewerAPI.init();
    
    // Create and initialize app
    window.app = new MarkdownViewerApp();

    // Auto-load file passed via ?file= URL parameter (browser/CLI mode)
    const urlFile = new URLSearchParams(window.location.search).get('file');
    if (urlFile) {
        window.app.loadFileFromServer(urlFile);
    } else {
        // No file param — show the welcome screen
        const welcome = document.getElementById('welcome');
        if (welcome) welcome.style.display = '';
    }
});
