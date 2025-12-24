/**
 * SomaAgent SaaS — Chat View
 * Per UI_SCREENS_SRS.md Section 5 and AGENT_USER_UI_SRS.md Section 7
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - WebSocket streaming support
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - 6 Agent Modes: STD, TRN, ADM, DEV, RO, DGR
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state, query } from 'lit/decorators.js';
import { wsClient } from '../services/websocket-client.js';
import { apiClient } from '../services/api-client.js';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    confidence?: number;
    streaming?: boolean;
}

export interface Conversation {
    id: string;
    title: string;
    lastMessage: string;
    updatedAt: string;
    messageCount: number;
}

type AgentMode = 'STD' | 'TRN' | 'ADM' | 'DEV' | 'RO' | 'DGR';

@customElement('saas-chat')
export class SaasChat extends LitElement {
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

        /* Material Symbols - Required for Shadow DOM */
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        /* ========================================
           SIDEBAR
           ======================================== */
        .sidebar {
            width: 280px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }

        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon {
            width: 36px;
            height: 36px;
            background: #1a1a1a;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-icon svg {
            width: 18px;
            height: 18px;
            stroke: white;
            fill: none;
        }

        .brand-name {
            font-size: 16px;
            font-weight: 600;
        }

        /* New Conversation Button */
        .new-chat-btn {
            margin: 16px 20px;
            padding: 12px 16px;
            border-radius: 8px;
            background: #1a1a1a;
            color: white;
            border: none;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: background 0.15s ease;
        }

        .new-chat-btn:hover {
            background: #333;
        }

        /* Conversation List */
        .conversations-section {
            padding: 0 12px;
            flex: 1;
            overflow-y: auto;
        }

        .section-label {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--saas-text-muted, #999);
            padding: 16px 8px 8px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .conversation-item {
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.1s ease;
            margin-bottom: 4px;
        }

        .conversation-item:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .conversation-item.active {
            background: var(--saas-bg-active, #f0f0f0);
        }

        .conversation-title {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .conversation-preview {
            font-size: 12px;
            color: var(--saas-text-secondary, #666);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Quick Links */
        .quick-links {
            padding: 16px 12px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .quick-link {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .quick-link:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .quick-link-icon {
            font-size: 18px;
            width: 20px;
            text-align: center;
        }

        /* User Section */
        .user-section {
            padding: 16px 20px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--saas-bg-active, #f0f0f0);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
        }

        .user-info {
            flex: 1;
        }

        .user-name {
            font-size: 14px;
            font-weight: 500;
        }

        .user-role {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        .logout-btn {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            background: transparent;
            border: none;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.1s ease;
        }

        .logout-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-status-danger, #ef4444);
        }


        /* ========================================
           MAIN CHAT AREA
           ======================================== */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }

        /* Header */
        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .agent-name {
            font-size: 16px;
            font-weight: 600;
        }

        /* Mode Selector */
        .mode-selector {
            position: relative;
        }

        .mode-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 8px;
            background: var(--saas-bg-hover, #fafafa);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .mode-btn:hover {
            background: var(--saas-bg-active, #f0f0f0);
        }

        .mode-badge {
            padding: 2px 6px;
            border-radius: 4px;
            background: #1a1a1a;
            color: white;
            font-size: 11px;
            font-weight: 600;
        }

        .mode-dropdown {
            position: absolute;
            top: calc(100% + 4px);
            right: 0;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.1));
            min-width: 220px;
            z-index: 100;
            overflow: hidden;
            display: none;
        }

        .mode-dropdown.open {
            display: block;
        }

        .mode-option {
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            transition: background 0.1s ease;
        }

        .mode-option:last-child {
            border-bottom: none;
        }

        .mode-option:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .mode-option.active {
            background: var(--saas-bg-active, #f0f0f0);
        }

        .mode-option.locked {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .mode-option-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }

        .mode-option-title {
            font-size: 14px;
            font-weight: 500;
        }

        .mode-option-desc {
            font-size: 12px;
            color: var(--saas-text-secondary, #666);
        }

        .lock-icon {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        /* Messages */
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            padding-bottom: 120px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            max-width: 75%;
            padding: 14px 18px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.6;
        }

        .message.user {
            align-self: flex-end;
            background: #1a1a1a;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.assistant {
            align-self: flex-start;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            color: var(--saas-text-primary, #1a1a1a);
            border-bottom-left-radius: 4px;
        }

        .message.system {
            align-self: center;
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-secondary, #666);
            font-size: 13px;
            border-radius: 99px;
            padding: 8px 16px;
        }

        .message-time {
            font-size: 11px;
            color: inherit;
            opacity: 0.6;
            margin-top: 6px;
        }

        .message.user .message-time {
            color: rgba(255,255,255,0.7);
        }

        /* Confidence Indicator */
        .confidence {
            font-size: 11px;
            color: var(--saas-text-muted, #999);
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .confidence-bar {
            width: 60px;
            height: 4px;
            background: var(--saas-border-light, #e0e0e0);
            border-radius: 2px;
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            background: var(--saas-status-success, #22c55e);
            border-radius: 2px;
        }

        /* Quick Replies */
        .quick-replies {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 12px;
        }

        .quick-reply {
            padding: 8px 14px;
            border-radius: 99px;
            background: var(--saas-bg-hover, #fafafa);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .quick-reply:hover {
            background: var(--saas-bg-active, #f0f0f0);
            border-color: var(--saas-border-medium, #ccc);
        }

        /* Empty State */
        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px;
        }

        .empty-icon {
            width: 64px;
            height: 64px;
            background: var(--saas-bg-hover, #fafafa);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            margin-bottom: 20px;
        }

        .empty-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .empty-desc {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            max-width: 320px;
        }

        /* ========================================
           INPUT DOCK (Floating)
           ======================================== */
        .input-dock {
            position: absolute;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            width: calc(100% - 48px);
            max-width: 700px;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 24px;
            padding: 8px;
            display: flex;
            align-items: flex-end;
            gap: 8px;
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.1));
            transition: box-shadow 0.2s ease;
        }

        .input-dock:focus-within {
            border-color: var(--saas-border-medium, #ccc);
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.1)), 0 0 0 2px rgba(0,0,0,0.05);
        }

        /* Attachment Button */
        .attach-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: var(--saas-text-secondary, #666);
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.1s ease;
            flex-shrink: 0;
        }

        .attach-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .input-field {
            flex: 1;
            padding: 8px 4px;
        }

        .input-field textarea {
            width: 100%;
            padding: 4px 0;
            border: none;
            background: transparent;
            color: var(--saas-text-primary, #1a1a1a);
            font-family: inherit;
            font-size: 14px;
            resize: none;
            outline: none;
            max-height: 120px;
            line-height: 1.5;
        }

        .input-field textarea::placeholder {
            color: var(--saas-text-muted, #999);
        }

        /* Voice Button */
        .voice-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: var(--saas-text-secondary, #666);
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.1s ease;
            flex-shrink: 0;
        }

        .voice-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .voice-btn.active {
            background: var(--saas-status-danger, #ef4444);
            color: white;
        }

        /* Send Button */
        .send-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #1a1a1a;
            border: none;
            color: white;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s ease;
            flex-shrink: 0;
        }

        .send-btn:hover:not(:disabled) {
            background: #333;
            transform: scale(1.05);
        }

        .send-btn:disabled {
            background: var(--saas-border-light, #e0e0e0);
            color: var(--saas-text-muted, #999);
            cursor: not-allowed;
        }

        /* ========================================
           ANIMATIONS
           ======================================== */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message {
            animation: fadeIn 0.2s ease-out;
        }

        /* Typing Indicator */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 14px 18px;
            align-self: flex-start;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 16px;
            border-bottom-left-radius: 4px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--saas-text-muted, #999);
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
            30% { transform: translateY(-6px); opacity: 1; }
        }
    `;

    @property({ type: String }) sessionId = '';
    @state() private _messages: ChatMessage[] = [];
    @state() private _conversations: Conversation[] = [];
    @state() private _input = '';
    @state() private _isStreaming = false;
    @state() private _streamContent = '';
    @state() private _currentMode: AgentMode = 'STD';
    @state() private _showModeDropdown = false;
    @state() private _activeConversationId = '';

    @query('.messages') private _messagesContainer!: HTMLElement;

    private _unsubscribe?: () => void;

    private _modes = [
        { id: 'STD', name: 'Standard Mode', desc: 'Normal operation', locked: false },
        { id: 'DEV', name: 'Developer Mode', desc: 'Debug tools, logs', locked: false },
        { id: 'TRN', name: 'Training Mode', desc: 'Cognitive parameters', locked: true },
        { id: 'ADM', name: 'Admin Mode', desc: 'Agent configuration', locked: true },
        { id: 'RO', name: 'Read-Only Mode', desc: 'View only, no actions', locked: false },
        { id: 'DGR', name: 'Degraded Mode', desc: 'Limited functionality', locked: true },
    ];

    async connectedCallback() {
        super.connectedCallback();

        // Sample conversations for demo
        this._conversations = [
            { id: '1', title: 'Database Configuration', lastMessage: 'User asked about PostgreSQL...', updatedAt: 'Dec 22', messageCount: 12 },
            { id: '2', title: 'Server Setup Help', lastMessage: 'I need help with Docker...', updatedAt: 'Dec 21', messageCount: 8 },
            { id: '3', title: 'Data Migration Query', lastMessage: 'How do I migrate from MySQL?', updatedAt: 'Dec 20', messageCount: 15 },
            { id: '4', title: 'Code Review', lastMessage: 'Can you review this function?', updatedAt: 'Dec 19', messageCount: 5 },
        ];

        // Subscribe to WebSocket events
        this._unsubscribe = wsClient.on('chat.message', (data) => {
            this._handleIncomingMessage(data as ChatMessage);
        });

        wsClient.on('chat.stream', (data: unknown) => {
            const chunk = data as { content: string; done: boolean; confidence?: number };
            this._handleStreamChunk(chunk);
        });

        // Close dropdown on outside click
        document.addEventListener('click', this._handleOutsideClick);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._unsubscribe?.();
        document.removeEventListener('click', this._handleOutsideClick);
    }

    private _handleOutsideClick = (e: Event) => {
        const target = e.target as HTMLElement;
        if (!target.closest('.mode-selector')) {
            this._showModeDropdown = false;
        }
    };

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <div class="brand">
                        <div class="brand-icon">
                            <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="3" width="7" height="7" rx="1"/>
                                <rect x="14" y="3" width="7" height="7" rx="1"/>
                                <rect x="14" y="14" width="7" height="7" rx="1"/>
                                <rect x="3" y="14" width="7" height="7" rx="1"/>
                            </svg>
                        </div>
                        <span class="brand-name">SomaAgent</span>
                    </div>
                </div>

                <button class="new-chat-btn" @click=${this._startNewChat}>
                    <span>+</span> New Conversation
                </button>

                <div class="conversations-section">
                    <div class="section-label">Conversations</div>
                    ${this._conversations.map(conv => html`
                        <div 
                            class="conversation-item ${conv.id === this._activeConversationId ? 'active' : ''}"
                            @click=${() => this._selectConversation(conv.id)}
                        >
                            <div class="conversation-title">${conv.title}</div>
                            <div class="conversation-preview">${conv.lastMessage}</div>
                        </div>
                    `)}
                </div>

                <div class="quick-links">
                    <div class="section-label">Quick Access</div>
                    <div class="quick-link" @click=${() => this._navigate('/memory')}>
                        <span class="material-symbols-outlined quick-link-icon">psychology</span> Memory
                    </div>
                    <div class="quick-link" @click=${() => this._navigate('/tools')}>
                        <span class="material-symbols-outlined quick-link-icon">construction</span> Tools
                    </div>
                    <div class="quick-link" @click=${() => this._navigate('/settings')}>
                        <span class="material-symbols-outlined quick-link-icon">settings</span> Settings
                    </div>
                    <div class="quick-link" @click=${() => this._navigate('/themes')}>
                        <span class="material-symbols-outlined quick-link-icon">palette</span> Theme
                    </div>
                </div>

                <div class="user-section">
                    <div class="user-avatar">JD</div>
                    <div class="user-info">
                        <div class="user-name">John Doe</div>
                        <div class="user-role">Member</div>
                    </div>
                    <button class="logout-btn" @click=${this._logout} title="Logout">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                            <polyline points="16 17 21 12 16 7"/>
                            <line x1="21" y1="12" x2="9" y2="12"/>
                        </svg>
                    </button>
                </div>
            </aside>

            <!-- Main Chat Area -->
            <main class="main">
                <header class="header">
                    <div class="header-left">
                        <span class="agent-name">Support-AI</span>
                    </div>

                    <!-- Mode Selector -->
                    <div class="mode-selector">
                        <button class="mode-btn" @click=${this._toggleModeDropdown}>
                            <span class="mode-badge">${this._currentMode}</span>
                            ${this._getModeLabel(this._currentMode)}
                            <span>▼</span>
                        </button>
                        <div class="mode-dropdown ${this._showModeDropdown ? 'open' : ''}">
                            ${this._modes.map(mode => html`
                                <div 
                                    class="mode-option ${mode.id === this._currentMode ? 'active' : ''} ${mode.locked ? 'locked' : ''}"
                                    @click=${() => this._selectMode(mode.id as AgentMode, mode.locked)}
                                >
                                    <div class="mode-option-header">
                                        <span class="mode-badge" style="background: ${mode.id === this._currentMode ? '#1a1a1a' : '#e0e0e0'}; color: ${mode.id === this._currentMode ? 'white' : '#666'}">${mode.id}</span>
                                        <span class="mode-option-title">${mode.name}</span>
                                        ${mode.locked ? html`<span class="lock-icon">🔒</span>` : ''}
                                    </div>
                                    <div class="mode-option-desc">${mode.desc}</div>
                                </div>
                            `)}
                        </div>
                    </div>
                </header>

                <div class="messages">
                    ${this._messages.length === 0 ? this._renderEmptyState() : html`
                        ${this._messages.map(msg => this._renderMessage(msg))}
                        ${this._isStreaming ? this._renderTypingIndicator() : ''}
                    `}
                </div>

                <!-- Floating Input Dock -->
                <div class="input-dock">
                    <button class="attach-btn" title="Attach file">
                        +
                    </button>
                    <div class="input-field">
                        <textarea
                            rows="1"
                            placeholder="Type your message..."
                            .value=${this._input}
                            @input=${this._handleInput}
                            @keydown=${this._handleKeydown}
                        ></textarea>
                    </div>
                    <button class="voice-btn" title="Voice input">
                        <span class="material-symbols-outlined">mic</span>
                    </button>
                    <button 
                        class="send-btn"
                        ?disabled=${!this._input.trim() || this._isStreaming}
                        @click=${this._sendMessage}
                        title="Send message"
                    >
                        ➤
                    </button>
                </div>
            </main>
        `;
    }

    private _renderEmptyState() {
        return html`
            <div class="empty-state">
                <div class="empty-icon"><span class="material-symbols-outlined">chat</span></div>
                <div class="empty-title">Start a Conversation</div>
                <div class="empty-desc">
                    Ask me anything about your data, configurations, or system management.
                </div>
            </div>
        `;
    }

    private _renderMessage(msg: ChatMessage) {
        const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        return html`
            <div class="message ${msg.role}">
                <div class="message-content" style="white-space: pre-wrap;">${msg.content}</div>
                <div class="message-time">${time}</div>
                ${msg.confidence != null ? html`
                    <div class="confidence">
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${msg.confidence * 100}%"></div>
                        </div>
                        <span>${Math.round(msg.confidence * 100)}%</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    private _renderTypingIndicator() {
        return html`
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
    }

    private _getModeLabel(mode: AgentMode): string {
        const modeInfo = this._modes.find(m => m.id === mode);
        return modeInfo?.name.replace(' Mode', '') || mode;
    }

    private _toggleModeDropdown(e: Event) {
        e.stopPropagation();
        this._showModeDropdown = !this._showModeDropdown;
    }

    private _selectMode(mode: AgentMode, locked: boolean) {
        if (locked) return;
        this._currentMode = mode;
        this._showModeDropdown = false;
    }

    private _handleInput(e: Event) {
        const textarea = e.target as HTMLTextAreaElement;
        this._input = textarea.value;

        // Auto-resize textarea
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
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

        // Reset textarea height
        const textarea = this.shadowRoot?.querySelector('textarea');
        if (textarea) textarea.style.height = 'auto';

        this.updateComplete.then(() => this._scrollToBottom());

        try {
            wsClient.send('chat.send', {
                session_id: this.sessionId,
                content,
                mode: this._currentMode,
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

    private _scrollToBottom() {
        if (this._messagesContainer) {
            this._messagesContainer.scrollTop = this._messagesContainer.scrollHeight;
        }
    }

    private _startNewChat() {
        this._messages = [];
        this._activeConversationId = '';
    }

    private _selectConversation(id: string) {
        this._activeConversationId = id;
        // Would load conversation history here
    }

    private _navigate(path: string) {
        window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route: path } }));
    }

    private _logout() {
        // Clear all auth tokens
        localStorage.removeItem('eog_auth_token');
        localStorage.removeItem('eog_user');
        localStorage.removeItem('eog_keycloak_token');
        sessionStorage.removeItem('eog_auth_state');
        sessionStorage.removeItem('eog_auth_nonce');

        // Redirect to login
        window.location.href = '/login';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-chat': SaasChat;
    }
}
