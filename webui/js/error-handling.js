// Comprehensive error handling system for web UI components
// Provides consistent error handling, logging, recovery, and user feedback

import { emit } from "./event-bus.js";

// Error handling configuration
const errorConfig = {
  enableConsole: true,
  enableEvents: true,
  enableUserFeedback: true,
  enableRecovery: true,
  enableReporting: false, // Could be enabled for production
  maxErrorHistory: 100,
  defaultUserMessage: 'An unexpected error occurred. Please try again.',
  recoveryAttempts: 3,
  recoveryDelay: 1000
};

// Error classification system
const ErrorTypes = {
  NETWORK: 'network',
  VALIDATION: 'validation',
  AUTHENTICATION: 'authentication',
  AUTHORIZATION: 'authorization',
  NOT_FOUND: 'not_found',
  SERVER: 'server',
  CLIENT: 'client',
  TIMEOUT: 'timeout',
  RATE_LIMIT: 'rate_limit',
  UNKNOWN: 'unknown'
};

// Error severity levels
const ErrorSeverity = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

// Error history and statistics
const errorHistory = new Map(); // errorId -> error data
const errorStats = {
  total: 0,
  byType: new Map(),
  bySeverity: new Map(),
  recovered: 0,
  unresolved: 0
};

// Error ID generation
let errorIdCounter = 0;
function generateErrorId() {
  return `err_${Date.now()}_${++errorIdCounter}`;
}

// Error classification helper
function classifyError(error) {
  const message = (error.message || '').toLowerCase();
  const status = error.status || error.statusCode;
  
  // Network errors
  if (error.name === 'NetworkError' || message.includes('network') || message.includes('fetch')) {
    return ErrorTypes.NETWORK;
  }
  
  // Authentication errors
  if (status === 401 || message.includes('unauthorized') || message.includes('authentication')) {
    return ErrorTypes.AUTHENTICATION;
  }
  
  // Authorization errors
  if (status === 403 || message.includes('forbidden') || message.includes('authorization')) {
    return ErrorTypes.AUTHORIZATION;
  }
  
  // Not found errors
  if (status === 404 || message.includes('not found')) {
    return ErrorTypes.NOT_FOUND;
  }
  
  // Rate limiting
  if (status === 429 || message.includes('rate limit') || message.includes('too many requests')) {
    return ErrorTypes.RATE_LIMIT;
  }
  
  // Timeout errors
  if (error.name === 'TimeoutError' || message.includes('timeout')) {
    return ErrorTypes.TIMEOUT;
  }
  
  // Server errors
  if (status >= 500 && status < 600) {
    return ErrorTypes.SERVER;
  }
  
  // Validation errors
  if (status === 400 || message.includes('validation') || message.includes('invalid')) {
    return ErrorTypes.VALIDATION;
  }
  
  // Client errors
  if (status >= 400 && status < 500) {
    return ErrorTypes.CLIENT;
  }
  
  return ErrorTypes.UNKNOWN;
}

// Severity determination
function determineSeverity(error, type) {
  const status = error.status || error.statusCode;
  
  // Critical errors
  if (type === ErrorTypes.AUTHENTICATION || type === ErrorTypes.AUTHORIZATION) {
    return ErrorSeverity.CRITICAL;
  }
  
  if (status >= 500) {
    return ErrorSeverity.HIGH;
  }
  
  // High severity errors
  if (type === ErrorTypes.SERVER || type === ErrorTypes.NETWORK) {
    return ErrorSeverity.HIGH;
  }
  
  // Medium severity errors
  if (type === ErrorTypes.VALIDATION || type === ErrorTypes.TIMEOUT || type === ErrorTypes.RATE_LIMIT) {
    return ErrorSeverity.MEDIUM;
  }
  
  // Low severity for everything else
  return ErrorSeverity.LOW;
}

// User-friendly error messages
function getUserMessage(error, type, severity) {
  const customMessages = {
    [ErrorTypes.NETWORK]: 'Network connection error. Please check your internet connection.',
    [ErrorTypes.AUTHENTICATION]: 'Authentication required. Please log in again.',
    [ErrorTypes.AUTHORIZATION]: 'You don\'t have permission to perform this action.',
    [ErrorTypes.NOT_FOUND]: 'The requested resource was not found.',
    [ErrorTypes.SERVER]: 'Server error occurred. Our team has been notified.',
    [ErrorTypes.TIMEOUT]: 'Request timed out. Please try again.',
    [ErrorTypes.RATE_LIMIT]: 'Too many requests. Please wait and try again.',
    [ErrorTypes.VALIDATION]: 'Invalid input. Please check your data and try again.',
    [ErrorTypes.CLIENT]: 'Request error. Please check your input and try again.'
  };
  
  return customMessages[type] || errorConfig.defaultUserMessage;
}

