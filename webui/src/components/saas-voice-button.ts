import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('saas-voice-button')
export class SaasVoiceButton extends LitElement {
    static styles = css`
        :host {
            display: inline-block;
        }

        button {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: none;
            background: var(--saas-primary, #3b82f6);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        button:hover {
            transform: scale(1.05);
            background: var(--saas-primary-hover, #2563eb);
        }

        button.listening {
            background: var(--saas-danger, #ef4444);
            animation: pulse 1.5s infinite;
        }

        button.processing {
            background: var(--saas-warning, #f59e0b);
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        .icon {
            font-family: 'Material Symbols Outlined';
            font-size: 24px;
            z-index: 2;
        }

        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        }

        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;

    @property({ type: Boolean }) listening = false;
    @property({ type: Boolean }) processing = false;

    private _handleClick(e: MouseEvent) {
        this.dispatchEvent(new CustomEvent('voice-toggle', {
            bubbles: true,
            composed: true
        }));

        // Ripple effect
        const btn = e.currentTarget as HTMLElement;
        const circle = document.createElement('span');
        const diameter = Math.max(btn.clientWidth, btn.clientHeight);
        const radius = diameter / 2;

        circle.style.width = circle.style.height = `${diameter}px`;
        circle.style.left = `${e.clientX - btn.getBoundingClientRect().left - radius}px`;
        circle.style.top = `${e.clientY - btn.getBoundingClientRect().top - radius}px`;
        circle.classList.add('ripple');

        const ripple = btn.getElementsByClassName('ripple')[0];
        if (ripple) {
            ripple.remove();
        }

        btn.appendChild(circle);
    }

    render() {
        return html`
            <button 
                class="${this.listening ? 'listening' : ''} ${this.processing ? 'processing' : ''}"
                @click="${this._handleClick}"
            >
                <span class="icon">
                    ${this.listening ? 'mic' : (this.processing ? 'hourglass_empty' : 'mic_none')}
                </span>
            </button>
        `;
    }
}
