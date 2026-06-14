/**
 * Chat Streaming Controller
 * Manages WebSocket connection, streaming deltas, and message sending logic.
 */

import { WebSocketClient } from '../services/websocket-client.js';
import type { ChatMessage } from '../views/saas-chat.js';

export interface ChatStreamingControllerOptions {
    onMessage: (msg: ChatMessage) => void;
    onDelta: (delta: string) => void;
    onDone: (content?: string, confidence?: number) => void;
    onStatusChange: (status: { connected: boolean; reconnecting: boolean }) => void;
}

export class ChatStreamingController {
    private _wsClient: WebSocketClient | null = null;
    private _agentId = '';
    private _options: ChatStreamingControllerOptions;
    private _connected = false;
    private _reconnecting = false;

    constructor(options: ChatStreamingControllerOptions) {
        this._options = options;
    }

    get connected(): boolean {
        return this._connected;
    }

    get reconnecting(): boolean {
        return this._reconnecting;
    }

    connect(agentId: string): void {
        if (this._wsClient) {
            this._wsClient.disconnect();
            this._wsClient = null;
        }

        this._agentId = agentId;
        if (!agentId) {
            console.warn('[ChatStreamingController] No agent selected');
            return;
        }

        this._wsClient = new WebSocketClient({ url: `/ws/chat/${agentId}` });

        this._wsClient.on('chat.message', (data) => {
            this._options.onMessage(data as ChatMessage);
        });
        this._wsClient.on('chat.delta', (data) => {
            const chunk = data as { delta?: string; content?: string };
            const delta = chunk.delta ?? chunk.content ?? '';
            this._options.onDelta(delta);
        });
        this._wsClient.on('chat.done', (data) => {
            const chunk = data as { content?: string; confidence?: number };
            this._options.onDone(chunk.content, chunk.confidence);
        });
        this._wsClient.on('connected', () => {
            this._connected = true;
            this._reconnecting = false;
            this._emitStatus();
            console.log('[ChatStreamingController] WebSocket connected');
        });
        this._wsClient.on('disconnected', () => {
            this._connected = false;
            this._reconnecting = true;
            this._emitStatus();
            console.log('[ChatStreamingController] WebSocket disconnected, reconnecting...');
        });
        this._wsClient.on('error', () => {
            this._reconnecting = true;
            this._emitStatus();
        });

        this._wsClient.connect();
    }

    disconnect(): void {
        if (this._wsClient) {
            this._wsClient.disconnect();
            this._wsClient = null;
        }
        this._connected = false;
        this._reconnecting = false;
        this._emitStatus();
    }

    async ensureConnected(timeout = 5000): Promise<boolean> {
        if (!this._wsClient) {
            return false;
        }
        if (this._wsClient.connected) {
            return true;
        }

        this._wsClient.connect();

        return new Promise((resolve) => {
            const unsubscribe = this._wsClient!.on('connected', () => {
                unsubscribe();
                resolve(true);
            });
            const timer = setTimeout(() => {
                unsubscribe();
                resolve(false);
            }, timeout);
        });
    }

    sendMessage(conversationId: string, content: string): void {
        if (!this._wsClient) {
            console.error('[ChatStreamingController] WebSocket not initialized');
            return;
        }
        if (!this._wsClient.connected) {
            console.error('[ChatStreamingController] WebSocket not connected');
            return;
        }

        this._wsClient.send({
            type: 'chat.message',
            payload: {
                conversation_id: conversationId,
                content,
            },
        });
    }

    private _emitStatus(): void {
        this._options.onStatusChange({
            connected: this._connected,
            reconnecting: this._reconnecting,
        });
    }
}
