/**
 * Accessibility Utilities
 * 
 * Provides ARIA labels, live regions, and accessibility helpers.
 * Ensures WCAG 2.1 AA compliance across all components.
 * 
 * @module core/accessibility
 */

/**
 * ARIA label templates for common UI elements
 */
export const ARIA_LABELS = {
  // Navigation
  sidebar: 'Main navigation',
  sidebarToggle: 'Toggle sidebar navigation',
  mainContent: 'Main content area',
  breadcrumb: 'Breadcrumb navigation',
  
  // Chat
  chatInput: 'Message input',
  chatInputPlaceholder: 'Type your message here',
  sendMessage: 'Send message',
  attachFile: 'Attach file',
  voiceInput: 'Voice input',
  messageList: 'Chat messages',
  userMessage: 'Your message',
  assistantMessage: 'Assistant response',
  thinkingIndicator: 'Assistant is thinking',
  streamingIndicator: 'Assistant is responding',
  
  // Settings
  settingsModal: 'Settings dialog',
  settingsClose: 'Close settings',
  settingsSave: 'Save settings',
  settingsCancel: 'Cancel changes',
  settingsTab: (name) => `${name} settings tab`,
  settingsCard: (name) => `${name} settings`,
  expandCard: (name) => `Expand ${name} settings`,
  collapseCard: (name) => `Collapse ${name} settings`,
  
  // Forms
  showPassword: 'Show password',
  hidePassword: 'Hide password',
  clearInput: 'Clear input',
  searchInput: 'Search',
  filterSelect: 'Filter options',
  
  // Sessions
  sessionList: 'Chat sessions',
  newSession: 'Start new chat',
  deleteSession: 'Delete session',
  renameSession: 'Rename session',
  
  // Memory
  memoryList: 'Stored memories',
  memorySearch: 'Search memories',
  deleteMemory: 'Delete memory',
  
  // Scheduler
  taskList: 'Scheduled tasks',
  createTask: 'Create new task',
  deleteTask: 'Delete task',
  editTask: 'Edit task',
  
  // Health
  healthStatus: 'System health status',
  serviceStatus: (name) => `${name} service status`,
  
  // Upload
  dropZone: 'File drop zone',
  uploadProgress: 'Upload progress',
  removeFile: 'Remove file',
  
  // Notifications
  notifications: 'Notifications',
  dismissNotification: 'Dismiss notification',
  
  // Command Palette
  commandPalette: 'Command palette',
  commandSearch: 'Search commands',
  
  // Connection
  connectionStatus: 'Connection status',
  reconnect: 'Reconnect to server',
};

/**
 * Create a live region for screen reader announcements
 * @param {string} id - Region ID
 * @param {string} politeness - 'polite' or 'assertive'
 * @returns {HTMLElement} Live region element
 */
export function createLiveRegion(id = 'live-region', politeness = 'polite') {
  let region = document.getElementById(id);
  
  if (!region) {
    region = document.createElement('div');
    region.id = id;
    region.setAttribute('role', 'status');
    region.setAttribute('aria-live', politeness);
    region.setAttribute('aria-atomic', 'true');
    region.className = 'sr-only';
    document.body.appendChild(region);
  }
  
  return region;
}

/**
 * Announce a message to screen readers
 * @param {string} message - Message to announce
 * @param {string} politeness - 'polite' or 'assertive'
 */
export function announce(message, politeness = 'polite') {
  const regionId = politeness === 'assertive' ? 'live-region-assertive' : 'live-region-polite';
  const region = createLiveRegion(regionId, politeness);
  
  // Clear and set message (triggers announcement)
  region.textContent = '';
  requestAnimationFrame(() => {
    region.textContent = message;
  });
}

/**
 * Announce an error to screen readers (assertive)
 * @param {string} message - Error message
 */
export function announceError(message) {
  announce(message, 'assertive');
}

/**
 * Generate unique ID for ARIA relationships
 * @param {string} prefix - ID prefix
 * @returns {string} Unique ID
 */
