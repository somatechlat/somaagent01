/**
 * SSE Connection Manager
 * 
 * Manages Server-Sent Events connections with:
 * - Automatic reconnection with exponential backoff
 * - Connection state tracking
 * - Event parsing and dispatch
 * - Heartbeat monitoring
 * 
 * @module core/sse/manager
 */

import { emit } from '../../js/event-bus.js';
import { STREAM, SSE } from '../events/types.js';
import { ENDPOINTS, API_VERSION } from '../api/endpoints.js';

/**
 * SSE Connection States
 */
export const ConnectionState = Object.freeze({
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting',
  FAILED: 'failed',
});

/**
 * SSE Manager Configuration
 */
const DEFAULT_CONFIG = {
  reconnectBaseDelay: 1000,      // 1 second
  reconnectMaxDelay: 30000,      // 30 seconds
  reconnectMaxAttempts: 10,
  heartbeatTimeout: 45000,       // 45 seconds (backend sends every 20s)
  heartbeatCheckInterval: 5000,  // Check every 5 seconds
};

/**
 * SSE Manager Class
 * Singleton pattern for managing SSE connections
 */
class SSEManager {
  constructor() {
    this.eventSource = null;
    this.sessionId = null;
    this.state = ConnectionState.DISCONNECTED;
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    this.heartbeatTimer = null;
    this.lastEventTime = 0;
    this.lastEventId = null;
    this.config = { ...DEFAULT_CONFIG };
    this.callbacks = {
      onMessage: null,
      onConnect: null,
      onDisconnect: null,
      onReconnecting: null,
      onStateChange: null,
    };
  }

