/**
 * Keyboard Module
 *
 * Keyboard navigation and shortcuts.
 *
 * @module core/keyboard
 */

export {
  KEYS,
  getFocusableElements,
  focusNext,
  focusPrevious,
  focusFirst,
  focusLast,
  createNavigationHandler,
  createRovingTabindex,
  keyboardNavDirective,
} from './navigation.js';

export {
  SHORTCUTS,
  SHORTCUT_EVENTS,
  registerShortcut,
  unregisterShortcut,
  getShortcuts,
  formatShortcut,
  initShortcuts,
  cleanupShortcuts,
  showShortcutToast,
} from './shortcuts.js';