// Error logging
function logError(errorData) {
  if (errorConfig.enableConsole) {
    const logMethod = errorData.severity === ErrorSeverity.CRITICAL ? 'error' : 
                     errorData.severity === ErrorSeverity.HIGH ? 'warn' : 'log';
    
    console[logMethod](`[${errorData.severity.toUpperCase()}] ${errorData.type}: ${errorData.message}`, {
      errorId: errorData.id,
      timestamp: errorData.timestamp,
      context: errorData.context,
      stack: errorData.stack
    });
  }
}

// Event emission for errors
function emitErrorEvent(errorData) {
  if (errorConfig.enableEvents) {
    emit('error.occurred', errorData);
    emit(`error.${errorData.type}`, errorData);
    emit(`error.${errorData.severity}`, errorData);
  }
}

// User feedback
function showUserFeedback(errorData) {
  if (!errorConfig.enableUserFeedback) return;
  
  // Use the notification system if available
  if (globalThis.notificationsSseStore) {
    try {
      globalThis.notificationsSseStore.create({
        type: 'error',
        title: errorData.userMessage,
        body: errorData.message,
        severity: errorData.severity,
        ttl_seconds: Math.max(3, Math.min(15, errorData.severity === ErrorSeverity.CRITICAL ? 15 : 8)),
        metadata: {
          errorId: errorData.id,
          errorType: errorData.type,
          context: errorData.context
        }
      });
    } catch (notificationError) {
      console.warn('Failed to show error notification:', notificationError);
      // Fallback to alert
      if (errorData.severity === ErrorSeverity.CRITICAL || errorData.severity === ErrorSeverity.HIGH) {
        alert(errorData.userMessage);
      }
    }
  }
}

// Error recovery strategies
const recoveryStrategies = {
  [ErrorTypes.NETWORK]: async (errorData) => {
    // Network recovery: retry with exponential backoff
    for (let attempt = 1; attempt <= errorConfig.recoveryAttempts; attempt++) {
      try {
        await new Promise(resolve => setTimeout(resolve, errorConfig.recoveryDelay * attempt));
        // Try to fetch a simple endpoint to check connectivity
        const response = await fetch('/health', { method: 'HEAD' });
        if (response.ok) {
          return { recovered: true, attempt };
        }
      } catch (retryError) {
        // Continue to next attempt
      }
    }
    return { recovered: false, attempt: errorConfig.recoveryAttempts };
  },
  
  [ErrorTypes.TIMEOUT]: async (errorData) => {
    // Timeout recovery: retry with longer timeout
    return { recovered: false, suggestion: 'Try again with a longer timeout' };
  },
  
  [ErrorTypes.RATE_LIMIT]: async (errorData) => {
    // Rate limit recovery: wait and retry
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
    return { recovered: true, suggestion: 'Rate limit window passed' };
  },
  
  default: async (errorData) => {
    return { recovered: false, suggestion: 'No automatic recovery available' };
  }
};

// Main error handling function
export async function handleError(error, context = {}) {
  const errorId = generateErrorId();
  const timestamp = Date.now();
  
  // Normalize error
  const normalizedError = {
    message: error.message || error.toString() || 'Unknown error',
    stack: error.stack,
    status: error.status || error.statusCode,
    name: error.name,
    code: error.code
  };
  
  // Classify error
  const type = classifyError(normalizedError);
  const severity = determineSeverity(normalizedError, type);
  const userMessage = getUserMessage(normalizedError, type, severity);
  
  // Create error data object
  const errorData = {
    id: errorId,
    timestamp,
    type,
    severity,
    message: normalizedError.message,
    stack: normalizedError.stack,
    status: normalizedError.status,
    userMessage,
    context: {
      ...context,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp
    },
    recovered: false,
    recoveryAttempted: false
  };
  
  // Update statistics
  errorStats.total++;
  errorStats.byType.set(type, (errorStats.byType.get(type) || 0) + 1);
  errorStats.bySeverity.set(severity, (errorStats.bySeverity.get(severity) || 0) + 1);
  
  // Add to history
  errorHistory.set(errorId, errorData);
  
  // Trim history if it gets too large
  if (errorHistory.size > errorConfig.maxErrorHistory) {
    const oldestId = [...errorHistory.keys()][0];
    errorHistory.delete(oldestId);
  }
  
  // Log error
  logError(errorData);
  
  // Emit error event
  emitErrorEvent(errorData);
  
  // Show user feedback
  showUserFeedback(errorData);
  
  // Attempt recovery if enabled
  if (errorConfig.enableRecovery && severity !== ErrorSeverity.CRITICAL) {
    try {
      const strategy = recoveryStrategies[type] || recoveryStrategies.default;
      const recoveryResult = await strategy(errorData);
      
      errorData.recoveryAttempted = true;
      errorData.recoveryResult = recoveryResult;
      
      if (recoveryResult.recovered) {
        errorData.recovered = true;
        errorStats.recovered++;
        emit('error.recovered', errorData);
        
        if (errorConfig.enableConsole) {
          console.log(`Error recovered: ${errorId}`, recoveryResult);
        }
      } else {
        errorStats.unresolved++;
        emit('error.unresolved', errorData);
      }
    } catch (recoveryError) {
      console.error('Error recovery failed:', recoveryError);
      errorStats.unresolved++;
      emit('error.recovery.failed', { ...errorData, recoveryError });
    }
  } else {
    errorStats.unresolved++;
  }
  
  return errorData;
}

