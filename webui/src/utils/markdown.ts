/**
 * Lightweight, XSS-safe markdown renderer for chat bubbles.
 *
 * Supports: fenced code blocks, inline code, bold, italic, strikethrough,
 * links, unordered/ordered lists, headings, blockquotes, horizontal rules,
 * and paragraphs. All input is HTML-escaped before any markup is applied.
 */

export interface MarkdownOptions {
    /** Called for each fenced code block so the host can add a copy button. */
    onCodeBlock?: (lang: string, code: string) => string;
}

/**
 * Render one fenced code block: language chip + working copy button + body.
 *
 * This is the `onCodeBlock` implementation hosts pass into `renderMarkdown`.
 * The copy button carries `data-md-copy` and the raw source in `data-md-code`
 * so a delegated click handler on the host can copy without inline JS (which
 * would be an XSS vector through `unsafeHTML`).
 *
 * Honesty: this adds a language chip and a copy affordance. It does NOT claim
 * token-level syntax highlighting — no highlighter ships in this bundle
 * (SOMA-01-UIUX-001 UI-X-04 honesty notes).
 */
export function renderCodeBlock(lang: string, code: string): string {
    const label = lang || 'text';
    // data-md-code holds the escaped source; the click handler decodes textContent.
    return (
        `<div class="md-codeblock-wrap">` +
        `<div class="md-codeblock-bar">` +
        `<span class="md-codeblock-lang">${escapeHtml(label)}</span>` +
        `<button type="button" class="md-copy-btn" data-md-copy title="Copy code">Copy</button>` +
        `</div>` +
        `<pre class="md-pre"><code class="md-codeblock" data-md-code>${escapeHtml(code)}</code></pre>` +
        `</div>`
    );
}

/**
 * Attach a delegated copy handler to a container that holds `renderCodeBlock`
 * output. Returns a cleanup function. Uses textContent of the paired
 * `[data-md-code]` node — never reads the HTML — so copied output is the real
 * source, not the escaped markup.
 */
