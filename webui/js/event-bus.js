// Enhanced event bus for UI modules with improved architecture, error handling, and performance
import { handleError } from '/js/error-handling.js';
// API: on(event, handler) => unsubscribe fn; emit(event, payload); once(event, handler)
// Namespacing: use dot notation (e.g., 'ui.status.progress'); wildcard subscription not implemented for simplicity.

// Core event handlers storage with metadata
const handlers = new Map(); // eventName -> Set<{fn: Function, metadata: Object}>
const eventHistory = new Map(); // eventName -> Array<{timestamp: number, payload: any}>
const eventStats = new Map(); // eventName -> {emits: number, errors: number}

// Event bus configuration
const config = {
  maxHistorySize: 100,
  enableDebug: false,
  enableProfiling: false,
  enableWildcard: false,
  maxHandlersPerEvent: 1000,
  emitTimeout: 5000
};

// Performance monitoring
const performanceMetrics = {
  totalEmits: 0,
  totalHandlers: 0,
  averageEmitTime: 0,
  lastEmitTime: 0
};

// Enhanced event subscription with metadata and validation
export function on(event, fn, options = {}) {
  if (typeof event !== 'string' || !event.trim()) {
    throw new Error('Event name must be a non-empty string');
  }
  
  if (typeof fn !== 'function') {
    throw new Error('Handler must be a function');
  }

  // Check handler limit per event
  const existingHandlers = handlers.get(event);
  if (existingHandlers && existingHandlers.size >= config.maxHandlersPerEvent) {
    console.warn(`Maximum handlers (${config.maxHandlersPerEvent}) reached for event: ${event}`);
    return () => {}; // Return no-op unsubscribe function
  }

  if (!handlers.has(event)) {
    handlers.set(event, new Set());
  }

  const handlerData = {
    fn,
    metadata: {
      subscribedAt: Date.now(),
      callCount: 0,
      lastCalled: null,
      ...options
    }
  };

  handlers.get(event).add(handlerData);
  
  if (config.enableDebug) {
    console.log(`Event handler subscribed: ${event}`, handlerData.metadata);
  }

  // Return unsubscribe function with cleanup
  return () => off(event, handlerData.fn);
}

// Enhanced event unsubscription with cleanup
export function off(event, fn) {
  const set = handlers.get(event);
  if (set) {
    // Find and remove the specific handler
    for (const handlerData of set) {
      if (handlerData.fn === fn) {
        set.delete(handlerData);
        
        if (config.enableDebug) {
          console.log(`Event handler unsubscribed: ${event}`, handlerData.metadata);
        }
        
        break;
      }
    }
    
    // Clean up empty event entries
    if (set.size === 0) {
      handlers.delete(event);
      eventStats.delete(event);
    }
  }
}

// Enhanced one-time event subscription with error handling
export function once(event, fn, options = {}) {
  let unsubscribe;
  
  const wrap = (payload) => {
    try {
      fn(payload);
    } catch (error) {
      console.error('Event bus once handler error:', event, error);
      throw error;
    } finally {
      // Always unsubscribe, even if handler throws
      if (unsubscribe) {
        unsubscribe();
      }
    }
  };
  
  unsubscribe = on(event, wrap, { ...options, once: true });
  return unsubscribe;
}