// Error boundary for components
export function createErrorBoundary(componentName, fallbackUI = null) {
  return {
    async withErrorHandling(fn, context = {}) {
      try {
        return await fn();
      } catch (error) {
        const errorData = await handleError(error, {
          component: componentName,
          ...context
        });
        
        if (fallbackUI) {
          return fallbackUI(errorData);
        }
        
        throw error;
      }
    },
    
    wrapAsync(fn, context = {}) {
      return async (...args) => {
        try {
          return await fn(...args);
        } catch (error) {
          const errorData = await handleError(error, {
            component: componentName,
            function: fn.name,
            args: args.length,
            ...context
          });
          
          if (fallbackUI) {
            return fallbackUI(errorData);
          }
          
          throw error;
        }
      };
    },
    
    wrapSync(fn, context = {}) {
      return (...args) => {
        try {
          return fn(...args);
        } catch (error) {
          // Handle synchronously but still log properly
          const errorData = {
            id: generateErrorId(),
            timestamp: Date.now(),
            type: classifyError(error),
            severity: determineSeverity(error, classifyError(error)),
            message: error.message || error.toString(),
            stack: error.stack,
            context: {
              component: componentName,
              function: fn.name,
              args: args.length,
              ...context
            },
            recovered: false,
            recoveryAttempted: false,
            userMessage: getUserMessage(error, classifyError(error), determineSeverity(error, classifyError(error)))
          };
          
          logError(errorData);
          emitErrorEvent(errorData);
          
          if (fallbackUI) {
            return fallbackUI(errorData);
          }
          
          throw error;
        }
      };
    }
  };
}

// Utility functions
export function getErrorHistory(limit = 50) {
  return Array.from(errorHistory.values())
    .sort((a, b) => b.timestamp - a.timestamp)
    .slice(0, limit);
}

export function getErrorStats() {
  return {
    total: errorStats.total,
    recovered: errorStats.recovered,
    unresolved: errorStats.unresolved,
    byType: Object.fromEntries(errorStats.byType),
    bySeverity: Object.fromEntries(errorStats.bySeverity),
    recoveryRate: errorStats.total > 0 ? (errorStats.recovered / errorStats.total * 100).toFixed(2) + '%' : '0%'
  };
}

export function clearErrorHistory() {
  errorHistory.clear();
  errorStats.total = 0;
  errorStats.recovered = 0;
  errorStats.unresolved = 0;
  errorStats.byType.clear();
  errorStats.bySeverity.clear();
}

// Global error handlers
export function setupGlobalErrorHandlers() {
  // Unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    handleError(event.reason, {
      source: 'unhandledrejection',
      promise: event.promise
    });
    
    // Prevent default behavior only if we've handled it
    event.preventDefault();
  });
  
  // Uncaught errors
  window.addEventListener('error', (event) => {
    handleError(event.error, {
      source: 'window.error',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    });
    
    // Prevent default behavior
    event.preventDefault();
  });
}

// Export constants and utilities
export { ErrorTypes, ErrorSeverity, errorConfig };

// Auto-setup global error handlers
if (typeof window !== 'undefined') {
  setupGlobalErrorHandlers();
}

// Global exposure for debugging
if (!globalThis.errorHandler) {
  globalThis.errorHandler = {
    handleError,
    createErrorBoundary,
    getErrorHistory,
    getErrorStats,
    clearErrorHistory,
    ErrorTypes,
    ErrorSeverity,
    setupGlobalErrorHandlers
  };
}

export default {
  handleError,
  createErrorBoundary,
  getErrorHistory,
  getErrorStats,
  clearErrorHistory,
  ErrorTypes,
  ErrorSeverity,
  setupGlobalErrorHandlers
};