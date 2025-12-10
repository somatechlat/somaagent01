/**
 * State Store Factory
 * 
 * Creates reactive stores that work with Alpine.js.
 * Provides a clean abstraction over Alpine.store() with persistence support.
 * 
 * @module core/state/store
 */

/** Registry of all created stores */
const storeRegistry = new Map();

/** Store change listeners */
const changeListeners = new Map();

/**
 * Create a reactive store
 * 
 * @template T
 * @param {string} name - Store name (must be unique)
 * @param {T} initialState - Initial state object
 * @param {Object} [options] - Store options
 * @param {boolean} [options.persist] - Persist to localStorage
 * @param {string[]} [options.persistKeys] - Specific keys to persist
 * @returns {T} Reactive store proxy
 */
export function createStore(name, initialState, options = {}) {
  if (storeRegistry.has(name)) {
    console.warn(`Store "${name}" already exists, returning existing instance`);
    return storeRegistry.get(name);
  }
  
  // Load persisted state if enabled
  let state = { ...initialState };
  if (options.persist) {
    try {
      const persisted = localStorage.getItem(`store:${name}`);
      if (persisted) {
        const parsed = JSON.parse(persisted);
        if (options.persistKeys) {
          // Only restore specific keys
          for (const key of options.persistKeys) {
            if (key in parsed) {
              state[key] = parsed[key];
            }
          }
        } else {
          state = { ...state, ...parsed };
        }
      }
    } catch (e) {
      console.warn(`Failed to load persisted state for store "${name}":`, e);
    }
  }
  
  // Create proxy for reactivity
  const proxy = new Proxy(state, {
    set(target, prop, value) {
      const oldValue = target[prop];
      
      // Update Alpine store if available
      const alpineStore = globalThis.Alpine?.store(name);
      if (alpineStore) {
        alpineStore[prop] = value;
      } else {
        target[prop] = value;
      }
      
      // Notify listeners
      notifyListeners(name, prop, value, oldValue);
      
      // Persist if enabled
      if (options.persist) {
        persistStore(name, target, options.persistKeys);
      }
      
      return true;
    },
    
    get(target, prop) {
      // Get from Alpine store if available
      const alpineStore = globalThis.Alpine?.store(name);
      if (alpineStore) {
        return alpineStore[prop];
      }
      return target[prop];
    }
  });
  
  // Register with Alpine when ready
  if (globalThis.Alpine) {
    globalThis.Alpine.store(name, state);
  } else {
    document.addEventListener('alpine:init', () => {
      Alpine.store(name, state);
    });
  }
  
  // Store in registry
  storeRegistry.set(name, proxy);
  
  return proxy;
}

/**
 * Get an existing store by name
 * @template T
 * @param {string} name - Store name
 * @returns {T|undefined} Store instance or undefined
 */
export function getStore(name) {
  return storeRegistry.get(name);
}

/**
 * Subscribe to store changes
 * @param {string} storeName - Store name
 * @param {string} [key] - Specific key to watch (optional)
 * @param {Function} callback - Callback(newValue, oldValue, key)
 * @returns {Function} Unsubscribe function
 */
export function subscribe(storeName, key, callback) {
  // Handle overloaded signature
  if (typeof key === 'function') {
    callback = key;
    key = null;
  }
  
  if (!changeListeners.has(storeName)) {
    changeListeners.set(storeName, new Set());
  }
  
  const listener = { key, callback };
  changeListeners.get(storeName).add(listener);
  
  return () => {
    changeListeners.get(storeName)?.delete(listener);
  };
}

/**
 * Notify listeners of store changes
 * @param {string} storeName - Store name
 * @param {string} key - Changed key
 * @param {any} newValue - New value
 * @param {any} oldValue - Old value
 */
function notifyListeners(storeName, key, newValue, oldValue) {
  const listeners = changeListeners.get(storeName);
  if (!listeners) return;
  
  for (const listener of listeners) {
    if (!listener.key || listener.key === key) {
      try {
        listener.callback(newValue, oldValue, key);
      } catch (e) {
        console.error(`Store listener error for "${storeName}.${key}":`, e);
      }
    }
  }
}

/**
 * Persist store to localStorage
 * @param {string} name - Store name
 * @param {Object} state - Current state
 * @param {string[]} [keys] - Specific keys to persist
 */
function persistStore(name, state, keys) {
  try {
    const toPersist = keys 
      ? Object.fromEntries(keys.filter(k => k in state).map(k => [k, state[k]]))
      : state;
    localStorage.setItem(`store:${name}`, JSON.stringify(toPersist));
  } catch (e) {
    console.warn(`Failed to persist store "${name}":`, e);
  }
}

/**
 * Reset a store to its initial state
 * @param {string} name - Store name
 * @param {Object} initialState - Initial state to reset to
 */
export function resetStore(name, initialState) {
  const store = storeRegistry.get(name);
  if (!store) return;
  
  // Clear persisted state
  try {
    localStorage.removeItem(`store:${name}`);
  } catch (e) {
    // Ignore
  }
  
  // Reset all properties
  for (const key of Object.keys(initialState)) {
    store[key] = initialState[key];
  }
}

/**
 * Get all registered store names
 * @returns {string[]} Array of store names
 */
export function getStoreNames() {
  return [...storeRegistry.keys()];
}

export default { createStore, getStore, subscribe, resetStore, getStoreNames };
