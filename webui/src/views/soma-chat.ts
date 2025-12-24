/**
 * Eye of God Chat View
 * Per Eye of God UIX Design Section 4.3
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - WebSocket streaming support
 * - Message rendering
 * - White Glassmorphism Theme
 * - Integrated Dashboard Slider
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state, query } from 'lit/decorators.js';
import { wsClient } from '../services/websocket-client.js';
import { apiClient } from '../services/api-client.js';
import '../components/soma-button.js';
import '../components/soma-input.js';
import './soma-platform-dashboard.js'; // Import Dashboard for embedding

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    confidence?: number;
    streaming?: boolean;
}

@customElement('soma-chat')
export class SomaChat extends LitElement {
    static styles = css`
        :host {
            display: flex;
            flex-direction: column;
            height: 100vh;
            background: #ffffff; /* Reference: White Palette */
            font-family: 'Inter', sans-serif;
            color: #1e293b;
            position: relative;
            overflow: hidden;
        }

        /* ========== Glassmorphism Background Elements ========== */
        .glass-background {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
            background: 
                radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 40%);
        }

        /* ========== Main Chat Layout ========== */
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 1;
            height: 100%;
        }

        .header {
            padding: 20px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            z-index: 10;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-icon {
            font-size: 20px;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px 24px 100px 24px; /* Bottom padding for FAB/Input */
            display: flex;
            flex-direction: column;
            gap: 20px;
            scroll-behavior: smooth;
        }

        /* ========== Messages ========== */
        .message {
            max-width: 80%;
            padding: 16px 20px;
            border-radius: 20px;
            position: relative;
            font-size: 15px;
            line-height: 1.6;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
            backdrop-filter: blur(8px);
        }

        .message.user {
            align-self: flex-end;
            background: #000000; /* Black for user - strong contrast */
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.assistant {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.05);
            color: #334155;
            border-bottom-left-radius: 4px;
        }

        .message.system {
            align-self: center;
            background: rgba(241, 245, 249, 0.8);
            color: #64748b;
            font-size: 13px;
            border-radius: 99px;
            padding: 8px 16px;
            box-shadow: none;
        }

        /* ========== Floating Input Area ========== */
        .input-dock {
            position: absolute;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 800px;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 60px; /* Pill shape */
            border: 1px solid rgba(0, 0, 0, 0.08);
            padding: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
            z-index: 20;
            transition: all 0.3s ease;
        }

        .input-dock:focus-within {
            box-shadow: 0 20px 35px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            transform: translateX(-50%) translateY(-2px);
        }

        .chat-input {
            flex: 1;
            padding: 0 16px;
        }

        .chat-input textarea {
            width: 100%;
            padding: 12px 0;
            border: none;
            background: transparent;
            color: #0f172a;
            font-family: inherit;
            font-size: 15px;
            resize: none;
            outline: none;
            max-height: 100px;
        }

        .chat-input textarea::placeholder {
            color: #94a3b8;
        }

        .send-button {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #000000;
            color: white;
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.2s ease;
        }

        .send-button:hover:not(:disabled) {
            transform: scale(1.05);
        }
        
        .send-button:disabled {
            background: #cbd5e1;
            cursor: not-allowed;
        }

        /* ========== Server Status FAB ========== */
        .fab-container {
            position: fixed;
            bottom: 32px;
            right: 32px;
            z-index: 30;
        }

        .fab {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 0, 0, 0.05);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .fab:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }

        .fab-icon {
            font-size: 24px;
            color: #000000;
        }
        
        /* Rotating loading ring for FAB */
        .fab-ring {
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            border-radius: 50%;
            border: 2px solid transparent;
            border-top-color: #10b981; /* Green status */
            animation: spin 3s linear infinite;
        }

        @keyframes spin { 100% { transform: rotate(360deg); } }

        /* ========== Bottom Slider (Dashboard) ========== */
        .slider-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(4px);
            z-index: 40;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }

        .slider-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .slider-pane {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 60vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(24px);
            border-top-left-radius: 32px;
            border-top-right-radius: 32px;
            box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.1);
            transform: translateY(100%);
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            z-index: 50;
            display: flex;
            flex-direction: column;
        }

        .slider-pane.active {
            transform: translateY(0);
        }

        .slider-handle {
            width: 40px;
            height: 4px;
            background: #cbd5e1;
            border-radius: 2px;
            margin: 16px auto;
            flex-shrink: 0;
        }
        
        .slider-content {
            flex: 1;
            overflow: hidden; /* Dashboard handles its own scroll */
            padding: 0 24px 24px 24px;
        }

        /* ========== Animations ========== */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .message { animation: fadeIn 0.3s ease-out forwards; }
    `;

    @property({ type: String }) sessionId = '';
    @state() private _messages: ChatMessage[] = [];
    @state() private _input = '';
    @state() private _isStreaming = false;
    @state() private _streamContent = '';
    @state() private _showDashboard = false;

    @query('.messages') private _messagesContainer!: HTMLElement;

    private _unsubscribe?: () => void;

    async connectedCallback() {
        super.connectedCallback();
        // Subscribe to WebSocket events
        this._unsubscribe = wsClient.on('chat.message', (data) => {
            this._handleIncomingMessage(data as ChatMessage);
        });

        wsClient.on('chat.stream', (data: unknown) => {
            const chunk = data as { content: string; done: boolean; confidence?: number };
            this._handleStreamChunk(chunk);
        });

        if (this.sessionId) {
            await this._loadHistory();
        }
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._unsubscribe?.();
    }

    render() {
        return html`
            <div class="glass-background"></div>

            <div class="chat-container">
                <div class="header">
                    <div class="header-title">
                        <span class="header-icon">👁️</span> Eye of God
                    </div>
                    <!-- Mode toggles could go here -->
                </div>

                <div class="messages">
                    ${this._messages.length === 0 ? this._renderEmptyState() : html`
                        ${this._messages.map(msg => this._renderMessage(msg))}
                        ${this._isStreaming ? this._renderStreamingMessage() : ''}
                    `}
                </div>

                <div class="input-dock">
                    <div class="chat-input">
                        <textarea
                            rows="1"
                            placeholder="Ask the Eye..."
                            .value=${this._input}
                            @input=${(e: Event) => this._input = (e.target as HTMLTextAreaElement).value}
                            @keydown=${this._handleKeydown}
                        ></textarea>
                    </div>
                    <button 
                        class="send-button"
                        ?disabled=${!this._input.trim() || this._isStreaming}
                        @click=${this._sendMessage}
                    >
                        ➤
                    </button>
                </div>
            </div>

            <!-- Server Status FAB -->
            <div class="fab-container">
                <div class="fab-ring"></div>
                <div class="fab" @click=${() => this._showDashboard = true}>
                    <span class="fab-icon">⚡</span>
                </div>
            </div>

            <!-- Bottom Slider Pane -->
            <div class="slider-overlay ${this._showDashboard ? 'active' : ''}" @click=${() => this._showDashboard = false}></div>
            <div class="slider-pane ${this._showDashboard ? 'active' : ''}">
                <div class="slider-handle"></div>
                <div class="slider-content">
                    <!-- Embed Dashboard in Simple Mode -->
                    <soma-platform-dashboard ?simple=${true}></soma-platform-dashboard>
                </div>
            </div>
        `;
    }

    private _renderEmptyState() {
        return html`
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; opacity: 0.5;">
                <div style="font-size: 40px; margin-bottom: 20px;">👁️</div>
                <p>The Eye is listening...</p>
            </div>
        `;
    }

    private _renderMessage(msg: ChatMessage) {
        return html`
            <div class="message ${msg.role}">
                <div class="message-content" style="white-space: pre-wrap;">${msg.content}</div>
                ${this._renderConfidence(msg.confidence)}
            </div>
        `;
    }

    private _renderStreamingMessage() {
        return html`
            <div class="message assistant">
                <div class="message-content">${this._streamContent || '...'}</div>
            </div>
        `;
    }

    private _renderConfidence(confidence?: number) {
        if (confidence == null) return '';
        return html`
            <div style="font-size: 11px; opacity: 0.7; margin-top: 8px; display: flex; align-items: center; gap: 4px;">
                <span>${(confidence * 100).toFixed(0)}% Confidence</span>
            </div>
        `;
    }

    private _handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this._sendMessage();
        }
    }

    private async _sendMessage() {
        const content = this._input.trim();
        if (!content || this._isStreaming) return;

        const userMessage: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: 'user',
            content,
            timestamp: new Date().toISOString(),
        };
        this._messages = [...this._messages, userMessage];
        this._input = '';
        this._isStreaming = true;
        this._streamContent = '';

        this.updateComplete.then(() => this._scrollToBottom());

        try {
            wsClient.send('chat.send', {
                session_id: this.sessionId,
                content,
            });
        } catch (error) {
            console.error('Failed to send message:', error);
            this._isStreaming = false;
        }
    }

    private _handleIncomingMessage(msg: ChatMessage) {
        this._isStreaming = false;
        this._streamContent = '';
        this._messages = [...this._messages, msg];
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private _handleStreamChunk(chunk: { content: string; done: boolean; confidence?: number }) {
        this._streamContent += chunk.content;
        if (chunk.done) {
            const message: ChatMessage = {
                id: `msg-${Date.now()}`,
                role: 'assistant',
                content: this._streamContent,
                timestamp: new Date().toISOString(),
                confidence: chunk.confidence,
            };
            this._handleIncomingMessage(message);
        }
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private async _loadHistory() {
        try {
            const messages = await apiClient.get<ChatMessage[]>(`/chat/${this.sessionId}/messages`);
            this._messages = messages;
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    private _scrollToBottom() {
        if (this._messagesContainer) {
            this._messagesContainer.scrollTop = this._messagesContainer.scrollHeight;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-chat': SomaChat;
    }
}
