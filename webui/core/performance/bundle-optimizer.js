/**
 * Bundle Optimization Utilities
 * Target: < 200KB gzipped (excluding vendor)
 * Requirements: 16.6
 */

/**
 * Dynamic import helper with loading state
 * @param {string} modulePath - Path to module
 * @param {Function} onLoading - Called when loading starts
 * @param {Function} onLoaded - Called when loading completes
 */
export async function dynamicImport(modulePath, onLoading, onLoaded) {
  if (onLoading) onLoading();
  
  try {
    const module = await import(modulePath);
    if (onLoaded) onLoaded(module);
    return module;
  } catch (error) {
    console.error(`Failed to load module: ${modulePath}`, error);
    throw error;
  }
}

/**
 * Preload critical resources
 * @param {string[]} resources - Array of resource URLs
 */
export function preloadResources(resources) {
  resources.forEach(url => {
    const link = document.createElement('link');
    link.rel = 'preload';
    
    // Determine resource type
    if (url.endsWith('.js')) {
      link.as = 'script';
    } else if (url.endsWith('.css')) {
      link.as = 'style';
    } else if (url.endsWith('.woff2') || url.endsWith('.woff')) {
      link.as = 'font';
      link.crossOrigin = 'anonymous';
    } else if (/\.(png|jpg|jpeg|gif|webp|svg)$/i.test(url)) {
      link.as = 'image';
    }
    
    link.href = url;
    document.head.appendChild(link);
  });
}

/**
 * Prefetch resources for future navigation
 * @param {string[]} resources - Array of resource URLs
 */
export function prefetchResources(resources) {
  // Only prefetch on fast connections
  if (navigator.connection) {
    const { effectiveType, saveData } = navigator.connection;
    if (saveData || effectiveType === 'slow-2g' || effectiveType === '2g') {
      return;
    }
  }
  
  resources.forEach(url => {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    document.head.appendChild(link);
  });
}

/**
 * Load CSS asynchronously (non-blocking)
 * @param {string} href - CSS file URL
 * @returns {Promise<void>}
 */
export function loadCSSAsync(href) {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.media = 'print'; // Load without blocking
    link.onload = () => {
      link.media = 'all'; // Apply styles
      resolve();
    };
    link.onerror = reject;
    document.head.appendChild(link);
  });
}

/**
 * Load script asynchronously
 * @param {string} src - Script URL
 * @param {Object} options - Script options
 * @returns {Promise<void>}
 */
export function loadScriptAsync(src, options = {}) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = options.async !== false;
    script.defer = options.defer || false;
    if (options.type) script.type = options.type;
    if (options.crossOrigin) script.crossOrigin = options.crossOrigin;
    
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

/**
 * Code splitting helper - load feature modules on demand
 */
export const featureModules = {
  async loadChat() {
    return import('../features/chat/index.js');
  },
  
  async loadSettings() {
    return import('../features/settings/index.js');
  },
  
  async loadMemory() {
    return import('../features/memory/index.js');
  },
  
  async loadScheduler() {
    return import('../features/scheduler/index.js');
  },
  
  async loadHealth() {
    return import('../features/health/index.js');
  },
  
  async loadUpload() {
    return import('../features/upload/index.js');
  }
};

/**
 * Vendor module lazy loading
 */
export const vendorModules = {
  async loadKatex() {
    // KaTeX for math rendering
    if (window.katex) return window.katex;
    await loadScriptAsync('vendor/katex/katex.min.js');
    await loadScriptAsync('vendor/katex/katex.auto-render.min.js');
    return window.katex;
  },
  
  async loadAce() {
    // Ace editor for code editing
    if (window.ace) return window.ace;
    await loadScriptAsync('vendor/ace-min/ace.js');
    return window.ace;
  },
  
  async loadFlatpickr() {
    // Flatpickr for date picking
    if (window.flatpickr) return window.flatpickr;
    await loadScriptAsync('vendor/flatpickr/flatpickr.min.js');
    return window.flatpickr;
  },
  
  async loadQRCode() {
    // QR Code generator
    if (window.QRCode) return window.QRCode;
    await loadScriptAsync('vendor/qrcode.min.js');
    return window.QRCode;
  }
};

/**
 * Resource hints for critical path optimization
 */
export function addResourceHints() {
  // DNS prefetch for external resources
  const dnsPrefetch = [
    'https://fonts.googleapis.com',
    'https://fonts.gstatic.com'
  ];
  
  dnsPrefetch.forEach(origin => {
    const link = document.createElement('link');
    link.rel = 'dns-prefetch';
    link.href = origin;
    document.head.appendChild(link);
  });
  
  // Preconnect to critical origins
  const preconnect = [
    'https://fonts.googleapis.com',
    'https://fonts.gstatic.com'
  ];
  
  preconnect.forEach(origin => {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = origin;
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
}

/**
 * Estimate bundle size (for development)
 */
export async function estimateBundleSize() {
  const scripts = Array.from(document.querySelectorAll('script[src]'));
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
  
  let totalJS = 0;
  let totalCSS = 0;
  
  // Estimate JS size
  for (const script of scripts) {
    try {
      const response = await fetch(script.src, { method: 'HEAD' });
      const size = parseInt(response.headers.get('content-length') || '0', 10);
      totalJS += size;
    } catch (e) {
      // Ignore cross-origin errors
    }
  }
  
  // Estimate CSS size
  for (const style of styles) {
    try {
      const response = await fetch(style.href, { method: 'HEAD' });
      const size = parseInt(response.headers.get('content-length') || '0', 10);
      totalCSS += size;
    } catch (e) {
      // Ignore cross-origin errors
    }
  }
  
  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };
  
  console.group('Bundle Size Estimate');
  console.log(`JavaScript: ${formatSize(totalJS)}`);
  console.log(`CSS: ${formatSize(totalCSS)}`);
  console.log(`Total: ${formatSize(totalJS + totalCSS)}`);
  console.log(`Gzipped estimate: ~${formatSize((totalJS + totalCSS) * 0.3)}`);
  console.groupEnd();
  
  return { js: totalJS, css: totalCSS, total: totalJS + totalCSS };
}
