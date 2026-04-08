/**
 * API client for backend communication
 */

const BACKEND_URL = `http://localhost:${window.electronAPI?.getEnv('BACKEND_PORT') || 5000}`;

// CSRF token management
let csrfToken = null;

const API = {
    /**
     * Initialize API client and fetch CSRF token
     */
    async init() {
        try {
            // Fetch CSRF token for subsequent requests
            const response = await axios.get(`${BACKEND_URL}/api/csrf`);
            if (response.data && response.data.csrf_token) {
                csrfToken = response.data.csrf_token;
                // Set CSRF token for all future requests
                axios.defaults.headers.common['X-CSRFToken'] = csrfToken;
            }
        } catch (error) {
            console.warn('Failed to fetch CSRF token:', error);
        }
    },

    /**
     * Render markdown content
     */
    async renderMarkdown(content, options = {}) {
        try {
            const response = await axios.post(`${BACKEND_URL}/api/render`, {
                content,
                options
            });
            return response.data;
        } catch (error) {
            console.error('Error rendering markdown:', error);
            throw error;
        }
    },

    /**
     * Open and render a markdown file
     */
    async openFile(filePath) {
        try {
            const response = await axios.post(`${BACKEND_URL}/api/file/open`, {
                path: filePath
            });
            return response.data;
        } catch (error) {
            console.error('Error opening file:', error);
            throw error;
        }
    },

    /**
     * Export to PDF
     */
    async exportPDF(html, filename) {
        try {
            const response = await axios.post(`${BACKEND_URL}/api/export/pdf`, {
                html,
                filename
            }, {
                responseType: 'blob'
            });
            return response.data;
        } catch (error) {
            console.error('Error exporting PDF:', error);
            throw error;
        }
    },

    /**
     * Export to Word
     */
    async exportWord(html, markdown, filename) {
        try {
            const response = await axios.post(`${BACKEND_URL}/api/export/word`, {
                html,
                markdown,
                filename
            }, {
                responseType: 'blob'
            });
            return response.data;
        } catch (error) {
            console.error('Error exporting Word:', error);
            throw error;
        }
    },

    /**
     * Translate content
     */
    async translate(content, sourceLang, targetLang) {
        try {
            const response = await axios.post(`${BACKEND_URL}/api/translate`, {
                content,
                source: sourceLang,
                target: targetLang
            });
            return response.data;
        } catch (error) {
            console.error('Error translating:', error);
            throw error;
        }
    },

    /**
     * Check backend health
     */
    async healthCheck() {
        try {
            const response = await axios.get(`${BACKEND_URL}/api/health`);
            return response.data;
        } catch (error) {
            console.error('Backend not available:', error);
            return { status: 'error' };
        }
    }
};

// Make API available globally
window.MarkdownViewerAPI = API;
