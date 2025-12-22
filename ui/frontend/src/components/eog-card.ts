/**
 * Eye of God Card Component
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Flexible card layout
 * - Hover effects and variants
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('eog-card')
export class EogCard extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .card {
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--eog-radius-lg, 12px);
            overflow: hidden;
            transition: all 0.2s ease;
        }

        .card.clickable {
            cursor: pointer;
        }

        .card.clickable:hover {
            border-color: var(--eog-accent, #94a3b8);
            transform: translateY(-2px);
        }

        .card.elevated {
            box-shadow: var(--eog-shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.3));
        }

        .card.flat {
            border: none;
            background: transparent;
        }

        .card.outlined {
            background: transparent;
            border-width: 2px;
        }

        .card-header {
            padding: var(--eog-spacing-md, 16px) var(--eog-spacing-lg, 24px);
            border-bottom: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: var(--eog-text-lg, 16px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0;
        }

        .card-subtitle {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
            margin-top: var(--eog-spacing-xs, 4px);
        }

        .card-body {
            padding: var(--eog-spacing-lg, 24px);
        }

        .card-body.compact {
            padding: var(--eog-spacing-md, 16px);
        }

        .card-footer {
            padding: var(--eog-spacing-md, 16px) var(--eog-spacing-lg, 24px);
            border-top: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            justify-content: flex-end;
            gap: var(--eog-spacing-sm, 8px);
        }

        .card-image {
            width: 100%;
            height: auto;
            display: block;
        }

        ::slotted([slot="actions"]) {
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
        }
    `;

    @property({ type: String }) title = '';
    @property({ type: String }) subtitle = '';
    @property({ type: String }) variant: 'default' | 'elevated' | 'flat' | 'outlined' = 'default';
    @property({ type: Boolean }) clickable = false;
    @property({ type: Boolean }) compact = false;

    render() {
        return html`
            <article 
                class="card ${this.variant} ${this.clickable ? 'clickable' : ''}"
                @click=${this._handleClick}
            >
                <slot name="image"></slot>
                
                ${this.title || this.hasSlot('header') ? html`
                    <header class="card-header">
                        <div>
                            ${this.title ? html`<h3 class="card-title">${this.title}</h3>` : ''}
                            ${this.subtitle ? html`<p class="card-subtitle">${this.subtitle}</p>` : ''}
                            <slot name="header"></slot>
                        </div>
                        <slot name="actions"></slot>
                    </header>
                ` : ''}
                
                <div class="card-body ${this.compact ? 'compact' : ''}">
                    <slot></slot>
                </div>
                
                ${this.hasSlot('footer') ? html`
                    <footer class="card-footer">
                        <slot name="footer"></slot>
                    </footer>
                ` : ''}
            </article>
        `;
    }

    private hasSlot(name: string): boolean {
        return this.querySelector(`[slot="${name}"]`) !== null;
    }

    private _handleClick() {
        if (this.clickable) {
            this.dispatchEvent(new CustomEvent('eog-click', {
                bubbles: true,
                composed: true,
            }));
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-card': EogCard;
    }
}
