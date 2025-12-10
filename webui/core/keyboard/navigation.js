/**
 * Keyboard Navigation Module
 *
 * Provides keyboard navigation support for the application.
 * Handles Tab, Arrow keys, Enter, and Escape for navigation.
 *
 * @module core/keyboard/navigation
 * Requirements: 3.4
 */

import { emit } from '../../js/event-bus.js';

/**
 * Navigation key codes
 */
export const KEYS = Object.freeze({
  TAB: 'Tab',
  ENTER: 'Enter',
  SPACE: ' ',
  ESCAPE: 'Escape',
  ARROW_UP: 'ArrowUp',
  ARROW_DOWN: 'ArrowDown',
  ARROW_LEFT: 'ArrowLeft',
  ARROW_RIGHT: 'ArrowRight',
  HOME: 'Home',
  END: 'End',
});

/**
 * Focusable element selectors
 */
const FOCUSABLE_SELECTORS = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable="true"]',
].join(', ');

/**
 * Get all focusable elements within a container
 * @param {HTMLElement} container - Container element
 * @returns {HTMLElement[]} Array of focusable elements
 */
export function getFocusableElements(container = document) {
  return Array.from(container.querySelectorAll(FOCUSABLE_SELECTORS)).filter(
    (el) => !el.hasAttribute('disabled') && el.offsetParent !== null
  );
}

/**
 * Focus the next element in a list
 * @param {HTMLElement[]} elements - List of elements
 * @param {HTMLElement} current - Currently focused element
 * @param {boolean} wrap - Whether to wrap around
 * @returns {HTMLElement|null} Newly focused element
 */
export function focusNext(elements, current, wrap = true) {
  const index = elements.indexOf(current);
  let nextIndex = index + 1;

  if (nextIndex >= elements.length) {
    nextIndex = wrap ? 0 : elements.length - 1;
  }

  const next = elements[nextIndex];
  next?.focus();
  return next;
}

/**
 * Focus the previous element in a list
 * @param {HTMLElement[]} elements - List of elements
 * @param {HTMLElement} current - Currently focused element
 * @param {boolean} wrap - Whether to wrap around
 * @returns {HTMLElement|null} Newly focused element
 */
export function focusPrevious(elements, current, wrap = true) {
  const index = elements.indexOf(current);
  let prevIndex = index - 1;

  if (prevIndex < 0) {
    prevIndex = wrap ? elements.length - 1 : 0;
  }

  const prev = elements[prevIndex];
  prev?.focus();
  return prev;
}

/**
 * Focus the first element in a list
 * @param {HTMLElement[]} elements - List of elements
 * @returns {HTMLElement|null} Focused element
 */
export function focusFirst(elements) {
  const first = elements[0];
  first?.focus();
  return first;
}

/**
 * Focus the last element in a list
 * @param {HTMLElement[]} elements - List of elements
 * @returns {HTMLElement|null} Focused element
 */
export function focusLast(elements) {
  const last = elements[elements.length - 1];
  last?.focus();
  return last;
}

/**
 * Create a keyboard navigation handler for a container
 * @param {Object} options - Handler options
 * @param {HTMLElement} options.container - Container element
 * @param {string} options.itemSelector - Selector for navigable items
 * @param {string} options.orientation - 'horizontal' | 'vertical' | 'both'
 * @param {boolean} options.wrap - Whether to wrap around
 * @param {Function} options.onSelect - Callback when item is selected
 * @param {Function} options.onEscape - Callback when Escape is pressed
 * @returns {Function} Cleanup function
 */
