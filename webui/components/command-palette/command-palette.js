/**
 * Command Palette Component
 *
 * Quick navigation and action palette with fuzzy search.
 * Opens with Cmd/Ctrl+K.
 *
 * @module components/command-palette/command-palette
 * Requirements: 3.5, 3.6, 13.1
 */

import { emit, on, off } from '../../js/event-bus.js';
import { SHORTCUT_EVENTS, formatShortcut } from '../../core/keyboard/shortcuts.js';

/**
 * Default commands
 */
const DEFAULT_COMMANDS = [
  {
    id: 'new-chat',
    label: 'New Chat',
    icon: '💬',
    category: 'Chat',
    shortcut: { key: 'n', meta: true },
    action: () => emit('command:new-chat'),
  },
  {
    id: 'settings',
    label: 'Open Settings',
    icon: '⚙️',
    category: 'Navigation',
    shortcut: { key: ',', meta: true },
    action: () => emit('command:settings'),
  },
  {
    id: 'memory',
    label: 'Memory Dashboard',
    icon: '🧠',
    category: 'Navigation',
    action: () => emit('command:navigate', { to: 'memory' }),
  },
  {
    id: 'scheduler',
    label: 'Scheduler',
    icon: '📅',
    category: 'Navigation',
    action: () => emit('command:navigate', { to: 'scheduler' }),
  },
  {
    id: 'health',
    label: 'Health Dashboard',
    icon: '💚',
    category: 'Navigation',
    action: () => emit('command:navigate', { to: 'health' }),
  },
  {
    id: 'toggle-theme',
    label: 'Toggle Dark/Light Mode',
    icon: '🌓',
    category: 'Appearance',
    action: () => emit('command:toggle-theme'),
  },
  {
    id: 'keyboard-shortcuts',
    label: 'Keyboard Shortcuts',
    icon: '⌨️',
    category: 'Help',
    shortcut: { key: '/', meta: true },
    action: () => emit('command:show-shortcuts'),
  },
  {
    id: 'clear-chat',
    label: 'Clear Chat History',
    icon: '🗑️',
    category: 'Chat',
    action: () => emit('command:clear-chat'),
  },
  {
    id: 'export-chat',
    label: 'Export Chat',
    icon: '📤',
    category: 'Chat',
    action: () => emit('command:export-chat'),
  },
];

/**
 * Simple fuzzy match scoring
 * @param {string} query - Search query
 * @param {string} text - Text to match against
 * @returns {number} Match score (higher is better, -1 for no match)
 */
function fuzzyMatch(query, text) {
  if (!query) return 0;

  const queryLower = query.toLowerCase();
  const textLower = text.toLowerCase();

  // Exact match
  if (textLower === queryLower) return 100;

  // Starts with
  if (textLower.startsWith(queryLower)) return 80;

  // Contains
  if (textLower.includes(queryLower)) return 60;

  // Fuzzy match - all characters in order
  let queryIndex = 0;
  let score = 0;
  let lastMatchIndex = -1;

  for (let i = 0; i < textLower.length && queryIndex < queryLower.length; i++) {
    if (textLower[i] === queryLower[queryIndex]) {
      // Bonus for consecutive matches
      if (lastMatchIndex === i - 1) {
        score += 10;
      }
      // Bonus for matching at word boundaries
      if (i === 0 || text[i - 1] === ' ' || text[i - 1] === '-') {
        score += 5;
      }
      score += 1;
      lastMatchIndex = i;
      queryIndex++;
    }
  }

  // All query characters must be found
  if (queryIndex < queryLower.length) return -1;

  return score;
}

/**
 * Command Palette component factory
 * @param {Object} options - Component options
 * @param {Array} options.commands - Additional commands
 * @returns {Object} Alpine component data
 */
