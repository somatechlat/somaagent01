import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

export interface Tab {
    id: string;
    label: string;
    icon?: string;
}

@customElement('saas-tabs')
export class SaasTabs extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .tabs-container {
            display: flex;
            gap: 2px;
            border-bottom: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.1));
            margin-bottom: 24px;
        }

        .tab {
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 500;
            color: var(--saas-text-dim, #94a3b8);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .tab:hover {
            color: var(--saas-text-main, #e2e8f0);
            background: rgba(255, 255, 255, 0.02);
        }

        .tab.active {
            color: var(--saas-primary, #3b82f6);
            border-bottom-color: var(--saas-primary, #3b82f6);
        }

        .tab-icon {
            font-family: 'Material Symbols Outlined';
            font-size: 18px;
        }
    `;

    @property({ type: Array }) tabs: Tab[] = [];
    @property({ type: String }) activeTab = '';

    private _handleTabClick(id: string) {
        this.activeTab = id;
        this.dispatchEvent(new CustomEvent('tab-change', {
            detail: { tabId: id },
            bubbles: true,
            composed: true
        }));
    }

    render() {
        return html`
            <div class="tabs-container">
                ${this.tabs.map(tab => html`
                    <div 
                        class="tab ${this.activeTab === tab.id ? 'active' : ''}"
                        @click="${() => this._handleTabClick(tab.id)}"
                    >
                        ${tab.icon ? html`<span class="tab-icon">${tab.icon}</span>` : ''}
                        ${tab.label}
                    </div>
                `)}
            </div>
            <div class="tab-content">
                <slot></slot>
            </div>
        `;
    }
}
