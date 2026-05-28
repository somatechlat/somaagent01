/**
 * SomaAgent01 — Agent Workspace
 * 3-Panel Layout: Sidebar | Chat Panel | Right Panel
 * VIBE COMPLIANT: Real Lit 3.x, no mocks
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { workspaceStore } from '../stores/workspace-store.js';

@customElement('saas-workspace')
export class SaasWorkspace extends LitElement {
    @state() private _rightPanelOpen = false;
    @state() private _panelWidth = 400;
    @state() private _isResizing = false;

    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            background: var(--aaas-bg-void, #0a0a0a);
            color: var(--aaas-text-primary, #ffffff);
            font-family: var(--aaas-font-sans, 'Inter', sans-serif);
        }

        .workspace {
            display: flex;
            width: 100%;
            height: 100%;
        }

        .main-area {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-width: 0;
            position: relative;
        }

        .chat-container {
            flex: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
        }

        .right-panel-wrapper {
            position: relative;
            flex-shrink: 0;
            background: var(--aaas-bg-card, #1e1e1e);
            border-left: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            overflow: hidden;
            transition: width 250ms ease-out;
        }

        .right-panel-wrapper.closed {
            width: 0;
            border-left: none;
        }

        .resize-handle {
            position: absolute;
            left: -3px;
            top: 0;
            bottom: 0;
            width: 6px;
            cursor: col-resize;
            z-index: 10;
            background: transparent;
            transition: background 150ms ease;
        }

        .resize-handle:hover,
        .resize-handle.resizing {
            background: var(--aaas-accent, #e8e4dc);
            opacity: 0.3;
        }

        .panel-toggle {
            position: absolute;
            left: -28px;
            top: 50%;
            transform: translateY(-50%);
            width: 28px;
            height: 48px;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-right: none;
            border-radius: 8px 0 0 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--aaas-text-secondary, #a1a1a1);
            font-size: 14px;
            z-index: 5;
            transition: color 150ms ease, background 150ms ease;
        }

        .panel-toggle:hover {
            color: var(--aaas-accent, #e8e4dc);
            background: var(--aaas-bg-hover, #141414);
        }

        .panel-content {
            width: 100%;
            height: 100%;
            overflow-y: auto;
            overflow-x: hidden;
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        workspaceStore.subscribe(() => this._syncWorkspaceState());
        document.addEventListener('mousemove', this._onResizeMove);
        document.addEventListener('mouseup', this._onResizeEnd);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('mousemove', this._onResizeMove);
        document.removeEventListener('mouseup', this._onResizeEnd);
    }

    private _syncWorkspaceState() {
        const s = workspaceStore.state;
        this._rightPanelOpen = s.rightPanelOpen;
        this._panelWidth = s.panelWidth;
    }

    private _onResizeStart = (e: MouseEvent) => {
        e.preventDefault();
        this._isResizing = true;
    };

    private _onResizeMove = (e: MouseEvent) => {
        if (!this._isResizing) return;
        const rect = this.getBoundingClientRect();
        const newWidth = rect.width - e.clientX;
        workspaceStore.setPanelWidth(newWidth);
    };

    private _onResizeEnd = () => {
        this._isResizing = false;
    };

    private _togglePanel() {
        workspaceStore.toggleRightPanel();
    }

    render() {
        return html`
            <div class="workspace">
                <saas-sidebar-workspace></saas-sidebar-workspace>
                
                <div class="main-area">
                    <saas-agent-header></saas-agent-header>
                    <div class="chat-container">
                        <saas-chat-workspace></saas-chat-workspace>
                    </div>
                </div>

                <div 
                    class="right-panel-wrapper ${this._rightPanelOpen ? '' : 'closed'}"
                    style="width: ${this._rightPanelOpen ? this._panelWidth + 'px' : '0'}"
                >
                    <div 
                        class="resize-handle ${this._isResizing ? 'resizing' : ''}"
                        @mousedown=${this._onResizeStart}
                    ></div>
                    <div class="panel-toggle" @click=${this._togglePanel} title="Toggle Toolkit">
                        ${this._rightPanelOpen ? '»' : '«'}
                    </div>
                    <div class="panel-content">
                        ${this._rightPanelOpen ? html`<saas-right-panel></saas-right-panel>` : ''}
                    </div>
                </div>
            </div>
        `;
    }
}
