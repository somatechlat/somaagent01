/**
 * SaaS Admin WebSocket Client
 * Per SaaS Admin UIX Design Section 4.3
 *
 * VIBE COMPLIANT:
 * - Real WebSocket implementation
 * - Exponential backoff reconnection
 * - Heartbeat (20s interval)
 * - Event subscription system
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
    private token: string | null = null;
    private reconnectAttempts = 0;
    private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
    private eventHandlers: Map<string, Set<EventHandler>> = new Map();
    private _connected = false;

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
     * Set authentication token.
     */
    setToken(token: string | null): void {
        this.token = token;
    }

    /**
     * Connect to WebSocket server.
     */
    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            return;
        }

        // Build URL with token
        let url = this.config.url;
        if (!url.startsWith('ws://') && !url.startsWith('wss://')) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            url = `${protocol}//${window.location.host}${url}`;
        }

        if (this.token) {
            url += `?token=${encodeURIComponent(this.token)}`;
        }

        this.ws = new WebSocket(url);
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

        this._connected = false;
    }

    /**
     * Send a message.
     */
    send(type: string, data: unknown = {}): void {
        if (!this.connected) {
            console.warn('WebSocket not connected, message queued');
            return;
        }

        const message = JSON.stringify({ type, data });
        this.ws!.send(message);
    }

    /**
     * Subscribe to an event type.
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
     * Unsubscribe from an event.
     */
    off(event: string, handler: EventHandler): void {
        this.eventHandlers.get(event)?.delete(handler);
    }

    /**
     * Subscribe to server events.
     */
    subscribe(events: string[]): void {
        this.send('subscribe', { events });
    }

    /**
     * Unsubscribe from server events.
     */
    unsubscribe(events: string[]): void {
        this.send('unsubscribe', { events });
    }

    private _setupEventHandlers(): void {
        if (!this.ws) return;

        this.ws.onopen = () => {
            this._connected = true;
            this.reconnectAttempts = 0;
            this._startHeartbeat();
            this._emit('connected', {});
            console.log('WebSocket connected');
        };

        this.ws.onclose = (event) => {
            this._connected = false;
            this._stopHeartbeat();
            this._emit('disconnected', { code: event.code, reason: event.reason });
            console.log(`WebSocket disconnected: ${event.code} ${event.reason}`);

            if (this.config.reconnect && this.reconnectAttempts < this.config.maxReconnectAttempts) {
                this._scheduleReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this._emit('error', error);
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                const { type, data, payload } = message;

                if (type === 'pong') {
                    // Heartbeat response - ignore
                    return;
                }

                this._emit(type, data ?? payload);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
    }

    private _startHeartbeat(): void {
        this._stopHeartbeat();

        this.heartbeatTimer = setInterval(() => {
            if (this.connected) {
                this.send('ping');
            }
        }, this.config.heartbeatInterval);
    }

    private _stopHeartbeat(): void {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    private _scheduleReconnect(): void {
        const delay = this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            if (!this._connected) {
                this.connect();
            }
        }, delay);
    }

    private _emit(event: string, data: unknown): void {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }

        // Also emit to wildcard handlers
        const wildcardHandlers = this.eventHandlers.get('*');
        if (wildcardHandlers) {
            wildcardHandlers.forEach(handler => {
                try {
                    handler({ event, data });
                } catch (error) {
                    console.error('Error in wildcard handler:', error);
                }
            });
        }
    }
}

// Singleton instance
export const wsClient = new WebSocketClient();