  /**
   * Configure the SSE manager
   * @param {Object} config - Configuration options
   */
  configure(config) {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current connection state
   * @returns {string} Current state
   */
  getState() {
    return this.state;
  }

  /**
   * Check if connected
   * @returns {boolean}
   */
  isConnected() {
    return this.state === ConnectionState.CONNECTED;
  }

  /**
   * Set connection state and notify
   * @param {string} newState - New state
   */
  setState(newState) {
    const oldState = this.state;
    this.state = newState;
    
    if (oldState !== newState) {
      this.callbacks.onStateChange?.(newState, oldState);
      
      // Emit state change events
      switch (newState) {
        case ConnectionState.CONNECTED:
          emit(STREAM.ONLINE, { sessionId: this.sessionId });
          this.callbacks.onConnect?.();
          break;
        case ConnectionState.DISCONNECTED:
        case ConnectionState.FAILED:
          emit(STREAM.OFFLINE, { sessionId: this.sessionId, state: newState });
          this.callbacks.onDisconnect?.();
          break;
        case ConnectionState.RECONNECTING:
          emit(STREAM.RECONNECTING, { 
            sessionId: this.sessionId, 
            attempt: this.reconnectAttempts 
          });
          this.callbacks.onReconnecting?.();
          break;
      }
    }
  }

  /**
   * Connect to SSE endpoint for a session
   * @param {string} sessionId - Session ID to connect to
   * @param {Object} callbacks - Event callbacks
   */
  connect(sessionId, callbacks = {}) {
    // Store callbacks
    this.callbacks = { ...this.callbacks, ...callbacks };
    
    // If already connected to same session, do nothing
    if (this.sessionId === sessionId && this.isConnected()) {
      return;
    }
    
    // Disconnect existing connection
    if (this.eventSource) {
      this.disconnect();
    }
    
    this.sessionId = sessionId;
    this.reconnectAttempts = 0;
    this.createConnection();
  }

  /**
   * Create EventSource connection
   */
  createConnection() {
    if (!this.sessionId) {
      console.error('SSE: No session ID provided');
      return;
    }

    this.setState(ConnectionState.CONNECTING);
    
    // Build URL with last event ID for resumption
    let url = `${API_VERSION}/session/${encodeURIComponent(this.sessionId)}/events?stream=true`;
    if (this.lastEventId) {
      url += `&lastEventId=${encodeURIComponent(this.lastEventId)}`;
    }

    try {
      this.eventSource = new EventSource(url, { withCredentials: true });
      
      this.eventSource.onopen = () => {
        this.reconnectAttempts = 0;
        this.lastEventTime = Date.now();
        this.setState(ConnectionState.CONNECTED);
        this.startHeartbeatMonitor();
        
        // Emit retry success if we were reconnecting
        if (this.reconnectAttempts > 0) {
          emit(STREAM.RETRY_SUCCESS, { sessionId: this.sessionId });
        }
      };
      
      this.eventSource.onerror = (error) => {
        console.warn('SSE connection error:', error);
        this.handleConnectionError();
      };
      
      this.eventSource.onmessage = (event) => {
        this.handleMessage(event);
      };
      
      // Listen for specific event types
      this.eventSource.addEventListener('assistant.started', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('assistant.delta', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('assistant.final', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('assistant.thinking.started', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('assistant.thinking.final', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('assistant.tool.started', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('assistant.tool.delta', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('assistant.tool.final', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('system.keepalive', (e) => this.handleMessage(e));
      this.eventSource.addEventListener('uploads.progress', (e) => this.handleMessage(e));
      
    } catch (error) {
      console.error('SSE: Failed to create EventSource:', error);
      this.handleConnectionError();
    }
  }

  /**
   * Handle incoming SSE message
   * @param {MessageEvent} event - SSE message event
   */
  handleMessage(event) {
    this.lastEventTime = Date.now();
    
    // Store last event ID for resumption
    if (event.lastEventId) {
      this.lastEventId = event.lastEventId;
    }
    
    try {
      const data = JSON.parse(event.data);
      const eventType = event.type || data.type || 'message';
      
      // Handle keepalive
      if (eventType === 'system.keepalive' || data.type === 'system.keepalive') {
        emit(STREAM.HEARTBEAT, { timestamp: Date.now() });
        return;
      }
      
      // Emit generic SSE event
      emit(SSE.EVENT, { type: eventType, data });
      
      // Emit specific event type
      const sseEventKey = eventType.replace(/\./g, '_').toUpperCase();
      if (SSE[sseEventKey]) {
        emit(SSE[sseEventKey], data);
      }
      
      // Call message callback
      this.callbacks.onMessage?.({ type: eventType, data });
      
    } catch (error) {
      console.warn('SSE: Failed to parse message:', error, event.data);
    }
  }

  /**
   * Handle connection error
   */
  handleConnectionError() {
    this.stopHeartbeatMonitor();
    
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    
    // Check if we should retry
    if (this.reconnectAttempts < this.config.reconnectMaxAttempts) {
      this.scheduleReconnect();
    } else {
      this.setState(ConnectionState.FAILED);
      emit(STREAM.RETRY_GIVEUP, { 
        sessionId: this.sessionId, 
        attempts: this.reconnectAttempts 
      });
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  scheduleReconnect() {
    this.setState(ConnectionState.RECONNECTING);
    this.reconnectAttempts++;
    
    // Calculate delay with exponential backoff
    const delay = Math.min(
      this.config.reconnectBaseDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.config.reconnectMaxDelay
    );
    
    console.log(`SSE: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.createConnection();
    }, delay);
  }

  /**
   * Start heartbeat monitoring
   */
  startHeartbeatMonitor() {
    this.stopHeartbeatMonitor();
    
    this.heartbeatTimer = setInterval(() => {
      const timeSinceLastEvent = Date.now() - this.lastEventTime;
      
      if (timeSinceLastEvent > this.config.heartbeatTimeout) {
        console.warn('SSE: Heartbeat timeout, connection may be stale');
        emit(STREAM.STALE, { 
          sessionId: this.sessionId, 
          lastEventTime: this.lastEventTime 
        });
        
        // Force reconnect
        this.handleConnectionError();
      }
    }, this.config.heartbeatCheckInterval);
  }

  /**
   * Stop heartbeat monitoring
   */
  stopHeartbeatMonitor() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Disconnect from SSE
   */
  disconnect() {
    // Clear timers
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeatMonitor();
    
    // Close EventSource
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    
    this.setState(ConnectionState.DISCONNECTED);
    this.sessionId = null;
    this.lastEventId = null;
  }

  /**
   * Force reconnect
   */
  reconnect() {
    if (this.sessionId) {
      const sessionId = this.sessionId;
      this.disconnect();
      this.connect(sessionId, this.callbacks);
    }
  }

  /**
   * Get connection info
   * @returns {Object} Connection information
   */
  getInfo() {
    return {
      state: this.state,
      sessionId: this.sessionId,
      reconnectAttempts: this.reconnectAttempts,
      lastEventTime: this.lastEventTime,
      lastEventId: this.lastEventId,
      isConnected: this.isConnected(),
    };
  }
}

// Singleton instance
export const sseManager = new SSEManager();

// Export for direct use
export default sseManager;
