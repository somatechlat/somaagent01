import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('saas-voice-overlay')
export class SaasVoiceOverlay extends LitElement {
    static styles = css`
        :host {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 9998;
            pointer-events: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        :host([active]) {
            pointer-events: auto;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(8px);
        }

        .container {
            text-align: center;
            color: white;
            opacity: 0;
            transform: scale(0.9);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        :host([active]) .container {
            opacity: 1;
            transform: scale(1);
        }

        .orb {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.8), rgba(30, 64, 175, 0.4));
            box-shadow: 0 0 60px rgba(59, 130, 246, 0.4);
            margin: 0 auto 32px;
            position: relative;
            animation: float 6s ease-in-out infinite;
        }

        .orb::after {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            border-radius: 50%;
            background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, transparent 60%);
            mix-blend-mode: overlay;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }

        .transcript {
            font-size: 24px;
            font-weight: 500;
            max-width: 600px;
            line-height: 1.4;
            min-height: 1.4em;
        }

        .status {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.6);
            margin-top: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
    `;

    @property({ type: Boolean, reflect: true }) active = false;
    @property() transcript = '';
    @property() status = 'Listening...';

    render() {
        return html`
            <div class="container">
                <div class="orb"></div>
                <div class="transcript">${this.transcript}</div>
                <div class="status">${this.status}</div>
            </div>
        `;
    }
}