export default function CommandPalette(options = {}) {
  return {
    // State
    isOpen: false,
    query: '',
    selectedIndex: 0,
    commands: [...DEFAULT_COMMANDS, ...(options.commands ?? [])],

    // Event listener cleanup
    _cleanup: null,

    /**
     * Initialize component
     */
    init() {
      // Listen for shortcut to open
      this._cleanup = on(SHORTCUT_EVENTS.COMMAND_PALETTE, () => {
        this.open();
      });
    },

    /**
     * Cleanup component
     */
    destroy() {
      if (this._cleanup) {
        this._cleanup();
      }
    },

    /**
     * Get filtered and sorted commands
     */
    get filteredCommands() {
      if (!this.query.trim()) {
        return this.commands;
      }

      return this.commands
        .map((cmd) => ({
          ...cmd,
          score: Math.max(
            fuzzyMatch(this.query, cmd.label),
            fuzzyMatch(this.query, cmd.category ?? '')
          ),
        }))
        .filter((cmd) => cmd.score >= 0)
        .sort((a, b) => b.score - a.score);
    },

    /**
     * Get commands grouped by category
     */
    get groupedCommands() {
      const groups = new Map();

      for (const cmd of this.filteredCommands) {
        const category = cmd.category ?? 'Other';
        if (!groups.has(category)) {
          groups.set(category, []);
        }
        groups.get(category).push(cmd);
      }

      return Array.from(groups.entries()).map(([category, commands]) => ({
        category,
        commands,
      }));
    },

    /**
     * Get flat list of filtered commands for keyboard navigation
     */
    get flatCommands() {
      return this.filteredCommands;
    },

    /**
     * Get selected command
     */
    get selectedCommand() {
      return this.flatCommands[this.selectedIndex] ?? null;
    },

    /**
     * Open the palette
     */
    open() {
      this.isOpen = true;
      this.query = '';
      this.selectedIndex = 0;

      // Focus input after render
      this.$nextTick(() => {
        const input = this.$refs?.searchInput;
        input?.focus();
      });
    },

    /**
     * Close the palette
     */
    close() {
      this.isOpen = false;
      this.query = '';
      this.selectedIndex = 0;
    },

    /**
     * Handle input change
     */
    onInput() {
      this.selectedIndex = 0;
    },

    /**
     * Handle keydown
     * @param {KeyboardEvent} event
     */
    onKeyDown(event) {
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          this.selectNext();
          break;

        case 'ArrowUp':
          event.preventDefault();
          this.selectPrevious();
          break;

        case 'Enter':
          event.preventDefault();
          this.executeSelected();
          break;

        case 'Escape':
          event.preventDefault();
          this.close();
          break;

        case 'Tab':
          event.preventDefault();
          if (event.shiftKey) {
            this.selectPrevious();
          } else {
            this.selectNext();
          }
          break;
      }
    },

    /**
     * Select next command
     */
    selectNext() {
      const max = this.flatCommands.length - 1;
      this.selectedIndex = Math.min(this.selectedIndex + 1, max);
      this.scrollToSelected();
    },

    /**
     * Select previous command
     */
    selectPrevious() {
      this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
      this.scrollToSelected();
    },

    /**
     * Scroll selected item into view
     */
    scrollToSelected() {
      this.$nextTick(() => {
        const selected = this.$el?.querySelector('[data-selected="true"]');
        selected?.scrollIntoView({ block: 'nearest' });
      });
    },

    /**
     * Execute selected command
     */
    executeSelected() {
      const cmd = this.selectedCommand;
      if (cmd) {
        this.execute(cmd);
      }
    },

    /**
     * Execute a command
     * @param {Object} command - Command to execute
     */
    execute(command) {
      this.close();

      if (typeof command.action === 'function') {
        command.action();
      }

      emit('command:executed', { command });
    },

    /**
     * Check if command is selected
     * @param {number} index - Command index
     * @returns {boolean}
     */
    isSelected(index) {
      return this.selectedIndex === index;
    },

    /**
     * Select command by index
     * @param {number} index - Command index
     */
    select(index) {
      this.selectedIndex = index;
    },

    /**
     * Format shortcut for display
     * @param {Object} shortcut - Shortcut definition
     * @returns {string}
     */
    formatShortcut(shortcut) {
      if (!shortcut) return '';
      return formatShortcut(shortcut);
    },

    /**
     * Add a command
     * @param {Object} command - Command to add
     */
    addCommand(command) {
      this.commands.push(command);
    },

    /**
     * Remove a command
     * @param {string} id - Command ID
     */
    removeCommand(id) {
      this.commands = this.commands.filter((c) => c.id !== id);
    },

    /**
     * Register commands from a feature
     * @param {Array} commands - Commands to register
     */
    registerCommands(commands) {
      this.commands = [...this.commands, ...commands];
    },
  };
}

export { DEFAULT_COMMANDS, fuzzyMatch };
