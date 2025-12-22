/**
 * SomaStack UI - Core Utilities
 * Version: 1.0.0
 */

window.SomaStackUI = window.SomaStackUI || {};

SomaStackUI.version = '1.0.0';

/**
 * Format a number with K/M/B suffixes
 */
SomaStackUI.formatNumber = function(num, precision = 1) {
  if (num === null || num === undefined) return '—';
  
  if (Math.abs(num) >= 1e9) {
    return (num / 1e9).toFixed(precision) + 'B';
  }
  if (Math.abs(num) >= 1e6) {
    return (num / 1e6).toFixed(precision) + 'M';
  }
  if (Math.abs(num) >= 1e3) {
    return (num / 1e3).toFixed(precision) + 'K';
  }
  
  return num.toLocaleString();
};

/**
 * Format a duration in milliseconds
 */
SomaStackUI.formatDuration = function(ms) {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m`;
  return `${(ms / 3600000).toFixed(1)}h`;
};

/**
 * Format a relative time
 */
SomaStackUI.formatRelativeTime = function(date) {
  if (!date) return 'Never';
  
  const now = new Date();
  const diff = now - new Date(date);
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) {
    const mins = Math.floor(diff / 60000);
    return `${mins}m ago`;
  }
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000);
    return `${hours}h ago`;
  }
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000);
    return `${days}d ago`;
  }
  
  return new Date(date).toLocaleDateString();
};

/**
 * Debounce a function
 */
SomaStackUI.debounce = function(fn, delay = 300) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
};

/**
 * Throttle a function
 */
SomaStackUI.throttle = function(fn, limit = 300) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Generate a unique ID
 */
SomaStackUI.uniqueId = function(prefix = 'soma') {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Deep clone an object
 */
SomaStackUI.deepClone = function(obj) {
  return JSON.parse(JSON.stringify(obj));
};

/**
 * Check if an element is visible in viewport
 */
SomaStackUI.isInViewport = function(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
};

/**
 * Copy text to clipboard
 */
SomaStackUI.copyToClipboard = async function(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
};

/**
 * Calculate WCAG contrast ratio between two colors
 */
SomaStackUI.getContrastRatio = function(color1, color2) {
  const getLuminance = (r, g, b) => {
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };
  
  const parseColor = (color) => {
    if (color.startsWith('#')) {
      const hex = color.slice(1);
      return [
        parseInt(hex.slice(0, 2), 16),
        parseInt(hex.slice(2, 4), 16),
        parseInt(hex.slice(4, 6), 16)
      ];
    }
    return [0, 0, 0];
  };
  
  const [r1, g1, b1] = parseColor(color1);
  const [r2, g2, b2] = parseColor(color2);
  
  const l1 = getLuminance(r1, g1, b1);
  const l2 = getLuminance(r2, g2, b2);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SomaStackUI;
}
