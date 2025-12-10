/**
 * Keyboard Shortcuts Module
 *
 * Global keyboard shortcuts for the application.
 * Handles Cmd/Ctrl+K, Cmd/Ctrl+N, Cmd/Ctrl+,, Escape, etc.
 *
 * @module core/keyboard/shortcuts
 * Requirements: 13.2, 13.3, 13.4, 13.5, 13.6, 13.7
 */

import { emit } from '../../js/event-bus.js';

/**
 * Shortcut definitions
 */
export const SHORTCUTS = Object.freeze({
  COMMAND_PALETTE: { key: 'k', meta: true, description: 'Open command palette' },
  NEW_CHAT: { key: 'n', meta: true, description: 'New chat' },
  SETTINGS: { key: ',', meta: true, description: 'Open settings' },
  CLOSE: { key: 'Escape', description: 'Close modal/panel' },
  HELP: { key: '/', meta: true, description: 'Show keyboard shortcuts' },
  SEARCH: { key: 'f', meta: true, description: 'Search' },
  SAVE: { key: 's', meta: true, description: 'Save' },
});

/**
 * Shortcut event names
 */
export const SHORTCUT_EVENTS = Object.freeze({
  COMMAND_PALETTE: 'shortcut:command-palette',
  NEW_CHAT: 'shortcut:new-chat',
  SETTINGS: 'shortcut:settings',
  CLOSE: 'shortcut:close',
  HELP: 'shortcut:help',
  SEARCH: 'shortcut:search',
  SAVE: 'shortcut:save',
});

/**
 * Registered shortcuts
 */
const registeredShortcuts = new Map();

/**
 * Check if event matches a shortcut
 * @param {KeyboardEvent} event - Keyboard event
 * @param {Object} shortcut - Shortcut definition
 * @returns {boolean}
 */
function matchesShortcut(event, shortcut) {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const metaKey = isMac ? event.metaKey : event.ctrlKey;

  if (shortcut.meta && !metaKey) return false;
  if (shortcut.shift && !event.shiftKey) return false;
  if (shortcut.alt && !event.altKey) return false;

  return event.key.toLowerCase() === shortcut.key.toLowerCase();
}

/**
 * Check if focus is in an input element
 * @returns {boolean}
 */
function isInInput() {
  const active = document.activeElement;
  if (!active) return false;

  const tagName = active.tagName.toLowerCase();
  if (tagName === 'input' || tagName === 'textarea') return true;
  if (active.isContentEditable) return true;

  return false;
}

/**
 * Handle global keydown event
 * @param {KeyboardEvent} event - Keyboard event
 */
function handleKeyDown(event) {
  // Check registered shortcuts
  for (const [id, { shortcut, handler, allowInInput }] of registeredShortcuts) {
    if (matchesShortcut(event, shortcut)) {
      // Skip if in input and not allowed
      if (!allowInInput && isInInput()) continue;

      event.preventDefault();
      event.stopPropagation();
      handler(event);
      return;
    }
  }

  // Built-in shortcuts
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const metaKey = isMac ? event.metaKey : event.ctrlKey;

  // Command palette: Cmd/Ctrl+K
  if (metaKey && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    emit(SHORTCUT_EVENTS.COMMAND_PALETTE);
    return;
  }

  // New chat: Cmd/Ctrl+N
  if (metaKey && event.key.toLowerCase() === 'n') {
    event.preventDefault();
    emit(SHORTCUT_EVENTS.NEW_CHAT);
    return;
  }

  // Settings: Cmd/Ctrl+,
  if (metaKey && event.key === ',') {
    event.preventDefault();
    emit(SHORTCUT_EVENTS.SETTINGS);
    return;
  }

  // Help: Cmd/Ctrl+/
  if (metaKey && event.key === '/') {
    event.preventDefault();
    emit(SHORTCUT_EVENTS.HELP);
    return;
  }

  // Close: Escape (only when not in input)
  if (event.key === 'Escape' && !isInInput()) {
    emit(SHORTCUT_EVENTS.CLOSE);
    return;
  }

  // Load last message: Up Arrow in empty input
  if (event.key === 'ArrowUp' && isInInput()) {
    const input = document.activeElement;
    if (input.value === '' || input.textContent === '') {
      emit('shortcut:load-last-message');
    }
  }
}

/**
 * Register a custom shortcut
 * @param {string} id - Unique shortcut ID
 * @param {Object} shortcut - Shortcut definition
 * @param {Function} handler - Handler function
 * @param {boolean} allowInInput - Allow in input fields
 * @returns {Function} Unregister function
 */
export function registerShortcut(id, shortcut, handler, allowInInput = false) {
  registeredShortcuts.set(id, { shortcut, handler, allowInInput });

  return () => {
    registeredShortcuts.delete(id);
  };
}

/**
 * Unregister a shortcut
 * @param {string} id - Shortcut ID
 */
export function unregisterShortcut(id) {
  registeredShortcuts.delete(id);
}

/**
 * Get all registered shortcuts
 * @returns {Array} Array of shortcut info
 */
export function getShortcuts() {
  const shortcuts = [];

  // Built-in shortcuts
  for (const [name, shortcut] of Object.entries(SHORTCUTS)) {
    shortcuts.push({
      id: name.toLowerCase(),
      ...shortcut,
      builtin: true,
    });
  }

  // Custom shortcuts
  for (const [id, { shortcut }] of registeredShortcuts) {
    shortcuts.push({
      id,
      ...shortcut,
      builtin: false,
    });
  }

  return shortcuts;
}

/**
 * Format shortcut for display
 * @param {Object} shortcut - Shortcut definition
 * @returns {string} Formatted shortcut string
 */
export function formatShortcut(shortcut) {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const parts = [];

  if (shortcut.meta) {
    parts.push(isMac ? '⌘' : 'Ctrl');
  }
  if (shortcut.shift) {
    parts.push(isMac ? '⇧' : 'Shift');
  }
  if (shortcut.alt) {
    parts.push(isMac ? '⌥' : 'Alt');
  }

  // Format key
  let key = shortcut.key;
  if (key === 'Escape') key = 'Esc';
  if (key === ' ') key = 'Space';
  if (key.length === 1) key = key.toUpperCase();

  parts.push(key);

  return parts.join(isMac ? '' : '+');
}

/**
 * Initialize keyboard shortcuts
 */
export function initShortcuts() {
  document.addEventListener('keydown', handleKeyDown);
}

/**
 * Cleanup keyboard shortcuts
 */
export function cleanupShortcuts() {
  document.removeEventListener('keydown', handleKeyDown);
  registeredShortcuts.clear();
}

/**
 * Show toast notification for shortcut
 * @param {string} action - Action description
 */
export function showShortcutToast(action) {
  emit('toast:show', {
    message: action,
    type: 'info',
    duration: 1500,
  });
}

export default {
  SHORTCUTS,
  SHORTCUT_EVENTS,
  registerShortcut,
  unregisterShortcut,
  getShortcuts,
  formatShortcut,
  initShortcuts,
  cleanupShortcuts,
  showShortcutToast,
};
