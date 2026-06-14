/**
 * SomaAgent SaaS — Memory View
 * Per AGENT_USER_UI_SRS.md Section 8 and UI_SCREENS_SRS.md
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - SomaBrain API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import {
    MemoryViewController,
    type Memory,
    type MemoryFilter,
    type MemorySort,
} from '../controllers/memory-view-controller.js';
import '../components/saas-memory-search-bar.js';
import '../components/saas-memory-list.js';
import '../components/saas-memory-detail-panel.js';

export type { Memory, MemoryFilter, MemorySort };

@customElement('saas-memory-view')
export class SaasMemoryView extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * {
            box-sizing: border-box;
        }

        .main {
            flex: 1;
            display: flex;
            overflow: hidden;
        }
    `;

    @state() memories: Memory[] = [];
    @state() isLoading = false;
    @state() searchQuery = '';
    @state() filter: MemoryFilter = 'all';
    @state() sort: MemorySort = 'newest';
    @state() selectedMemory: Memory | null = null;
    @state() totalCount = 0;

    private controller = new MemoryViewController(this);

    async connectedCallback() {
        super.connectedCallback();
        await this.controller.connect();
    }

    render() {
        return html`
            <saas-memory-search-bar
                .searchQuery=${this.searchQuery}
                .filter=${this.filter}
                .sort=${this.sort}
                .totalCount=${this.totalCount}
                @search-input=${this._onSearchInput}
                @search-submit=${this._onSearchSubmit}
                @filter-change=${this._onFilterChange}
                @sort-change=${this._onSortChange}
                @navigate-back=${this._onNavigateBack}
            ></saas-memory-search-bar>

            <main class="main">
                <saas-memory-list
                    .memories=${this.memories}
                    .isLoading=${this.isLoading}
                    .selectedMemory=${this.selectedMemory}
                    .searchQuery=${this.searchQuery}
                    @memory-select=${this._onMemorySelect}
                    @memory-copy=${this._onMemoryCopy}
                    @memory-delete=${this._onMemoryDelete}
                    @export-memories=${this._onExportMemories}
                    @refresh-memories=${this._onRefreshMemories}
                ></saas-memory-list>

                ${this.selectedMemory ? html`
                    <saas-memory-detail-panel
                        .memory=${this.selectedMemory}
                        @memory-copy=${this._onMemoryCopy}
                        @memory-delete=${this._onMemoryDelete}
                    ></saas-memory-detail-panel>
                ` : ''}
            </main>
        `;
    }

    private _onSearchInput(e: CustomEvent<string>) {
        this.controller.setSearchQuery(e.detail);
    }

    private _onSearchSubmit() {
        this.controller.handleSearchSubmit();
    }

    private _onFilterChange(e: CustomEvent<MemoryFilter>) {
        this.controller.setFilter(e.detail);
    }

    private _onSortChange(e: CustomEvent<MemorySort>) {
        this.controller.setSort(e.detail);
    }

    private _onNavigateBack() {
        window.location.href = '/chat';
    }

    private _onMemorySelect(e: CustomEvent<Memory>) {
        this.controller.selectMemory(e.detail);
    }

    private _onMemoryCopy(e: CustomEvent<Memory>) {
        this.controller.copyMemory(e.detail);
    }

    private _onMemoryDelete(e: CustomEvent<Memory>) {
        this.controller.deleteMemory(e.detail);
    }

    private _onExportMemories() {
        this.controller.exportMemories();
    }

    private _onRefreshMemories() {
        this.controller.refreshMemories();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-memory-view': SaasMemoryView;
    }
}