export function bindCodeCopy(container: HTMLElement): () => void {
    const onClick = (event: Event) => {
        const target = event.target as HTMLElement | null;
        const btn = target?.closest?.('[data-md-copy]') as HTMLElement | null;
        if (!btn || !container.contains(btn)) return;
        const wrap = btn.closest('.md-codeblock-wrap');
        const codeEl = wrap?.querySelector('[data-md-code]');
        const text = codeEl?.textContent ?? '';
        if (!text) return;
        void navigator.clipboard.writeText(text).then(() => {
            const prev = btn.textContent;
            btn.textContent = 'Copied';
            setTimeout(() => {
                btn.textContent = prev;
            }, 1500);
        }).catch((err) => {
            console.warn('[Markdown] clipboard write failed', err);
        });
    };
    container.addEventListener('click', onClick);
    return () => container.removeEventListener('click', onClick);
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderInline(escaped: string): string {
    let out = escaped;
    // Inline code first so other transforms don't touch its contents.
    out = out.replace(/`([^`\n]+)`/g, (_m, code: string) => `<code class="md-code">${code}</code>`);
    // Bold **text** or __text__
    out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    // Italic *text* or _text_ (avoid clashing with bold leftovers)
    out = out.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
    out = out.replace(/(^|[^_])_([^_\n]+)_(?!_)/g, '$1<em>$2</em>');
    // Strikethrough ~~text~~
    out = out.replace(/~~([^~]+)~~/g, '<del>$1</del>');
    // Links [text](url) — only http(s) and relative paths, no javascript:
    out = out.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_m, text: string, href: string) => {
        const safe = /^(https?:\/\/|\/|#|mailto:)/i.test(href) ? href : '#';
        const external = /^https?:\/\//i.test(safe);
        const attrs = external ? ' target="_blank" rel="noopener noreferrer"' : '';
        return `<a href="${safe}"${attrs} class="md-link">${text}</a>`;
    });
    return out;
}

/**
 * Render a markdown-ish string to sanitized HTML.
 * The result is safe to inject via lit's `unsafeHTML` because every input
 * character is escaped before markup is reintroduced.
 */
export function renderMarkdown(source: string, options: MarkdownOptions = {}): string {
    if (!source) return '';

    const codeBlocks: string[] = [];
    // Extract fenced code blocks first so inline rules can't mangle them.
    let working = source.replace(/```([\w+-]*)\n?([\s\S]*?)```/g, (_m, lang: string, code: string) => {
        const idx = codeBlocks.length;
        const body = code.replace(/\n$/, '');
        codeBlocks.push(options.onCodeBlock
            ? options.onCodeBlock(lang || '', body)
            : `<pre class="md-pre"><code class="md-codeblock">${escapeHtml(body)}</code></pre>`);
        return `\u0000CODE${idx}\u0000`;
    });

    // Also support single-line ```code``` without a language.
    working = working.replace(/```([^`\n]+)```/g, (_m, code: string) => {
        const idx = codeBlocks.length;
        codeBlocks.push(options.onCodeBlock
            ? options.onCodeBlock('', code)
            : `<pre class="md-pre"><code class="md-codeblock">${escapeHtml(code)}</code></pre>`);
        return `\u0000CODE${idx}\u0000`;
    });

    const lines = working.split('\n');
    const htmlParts: string[] = [];
    let paragraph: string[] = [];
    let listType: 'ul' | 'ol' | null = null;
    let inQuote = false;

    const flushParagraph = () => {
        if (paragraph.length > 0) {
            htmlParts.push(`<p>${renderInline(paragraph.join(' '))}</p>`);
            paragraph = [];
        }
    };

    const closeList = () => {
        if (listType) {
            htmlParts.push(`</${listType}>`);
            listType = null;
        }
    };

    const closeQuote = () => {
        if (inQuote) {
            htmlParts.push('</blockquote>');
            inQuote = false;
        }
    };

    for (const rawLine of lines) {
        const line = rawLine.trimEnd();

        // Restored code block placeholder
        const codeMatch = line.match(/^\u0000CODE(\d+)\u0000$/);
        if (codeMatch) {
            flushParagraph();
            closeList();
            closeQuote();
            htmlParts.push(codeBlocks[Number(codeMatch[1])] ?? '');
            continue;
        }

        if (line.trim() === '') {
            flushParagraph();
            closeList();
            closeQuote();
            continue;
        }

        // Horizontal rule
        if (/^(-{3,}|\*{3,}|_{3,})$/.test(line.trim())) {
            flushParagraph();
            closeList();
            closeQuote();
            htmlParts.push('<hr class="md-hr"/>');
            continue;
        }

        // Heading
        const heading = line.match(/^(#{1,6})\s+(.*)$/);
        if (heading) {
            flushParagraph();
            closeList();
            closeQuote();
            const level = heading[1].length;
            htmlParts.push(`<h${level} class="md-h md-h${level}">${renderInline(heading[2])}</h${level}>`);
            continue;
        }

        // Blockquote
        if (line.startsWith('>')) {
            flushParagraph();
            closeList();
            const text = line.replace(/^>\s?/, '');
            if (!inQuote) {
                htmlParts.push('<blockquote class="md-quote">');
                inQuote = true;
            }
            htmlParts.push(`<p>${renderInline(text)}</p>`);
            continue;
        } else if (inQuote && !line.startsWith('>')) {
            closeQuote();
        }

        // Unordered list
        const ul = line.match(/^[-*+]\s+(.*)$/);
        if (ul) {
            flushParagraph();
            if (listType !== 'ul') {
                closeList();
                htmlParts.push('<ul class="md-ul">');
                listType = 'ul';
            }
            htmlParts.push(`<li>${renderInline(ul[1])}</li>`);
            continue;
        }

        // Ordered list
        const ol = line.match(/^\d+[.)]\s+(.*)$/);
        if (ol) {
            flushParagraph();
            if (listType !== 'ol') {
                closeList();
                htmlParts.push('<ol class="md-ol">');
                listType = 'ol';
            }
            htmlParts.push(`<li>${renderInline(ol[1])}</li>`);
            continue;
        }

        closeList();
        paragraph.push(line.trim());
    }

    flushParagraph();
    closeList();
    closeQuote();

    return htmlParts.join('\n');
}

/** Format a byte count for attachment chips. */
export function formatBytes(bytes: number): string {
    if (!Number.isFinite(bytes) || bytes < 0) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Format an ISO timestamp as a short locale time. */
export function formatTime(iso: string): string {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/** Format an ISO timestamp as a relative "3m ago" label for sidebar rows. */
export function formatRelative(iso: string): string {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    const diff = Date.now() - d.getTime();
    if (diff < 60_000) return 'just now';
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
    if (diff < 604_800_000) return `${Math.floor(diff / 86_400_000)}d ago`;
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}
