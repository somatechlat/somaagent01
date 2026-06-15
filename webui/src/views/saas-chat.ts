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
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { ChatStreamingController } from '../controllers/chat-streaming-controller.js';

// Register extracted components
import '../components/saas-conversation-list.js';
import '../components/saas-chat-message-list.js';
import '../components/saas-chat-input.js';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    coordinate?: string;
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

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }

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

        .input-dock-wrapper {
            position: absolute;
            bottom: 24px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            padding: 0 24px;
            pointer-events: none;
        }

        .input-dock-wrapper > * {
            pointer-events: auto;
        }

        .reconnecting-banner {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            background: var(--saas-status-warning, #f59e0b);
            color: white;
            padding: 8px 16px;
            font-size: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            z-index: 50;
        }

        .reconnecting-spinner {
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;

    @state() private _messages: ChatMessage[] = [];
    @state() private _conversations: Conversation[] = [];
    @state() private _input = '';
    @state() private _isStreaming = false;
    @state() private _streamContent = '';
    @state() private _currentMode: AgentMode = 'STD';
    @state() private _showModeDropdown = false;
    @state() private _activeConversationId = '';
    @state() private _wsReconnecting = false;
    @state() private _agents: { id: string; name: string; status?: string }[] = [];
    @state() private _selectedAgentId = '';
    @state() private _userName = '';
    @state() private _userRole = '';

    private _streamingController: ChatStreamingController;

    private _modes = [
        { id: 'STD', name: 'Standard Mode', desc: 'Normal operation', locked: false },
        { id: 'DEV', name: 'Developer Mode', desc: 'Debug tools, logs', locked: false },
        { id: 'TRN', name: 'Training Mode', desc: 'Cognitive parameters', locked: true },
        { id: 'ADM', name: 'Admin Mode', desc: 'Agent configuration', locked: true },
        { id: 'RO', name: 'Read-Only Mode', desc: 'View only, no actions', locked: false },
        { id: 'DGR', name: 'Degraded Mode', desc: 'Limited functionality', locked: true },
    ];

    constructor() {
        super();
        this._streamingController = new ChatStreamingController({
            onMessage: (msg) => this._handleIncomingMessage(msg),
            onDelta: (delta) => this._handleStreamDelta(delta),
            onDone: (content, confidence) => this._handleStreamDone({ content, confidence }),
            onStatusChange: (status) => {
                this._wsReconnecting = status.reconnecting;
            },
        });
    }

    async connectedCallback() {
        super.connectedCallback();

        await this._loadAgents();
        this._loadUser();
        await this._loadConversations();

        document.addEventListener('click', this._handleOutsideClick);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._streamingController.disconnect();
        document.removeEventListener('click', this._handleOutsideClick);
    }

    /**
     * Load agents from API (filtered by SpiceDB permissions).
     * Per design.md Section 7.1-7.3 - Agent Selection
     */
    private async _loadAgents(): Promise<void> {
        try {
            const data = await apiClient.get<{ data?: Array<{ id: string; name: string; status?: string }> }>('/aaas/admin/agents');
            const agents = (data.data || []).map((agent) => ({
                id: agent.id,
                name: agent.name,
                status: agent.status,
            }));
            this._agents = agents;

            const params = new URLSearchParams(window.location.search);
            const queryAgentId = params.get('agent');
            if (queryAgentId && agents.some((a) => a.id === queryAgentId)) {
                this._selectedAgentId = queryAgentId;
            } else if (agents.length === 1) {
                this._selectedAgentId = agents[0].id;
            }

            if (this._selectedAgentId) {
                this._streamingController.connect(this._selectedAgentId);
            }
        } catch (error) {
            console.error('[SaasChat] Failed to load agents:', error);
        }
    }

    private async _loadUser() {
        try {
            const userStr = sessionStorage.getItem('saas_user');
            if (userStr) {
                const user = JSON.parse(userStr);
                this._userName = user.name || '';
                this._userRole = user.role || '';
                return;
            }
            const user = await apiClient.get<{ name?: string; role?: string }>('/auth/me');
            this._userName = user?.name || '';
            this._userRole = user?.role || '';
        } catch (error) {
            console.error('[SaasChat] Failed to load user:', error);
        }
    }

    /**
     * Load conversations from API.
     */
    private async _loadConversations(): Promise<void> {
        try {
            const response = await apiClient.get('/chat/conversations');
            const items = Array.isArray(response)
                ? response
                : (response as { data?: Conversation[] }).data || [];

            this._conversations = items.map((conv: any) => ({
                id: conv.id,
                title: conv.title ?? 'Untitled',
                lastMessage: conv.last_message ?? '',
                updatedAt: conv.updated_at ?? '',
                messageCount: conv.message_count ?? 0,
            }));
            if (!this._activeConversationId && this._conversations.length > 0) {
                this._activeConversationId = this._conversations[0].id;
                await this._loadConversationMessages(this._activeConversationId);
            }
        } catch (error) {
            console.error('[SaasChat] Failed to load conversations:', error);
            this._conversations = [];
        }
    }

    /**
     * Create new conversation via API.
     * Per design.md Section 8.1 - Conversation Creation
     */
    private async _createConversation(agentId: string): Promise<string | null> {
        try {
            const data = await apiClient.post<{ id?: string }>('/chat/conversations', {
                agent_id: agentId,
            });
            return data?.id ?? null;
        } catch (error) {
            console.error('[SaasChat] Failed to create conversation:', error);
            return null;
        }
    }

    private _handleOutsideClick = (e: Event) => {
        const target = e.target as HTMLElement;
        if (!target.closest('.mode-selector')) {
            this._showModeDropdown = false;
        }
    };

    render() {
        return html`
            <saas-conversation-list
                .conversations=${this._conversations}
                .activeConversationId=${this._activeConversationId}
                .userName=${this._userName}
                .userRole=${this._userRole}
                @saas-select-conversation=${this._onSelectConversation}
                @saas-new-chat=${this._startNewChat}
                @saas-navigate=${this._onNavigate}
                @saas-logout=${() => this._onNavigate(new CustomEvent('navigate', { detail: { route: '/logout' } }))}
            ></saas-conversation-list>

            <main class="main">
                ${this._wsReconnecting ? html`
                    <div class="reconnecting-banner">
                        <div class="reconnecting-spinner"></div>
                        Reconnecting...
                    </div>
                ` : ''}

                <header class="header">
                    <div class="header-left">
                        ${this._renderAgentSelector()}
                    </div>

                    <div class="mode-selector">
                        <button class="mode-btn" @click=${this._toggleModeDropdown}>
                            <span class="mode-badge">${this._currentMode}</span>
                            ${this._getModeLabel(this._currentMode)}
                            <span class="material-symbols-outlined">expand_more</span>
                        </button>
                        <div class="mode-dropdown ${this._showModeDropdown ? 'open' : ''}">
                            ${this._modes.map((mode) => html`
                                <div
                                    class="mode-option ${mode.id === this._currentMode ? 'active' : ''} ${mode.locked ? 'locked' : ''}"
                                    @click=${() => this._selectMode(mode.id as AgentMode, mode.locked)}
                                >
                                    <div class="mode-option-header">
                                        <span class="mode-badge" style="background: ${mode.id === this._currentMode ? '#1a1a1a' : '#e0e0e0'}; color: ${mode.id === this._currentMode ? 'white' : '#666'}">${mode.id}</span>
                                        <span class="mode-option-title">${mode.name}</span>
                                        ${mode.locked ? html`<span class="lock-icon material-symbols-outlined">lock</span>` : ''}
                                    </div>
                                    <div class="mode-option-desc">${mode.desc}</div>
                                </div>
                            `)}
                        </div>
                    </div>
                </header>

                <saas-chat-message-list
                    .messages=${this._messages}
                    .streamContent=${this._streamContent}
                    .isStreaming=${this._isStreaming}
                ></saas-chat-message-list>

                <div class="input-dock-wrapper">
                    <saas-chat-input
                        .value=${this._input}
                        .disabled=${!this._selectedAgentId}
                        .isStreaming=${this._isStreaming}
                        @saas-input=${this._onInput}
                        @saas-send=${this._onSend}
                    ></saas-chat-input>
                </div>
            </main>
        `;
    }

    private _renderAgentSelector() {
        if (!this._selectedAgentId) {
            return html`<span class="agent-name">Select an agent</span>`;
        }
        if (this._agents.length <= 1) {
            const agent = this._agents.find((a) => a.id === this._selectedAgentId);
            return html`<span class="agent-name">${agent?.name ?? ''}</span>`;
        }
        return html`
            <select
                class="agent-name"
                style="border: none; background: transparent; font: inherit; cursor: pointer; outline: none;"
                @change=${this._handleAgentSelect}
            >
                ${this._agents.map((agent) => html`
                    <option value=${agent.id} ?selected=${agent.id === this._selectedAgentId}>
                        ${agent.name}
                    </option>
                `)}
            </select>
        `;
    }

    private _handleAgentSelect(e: Event) {
        const select = e.target as HTMLSelectElement;
        const agentId = select.value;
        if (agentId && agentId !== this._selectedAgentId) {
            this._selectedAgentId = agentId;
            this._activeConversationId = '';
            this._messages = [];
            this._streamingController.connect(agentId);
        }
    }

    private _getModeLabel(mode: AgentMode): string {
        const modeInfo = this._modes.find((m) => m.id === mode);
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

    private _onInput(e: CustomEvent<string>) {
        this._input = e.detail;
    }

    private async _onSend() {
        const content = this._input.trim();
        if (!content || this._isStreaming || !this._selectedAgentId) {
            if (!this._selectedAgentId) {
                console.warn('[SaasChat] No agent selected');
            }
            return;
        }

        const wsReady = await this._streamingController.ensureConnected();
        if (!wsReady) {
            console.error('[SaasChat] WebSocket not connected');
            return;
        }

        let conversationId = this._activeConversationId;
        if (!conversationId && this._selectedAgentId) {
            const newId = await this._createConversation(this._selectedAgentId);
            conversationId = newId || '';
            if (!conversationId) {
                console.error('[SaasChat] Failed to create conversation');
                return;
            }
            this._activeConversationId = conversationId;
            await this._loadConversations();
        }
        if (!conversationId) {
            console.error('[SaasChat] No active conversation');
            return;
        }

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
            this._streamingController.sendMessage(conversationId, content);
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

    private _handleStreamDelta(delta: string) {
        this._streamContent += delta;
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private _handleStreamDone(chunk: { content?: string; confidence?: number }) {
        const message: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: chunk.content ?? this._streamContent,
            timestamp: new Date().toISOString(),
            confidence: chunk.confidence,
        };
        this._handleIncomingMessage(message);
    }

    private _scrollToBottom() {
        const messagesContainer = this.renderRoot.querySelector('saas-chat-message-list');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    private async _startNewChat() {
        if (this._selectedAgentId) {
            const conversationId = await this._createConversation(this._selectedAgentId);
            if (conversationId) {
                this._activeConversationId = conversationId;
                await this._loadConversations();
            }
        }
        this._messages = [];
    }

    private _onSelectConversation(e: CustomEvent<string>) {
        const id = e.detail;
        this._activeConversationId = id;
        this._loadConversationMessages(id);
    }

    private async _loadConversationMessages(conversationId: string): Promise<void> {
        try {
            const response = await apiClient.get(`/chat/messages/${conversationId}`);
            const items = Array.isArray(response)
                ? response
                : (response as { data?: ChatMessage[] }).data || [];

            this._messages = items.map((msg: any) => ({
                id: msg.id,
                role: msg.role,
                content: msg.content ?? '',
                coordinate: msg.coordinate,
                timestamp: msg.created_at,
                confidence: msg.metadata?.confidence,
            }));
            this.updateComplete.then(() => this._scrollToBottom());
        } catch (error) {
            console.error('[SaasChat] Failed to load messages:', error);
        }
    }

    private _onNavigate(e: CustomEvent<{ route: string }>) {
        window.dispatchEvent(new CustomEvent('saas-navigate', { detail: e.detail }));
    }

}

declare global {
    interface HTMLElementTagNameMap {
        'saas-chat': SaasChat;
    }
}
