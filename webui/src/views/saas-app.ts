import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';

@customElement('saas-app')
export class SaasApp extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100vh;
            width: 100vw;
            background: var(--saas-bg-page, #f8fafc);
            color: var(--saas-text-primary, #0f172a);
            font-family: var(--saas-font-sans, Inter, sans-serif);
        }
    `;

    render() {
        return html`<slot></slot>`;
    }
}