export function createNavigationHandler(options) {
  const {
    container,
    itemSelector = '[role="menuitem"], [role="option"], .nav-item',
    orientation = 'vertical',
    wrap = true,
    onSelect,
    onEscape,
  } = options;

  if (!container) return () => {};

  function handleKeyDown(event) {
    const items = Array.from(container.querySelectorAll(itemSelector));
    const current = document.activeElement;
    const currentIndex = items.indexOf(current);

    // Only handle if focus is within container
    if (!container.contains(current)) return;

    switch (event.key) {
      case KEYS.ARROW_DOWN:
        if (orientation === 'vertical' || orientation === 'both') {
          event.preventDefault();
          focusNext(items, current, wrap);
        }
        break;

      case KEYS.ARROW_UP:
        if (orientation === 'vertical' || orientation === 'both') {
          event.preventDefault();
          focusPrevious(items, current, wrap);
        }
        break;

      case KEYS.ARROW_RIGHT:
        if (orientation === 'horizontal' || orientation === 'both') {
          event.preventDefault();
          focusNext(items, current, wrap);
        }
        break;

      case KEYS.ARROW_LEFT:
        if (orientation === 'horizontal' || orientation === 'both') {
          event.preventDefault();
          focusPrevious(items, current, wrap);
        }
        break;

      case KEYS.HOME:
        event.preventDefault();
        focusFirst(items);
        break;

      case KEYS.END:
        event.preventDefault();
        focusLast(items);
        break;

      case KEYS.ENTER:
      case KEYS.SPACE:
        if (currentIndex >= 0) {
          event.preventDefault();
          onSelect?.(items[currentIndex], currentIndex);
          // Trigger click for accessibility
          items[currentIndex].click();
        }
        break;

      case KEYS.ESCAPE:
        event.preventDefault();
        onEscape?.();
        break;
    }
  }

  container.addEventListener('keydown', handleKeyDown);

  // Return cleanup function
  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
}

/**
 * Create a roving tabindex handler
 * Manages tabindex for a group of elements so only one is tabbable
 * @param {Object} options - Handler options
 * @param {HTMLElement} options.container - Container element
 * @param {string} options.itemSelector - Selector for items
 * @param {number} options.initialIndex - Initial focused index
 * @returns {Object} Handler with methods
 */
export function createRovingTabindex(options) {
  const { container, itemSelector, initialIndex = 0 } = options;

  let currentIndex = initialIndex;

  function getItems() {
    return Array.from(container.querySelectorAll(itemSelector));
  }

  function updateTabindex(newIndex) {
    const items = getItems();
    items.forEach((item, index) => {
      item.setAttribute('tabindex', index === newIndex ? '0' : '-1');
    });
    currentIndex = newIndex;
  }

  function focusItem(index) {
    const items = getItems();
    if (index >= 0 && index < items.length) {
      updateTabindex(index);
      items[index].focus();
    }
  }

  // Initialize
  updateTabindex(currentIndex);

  return {
    focusNext: () => {
      const items = getItems();
      const nextIndex = (currentIndex + 1) % items.length;
      focusItem(nextIndex);
    },
    focusPrevious: () => {
      const items = getItems();
      const prevIndex = (currentIndex - 1 + items.length) % items.length;
      focusItem(prevIndex);
    },
    focusFirst: () => focusItem(0),
    focusLast: () => focusItem(getItems().length - 1),
    focusItem,
    getCurrentIndex: () => currentIndex,
    refresh: () => updateTabindex(currentIndex),
  };
}

/**
 * Alpine directive for keyboard navigation
 * Usage: x-keyboard-nav="{ orientation: 'vertical', wrap: true }"
 */
export function keyboardNavDirective(Alpine) {
  Alpine.directive('keyboard-nav', (el, { expression }, { evaluate, cleanup }) => {
    const options = expression ? evaluate(expression) : {};

    const cleanupFn = createNavigationHandler({
      container: el,
      ...options,
    });

    cleanup(cleanupFn);
  });
}

export default {
  KEYS,
  getFocusableElements,
  focusNext,
  focusPrevious,
  focusFirst,
  focusLast,
  createNavigationHandler,
  createRovingTabindex,
  keyboardNavDirective,
};
