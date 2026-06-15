/**
 * SomaAgent01 — Chat Workspace Wrapper
 * Embeds existing saas-chat functionality within the workspace layout.
 * Wired to the real chat backend (agents API, conversations API, WebSocket).
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient, getData } from '../services/api-client.js';
import { ChatStreamingController } from '../controllers/chat-streaming-controller.js';
import { agentStore } from '../stores/agent-store.js';

interface AgentApiItem { id: string; name: string; status?: string; }
interface ConversationDetailOut { id: string; title?: string; agent_id?: string; }
interface MessageApiItem { id: string; role: string; coordinate?: string; content?: string; created_at?: string; }
interface WorkspaceMessage { id: string; role: 'user' | 'assistant'; content: string; timestamp: string; }

@customElement('saas-chat-workspace')
export class SaasChatWorkspace extends LitElement {
    @state() private _agents: AgentApiItem[] = [];
    @state() private _selectedAgentId = '';
    @state() private _activeConversationId = '';
    @state() private _messages: WorkspaceMessage[] = [];
    @state() private _isStreaming = false;
    @state() private _streamContent = '';
    @state() private _isSending = false;

    private _streamingController: ChatStreamingController | null = null;

    static styles = css`
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
        :host {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-height: 0;
            background: var(--aaas-bg-void, #0a0a0a);
        }

        .chat-area {
            flex: 1;
            min-height: 0;
            overflow-y: auto;
            padding: 20px;
        }

        .messages {
            max-width: 720px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            display: flex;
            gap: 12px;
            max-width: 85%;
        }

        .message.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .message-bubble {
            padding: 12px 16px;
            border-radius: var(--aaas-radius-lg, 12px);
            font-size: 14px;
            line-height: 1.6;
            word-wrap: break-word;
        }

        .message.user .message-bubble {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-text-primary, #ffffff);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-bottom-right-radius: 4px;
        }

        .message.assistant .message-bubble {
            background: var(--aaas-bg-card, #1e1e1e);
            color: var(--aaas-text-primary, #ffffff);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-bottom-left-radius: 4px;
        }

        .message-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
            background: var(--aaas-bg-hover, #141414);
        }

        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 16px;
        }

        .typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--aaas-text-muted, #6b6b6b);
            animation: typingBounce 1.4s ease-in-out infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typingBounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-6px); }
        }

    `;

    async connectedCallback() {
        super.connectedCallback();
        await this._loadAgents();

        this.addEventListener('send-message', this._handleSendMessage as unknown as EventListener);
        window.addEventListener('clear-chat', this._handleClearChat as unknown as EventListener);
        window.addEventListener('new-conversation', this._handleNewConversation as unknown as EventListener);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.removeEventListener('send-message', this._handleSendMessage as unknown as EventListener);
        window.removeEventListener('clear-chat', this._handleClearChat as unknown as EventListener);
        window.removeEventListener('new-conversation', this._handleNewConversation as unknown as EventListener);
        this._streamingController?.disconnect();
    }

    private async _loadAgents(): Promise<void> {
        try {
            const response = await apiClient.get<unknown>('/aaas/admin/agents');
            const agents = getData<AgentApiItem[]>(response) ?? [];
            this._agents = agents;

            const params = new URLSearchParams(window.location.search);
            const queryAgentId = params.get('agent');
            if (queryAgentId && agents.some(a => a.id === queryAgentId)) {
                this._selectedAgentId = queryAgentId;
            } else if (agents.length > 0) {
                this._selectedAgentId = agents[0].id;
            }

            if (this._selectedAgentId) {
                const agent = agents.find(a => a.id === this._selectedAgentId);
                if (agent) {
                    agentStore.setCurrentAgent({
                        id: agent.id,
                        name: agent.name,
                        description: '',
                        status: ['active', 'paused', 'archived', 'error'].includes(agent.status ?? '')
                            ? (agent.status as 'active' | 'paused' | 'archived' | 'error')
                            : 'active',
                    });
                }
                this._connectStreaming();
            }
        } catch (error) {
            console.error('[SaasChatWorkspace] Failed to load agents:', error);
        }
    }

    private _connectStreaming(): void {
        if (this._streamingController) {
            this._streamingController.disconnect();
            this._streamingController = null;
        }

        this._streamingController = new ChatStreamingController({
            onMessage: () => { /* full messages handled via chat.done */ },
            onDelta: (delta) => this._handleStreamDelta(delta),
            onDone: (content, tokenCount) => this._handleStreamDone(content, tokenCount),
            onStatusChange: () => { /* lifecycle ignored for now */ },
        });

        this._streamingController.connect(this._selectedAgentId);
    }

    private _handleSendMessage = async (e: CustomEvent) => {
        const text = e.detail?.text?.trim();
        if (!text || this._isSending || !this._selectedAgentId) {
            return;
        }

        this._isSending = true;
        this._appendUserMessage(text);

        try {
            if (!this._activeConversationId) {
                const conversationId = await this._createConversation();
                if (!conversationId) {
                    console.error('[SaasChatWorkspace] Failed to create conversation');
                    this._isSending = false;
                    return;
                }
                this._activeConversationId = conversationId;
                await this._loadMessages(conversationId);
            }

            const connected = await this._streamingController?.ensureConnected();
            if (!connected) {
                console.error('[SaasChatWorkspace] WebSocket not connected');
                this._isSending = false;
                return;
            }

            this._isStreaming = true;
            this._streamContent = '';
            this._streamingController!.sendMessage(this._activeConversationId, text);
        } catch (error) {
            console.error('[SaasChatWorkspace] Failed to send message:', error);
        } finally {
            this._isSending = false;
        }
    };

    private _handleClearChat = () => {
        this._messages = [];
        this._streamContent = '';
        this._isStreaming = false;
    };

    private _handleNewConversation = async () => {
        if (!this._selectedAgentId) {
            return;
        }
        const conversationId = await this._createConversation();
        if (conversationId) {
            this._activeConversationId = conversationId;
        }
        this._messages = [];
        this._streamContent = '';
        this._isStreaming = false;
    };

    private async _createConversation(): Promise<string | null> {
        try {
            const data = await apiClient.post<ConversationDetailOut>('/chat/conversations', {
                agent_id: this._selectedAgentId,
            });
            return data.id ?? null;
        } catch (error) {
            console.error('[SaasChatWorkspace] Failed to create conversation:', error);
            return null;
        }
    }

    private async _loadMessages(conversationId: string): Promise<void> {
        try {
            const response = await apiClient.get<unknown>(`/chat/conversations/${conversationId}/messages`);
            const items = getData<MessageApiItem[]>(response) ?? [];
            this._messages = items.map((msg) => ({
                id: msg.id,
                role: msg.role === 'user' ? 'user' : 'assistant',
                content: msg.coordinate ?? msg.content ?? '',
                timestamp: msg.created_at ?? new Date().toISOString(),
            }));
        } catch (error) {
            console.error('[SaasChatWorkspace] Failed to load messages:', error);
        }
    }

    private _appendUserMessage(text: string): void {
        const message: WorkspaceMessage = {
            id: `msg-${Date.now()}`,
            role: 'user',
            content: text,
            timestamp: new Date().toISOString(),
        };
        this._messages = [...this._messages, message];
    }

    private _handleStreamDelta(delta: string): void {
        this._streamContent += delta;
    }

    private _handleStreamDone(content?: string, _tokenCount?: number): void {
        const assistantMessage: WorkspaceMessage = {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: content ?? this._streamContent,
            timestamp: new Date().toISOString(),
        };
        this._messages = [...this._messages, assistantMessage];
        this._isStreaming = false;
        this._streamContent = '';
    }

    render() {
        if (!this._activeConversationId && this._messages.length === 0) {
            return html`
                <div style="flex:1;overflow:auto;">
                    <saas-welcome-dashboard></saas-welcome-dashboard>
                </div>
                <saas-composer .isStreaming=${this._isStreaming} .disabled=${!this._selectedAgentId}></saas-composer>
            `;
        }

        return html`
            <div class="chat-area">
                <div class="messages">
                    ${this._messages.map(m => html`
                        <div class="message ${m.role}">
                            <div class="message-avatar">
                                ${m.role === 'user'
                                    ? html`<span class='material-symbols-outlined'>person</span>`
                                    : html`<span class='material-symbols-outlined'>smart_toy</span>`}
                            </div>
                            <div class="message-bubble">
                                ${m.content}
                            </div>
                        </div>
                    `)}
                    ${this._isStreaming ? html`
                        <div class="message assistant">
                            <div class="message-avatar"><span class='material-symbols-outlined'>smart_toy</span></div>
                            <div class="message-bubble">
                                ${this._streamContent}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
            <saas-composer .isStreaming=${this._isStreaming} .disabled=${!this._selectedAgentId}></saas-composer>
        `;
    }
}
