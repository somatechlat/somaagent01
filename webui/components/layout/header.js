/**
 * Header Component
 * 
 * Application header with logo, navigation, and actions.
 * 
 * Usage:
 * <header x-data="header()" class="app-header">
 *   <div class="header-left">
 *     <button @click="$dispatch('toggle-sidebar')" class="sidebar-toggle">☰</button>
 *     <div class="app-logo">
 *       <img src="/favicon.svg" alt="Logo" />
 *       <span>SomaAgent</span>
 *     </div>
 *   </div>
 *   <div class="header-center">
 *     <div x-bind="connectionStatus" class="connection-status">
 *       <span class="connection-dot"></span>
 *       <span x-text="statusText"></span>
 *     </div>
 *   </div>
 *   <div class="header-right">
 *     <button @click="openSettings()" class="btn btn-icon">⚙</button>
 *   </div>
 * </header>
 * 
 * @module components/layout/header
 */

import { on, off } from '../../js/event-bus.js';
import { STREAM } from '../../core/events/types.js';

/**
 * Header component factory
 * @param {Object} options - Header options
 * @param {string} [options.title='SomaAgent'] - App title
 * @returns {Object} Alpine component data
 */
export default function Header(options = {}) {
  return {
    title: options.title ?? 'SomaAgent',
    connectionState: 'disconnected', // 'connected' | 'disconnected' | 'reconnecting'
    unsubscribers: [],
    
    init() {
      // Subscribe to connection events
      this.unsubscribers.push(
        on(STREAM.ONLINE, () => { this.connectionState = 'connected'; }),
        on(STREAM.OFFLINE, () => { this.connectionState = 'disconnected'; }),
        on(STREAM.RECONNECTING, () => { this.connectionState = 'reconnecting'; })
      );
    },
    
    destroy() {
      this.unsubscribers.forEach(unsub => unsub?.());
    },
    
    /**
     * Bind object for connection status
     */
    get connectionStatus() {
      return {
        ':data-status': () => this.connectionState,
      };
    },
    
    /**
     * Connection status text
     */
    get statusText() {
      switch (this.connectionState) {
        case 'connected': return 'Connected';
        case 'reconnecting': return 'Reconnecting...';
        default: return 'Disconnected';
      }
    },
    
    /**
     * Check if connected
     */
    get isConnected() {
      return this.connectionState === 'connected';
    },
    
    /**
     * Set connection state
     * @param {string} state - New state
     */
    setConnectionState(state) {
      this.connectionState = state;
    },
  };
}
