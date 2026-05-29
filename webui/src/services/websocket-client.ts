/**
 * SaaS Admin WebSocket Client
 * Per SaaS Admin UIX Design Section 4.3
 *
 * VIBE COMPLIANT:
 * - Real WebSocket implementation
 * - Exponential backoff reconnection
 * - Heartbeat (20s interval)
 * - Event subscription system
 *
 * SECURITY:
 * - Auth via Sec-WebSocket-Protocol subprotocol (P3-04)
 * - Falls back to httpOnly cookie for backward compatibility
 * - Never puts tokens in URL query string
 */

export interface WebSocketConfig {
    url: string;
    reconnect: boolean;
    maxReconnectAttempts: number;
    reconnectDelay: number;
    heartbeatInterval: number;
}

export type EventHandler = (data: unknown) => void;

export class WebSocketClient {
    private config: WebSocketConfig;
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
    private eventHandlers: Map<string, Set<EventHandler>> = new Map();
    private _connected = false;
    private _usingSubprotocol = false;
    private _fallbackWithoutSubprotocol = false;
    private _pendingUrl = '';

    constructor(config: Partial<WebSocketConfig> = {}) {
        this.config = {
            url: config.url ?? '/ws/v2/chat',
            reconnect: config.reconnect ?? true,
            maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
            reconnectDelay: config.reconnectDelay ?? 1000,
            heartbeatInterval: config.heartbeatInterval ?? 20000,
        };
    }

    /**
     * Check if connected.
     */
    get connected(): boolean {
        return this._connected && this.ws?.readyState === WebSocket.OPEN;
    }

    /**
     * Connect to WebSocket server.
     * Auth via Sec-WebSocket-Protocol subprotocol (P3-04) with cookie fallback.
     * Never put tokens in the URL query string.
     */
    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            return;
        }

        let url = this.config.url;
        if (!url.startsWith('ws://') && !url.startsWith('wss://')) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            url = `${protocol}//${window.location.host}${url}`;
        }
        this._pendingUrl = url;

        const token = this._getCookie('access_token');
        if (token && !this._fallbackWithoutSubprotocol) {
            // P3-04: Pass token via Sec-WebSocket-Protocol header
            this.ws = new WebSocket(url, [`soma-auth.${token}`]);
            this._usingSubprotocol = true;
        } else {
            // Fallback: cookie-only auth (backward compatible with old servers)
            this.ws = new WebSocket(url);
            this._usingSubprotocol = false;
        }
        this._setupEventHandlers();
    }

    /**
     * Disconnect from server.
     */
    disconnect(): void {
        this.config.reconnect = false;
        this._stopHeartbeat();

        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
    }

    /**
     * Send message to server.
     */
    send(message: unknown): void {
        if (!this.connected) {
            console.warn('[WebSocket] Not connected, message dropped');
            return;
        }

        this.ws!.send(JSON.stringify(message));
    }

    /**
     * Subscribe to event type.
     */
    on(event: string, handler: EventHandler): () => void {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }

        this.eventHandlers.get(event)!.add(handler);

        // Return unsubscribe function
        return () => {
            this.eventHandlers.get(event)?.delete(handler);
        };
    }

    /**
     * Setup WebSocket event handlers.
     */
    private _setupEventHandlers(): void {
        if (!this.ws) return;

        this.ws.onopen = () => {
            console.log('[WebSocket] Connected');
            this._connected = true;
            this.reconnectAttempts = 0;
            this._startHeartbeat();
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this._handleMessage(data);
            } catch {
                console.warn('[WebSocket] Invalid message format');
            }
        };

        this.ws.onclose = (event) => {
            console.log('[WebSocket] Disconnected');
            this._connected = false;
            this._stopHeartbeat();

            // Backward compatibility: if subprotocol handshake failed on first attempt,
            // retry without subprotocol (old servers rely on cookie only)
            if (this._usingSubprotocol && this.reconnectAttempts === 0 && event.code === 1006) {
                console.log('[WebSocket] Subprotocol not supported, falling back to cookie auth');
                this._usingSubprotocol = false;
                this._fallbackWithoutSubprotocol = true;
                this.ws = new WebSocket(this._pendingUrl);
                this._setupEventHandlers();
                return;
            }

            if (this.config.reconnect && this.reconnectAttempts < this.config.maxReconnectAttempts) {
                this.reconnectAttempts++;
                const delay = this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
                console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
                setTimeout(() => this.connect(), delay);
            }
        };

        this.ws.onerror = (error) => {
            console.error('[WebSocket] Error:', error);
        };
    }

    /**
     * Handle incoming message.
     */
    private _handleMessage(data: { type: string; payload: unknown }): void {
        const handlers = this.eventHandlers.get(data.type);
        if (handlers) {
            handlers.forEach((handler) => handler(data.payload));
        }
    }

    /**
     * Read a cookie value by name.
     */
    private _getCookie(name: string): string | null {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    /**
     * Start heartbeat.
     */
    private _startHeartbeat(): void {
        this._stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            if (this.connected) {
                this.send({ type: 'ping' });
            }
        }, this.config.heartbeatInterval);
    }

    /**
     * Stop heartbeat.
     */
    private _stopHeartbeat(): void {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
}

// Singleton instance
export const wsClient = new WebSocketClient();
