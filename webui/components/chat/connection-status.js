/**
 * Connection Status Component
 * 
 * Displays SSE connection status with reconnecting banner.
 * 
 * @module components/chat/connection-status
 */

import { chatStore } from '../../features/chat/chat.store.js';
import { sseManager } from '../../core/sse/manager.js';

/**
 * Connection Status component factory
 * @returns {Object} Alpine component data
 */
export default function ConnectionStatus() {
  return {
    /**
     * Get connection status from store
     */
    get status() {
      return chatStore.connectionStatus;
    },
    
    /**
     * Check if connected
     */
    get isConnected() {
      return this.status === 'online';
    },
    
    /**
     * Check if reconnecting
     */
    get isReconnecting() {
      return this.status === 'reconnecting';
    },
    
    /**
     * Check if offline
     */
    get isOffline() {
      return this.status === 'offline';
    },
    
    /**
     * Get status text
     */
    get statusText() {
      switch (this.status) {
        case 'online': return 'Connected';
        case 'offline': return 'Disconnected';
        case 'reconnecting': return 'Reconnecting...';
        case 'stale': return 'Connection stale';
        default: return 'Unknown';
      }
    },
    
    /**
     * Get status color class
     */
    get statusClass() {
      switch (this.status) {
        case 'online': return 'badge-success';
        case 'offline': return 'badge-error';
        case 'reconnecting': return 'badge-warning';
        case 'stale': return 'badge-warning';
        default: return '';
      }
    },
    
    /**
     * Force reconnect
     */
    reconnect() {
      sseManager.reconnect();
    },
    
    /**
     * Bind for status indicator
     */
    get indicator() {
      return {
        ':data-status': () => this.status,
        ':class': () => this.statusClass,
      };
    },
    
    /**
     * Bind for reconnecting banner
     */
    get banner() {
      return {
        'x-show': () => this.isReconnecting || this.isOffline,
        'x-transition': '',
        'class': 'connection-banner',
      };
    },
  };
}
