/**
 * Error Handling UI Component
 * User-friendly errors, offline banner, validation messages
 * Requirements: 28.1, 28.2, 28.3, 28.4, 28.5
 */

/**
 * Error Handler Class
 */
export class ErrorHandler {
  constructor() {
    this.errors = [];
    this.maxErrors = 10;
    this.listeners = new Set();
    
    this.setupGlobalHandlers();
  }

  /**
   * Setup global error handlers
   */
  setupGlobalHandlers() {
    // Unhandled errors
    window.addEventListener('error', (event) => {
      this.handleError({
        type: 'runtime',
        message: event.message,
        source: event.filename,
        line: event.lineno,
        column: event.colno,
        error: event.error
      });
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError({
        type: 'promise',
        message: event.reason?.message || String(event.reason),
        error: event.reason
      });
    });

    // Network errors
    window.addEventListener('offline', () => {
      this.handleError({
        type: 'network',
        message: 'You are offline. Some features may be unavailable.',
        recoverable: true
      });
    });
  }

  /**
   * Handle an error
   * @param {Object} error - Error details
   */
  handleError(error) {
    const errorEntry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...error,
      userFriendlyMessage: this.getUserFriendlyMessage(error)
    };

    this.errors.unshift(errorEntry);
    
    // Keep only recent errors
    if (this.errors.length > this.maxErrors) {
      this.errors.pop();
    }

    // Notify listeners
    this.notifyListeners(errorEntry);

    // Log to console in development
    if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
      console.error('[ErrorHandler]', errorEntry);
    }

    return errorEntry;
  }

  /**
   * Get user-friendly error message
   * @param {Object} error - Error details
   * @returns {string} User-friendly message
   */
  getUserFriendlyMessage(error) {
    // Network errors
    if (error.type === 'network' || error.message?.includes('fetch')) {
      return 'Unable to connect to the server. Please check your internet connection.';
    }

    // API errors
    if (error.status) {
      switch (error.status) {
        case 400:
          return 'Invalid request. Please check your input and try again.';
        case 401:
          return 'You need to log in to continue.';
        case 403:
          return 'You don\'t have permission to perform this action.';
        case 404:
          return 'The requested resource was not found.';
        case 429:
          return 'Too many requests. Please wait a moment and try again.';
        case 500:
        case 502:
        case 503:
          return 'The server is experiencing issues. Please try again later.';
        default:
          return error.message || 'An unexpected error occurred.';
      }
    }

    // Validation errors
    if (error.type === 'validation') {
      return error.message || 'Please check your input and try again.';
    }

    // Default message
    return error.message || 'Something went wrong. Please try again.';
  }

  /**
   * Add error listener
   * @param {Function} callback - Callback function
   */
  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Notify all listeners
   * @param {Object} error - Error entry
   */
  notifyListeners(error) {
    this.listeners.forEach(callback => {
      try {
        callback(error);
      } catch (e) {
        console.error('Error in error listener:', e);
      }
    });
  }

  /**
   * Clear all errors
   */
  clearErrors() {
    this.errors = [];
  }

  /**
   * Get recent errors
   * @returns {Array} Recent errors
   */
  getErrors() {
    return [...this.errors];
  }
}

// Singleton instance
export const errorHandler = new ErrorHandler();

/**
 * Error Boundary Alpine Component
 */
export function createErrorBoundary() {
  return {
    hasError: false,
    error: null,
    
    init() {
      // Listen for errors
      errorHandler.addListener((error) => {
        if (!error.recoverable) {
          this.hasError = true;
          this.error = error;
        }
      });
    },
    
    retry() {
      this.hasError = false;
      this.error = null;
      window.location.reload();
    },
    
    dismiss() {
      this.hasError = false;
      this.error = null;
    }
  };
}

/**
 * Error Toast Alpine Component
 */
export function createErrorToast() {
  return {
    errors: [],
    
    init() {
      errorHandler.addListener((error) => {
        this.showError(error);
      });
    },
    
    showError(error) {
      const toast = {
        id: error.id,
        message: error.userFriendlyMessage,
        type: error.recoverable ? 'warning' : 'error',
        visible: true
      };
      
      this.errors.push(toast);
      
      // Auto-dismiss recoverable errors
      if (error.recoverable) {
        setTimeout(() => {
          this.dismissError(toast.id);
        }, 5000);
      }
    },
    
    dismissError(id) {
      const index = this.errors.findIndex(e => e.id === id);
      if (index !== -1) {
        this.errors.splice(index, 1);
      }
    },
    
    dismissAll() {
      this.errors = [];
    }
  };
}

/**
 * Offline Banner Alpine Component
 */
export function createOfflineBanner() {
  return {
    isOffline: !navigator.onLine,
    dismissed: false,
    
    init() {
      window.addEventListener('online', () => {
        this.isOffline = false;
        this.dismissed = false;
      });
      
      window.addEventListener('offline', () => {
        this.isOffline = true;
        this.dismissed = false;
      });
    },
    
    dismiss() {
      this.dismissed = true;
    },
    
    get visible() {
      return this.isOffline && !this.dismissed;
    }
  };
}

/**
 * Form Validation Alpine Component
 */
export function createFormValidation() {
  return {
    errors: {},
    touched: {},
    
    validate(field, value, rules) {
      const fieldErrors = [];
      
      for (const rule of rules) {
        const error = this.checkRule(rule, value, field);
        if (error) {
          fieldErrors.push(error);
        }
      }
      
      this.errors[field] = fieldErrors;
      return fieldErrors.length === 0;
    },
    
    checkRule(rule, value, field) {
      switch (rule.type) {
        case 'required':
          if (!value || (typeof value === 'string' && !value.trim())) {
            return rule.message || `${field} is required`;
          }
          break;
        case 'email':
          if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            return rule.message || 'Please enter a valid email address';
          }
          break;
        case 'minLength':
          if (value && value.length < rule.value) {
            return rule.message || `Must be at least ${rule.value} characters`;
          }
          break;
        case 'maxLength':
          if (value && value.length > rule.value) {
            return rule.message || `Must be no more than ${rule.value} characters`;
          }
          break;
        case 'pattern':
          if (value && !rule.value.test(value)) {
            return rule.message || 'Invalid format';
          }
          break;
        case 'custom':
          if (rule.validator && !rule.validator(value)) {
            return rule.message || 'Invalid value';
          }
          break;
      }
      return null;
    },
    
    touch(field) {
      this.touched[field] = true;
    },
    
    hasError(field) {
      return this.touched[field] && this.errors[field]?.length > 0;
    },
    
    getError(field) {
      return this.errors[field]?.[0] || null;
    },
    
    reset() {
      this.errors = {};
      this.touched = {};
    },
    
    isValid() {
      return Object.values(this.errors).every(e => e.length === 0);
    }
  };
}

/**
 * Register Alpine components
 */
export function registerErrorComponents() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('errorBoundary', createErrorBoundary);
    Alpine.data('errorToast', createErrorToast);
    Alpine.data('offlineBanner', createOfflineBanner);
    Alpine.data('formValidation', createFormValidation);
  }
}

export default errorHandler;