export function generateId(prefix = 'aria') {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Set up ARIA description relationship
 * @param {HTMLElement} element - Element to describe
 * @param {HTMLElement} description - Description element
 */
export function setDescription(element, description) {
  const id = description.id || generateId('desc');
  description.id = id;
  element.setAttribute('aria-describedby', id);
}

/**
 * Set up ARIA label relationship
 * @param {HTMLElement} element - Element to label
 * @param {HTMLElement} label - Label element
 */
export function setLabelledBy(element, label) {
  const id = label.id || generateId('label');
  label.id = id;
  element.setAttribute('aria-labelledby', id);
}

/**
 * Focus trap utility for modals and dialogs
 * @param {HTMLElement} container - Container element
 * @returns {Object} Focus trap controls
 */
export function createFocusTrap(container) {
  const focusableSelector = [
    'button:not([disabled])',
    '[href]',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(', ');
  
  let previousActiveElement = null;
  
  function getFocusableElements() {
    return Array.from(container.querySelectorAll(focusableSelector));
  }
  
  function handleKeyDown(e) {
    if (e.key !== 'Tab') return;
    
    const focusable = getFocusableElements();
    if (focusable.length === 0) return;
    
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
  
  return {
    activate() {
      previousActiveElement = document.activeElement;
      container.addEventListener('keydown', handleKeyDown);
      
      // Focus first focusable element
      const focusable = getFocusableElements();
      if (focusable.length > 0) {
        focusable[0].focus();
      }
    },
    
    deactivate() {
      container.removeEventListener('keydown', handleKeyDown);
      
      // Restore focus
      if (previousActiveElement && previousActiveElement.focus) {
        previousActiveElement.focus();
      }
    },
  };
}

/**
 * Skip link utility for keyboard navigation
 * @param {string} targetId - ID of main content
 * @returns {HTMLElement} Skip link element
 */
export function createSkipLink(targetId = 'main-content') {
  const link = document.createElement('a');
  link.href = `#${targetId}`;
  link.className = 'skip-link';
  link.textContent = 'Skip to main content';
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.tabIndex = -1;
      target.focus();
    }
  });
  return link;
}

/**
 * Check if reduced motion is preferred
 * @returns {boolean}
 */
export function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Check if high contrast is preferred
 * @returns {boolean}
 */
export function prefersHighContrast() {
  return window.matchMedia('(prefers-contrast: more)').matches;
}

/**
 * Initialize accessibility features
 */
export function initAccessibility() {
  // Create live regions
  createLiveRegion('live-region-polite', 'polite');
  createLiveRegion('live-region-assertive', 'assertive');
  
  // Add skip link
  const skipLink = createSkipLink('main-content');
  document.body.insertBefore(skipLink, document.body.firstChild);
  
  // Set up reduced motion preference
  if (prefersReducedMotion()) {
    document.documentElement.classList.add('reduce-motion');
  }
  
  // Set up high contrast preference
  if (prefersHighContrast()) {
    document.documentElement.classList.add('high-contrast');
  }
  
  // Listen for preference changes
  window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
    document.documentElement.classList.toggle('reduce-motion', e.matches);
  });
  
  window.matchMedia('(prefers-contrast: more)').addEventListener('change', (e) => {
    document.documentElement.classList.toggle('high-contrast', e.matches);
  });
}

/**
 * Alpine.js directive for ARIA labels
 * Usage: x-aria-label="'Send message'"
 */
export function registerAriaDirective(Alpine) {
  Alpine.directive('aria-label', (el, { expression }, { evaluate }) => {
    const label = evaluate(expression);
    if (label) {
      el.setAttribute('aria-label', label);
    }
  });
}

/**
 * Ensure all images have alt text
 * Adds empty alt for decorative images, warns for missing alt
 */
export function auditImages() {
  const images = document.querySelectorAll('img');
  const issues = [];
  
  images.forEach((img, index) => {
    if (!img.hasAttribute('alt')) {
      issues.push({
        element: img,
        issue: 'Missing alt attribute',
        suggestion: img.src.includes('icon') || img.src.includes('logo') 
          ? 'Add descriptive alt text or alt="" for decorative images'
          : 'Add descriptive alt text',
      });
      console.warn(`[A11y] Image ${index + 1} missing alt attribute:`, img.src);
    }
  });
  
  return issues;
}

/**
 * Image component helper with required alt
 * @param {string} src - Image source
 * @param {string} alt - Alt text (required)
 * @param {boolean} decorative - If true, sets alt=""
 * @returns {Object} Image attributes
 */
export function imageAttrs(src, alt, decorative = false) {
  if (!decorative && !alt) {
    console.warn('[A11y] Non-decorative image requires alt text');
  }
  
  return {
    src,
    alt: decorative ? '' : alt,
    'aria-hidden': decorative ? 'true' : undefined,
    loading: 'lazy',
  };
}

/**
 * Create accessible form field with label association
 * @param {string} id - Field ID
 * @param {string} label - Label text
 * @param {Object} options - Additional options
 * @returns {Object} Field and label attributes
 */
export function formField(id, label, options = {}) {
  const fieldId = id || generateId('field');
  const labelId = `${fieldId}-label`;
  const errorId = `${fieldId}-error`;
  const descId = `${fieldId}-desc`;
  
  return {
    label: {
      id: labelId,
      for: fieldId,
      class: options.required ? 'required' : '',
    },
    field: {
      id: fieldId,
      name: options.name || fieldId,
      'aria-labelledby': labelId,
      'aria-describedby': options.description ? descId : undefined,
      'aria-invalid': options.error ? 'true' : undefined,
      'aria-errormessage': options.error ? errorId : undefined,
      'aria-required': options.required ? 'true' : undefined,
      required: options.required || undefined,
    },
    error: {
      id: errorId,
      role: 'alert',
      'aria-live': 'polite',
    },
    description: {
      id: descId,
    },
  };
}

