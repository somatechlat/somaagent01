/**
 * Performance Module Index
 * Exports all performance optimization utilities
 * Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7
 */

export {
  imageLazyLoader,
  componentLazyLoader,
  contentLazyLoader,
  observeNewImages,
  ImageLazyLoader,
  ComponentLazyLoader,
  ContentLazyLoader
} from './lazy-loader.js';

export {
  VirtualScroller,
  createVirtualScroller,
  registerVirtualScrollDirective
} from './virtual-scroll.js';

export {
  dynamicImport,
  preloadResources,
  prefetchResources,
  loadCSSAsync,
  loadScriptAsync,
  featureModules,
  vendorModules,
  addResourceHints,
  estimateBundleSize
} from './bundle-optimizer.js';

/**
 * Performance monitoring utilities
 */
export const performanceMonitor = {
  /**
   * Measure First Contentful Paint
   * Target: < 1.5s (Requirement 16.1)
   */
  measureFCP() {
    return new Promise((resolve) => {
      if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntriesByName('first-contentful-paint');
          if (entries.length > 0) {
            resolve(entries[0].startTime);
            observer.disconnect();
          }
        });
        observer.observe({ type: 'paint', buffered: true });
      } else {
        resolve(null);
      }
    });
  },

  /**
   * Measure Time to Interactive
   * Target: < 3s (Requirement 16.2)
   */
  measureTTI() {
    return new Promise((resolve) => {
      if ('PerformanceObserver' in window) {
        // Approximate TTI using Long Task API
        let lastLongTask = 0;
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            lastLongTask = entry.startTime + entry.duration;
          }
        });
        
        try {
          observer.observe({ type: 'longtask', buffered: true });
          
          // Check after a delay
          setTimeout(() => {
            observer.disconnect();
            resolve(lastLongTask || performance.now());
          }, 5000);
        } catch (e) {
          resolve(performance.now());
        }
      } else {
        resolve(performance.now());
      }
    });
  },

  /**
   * Measure interaction response time
   * Target: < 100ms (Requirement 16.3)
   */
  measureInteraction(callback) {
    const start = performance.now();
    callback();
    return performance.now() - start;
  },

  /**
   * Check if animations are running at 60fps
   * Target: 60fps without jank (Requirement 16.7)
   */
  measureFrameRate(duration = 1000) {
    return new Promise((resolve) => {
      let frames = 0;
      let lastTime = performance.now();
      const frameRates = [];

      function countFrame(currentTime) {
        frames++;
        const delta = currentTime - lastTime;
        
        if (delta >= 100) {
          frameRates.push(Math.round((frames * 1000) / delta));
          frames = 0;
          lastTime = currentTime;
        }

        if (currentTime - lastTime < duration) {
          requestAnimationFrame(countFrame);
        } else {
          const avgFps = frameRates.length > 0
            ? Math.round(frameRates.reduce((a, b) => a + b, 0) / frameRates.length)
            : 0;
          resolve({
            averageFps: avgFps,
            samples: frameRates,
            isSmooth: avgFps >= 55
          });
        }
      }

      requestAnimationFrame(countFrame);
    });
  },

  /**
   * Log performance metrics to console
   */
  async logMetrics() {
    console.group('Performance Metrics');
    
    const fcp = await this.measureFCP();
    console.log(`FCP: ${fcp ? fcp.toFixed(2) + 'ms' : 'N/A'} (target: <1500ms)`);
    
    const tti = await this.measureTTI();
    console.log(`TTI: ${tti.toFixed(2)}ms (target: <3000ms)`);
    
    const fps = await this.measureFrameRate();
    console.log(`FPS: ${fps.averageFps} (target: 60fps, smooth: ${fps.isSmooth})`);
    
    // Memory usage if available
    if (performance.memory) {
      const mb = (bytes) => (bytes / 1024 / 1024).toFixed(2) + 'MB';
      console.log(`Memory: ${mb(performance.memory.usedJSHeapSize)} / ${mb(performance.memory.totalJSHeapSize)}`);
    }
    
    console.groupEnd();
    
    return { fcp, tti, fps };
  }
};

/**
 * Debounce function for performance optimization
 */
export function debounce(fn, delay = 100) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Throttle function for performance optimization
 */
export function throttle(fn, limit = 100) {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Request Idle Callback polyfill and wrapper
 */
export function requestIdleCallback(callback, options = {}) {
  if ('requestIdleCallback' in window) {
    return window.requestIdleCallback(callback, options);
  }
  // Fallback using setTimeout
  return setTimeout(() => {
    callback({
      didTimeout: false,
      timeRemaining: () => Math.max(0, 50 - (Date.now() - Date.now()))
    });
  }, options.timeout || 1);
}

/**
 * Cancel idle callback
 */
export function cancelIdleCallback(id) {
  if ('cancelIdleCallback' in window) {
    window.cancelIdleCallback(id);
  } else {
    clearTimeout(id);
  }
}

/**
 * Initialize all performance optimizations
 */
export function initPerformance() {
  // Register Alpine directive if available
  if (typeof Alpine !== 'undefined') {
    registerVirtualScrollDirective();
  }
  
  // Log metrics in development
  if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    window.addEventListener('load', () => {
      setTimeout(() => performanceMonitor.logMetrics(), 2000);
    });
  }
}
