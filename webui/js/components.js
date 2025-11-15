// Enhanced component import system with improved caching, error handling, and performance
import { emit, on } from "/js/event-bus.js";
import { handleError, createErrorBoundary } from "/js/error-handling.js";

// Create error boundary for component system
const componentErrorBoundary = createErrorBoundary('ComponentSystem', (errorData) => {
  return {
    type: 'error',
    html: `<div class="component-error-boundary">
      <h3>Component Error</h3>
      <p>${errorData.userMessage}</p>
      <button onclick="window.location.reload()">Reload Page</button>
    </div>`
  };
});

// Advanced cache with metadata and versioning
const componentCache = new Map();
const cacheStats = {
  hits: 0,
  misses: 0,
  errors: 0,
  lastCleanup: Date.now()
};

// Enhanced lock system with timeout and metadata
const importLocks = new Map();
const lockTimeouts = new Map();

// Component loading configuration
const config = {
  cacheMaxAge: 5 * 60 * 1000, // 5 minutes
  cacheMaxSize: 100,
  lockTimeout: 30000, // 30 seconds
  retryAttempts: 2,
  retryDelay: 1000,
  enableDebug: false,
  enablePreloading: true
};

// Enhanced cache management utilities
function cleanupCache() {
  const now = Date.now();
  if (now - cacheStats.lastCleanup < config.cacheMaxAge) return;

  for (const [url, data] of componentCache.entries()) {
    if (now - data.timestamp > config.cacheMaxAge) {
      componentCache.delete(url);
    }
  }
  
  if (componentCache.size > config.cacheMaxSize) {
    const entries = Array.from(componentCache.entries())
      .sort((a, b) => a[1].timestamp - b[1].timestamp);
    const toRemove = entries.slice(0, entries.length - config.cacheMaxSize);
    toRemove.forEach(([url]) => componentCache.delete(url));
  }
  
  cacheStats.lastCleanup = now;
}

function getFromCache(url) {
  const cached = componentCache.get(url);
  if (cached && Date.now() - cached.timestamp < config.cacheMaxAge) {
    cacheStats.hits++;
    if (config.enableDebug) {
      console.log(`Cache hit for ${url}`);
    }
    return cached.data;
  }
  cacheStats.misses++;
  return null;
}

function setInCache(url, data) {
  componentCache.set(url, {
    data,
    timestamp: Date.now(),
    size: new Blob([data]).size
  });
  cleanupCache();
  
  if (config.enableDebug) {
    console.log(`Cached ${url} (${componentCache.size} items)`);
  }
}

// Enhanced lock management with timeout
function acquireLock(lockKey) {
  if (importLocks.has(lockKey)) {
    if (config.enableDebug) {
      console.log(`Component already loading for ${lockKey}`);
    }
    return false;
  }
  
  importLocks.set(lockKey, Date.now());
  
  // Set up timeout for lock release
  const timeoutId = setTimeout(() => {
    if (importLocks.has(lockKey)) {
      console.warn(`Lock timeout for ${lockKey}`);
      releaseLock(lockKey);
    }
  }, config.lockTimeout);
  
  lockTimeouts.set(lockKey, timeoutId);
  return true;
}

function releaseLock(lockKey) {
  importLocks.delete(lockKey);
  const timeoutId = lockTimeouts.get(lockKey);
  if (timeoutId) {
    clearTimeout(timeoutId);
    lockTimeouts.delete(lockKey);
  }
}