/**
 * Audit form fields for label association
 * @returns {Array} Issues found
 */
export function auditFormFields() {
  const inputs = document.querySelectorAll('input, select, textarea');
  const issues = [];
  
  inputs.forEach((input, index) => {
    const id = input.id;
    const hasLabel = id && document.querySelector(`label[for="${id}"]`);
    const hasAriaLabel = input.hasAttribute('aria-label');
    const hasAriaLabelledBy = input.hasAttribute('aria-labelledby');
    
    if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy) {
      issues.push({
        element: input,
        issue: 'Input has no associated label',
        suggestion: 'Add a <label for="..."> or aria-label attribute',
      });
      console.warn(`[A11y] Input ${index + 1} has no associated label:`, input);
    }
  });
  
  return issues;
}

/**
 * Calculate relative luminance of a color
 * @param {number} r - Red (0-255)
 * @param {number} g - Green (0-255)
 * @param {number} b - Blue (0-255)
 * @returns {number} Relative luminance
 */
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Parse color string to RGB
 * @param {string} color - CSS color string
 * @returns {Object|null} RGB values or null
 */
function parseColor(color) {
  // Handle hex colors
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    if (hex.length === 3) {
      return {
        r: parseInt(hex[0] + hex[0], 16),
        g: parseInt(hex[1] + hex[1], 16),
        b: parseInt(hex[2] + hex[2], 16),
      };
    }
    if (hex.length === 6) {
      return {
        r: parseInt(hex.slice(0, 2), 16),
        g: parseInt(hex.slice(2, 4), 16),
        b: parseInt(hex.slice(4, 6), 16),
      };
    }
  }
  
  // Handle rgb/rgba
  const rgbMatch = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (rgbMatch) {
    return {
      r: parseInt(rgbMatch[1]),
      g: parseInt(rgbMatch[2]),
      b: parseInt(rgbMatch[3]),
    };
  }
  
  return null;
}

/**
 * Calculate contrast ratio between two colors
 * @param {string} color1 - First color (CSS string)
 * @param {string} color2 - Second color (CSS string)
 * @returns {number} Contrast ratio (1-21)
 */
export function getContrastRatio(color1, color2) {
  const c1 = parseColor(color1);
  const c2 = parseColor(color2);
  
  if (!c1 || !c2) return 0;
  
  const l1 = getLuminance(c1.r, c1.g, c1.b);
  const l2 = getLuminance(c2.r, c2.g, c2.b);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if contrast meets WCAG AA requirements
 * @param {string} foreground - Foreground color
 * @param {string} background - Background color
 * @param {string} size - 'normal' or 'large' text
 * @returns {Object} Pass/fail status and ratio
 */
export function checkContrast(foreground, background, size = 'normal') {
  const ratio = getContrastRatio(foreground, background);
  const minRatio = size === 'large' ? 3 : 4.5;
  
  return {
    ratio: Math.round(ratio * 100) / 100,
    passes: ratio >= minRatio,
    level: ratio >= 7 ? 'AAA' : ratio >= 4.5 ? 'AA' : ratio >= 3 ? 'AA-large' : 'fail',
    required: minRatio,
  };
}

/**
 * Audit page for contrast issues
 * @returns {Array} Contrast issues found
 */
export function auditContrast() {
  const issues = [];
  const elements = document.querySelectorAll('body *');
  
  elements.forEach((el) => {
    const style = window.getComputedStyle(el);
    const color = style.color;
    const bgColor = style.backgroundColor;
    
    // Skip transparent backgrounds
    if (bgColor === 'rgba(0, 0, 0, 0)' || bgColor === 'transparent') return;
    
    const result = checkContrast(color, bgColor);
    
    if (!result.passes && result.ratio > 1) {
      issues.push({
        element: el,
        foreground: color,
        background: bgColor,
        ratio: result.ratio,
        required: result.required,
      });
    }
  });
  
  return issues;
}

export default {
  ARIA_LABELS,
  announce,
  announceError,
  generateId,
  setDescription,
  setLabelledBy,
  createFocusTrap,
  createSkipLink,
  prefersReducedMotion,
  prefersHighContrast,
  initAccessibility,
  registerAriaDirective,
  auditImages,
  imageAttrs,
  formField,
  auditFormFields,
  getContrastRatio,
  checkContrast,
  auditContrast,
};
