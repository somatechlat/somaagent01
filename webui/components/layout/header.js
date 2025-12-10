/**
 * Header Component
 * 
 * Application header with logo, navigation, and actions.
 * Includes full ARIA accessibility support.
 * 
 * Usage:
 * <header x-data="header()" x-bind="container" class="app-header">
 *   <div class="header-left">
 *     <button x-bind="sidebarToggle" class="sidebar-toggle">☰</button>
 *     <div class="app-logo">
 *       <img src="/favicon.svg" alt="SomaAgent Logo" />
 *       <span>SomaAgent</span>
 *     </div>
 *   </div>
 *   <div class="header-center">
 *     <div x-bind="connectionStatus" class="connection-status">
 *       <span class="connection-dot" aria-hidden="true"></span>
 *       <span x-text="statusText"></span>
 *     </div>
 *   </div>
 *   <div class="header-right">
 *     <button x-bind="settingsButton" class="btn btn-icon">⚙</button>
 *   </div>
 * </header>
 * 
 * @module components/layout/header
 */

import { on, off } from '../../js/event-bus.js';
import { STREAM } from '../../core/events/types.js';
import { ARIA_LABELS, announce } from '../../core/accessibility/index.js';

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
        on(STREAM.ONLINE, () => { 
          this.connectionState = 'connected';
          announce('Connected to server');
        }),
        on(STREAM.OFFLINE, () => { 
          this.connectionState = 'disconnected';
          announce('Disconnected from server', 'assertive');
        }),
        on(STREAM.RECONNECTING, () => { 
          this.connectionState = 'reconnecting';
          announce('Reconnecting to server');
        })
      );
    },
    
    destroy() {
      this.unsubscribers.forEach(unsub => unsub?.());
    },
    
    /**
     * Bind for header container
     */
    get container() {
      return {
        'role': 'banner',
      };
    },
    
    /**
     * Bind for sidebar toggle button
     */
    get sidebarToggle() {
      return {
        '@click': () => this.$dispatch('toggle-sidebar'),
        'aria-label': ARIA_LABELS.sidebarToggle,
        'aria-controls': 'app-sidebar',
        'type': 'button',
      };
    },
    
    /**
     * Bind for settings button
     */
    get settingsButton() {
      return {
        '@click': () => this.$dispatch('open-settings'),
        'aria-label': 'Open settings',
        'type': 'button',
      };
    },
    
    /**
     * Bind object for connection status
     */
    get connectionStatus() {
      return {
        ':data-status': () => this.connectionState,
        'role': 'status',
        'aria-live': 'polite',
        'aria-label': ARIA_LABELS.connectionStatus,
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
