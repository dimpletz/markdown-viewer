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

        // Configure Mermaid for cross-version compatibility (v8/v9/v10/v11 syntax)
        mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'antiscript',
            fontFamily: 'inherit',
            suppressErrors: true
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
     * Normalize diagram source for cross-version compatibility.
     * Decodes HTML entities that may be introduced by the markdown pipeline
     * and strips leading/trailing whitespace.
     */
    normalizeMermaidSource(source) {
        return source
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .trim();
    }

    /**
     * Render mermaid diagrams in DOM with per-diagram error isolation.
     * Each diagram is rendered independently so a single bad diagram
     * does not prevent the others from displaying.
     */
    async renderMermaidDiagrams(container) {
        const mermaidElements = container.querySelectorAll('.mermaid');
        if (mermaidElements.length === 0) return;

        let counter = 0;
        for (const el of mermaidElements) {
            // Restore and normalise the raw source text
            const rawSource = el.textContent || el.innerText || '';
            const source = this.normalizeMermaidSource(rawSource);
            el.textContent = source;
            el.removeAttribute('data-processed');

            try {
                const id = `mermaid-${Date.now()}-${counter++}`;
                const { svg } = await mermaid.render(id, source);
                el.innerHTML = svg;
            } catch (error) {
                console.warn('Mermaid diagram render failed:', error.message || error);
                const escaped = source
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
                el.innerHTML =
                    `<details style="border:1px solid #fca;background:#fff8f5;border-radius:4px;padding:8px">` +
                    `<summary style="cursor:pointer;color:#c60;font-weight:bold">` +
                    `\u26a0 Diagram could not be rendered (click to view source)</summary>` +
                    `<pre style="margin:8px 0 0;overflow:auto;font-size:13px">${escaped}</pre></details>`;
            }
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
