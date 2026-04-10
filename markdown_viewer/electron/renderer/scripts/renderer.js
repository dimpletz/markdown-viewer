/**
 * Markdown renderer with diagram and math support
 */

class MarkdownRenderer {
    constructor() {
        this.init();
    }

    init() {
        // Configure Marked with syntax highlighting via custom renderer
        // Note: marked.setOptions({ highlight }) was removed in marked v8.0.0;
        // use marked.use({ renderer }) instead.
        marked.use({
            breaks: true,
            gfm: true,
            renderer: {
                // marked.use() may call code(token) [v8+ token API] or code(codeStr, lang) [legacy].
                // Handle both by checking the type of the first argument.
                code(tokenOrCode, langArg) {
                    const text = (typeof tokenOrCode === 'object'
                        ? (tokenOrCode?.text ?? '')
                        : (tokenOrCode ?? ''));
                    const lang = (typeof tokenOrCode === 'object'
                        ? (tokenOrCode?.lang ?? '')
                        : (langArg ?? ''));
                    const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
                    try {
                        const highlighted = hljs.highlight(text, { language }).value;
                        return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`;
                    } catch (e) {
                        console.error('Highlight error:', e);
                        // Fall back to escaped plain text to avoid a second crash
                        const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        return `<pre><code class="hljs">${escaped}</code></pre>`;
                    }
                }
            }
        });

        // Configure Mermaid with strict security
        mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'antiscript',
            fontFamily: 'inherit'
        });
    }

    /**
     * Render markdown to HTML
     */
    async render(markdown) {
        try {
            // First pass: Convert markdown to HTML
            let html = marked.parse(markdown);

            // Process mermaid diagrams
            html = this.processMermaidDiagrams(html);

            // Sanitize HTML
            html = DOMPurify.sanitize(html, {
                ADD_TAGS: ['mermaid'],
                ADD_ATTR: ['class']
            });

            return html;
        } catch (error) {
            console.error('Render error:', error);
            throw error;
        }
    }

    /**
     * Process mermaid diagrams
     */
    processMermaidDiagrams(html) {
        // Replace mermaid code blocks with mermaid divs
        const mermaidRegex = /<pre><code class="language-mermaid">([\s\S]*?)<\/code><\/pre>/g;
        
        let counter = 0;
        html = html.replace(mermaidRegex, (match, code) => {
            counter++;
            const id = `mermaid-${Date.now()}-${counter}`;
            const decodedCode = this.decodeHTML(code);
            return `<div class="mermaid" id="${id}">${decodedCode}</div>`;
        });

        return html;
    }

    /**
     * Render mermaid diagrams in DOM
     */
    async renderMermaidDiagrams(container) {
        const mermaidElements = container.querySelectorAll('.mermaid');
        if (mermaidElements.length === 0) return;

        // Reset any previously rendered elements so Mermaid re-processes them
        mermaidElements.forEach(el => {
            el.removeAttribute('data-processed');
            el.innerHTML = el.textContent; // restore raw diagram source
        });

        try {
            // Use Mermaid v10 run() API — it manages IDs and rendering internally
            await mermaid.run({ nodes: Array.from(mermaidElements) });
        } catch (error) {
            console.error('Mermaid render error:', error);
            mermaidElements.forEach(el => {
                if (!el.querySelector('svg')) {
                    el.innerHTML = `<pre style="color: red; padding: 1em;">Diagram error: ${error.message}</pre>`;
                }
            });
        }
    }

    /**
     * Render math equations
     */
    renderMath(container) {
        try {
            renderMathInElement(container, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\[', right: '\\]', display: true},
                    {left: '\\(', right: '\\)', display: false}
                ],
                throwOnError: false
            });
        } catch (error) {
            console.error('Math render error:', error);
        }
    }

    /**
     * Decode HTML entities
     */
    decodeHTML(html) {
        const txt = document.createElement('textarea');
        txt.innerHTML = html;
        return txt.value;
    }
}

// Make renderer available globally
window.MarkdownRenderer = new MarkdownRenderer();
