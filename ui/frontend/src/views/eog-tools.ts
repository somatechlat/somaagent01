/**
 * Eye of God Tools View
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Tool catalog display
 * - Tool invocation
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import '../components/eog-card.js';
import '../components/eog-input.js';
import '../components/eog-modal.js';

interface ToolParameter {
    name: string;
    type: string;
    description: string;
    required: boolean;
    default?: unknown;
}

interface Tool {
    id: string;
    name: string;
    description: string;
    category: string;
    parameters: ToolParameter[];
    requires_permission?: string;
    is_enabled: boolean;
    is_dangerous: boolean;
}

interface ToolResult {
    tool_id: string;
    success: boolean;
    result?: unknown;
    error?: string;
    duration_ms: number;
}

@customElement('eog-tools')
export class EogTools extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: var(--eog-spacing-lg, 24px);
            height: 100%;
            overflow-y: auto;
        }

        .tools-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-lg, 24px);
        }

        h1 {
            font-size: var(--eog-text-2xl, 24px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0;
        }

        .search-bar {
            display: flex;
            gap: var(--eog-spacing-md, 16px);
            margin-bottom: var(--eog-spacing-lg, 24px);
        }

        .search-input {
            flex: 1;
            max-width: 400px;
        }

        .categories {
            display: flex;
            flex-wrap: wrap;
            gap: var(--eog-spacing-sm, 8px);
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .category-chip {
            padding: var(--eog-spacing-xs, 4px) var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-full, 9999px);
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            color: var(--eog-text-dim, #64748b);
            font-size: var(--eog-text-sm, 13px);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .category-chip:hover {
            border-color: var(--eog-accent, #94a3b8);
        }

        .category-chip.active {
            background: var(--eog-accent, #94a3b8);
            color: var(--eog-bg-void, #0f172a);
            border-color: var(--eog-accent, #94a3b8);
        }

        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: var(--eog-spacing-lg, 24px);
        }

        .tool-card {
            position: relative;
        }

        .tool-header {
            display: flex;
            align-items: flex-start;
            gap: var(--eog-spacing-sm, 8px);
            margin-bottom: var(--eog-spacing-sm, 8px);
        }

        .tool-icon {
            font-size: 24px;
        }

        .tool-info {
            flex: 1;
        }

        .tool-name {
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
        }

        .tool-category {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-accent, #94a3b8);
            text-transform: uppercase;
        }

        .tool-description {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
            line-height: 1.5;
            margin-bottom: var(--eog-spacing-md, 16px);
        }

        .tool-params {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
            margin-bottom: var(--eog-spacing-md, 16px);
        }

        .tool-badges {
            display: flex;
            gap: var(--eog-spacing-xs, 4px);
            position: absolute;
            top: var(--eog-spacing-md, 16px);
            right: var(--eog-spacing-md, 16px);
        }

        .badge {
            padding: 2px 8px;
            border-radius: var(--eog-radius-sm, 4px);
            font-size: var(--eog-text-xs, 11px);
            font-weight: 600;
        }

        .badge.dangerous {
            background: rgba(239, 68, 68, 0.2);
            color: var(--eog-danger, #ef4444);
        }

        .badge.permission {
            background: rgba(148, 163, 184, 0.2);
            color: var(--eog-accent, #94a3b8);
        }

        .tool-actions {
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
        }

        .invoke-modal {
            min-width: 500px;
        }

        .param-form {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-md, 16px);
        }

        .result-box {
            background: var(--eog-bg-base, #1e293b);
            border-radius: var(--eog-radius-md, 8px);
            padding: var(--eog-spacing-md, 16px);
            font-family: monospace;
            font-size: var(--eog-text-sm, 13px);
            max-height: 200px;
            overflow-y: auto;
        }

        .result-success {
            border: 1px solid var(--eog-success, #22c55e);
        }

        .result-error {
            border: 1px solid var(--eog-danger, #ef4444);
            color: var(--eog-danger, #ef4444);
        }

        .duration {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
            margin-top: var(--eog-spacing-sm, 8px);
        }
    `;

    @state() private _tools: Tool[] = [];
    @state() private _categories: string[] = [];
    @state() private _selectedCategory: string | null = null;
    @state() private _searchQuery = '';
    @state() private _isLoading = false;
    @state() private _invokeModalOpen = false;
    @state() private _selectedTool: Tool | null = null;
    @state() private _invokeParams: Record<string, unknown> = {};
    @state() private _invokeResult: ToolResult | null = null;
    @state() private _isInvoking = false;

    private _categoryIcons: Record<string, string> = {
        search: '🔍',
        code: '💻',
        filesystem: '📁',
        memory: '🧠',
        network: '🌐',
        utility: '🛠️',
        general: '⚙️',
    };

    connectedCallback() {
        super.connectedCallback();
        this._loadTools();
        this._loadCategories();
    }

    render() {
        const filteredTools = this._getFilteredTools();

        return html`
            <header class="tools-header">
                <h1>🔧 Tool Catalog</h1>
            </header>

            <div class="search-bar">
                <eog-input
                    class="search-input"
                    placeholder="Search tools..."
                    .value=${this._searchQuery}
                    @eog-input=${(e: CustomEvent) => this._searchQuery = e.detail.value}
                ></eog-input>
            </div>

            <div class="categories">
                <button
                    class="category-chip ${!this._selectedCategory ? 'active' : ''}"
                    @click=${() => this._selectedCategory = null}
                >
                    All
                </button>
                ${this._categories.map(cat => html`
                    <button
                        class="category-chip ${this._selectedCategory === cat ? 'active' : ''}"
                        @click=${() => this._selectedCategory = cat}
                    >
                        ${this._categoryIcons[cat] || '📦'} ${cat}
                    </button>
                `)}
            </div>

            <div class="tools-grid">
                ${filteredTools.map(tool => this._renderToolCard(tool))}
            </div>

            ${this._invokeModalOpen ? this._renderInvokeModal() : ''}
        `;
    }

    private _renderToolCard(tool: Tool) {
        const icon = this._categoryIcons[tool.category] || '📦';

        return html`
            <eog-card class="tool-card">
                <div class="tool-badges">
                    ${tool.is_dangerous ? html`<span class="badge dangerous">⚠️ Dangerous</span>` : ''}
                    ${tool.requires_permission ? html`<span class="badge permission">🔒</span>` : ''}
                </div>
                <div class="tool-header">
                    <span class="tool-icon">${icon}</span>
                    <div class="tool-info">
                        <div class="tool-name">${tool.name}</div>
                        <div class="tool-category">${tool.category}</div>
                    </div>
                </div>
                <div class="tool-description">${tool.description}</div>
                <div class="tool-params">
                    ${tool.parameters.length} parameter${tool.parameters.length !== 1 ? 's' : ''}
                </div>
                <div class="tool-actions">
                    <eog-button size="small" @click=${() => this._openInvokeModal(tool)}>
                        Invoke
                    </eog-button>
                    <eog-button size="small" variant="secondary" @click=${() => this._viewDetails(tool)}>
                        Details
                    </eog-button>
                </div>
            </eog-card>
        `;
    }

    private _renderInvokeModal() {
        if (!this._selectedTool) return '';

        return html`
            <eog-modal 
                class="invoke-modal"
                .open=${this._invokeModalOpen}
                title="Invoke: ${this._selectedTool.name}"
                @eog-close=${() => this._invokeModalOpen = false}
            >
                <div class="param-form">
                    ${this._selectedTool.parameters.map(param => html`
                        <eog-input
                            label="${param.name}${param.required ? ' *' : ''}"
                            placeholder="${param.description}"
                            .value=${String(this._invokeParams[param.name] ?? param.default ?? '')}
                            @eog-input=${(e: CustomEvent) => this._invokeParams[param.name] = e.detail.value}
                        ></eog-input>
                    `)}
                </div>

                ${this._invokeResult ? html`
                    <div class="result-box ${this._invokeResult.success ? 'result-success' : 'result-error'}">
                        ${this._invokeResult.success
                    ? JSON.stringify(this._invokeResult.result, null, 2)
                    : this._invokeResult.error}
                    </div>
                    <div class="duration">Completed in ${this._invokeResult.duration_ms}ms</div>
                ` : ''}

                <div slot="footer">
                    <eog-button 
                        @click=${this._invokeTool} 
                        ?loading=${this._isInvoking}
                        ?disabled=${this._isInvoking}
                    >
                        Execute
                    </eog-button>
                    <eog-button variant="secondary" @click=${() => this._invokeModalOpen = false}>
                        Close
                    </eog-button>
                </div>
            </eog-modal>
        `;
    }

    private async _loadTools() {
        this._isLoading = true;
        try {
            const response = await fetch('/api/v2/tools/', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) {
                this._tools = await response.json();
            }
        } catch (error) {
            console.error('Failed to load tools:', error);
        } finally {
            this._isLoading = false;
        }
    }

    private async _loadCategories() {
        try {
            const response = await fetch('/api/v2/tools/categories', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) {
                this._categories = await response.json();
            }
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    private _getFilteredTools(): Tool[] {
        let tools = this._tools;

        if (this._selectedCategory) {
            tools = tools.filter(t => t.category === this._selectedCategory);
        }

        if (this._searchQuery) {
            const query = this._searchQuery.toLowerCase();
            tools = tools.filter(t =>
                t.name.toLowerCase().includes(query) ||
                t.description.toLowerCase().includes(query)
            );
        }

        return tools;
    }

    private _openInvokeModal(tool: Tool) {
        this._selectedTool = tool;
        this._invokeParams = {};
        this._invokeResult = null;
        this._invokeModalOpen = true;
    }

    private async _invokeTool() {
        if (!this._selectedTool) return;

        this._isInvoking = true;
        try {
            const response = await fetch('/api/v2/tools/invoke', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}`
                },
                body: JSON.stringify({
                    tool_id: this._selectedTool.id,
                    parameters: this._invokeParams,
                }),
            });

            this._invokeResult = await response.json();
        } catch (error) {
            this._invokeResult = {
                tool_id: this._selectedTool.id,
                success: false,
                error: 'Failed to invoke tool',
                duration_ms: 0,
            };
        } finally {
            this._isInvoking = false;
        }
    }

    private _viewDetails(tool: Tool) {
        this.dispatchEvent(new CustomEvent('eog-navigate', {
            detail: { path: `/tools/${tool.id}` },
            bubbles: true, composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-tools': EogTools;
    }
}