export const importComponent = componentErrorBoundary.wrapAsync(async function(path, targetElement) {
  // Create a unique key for this import based on the target element
  const lockKey = `${targetElement.id || targetElement.getAttribute('data-component-id') || 'anonymous'}-${path}`;
  
  // If this component is already being loaded, return early
  if (!acquireLock(lockKey)) {
    if (config.enableDebug) {
      console.log(`Component ${path} is already being loaded for target`, targetElement);
    }
    return;
  }
  
  const startTime = Date.now();
  let attempt = 0;
  
  try {
    if (!targetElement) {
      throw new Error("Target element is required");
    }

    // Show enhanced loading indicator with path info
    targetElement.innerHTML = `
      <div class="loading">
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading ${path}...</div>
      </div>
    `;

    // Full component URL with error handling
    const componentUrl = path.startsWith('/') ? path.slice(1) : `components/${path}`;
    
    // Get HTML from cache or fetch with retry logic
    let html = getFromCache(componentUrl);
    
    if (!html) {
      let lastError;
      
      for (attempt = 0; attempt <= config.retryAttempts; attempt++) {
        try {
          const response = await fetch(componentUrl, {
            headers: {
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            },
            cache: 'no-store'
          });
          
          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
              `HTTP ${response.status} loading component ${path}: ${response.statusText} - ${errorText}`
            );
          }
          
          html = await response.text();
          
          // Validate HTML content
          if (!html || html.trim().length === 0) {
            throw new Error(`Empty content received for component ${path}`);
          }
          
          // Store in cache with metadata
          setInCache(componentUrl, html);
          break;
          
        } catch (error) {
          lastError = error;
          cacheStats.errors++;
          
          if (attempt < config.retryAttempts) {
            await new Promise(resolve => setTimeout(resolve, config.retryDelay * (attempt + 1)));
          }
        }
      }
      
      if (!html) {
        throw lastError || new Error(`Failed to load component ${path} after ${config.retryAttempts + 1} attempts`);
      }
    }
    
    // Parse HTML with error handling
    let doc;
    try {
      const parser = new DOMParser();
      doc = parser.parseFromString(html, "text/html");
      
      // Check for parsing errors
      const parserError = doc.querySelector('parsererror');
      if (parserError) {
        throw new Error(`HTML parsing error in component ${path}: ${parserError.textContent}`);
      }
    } catch (parseError) {
      throw new Error(`Failed to parse HTML for component ${path}: ${parseError.message}`);
    }

    // Process all nodes with enhanced error handling and tracking
    const allNodes = [
      ...doc.querySelectorAll("style"),
      ...doc.querySelectorAll("script"),
      ...doc.body.childNodes,
    ].filter(node => node && node.nodeType === 1); // Only element nodes

    const loadPromises = [];
    const loadedResources = new Set();
    let blobCounter = 0;

    for (const node of allNodes) {
      try {
        if (node.nodeName === "SCRIPT") {
          const isModule = node.type === "module" || node.getAttribute("type") === "module";

          if (isModule) {
            if (node.src) {
              // For <script type="module" src="..." use dynamic import
              const resolvedUrl = new URL(node.src, globalThis.location.origin).toString();

              // Check if module is already being loaded
              if (!loadedResources.has(resolvedUrl)) {
                loadedResources.add(resolvedUrl);
                
                const modulePromise = import(resolvedUrl)
                  .catch((err) => {
                    console.error(`Failed to load module ${resolvedUrl}:`, err);
                    emit('component.error', { type: 'module', url: resolvedUrl, error: err.message });
                    throw err;
                  });
                
                loadPromises.push(modulePromise);
              }
            } else {
              // Handle inline module scripts
              const virtualUrl = `${componentUrl.replace(/\//g, '_')}.${++blobCounter}.js`;

              if (!loadedResources.has(virtualUrl)) {
                loadedResources.add(virtualUrl);
                
                // Transform relative import paths to absolute URLs with enhanced regex
                let content = node.textContent.replace(
                  /import\s+([^'"]+)\s+from\s+["']([^"']+)["']/g,
                  (match, bindings, importPath) => {
                    // Convert relative OR root-based (e.g. /src/...) to absolute URLs
                    if (!/^https?:\/\//.test(importPath)) {
                      const absoluteUrl = new URL(importPath, globalThis.location.origin).href;
                      return `import ${bindings} from "${absoluteUrl}"`;
                    }
                    return match;
                  }
                );

                // Add sourceURL for debugging and error tracking
                content += `\n//# sourceURL=${virtualUrl}`;

                // Create a Blob from the rewritten content
                const blob = new Blob([content], { type: "text/javascript" });
                const blobUrl = URL.createObjectURL(blob);

                const modulePromise = import(blobUrl)
                  .catch((err) => {
                    console.error(`Failed to load inline module ${virtualUrl}:`, err);
                    emit('component.error', { type: 'inline-module', url: virtualUrl, error: err.message });
                    throw err;
                  })
                  .finally(() => {
                    // Clean up blob URL to prevent memory leaks
                    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
                  });

                loadPromises.push(modulePromise);
              }
            }
          } else {
            // Non-module script with enhanced handling
            const script = document.createElement("script");
            
            // Copy all attributes with filtering
            Array.from(node.attributes || []).forEach((attr) => {
              if (attr.name !== 'type' || attr.value !== 'module') {
                script.setAttribute(attr.name, attr.value);
              }
            });
            
            script.textContent = node.textContent;

            if (script.src) {
              const promise = new Promise((resolve, reject) => {
                script.onload = () => {
                  emit('component.loaded', { type: 'script', src: script.src });
                  resolve();
                };
                script.onerror = () => {
                  const error = new Error(`Failed to load script: ${script.src}`);
                  emit('component.error', { type: 'script', src: script.src, error: error.message });
                  reject(error);
                };
              });
              loadPromises.push(promise);
            }

            targetElement.appendChild(script);
          }
        } else if (node.nodeName === "STYLE" || (node.nodeName === "LINK" && node.rel === "stylesheet")) {
          // Enhanced style/link handling
          const clone = node.cloneNode(true);

          if (clone.tagName === "LINK" && clone.rel === "stylesheet") {
            const promise = new Promise((resolve, reject) => {
              clone.onload = () => {
                emit('component.loaded', { type: 'stylesheet', href: clone.href });
                resolve();
              };
              clone.onerror = () => {
                const error = new Error(`Failed to load stylesheet: ${clone.href}`);
                emit('component.error', { type: 'stylesheet', href: clone.href, error: error.message });
                reject(error);
              };
            });
            loadPromises.push(promise);
          }

          targetElement.appendChild(clone);
        } else {
          // Enhanced DOM node cloning with error handling
          try {
            const clone = node.cloneNode(true);
            targetElement.appendChild(clone);
          } catch (cloneError) {
            console.warn(`Failed to clone node ${node.nodeName}:`, cloneError);
            emit('component.warning', { type: 'clone-error', nodeName: node.nodeName, error: cloneError.message });
          }
        }
      } catch (nodeError) {
        console.error(`Error processing node ${node.nodeName}:`, nodeError);
        emit('component.error', { type: 'node-processing', nodeName: node.nodeName, error: nodeError.message });
      }
    }

    // Wait for all tracked external scripts/styles to finish loading with enhanced error handling
    try {
      await Promise.all(loadPromises);
    } catch (loadError) {
      console.error(`Error loading resources for component ${path}:`, loadError);
      throw new Error(`Component resource loading failed: ${loadError.message}`);
    }

    // Remove loading indicator with enhanced cleanup
    const loadingEl = targetElement.querySelector(':scope > .loading');
    if (loadingEl) {
      loadingEl.remove();
    }

    // Load any nested components with error handling
    try {
      await loadComponents([targetElement]);
    } catch (nestedError) {
      console.warn(`Error loading nested components for ${path}:`, nestedError);
      emit('component.warning', { type: 'nested-components', path, error: nestedError.message });
    }

    // Emit component loaded event
    const loadTime = Date.now() - startTime;
    emit('component.loaded', { 
      type: 'component', 
      path, 
      loadTime, 
      attempt: attempt + 1,
      cacheHit: getFromCache(componentUrl) !== null
    });

    if (config.enableDebug) {
      console.log(`Component ${path} loaded in ${loadTime}ms`);
    }

    // Return parsed document
    return doc;
  } catch (error) {
    // Enhanced error handling with the new system
    await handleError(error, {
      component: 'ComponentSystem',
      function: 'importComponent',
      path,
      targetElementId: targetElement.id || 'unknown',
      lockKey
    });
    
    // Show error in UI
    targetElement.innerHTML = `
      <div class="component-error">
        <div class="error-title">Component Loading Error</div>
        <div class="error-path">${path}</div>
        <div class="error-message">${error.message}</div>
        <div class="error-actions">
          <button class="error-retry" onclick="importComponent('${path}', this.parentElement.parentElement.parentElement)">Retry</button>
          <button class="error-refresh" onclick="window.location.reload()">Reload Page</button>
        </div>
      </div>
    `;
    
    throw error;
  } finally {
    // Release the lock when done, regardless of success or failure
    releaseLock(lockKey);
  }
});

// Load all x-component tags starting from root elements
export async function loadComponents(roots = [document.documentElement]) {
  try {
    // Convert single root to array if needed
    const rootElements = Array.isArray(roots) ? roots : [roots];

    // Find all top-level components and load them in parallel
    const components = rootElements.flatMap((root) =>
      Array.from(root.querySelectorAll("x-component"))
    );

    if (components.length === 0) return;

    await Promise.all(
      components.map(async (component) => {   
        const path = component.getAttribute("path");
        if (!path) {
          console.error("x-component missing path attribute:", component);
          return;
        }
        await importComponent(path, component);
      })
    );
  } catch (error) {
    console.error("Error loading components:", error);
  }
}

// Function to traverse parents and collect x-component attributes
export function getParentAttributes(el) {
  let element = el;
  let attrs = {};

  while (element) {
    if (element.tagName.toLowerCase() === 'x-component') {
      // Get all attributes
      for (let attr of element.attributes) {
        try {
          // Try to parse as JSON first
          attrs[attr.name] = JSON.parse(attr.value);
        } catch(_e) {
          // If not JSON, use raw value
          attrs[attr.name] = attr.value;
        }
      }
    }
    element = element.parentElement;
  }
  return attrs;
}
// expose as global for x-components in Alpine
globalThis.xAttrs = getParentAttributes;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => loadComponents());
} else {
  loadComponents();
}

// Watch for DOM changes to dynamically load x-components
const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType === 1) {
        // ELEMENT_NODE
        // Check if this node or its descendants contain x-component(s)
        if (node.matches?.("x-component")) {
          importComponent(node.getAttribute("path"), node);
        } else if (node.querySelectorAll) {
          loadComponents([node]);
        }
      }
    }
  }
});
observer.observe(document.body, { childList: true, subtree: true });
