// Enhanced event bus for UI modules with improved architecture, error handling, and performance
import { handleError } from "i18n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_error_handling_js')')";
// API: on(event, handler) => i18n.t('i18n.t('ui_i18n_t_ui_unsubscribe_fn_emit_event_payload_once_event_handler_namespacing_use_dot_notation_e_g_ui_status_progress_wildcard_subscription_not_implemented_for_simplicity_core_event_handlers_storage_with_metadata_const_handlers_new_map_eventname_set')')<{fi18n.t('ui_i18n_t_ui_i18n_t_ui_unsubscribe_fn_emit_event_payload_once_event_handler_namespacing_use_dot_notation_e_g_ui_status_progress_wildcard_subscription_not_implemented_for_simplicity_core_event_handlers_storage_with_metadata_const_handlers_new_map_eventname_set')ig = {
  maxHistorySize: 100,
  enai18n.t('ui_i18n_t_ui_i18n_t_ui_const_eventhistory_new_map_eventname_array')e,
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
  if (typeof event !== 'i18n.t('ui_string')' || !event.trim()) {
    throw new Error('i18n.t('ui_event_name_must_be_a_non_empty_string')');
  }
  
  if (typeof fn !== 'i18n.t('ui_function')') {
    throw new Error('i18n.t('ui_handler_must_be_a_function')');
  }

  // Check handler limit per event
  const existingHandlers = handlers.get(event);
  if (existingHandlers && existingHandlers.size >= config.maxHandlersPerEvent) {
    console.warn(`Maximum handlers (${config.maxHandlersPerEvent}) reached for event: ${event}`);
    return () => {}; // Return no-op unsubscribe function
  }

  if (!handlers.has(eventi18n.t('ui_maximum_handlers_config_maxhandlersperevent_reached_for_event_event'),
    metadata: {
      subscribedAt: Date.now(),
      callCount: 0,
      lastCalled: null,
      ...options
    }
  };

  handlers.get(event).add(handlerData);
  
  if (config.enableDebug) {
    // Debug: Event handler subscribed:, event, handlerData.metadata
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
          // Debug: Event handler unsubscribed:, event, handlerData.metadata
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
      console.error('i18n.t('ui_event_bus_once_handler_error')', event, error);
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
    if (typeof event !== 'i18n.t('ui_string')' || !event.trim()) {
      throw new Error('i18n.t('ui_event_name_must_be_a_non_empty_string')');
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
        for (const hai18n.t('ui_event_emit_timeout_for_event')          try {
            // Update handler metadata
            handlerData.metadata.callCount++;
            handlerData.metadata.lastCalled = now;
            
            // Execute handler
            handlerData.fn(payload);
            
          } catch (error) {
            stats.errors++;
            
            // Use centralized error handling
            handleError(error, {
              component: 'i18n.t('ui_eventbus')',
              function: 'i18n.t('ui_emit')',
              event,
              handler: handlerData.fn.name || 'i18n.t('ui_anonymous')',
              payloadType: typeof payload
            }).then(errorData => {
              // Emit error event if not already handling an error
              if (event !== 'i18n.t('ui_eventbus_error')') {
                emit('i18n.t('ui_eventbus_error')', {
                  event,
                  errorId: errorData.id,
                  handler: handlerData.fn.name || 'i18n.t('ui_anonymous')',
                  payload
                });
              }
            });
          }
        }
      };

      // Race between handlers and timeout
      Promise.race([emitHandlers(), timeoutPromise])
        .catch(error => {
          console.error(`Event emit failed for ${event}:`, error);
          i18n.t('ui_event_emit_failed_for_event') }

    // Update performance metrics
    if (config.enableProfiling) {
      const emitTime = performance.now() - startTime;
      performanceMetrics.lastEmitTime = emitTime;
      performanceMetrics.averageEmitTime = 
        (performanceMetrics.averageEmitTime * (performanceMetrics.totalEmits - 1) + emitTime) / 
        performanceMetrics.totalEmits;
    }

    if (config.enableDebug) {
      // Debug: Event emitted:, event, payload, handlerCount
    }

  } catch (error) {
    handleError(error, {
      component: 'i18n.t('ui_eventbus')',
      function: 'i18n.t('ui_emit')',
      event,
      severity: 'i18n.t('ui_critical')'
    }).then(errorData => {
      emit('i18n.t('ui_eventbus_critical')', { 
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
      reject(new Error(`i18n.t('ui_timeout_waiting_for_event_event')`));
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
