/**
 * Soma Admin WebSocket Client
 * Per Soma Admin UIX Design Section 4.3
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

/**
 * One frame this client actually sent or received.
 * Consumed by the Debug surface (UI-X-05) as a real WS frame log.
 */
export interface WsFrame {
    id: number;
    dir: 'in' | 'out';
    type: string;
    payload: unknown;
    ts: number;
}

/** Ring-buffer cap. Oldest entries drop once exceeded. */
export const WS_FRAME_LOG_LIMIT = 200;

/** Module-level ring buffer of real frames (newest at the end). */
export const wsFrameLog: WsFrame[] = [];

export type WsFrameListener = () => void;

const _frameListeners = new Set<WsFrameListener>();
let _nextFrameId = 1;

/**
 * Subscribe to frame-buffer updates. Returns an unsubscribe function.
 */
export function onWsFrame(listener: WsFrameListener): () => void {
    _frameListeners.add(listener);
    return () => {
        _frameListeners.delete(listener);
    };
}

function _frameType(message: unknown): string {
    if (
        message !== null &&
        typeof message === 'object' &&
        'type' in message &&
        typeof (message as { type: unknown }).type === 'string'
    ) {
        return (message as { type: string }).type;
    }
    return 'unknown';
}

function _pushFrame(dir: 'in' | 'out', type: string, payload: unknown): void {
    wsFrameLog.push({ id: _nextFrameId++, dir, type, payload, ts: Date.now() });
    if (wsFrameLog.length > WS_FRAME_LOG_LIMIT) {
        wsFrameLog.splice(0, wsFrameLog.length - WS_FRAME_LOG_LIMIT);
    }
    for (const listener of _frameListeners) {
        listener();
    }
}

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
        if (!config.url) {
            throw new Error('WebSocket URL is required');
        }
        this.config = {
            url: config.url,
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

        // Prefer ephemeral WS token (sessionStorage). httpOnly cookies are
        // invisible to JS, so subprotocol auth cannot use document.cookie.
        let token = this._getCookie('access_token');
        if (!token) {
            try {
                token = sessionStorage.getItem('soma_ws_token');
            } catch {
                token = null;
            }
        }
        if (token && !this._fallbackWithoutSubprotocol) {
            // P3-04: Pass token via Sec-WebSocket-Protocol header
            this.ws = new WebSocket(url, [`soma-auth.${token}`]);
            this._usingSubprotocol = true;
        } else {
            // Fallback: cookie-only auth (sent automatically if browser allows)
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

        const raw = JSON.stringify(message);
        _pushFrame('out', _frameType(message), message);
        this.ws!.send(raw);
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
            this._emit('connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                _pushFrame('in', _frameType(data), data);
                this._handleMessage(data);
            } catch {
                console.warn('[WebSocket] Invalid message format');
            }
        };

        this.ws.onclose = (event) => {
            console.log('[WebSocket] Disconnected');
            this._connected = false;
            this._stopHeartbeat();
            this._emit('disconnected', { code: event.code, reason: event.reason });

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
            this._emit('error', error);
        };
    }

    /**
     * Emit a lifecycle event to subscribers.
     */
    private _emit(event: string, payload?: unknown): void {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach((handler) => handler(payload));
        }
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

