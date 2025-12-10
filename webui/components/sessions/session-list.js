/**
 * Session List Component
 * 
 * Displays list of chat sessions with search and actions.
 * 
 * @module components/sessions/session-list
 */

import { chatStore, setSession, removeSession } from '../../features/chat/chat.store.js';
import { deleteSession, createSession } from '../../features/chat/chat.api.js';
import { toastManager } from '../base/toast.js';

/**
 * Session List component factory
 * @param {Object} options - Component options
 * @param {Function} [options.onSelect] - Session select handler
 * @returns {Object} Alpine component data
 */
export default function SessionList(options = {}) {
  return {
    // State from store
    get sessions() { return chatStore.sessions; },
    get currentSessionId() { return chatStore.sessionId; },
    
    // Local state
    searchQuery: '',
    sortBy: 'date', // 'date' | 'name'
    sortOrder: 'desc', // 'asc' | 'desc'
    isCreating: false,
    
    /**
     * Filtered and sorted sessions
     */
    get filteredSessions() {
      let result = [...this.sessions];
      
      // Filter by search
      if (this.searchQuery) {
        const q = this.searchQuery.toLowerCase();
        result = result.filter(s => 
          s.name?.toLowerCase().includes(q) ||
          s.id?.toLowerCase().includes(q)
        );
      }
      
      // Sort
      result.sort((a, b) => {
        let cmp = 0;
        if (this.sortBy === 'date') {
          cmp = new Date(b.created_at || 0) - new Date(a.created_at || 0);
        } else if (this.sortBy === 'name') {
          cmp = (a.name || '').localeCompare(b.name || '');
        }
        return this.sortOrder === 'desc' ? cmp : -cmp;
      });
      
      return result;
    },
    
    /**
     * Select a session
     * @param {Object} session - Session to select
     */
    selectSession(session) {
      setSession(session.id);
      options.onSelect?.(session);
    },
    
    /**
     * Create a new session
     */
    async createNewSession() {
      if (this.isCreating) return;
      
      this.isCreating = true;
      try {
        const session = await createSession();
        this.selectSession(session);
        toastManager.success('Session created', 'New chat session started.');
      } catch (err) {
        toastManager.error('Failed to create session', err.message);
      } finally {
        this.isCreating = false;
      }
    },
    
    /**
     * Delete a session
     * @param {Object} session - Session to delete
     */
    async deleteSessionItem(session) {
      if (!confirm(`Delete session "${session.name || session.id}"?`)) return;
      
      try {
        await deleteSession(session.id);
        removeSession(session.id);
        
        // If deleted current session, clear it
        if (session.id === this.currentSessionId) {
          setSession(null);
        }
        
        toastManager.success('Session deleted', 'Chat session has been removed.');
      } catch (err) {
        toastManager.error('Failed to delete session', err.message);
      }
    },
    
    /**
     * Format session date
     * @param {string} dateStr - ISO date string
     * @returns {string} Formatted date
     */
    formatDate(dateStr) {
      if (!dateStr) return '';
      
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now - date;
      
      // Today
      if (diff < 86400000 && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      
      // Yesterday
      if (diff < 172800000) {
        return 'Yesterday';
      }
      
      // This week
      if (diff < 604800000) {
        return date.toLocaleDateString([], { weekday: 'short' });
      }
      
      // Older
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    },
    
    /**
     * Check if session is active
     * @param {Object} session - Session to check
     * @returns {boolean}
     */
    isActive(session) {
      return session.id === this.currentSessionId;
    },
    
    /**
     * Bind for session item
     * @param {Object} session - Session object
     */
    sessionItem(session) {
      return {
        '@click': () => this.selectSession(session),
        ':data-active': () => this.isActive(session),
        ':class': () => ({
          'session-item': true,
          'session-item-active': this.isActive(session),
        }),
      };
    },
    
    /**
     * Bind for search input
     */
    get searchInput() {
      return {
        'x-model': 'searchQuery',
        'placeholder': 'Search sessions...',
        'class': 'input',
      };
    },
    
    /**
     * Bind for new session button
     */
    get newButton() {
      return {
        '@click': () => this.createNewSession(),
        ':disabled': () => this.isCreating,
        ':class': () => ({
          'btn-loading': this.isCreating,
        }),
      };
    },
  };
}
