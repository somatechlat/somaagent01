/**
 * Eye of God Tabs Component
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Accessible tab navigation
 * - Animated indicator
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state, queryAll } from 'lit/decorators.js';

export interface Tab {
    id: string;
    label: string;
    icon?: string;
    disabled?: boolean;
    badge?: string | number;
}

@customElement('soma-tabs')
export class SomaTabs extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .tabs-container {
            display: flex;
            flex-direction: column;
        }

        .tabs-header {
            display: flex;
            gap: var(--soma-spacing-xs, 4px);
            border-bottom: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.05));
            position: relative;
        }

        .tabs-header.vertical {
            flex-direction: column;
            border-bottom: none;
            border-right: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.05));
        }

        .tab {
            padding: var(--soma-spacing-sm, 8px) var(--soma-spacing-md, 16px);
            font-size: var(--soma-text-sm, 13px);
            font-weight: 500;
            color: var(--soma-text-dim, #64748b);
            background: transparent;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: var(--soma-spacing-xs, 4px);
            position: relative;
        }

        .tab:hover:not(:disabled) {
            color: var(--soma-text-main, #e2e8f0);
        }

        .tab.active {
            color: var(--soma-accent, #94a3b8);
        }

        .tab:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .tab:focus-visible {
            outline: 2px solid var(--soma-accent, #94a3b8);
            outline-offset: -2px;
        }

        .tab-icon {
            font-size: 16px;
        }

        .tab-badge {
            background: var(--soma-danger, #ef4444);
            color: white;
            font-size: var(--soma-text-xs, 11px);
            padding: 1px 6px;
            border-radius: var(--soma-radius-full, 9999px);
            line-height: 1.4;
        }

        .indicator {
            position: absolute;
            bottom: -1px;
            height: 2px;
            background: var(--soma-accent, #94a3b8);
            transition: all 0.3s ease;
        }

        .tabs-header.vertical .indicator {
            bottom: auto;
            right: -1px;
            width: 2px;
            height: auto;
        }

        .tabs-content {
            padding: var(--soma-spacing-lg, 24px) 0;
        }

        .tab-panel {
            display: none;
        }

        .tab-panel.active {
            display: block;
            animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;

    @property({ type: Array }) tabs: Tab[] = [];
    @property({ type: String }) selected = '';
    @property({ type: String }) orientation: 'horizontal' | 'vertical' = 'horizontal';

    @state() private _indicatorStyle = '';

    @queryAll('.tab') private _tabElements!: NodeListOf<HTMLButtonElement>;

    firstUpdated() {
        this._updateIndicator();
    }

    updated(changedProperties: Map<string, unknown>) {
        if (changedProperties.has('selected')) {
            this._updateIndicator();
        }
    }

    render() {
        return html`
            <div class="tabs-container">
                <div 
                    class="tabs-header ${this.orientation}" 
                    role="tablist"
                    aria-orientation=${this.orientation}
                >
                    ${this.tabs.map(tab => html`
                        <button
                            class="tab ${this.selected === tab.id ? 'active' : ''}"
                            role="tab"
                            id="tab-${tab.id}"
                            aria-selected=${this.selected === tab.id}
                            aria-controls="panel-${tab.id}"
                            ?disabled=${tab.disabled}
                            @click=${() => this._selectTab(tab.id)}
                            @keydown=${this._handleKeydown}
                        >
                            ${tab.icon ? html`<span class="tab-icon">${tab.icon}</span>` : ''}
                            ${tab.label}
                            ${tab.badge != null ? html`<span class="tab-badge">${tab.badge}</span>` : ''}
                        </button>
                    `)}
                    <div class="indicator" style=${this._indicatorStyle}></div>
                </div>
                
                <div class="tabs-content">
                    ${this.tabs.map(tab => html`
                        <div
                            class="tab-panel ${this.selected === tab.id ? 'active' : ''}"
                            role="tabpanel"
                            id="panel-${tab.id}"
                            aria-labelledby="tab-${tab.id}"
                        >
                            <slot name="${tab.id}"></slot>
                        </div>
                    `)}
                </div>
            </div>
        `;
    }

    private _selectTab(id: string) {
        const tab = this.tabs.find(t => t.id === id);
        if (tab?.disabled) return;

        this.selected = id;

        this.dispatchEvent(new CustomEvent('soma-tab-change', {
            detail: { id, tab },
            bubbles: true,
            composed: true,
        }));
    }

    private _handleKeydown(e: KeyboardEvent) {
        const currentIndex = this.tabs.findIndex(t => t.id === this.selected);
        let newIndex = currentIndex;

        switch (e.key) {
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault();
                newIndex = (currentIndex + 1) % this.tabs.length;
                break;
            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault();
                newIndex = (currentIndex - 1 + this.tabs.length) % this.tabs.length;
                break;
            case 'Home':
                e.preventDefault();
                newIndex = 0;
                break;
            case 'End':
                e.preventDefault();
                newIndex = this.tabs.length - 1;
                break;
        }

        if (newIndex !== currentIndex && !this.tabs[newIndex].disabled) {
            this._selectTab(this.tabs[newIndex].id);
            this._tabElements[newIndex]?.focus();
        }
    }

    private _updateIndicator() {
        requestAnimationFrame(() => {
            const activeTab = this.shadowRoot?.querySelector('.tab.active') as HTMLElement;
            if (!activeTab) return;

            if (this.orientation === 'horizontal') {
                this._indicatorStyle = `left: ${activeTab.offsetLeft}px; width: ${activeTab.offsetWidth}px`;
            } else {
                this._indicatorStyle = `top: ${activeTab.offsetTop}px; height: ${activeTab.offsetHeight}px`;
            }
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-tabs': SomaTabs;
    }
}
