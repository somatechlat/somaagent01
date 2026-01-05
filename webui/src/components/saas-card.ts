import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';

@customElement('saas-card')
export class SaasCard extends LitElement {
    static styles = css`
        :host {
            display: block;
            background: var(--saas-surface, #1e293b);
            border: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.05));
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
    `;

    render() {
        return html`<slot></slot>`;
    }
}