// Enhanced event emission with performance tracking and error handling
export function emit(event, payload) {
  const startTime = config.enableProfiling ? performance.now() : 0;
  
  try {
    if (typeof event !== 'string' || !event.trim()) {
      throw new Error('Event name must be a non-empty string');
    }

    // Update performance metrics
    performanceMetrics.totalEmits++;
    const now = Date.now();

    // Update event statistics
    if (!eventStats.has(event)) {
      eventStats.set(event, { emits: 0, errors: 0, firstEmit: now, lastEmit: now });
    }
    const stats = eventStats.get(event);
    stats.emits++;
    stats.lastEmit = now;

    // Add to event history
    if (!eventHistory.has(event)) {
      eventHistory.set(event, []);
    }
    const history = eventHistory.get(event);
    history.push({ timestamp: now, payload });
    
    // Trim history if it gets too large
    if (history.length > config.maxHistorySize) {
      history.shift();
    }

    const set = handlers.get(event);
    if (set && set.size > 0) {
      // Create shallow copy for safe iteration during emit
      const handlersToCall = [...set];
      
      // Set up timeout for long-running handlers
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error(`Event emit timeout for ${event}`)), config.emitTimeout);
      });

      const emitHandlers = async () => {
        for (const handlerData of handlersToCall) {
          try {
            // Update handler metadata
            handlerData.metadata.callCount++;
            handlerData.metadata.lastCalled = now;
            
            // Execute handler
            handlerData.fn(payload);
            
          } catch (error) {
            stats.errors++;
            
            // Use centralized error handling
            handleError(error, {
              component: 'EventBus',
              function: 'emit',
              event,
              handler: handlerData.fn.name || 'anonymous',
              payloadType: typeof payload
            }).then(errorData => {
              // Emit error event if not already handling an error
              if (event !== 'eventbus.error') {
                emit('eventbus.error', {
                  event,
                  errorId: errorData.id,
                  handler: handlerData.fn.name || 'anonymous',
                  payload
                });
              }
            });
        }
      };

      // Race between handlers and timeout
      Promise.race([emitHandlers(), timeoutPromise])
        .catch(error => {
          console.error(`Event emit failed for ${event}:`, error);
          stats.errors++;
        });
    }

    // Update performance metrics
    if (config.enableProfiling) {
      const emitTime = performance.now() - startTime;
      performanceMetrics.lastEmitTime = emitTime;
      performanceMetrics.averageEmitTime = 
        (performanceMetrics.averageEmitTime * (performanceMetrics.totalEmits - 1) + emitTime) / 
        performanceMetrics.totalEmits;
    }

    if (config.enableDebug) {
      console.log(`Event emitted: ${event}`, { payload, handlerCount: set?.size || 0 });
    }

  } catch (error) {
    handleError(error, {
      component: 'EventBus',
      function: 'emit',
      event,
      severity: 'critical'
    }).then(errorData => {
      emit('eventbus.critical', { 
        event, 
        errorId: errorData.id, 
        payload 
      });
    });
  }
}

// Enhanced health introspection with detailed metrics
export function listenerCount(event) {
  const set = handlers.get(event);
  return set ? set.size : 0;
}

export function events() {
  return [...handlers.keys()];
}

// Enhanced event history and statistics
export function getEventHistory(event, limit = 10) {
  const history = eventHistory.get(event) || [];
  return history.slice(-limit);
}

export function getEventStats(event) {
  return eventStats.get(event) || null;
}

export function getPerformanceMetrics() {
  return {
    ...performanceMetrics,
    totalEvents: handlers.size,
    totalListeners: [...handlers.values()].reduce((sum, set) => sum + set.size, 0),
    memoryUsage: {
      handlers: handlers.size,
      history: eventHistory.size,
      stats: eventStats.size
    }
  };
}

// Utility functions for advanced event management
export function clearEventHistory(event) {
  if (event) {
    eventHistory.delete(event);
  } else {
    eventHistory.clear();
  }
}

export function removeAllListeners(event) {
  if (event) {
    handlers.delete(event);
    eventStats.delete(event);
  } else {
    handlers.clear();
    eventStats.clear();
  }
}

export function waitForEvent(event, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      unsubscribe();
      reject(new Error(`Timeout waiting for event: ${event}`));
    }, timeout);

    const unsubscribe = once(event, (payload) => {
      clearTimeout(timeoutId);
      resolve(payload);
    });
  });
}

// Global convenience with enhanced safety
if (!globalThis.eventBus) {
  globalThis.eventBus = { 
    on, off, once, emit, listenerCount, events,
    getEventHistory, getEventStats, getPerformanceMetrics,
    clearEventHistory, removeAllListeners, waitForEvent
  };
}

export default { 
  on, off, once, emit, listenerCount, events,
  getEventHistory, getEventStats, getPerformanceMetrics,
  clearEventHistory, removeAllListeners, waitForEvent
};
