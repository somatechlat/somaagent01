/**
 * Lazy Loading Module
 * Implements lazy loading for images and heavy components
 * Requirements: 16.5
 */

/**
 * Lazy load images using Intersection Observer
 */
class ImageLazyLoader {
  constructor(options = {}) {
    this.rootMargin = options.rootMargin || '50px';
    this.threshold = options.threshold || 0.1;
    this.loadedImages = new Set();
    this.observer = null;
    this.init();
  }

  init() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        (entries) => this.handleIntersection(entries),
        {
          rootMargin: this.rootMargin,
          threshold: this.threshold
        }
      );
    }
  }

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        this.loadImage(entry.target);
        this.observer.unobserve(entry.target);
      }
    });
  }

  loadImage(img) {
    const src = img.dataset.src;
    const srcset = img.dataset.srcset;
    
    if (!src && !srcset) return;

    // Create a temporary image to preload
    const tempImg = new Image();
    
    tempImg.onload = () => {
      if (src) img.src = src;
      if (srcset) img.srcset = srcset;
      img.classList.add('lazy-loaded');
      img.classList.remove('lazy');
      this.loadedImages.add(img);
    };

    tempImg.onerror = () => {
      img.classList.add('lazy-error');
      console.warn('Failed to lazy load image:', src);
    };

    // Start loading
    tempImg.src = src || srcset.split(' ')[0];
  }

  observe(img) {
    if (!img || this.loadedImages.has(img)) return;
    
    if (this.observer) {
      this.observer.observe(img);
    } else {
      // Fallback for browsers without IntersectionObserver
      this.loadImage(img);
    }
  }

  observeAll(selector = 'img[data-src], img.lazy') {
    const images = document.querySelectorAll(selector);
    images.forEach(img => this.observe(img));
  }

  disconnect() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

/**
 * Lazy load components/modules dynamically
 */
class ComponentLazyLoader {
  constructor() {
    this.loadedModules = new Map();
    this.loadingPromises = new Map();
  }

  /**
   * Dynamically import a module
   * @param {string} modulePath - Path to the module
   * @returns {Promise<any>} - The loaded module
   */
  async loadModule(modulePath) {
    // Return cached module if already loaded
    if (this.loadedModules.has(modulePath)) {
      return this.loadedModules.get(modulePath);
    }

    // Return existing promise if currently loading
    if (this.loadingPromises.has(modulePath)) {
      return this.loadingPromises.get(modulePath);
    }

    // Start loading
    const loadPromise = import(modulePath)
      .then(module => {
        this.loadedModules.set(modulePath, module);
        this.loadingPromises.delete(modulePath);
        return module;
      })
      .catch(error => {
        this.loadingPromises.delete(modulePath);
        console.error(`Failed to load module: ${modulePath}`, error);
        throw error;
      });

    this.loadingPromises.set(modulePath, loadPromise);
    return loadPromise;
  }

  /**
   * Preload modules that might be needed soon
   * @param {string[]} modulePaths - Array of module paths to preload
   */
  preload(modulePaths) {
    modulePaths.forEach(path => {
      // Use link preload for better browser optimization
      const link = document.createElement('link');
      link.rel = 'modulepreload';
      link.href = path;
      document.head.appendChild(link);
    });
  }

  /**
   * Check if a module is loaded
   * @param {string} modulePath - Path to check
   * @returns {boolean}
   */
  isLoaded(modulePath) {
    return this.loadedModules.has(modulePath);
  }
}

/**
 * Lazy load content when element enters viewport
 */
class ContentLazyLoader {
  constructor(options = {}) {
    this.rootMargin = options.rootMargin || '100px';
    this.threshold = options.threshold || 0;
    this.observer = null;
    this.callbacks = new WeakMap();
    this.init();
  }

  init() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        (entries) => this.handleIntersection(entries),
        {
          rootMargin: this.rootMargin,
          threshold: this.threshold
        }
      );
    }
  }

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const callback = this.callbacks.get(entry.target);
        if (callback) {
          callback(entry.target);
          this.callbacks.delete(entry.target);
        }
        this.observer.unobserve(entry.target);
      }
    });
  }

  /**
   * Observe an element and call callback when it enters viewport
   * @param {HTMLElement} element - Element to observe
   * @param {Function} callback - Function to call when visible
   */
  observe(element, callback) {
    if (!element || !callback) return;

    this.callbacks.set(element, callback);
    
    if (this.observer) {
      this.observer.observe(element);
    } else {
      // Fallback: execute immediately
      callback(element);
    }
  }

  unobserve(element) {
    if (this.observer && element) {
      this.observer.unobserve(element);
      this.callbacks.delete(element);
    }
  }

  disconnect() {
    if (this.observer) {
      this.observer.disconnect();
    }
    this.callbacks = new WeakMap();
  }
}

// Create singleton instances
export const imageLazyLoader = new ImageLazyLoader();
export const componentLazyLoader = new ComponentLazyLoader();
export const contentLazyLoader = new ContentLazyLoader();

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    imageLazyLoader.observeAll();
  });
} else {
  imageLazyLoader.observeAll();
}

// Re-observe when new content is added (for dynamic content)
export function observeNewImages(container = document) {
  imageLazyLoader.observeAll();
}

export { ImageLazyLoader, ComponentLazyLoader, ContentLazyLoader };
