// Comprehensive error handling system for web UI components
// Provides consistent error handling, logging, recovery, and user feedback

import { emit } from "i18n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_event_bus_js')')";

// Error handling configuration
const errorConfig = {
  enableConsole: true,
  enableEvents: true,
  enableUserFeedback: true,
  enableRecovery: true,
  enableReporting: false, // Could be enabled for production
  maxErrorHistory: 100,
  defaultUserMessage: 'i18n.t('ui_an_unexpected_error_occurred_please_try_again')',
  recoveryAttempts: 3,
  recoveryDelay: 1000
};

// Error classification system
const ErrorTypes = {
  NETWORK: 'i18n.t('ui_network')',
  VALIDATION: 'i18n.t('ui_validation')',
  AUTHENTICATION: 'i18n.t('ui_authentication')',
  AUTHORIZATION: 'i18n.t('ui_authorization')',
  NOT_FOUND: 'i18n.t('ui_not_found')',
  SERVER: 'i18n.t('ui_server')',
  CLIENT: 'i18n.t('ui_client')',
  TIMEOUT: 'i18n.t('ui_timeout')',
  RATE_LIMIT: 'i18n.t('ui_rate_limit')',
  UNKNOWN: 'i18n.t('ui_unknown')'
};

// Error severity levels
const ErrorSeverity = {
  LOW: 'i18n.t('ui_low')',
  MEDIUM: 'i18n.t('ui_medium')',
  HIGH: 'i18n.t('ui_high')',
  CRITICAL: 'i18n.t('ui_critical')'
};

// Error history and statistics
const errorHistory = new Map(); // errorId -> i18n.t('i18n.t('ui_i18n_t_ui_error_data_const_errorstats_total_0_bytype_new_map_byseverity_new_map_recovered_0_unresolved_0_error_id_generation_let_erroridcounter_0_fui18n.t('ui_i18n_t_ui_i18n_t_ui_error_data_const_errorstats_total_0_bytype_new_map_byseverity_new_map_recovered_0_unresolved_0_error_id_generation_let_erroridcounter_0_function_generateerrorid_return_err_date_now_erroridcounter_error_classification_helper_function_classifyerror_error_const_message_error_message_tolowercase_const_status_error_status_error_statuscode_network_errors_if_error_name_networkerror_message_includes_network_message_includes_fetch_return_errortypes_network_authentication_errors_if_status_401_message_includes_unauthorized_message_includes_authentication_return_errortypes_authentication_authorization_errors_if_status_403_message_includes_forbidden_message_includes_authorization_return_errortypes_authorization_not_found_errors_if_status_404_message_includes_not_found_return_errortypes_not_found_rate_limiting_if_status_429_message_includes_rate_limit_message_includes_too_many_requests_return_errortypes_rate_limit_timeout_errors_if_error_name_timeouterror_message_includes_timeout_return_errortypes_timeout_server_errors_if_status_500_status')'i18n.t('ui_invalid')')) {
    return ErrorTypes.VALIDATION;
  }
  
  // Client errors
  if (status >i18n.t('i18n.t('ui_i18n_t_ui_400_status')')< 500) {
    return ErrorTypes.CLIENT;
  }
  
  return ErrorTypes.UNKNOWN;
}

// Severiti18n.t('ui_i18n_t_ui_i18n_t_ui_400_status')eSeverity(error, type) {
  const status = error.status || error.statusCode;
  
  // Critical errors
  if (type === ErrorTypes.AUTHENTICATION || type === ErrorTypes.AUTHORIZATION) {
    return ErrorSeverity.CRITICAL;
  }
  
  if (status >i18n.t('i18n.t('ui_i18n_t_ui_500_return_errorseverity_high_high_severity_errors_if_type_errortypes_server_type_errortypesi18n.t('ui_i18n_t_ui_i18n_t_ui_500_return_errorseverity_high_high_severity_errors_if_type_errortypes_server_type_errortypes_network_return_errorseverity_high_medium_severity_errors_if_type_errortypes_validation_type_errortypes_timeout_type_errortypes_rate_limit_return_errorseverity_medium_low_severity_for_everything_else_return_errorseverity_low_user_friendly_error_messages_function_getusermessage_error_type_severity_const_custommessages_errortypes_network_network_connection_error_please_check_your_internet_connection_errortypes_authentication_authentication_required_please_log_in_again_errortypes_authorization_you_don_t_have_permission_to_perform_this_action_errortypes_not_found_the_requested_resource_was_not_found_errortypes_server_server_error_occurred_our_team_has_been_notified_errortypes_timeout_request_timed_out_please_try_again_errortypes_rate_limit_too_many_requests_please_wait_and_try_again_errortypes_validation_invalid_input_please_check_your_data_and_try_again_errortypes_client_request_error_please_check_your_input_and_try_again_return_custommessages_type_errorconfig_defaultusermessage_error_logging_function_logerror_errordata_if_errorconfig_enableconsole_const_logmethod_errordata_severity_errorseverity_critical_error_errordata_severity_errorseverity_high_warn_log_console_logmethod_errordata_severity_touppercase_errordata_type_errordata_message_errorid_errordata_id_timestamp_errordata_timestamp_context_errordata_context_stack_errordata_stack_event_emission_for_errors_function_emiterrorevent_errordata_if_errorconfig_enableevents_emit_error_occurred_errordata_emit_error_errordata_type_errordata_emit_error_errordata_severity_errordata_user_feedback_function_showuserfeedback_errordata_if_errorconfig_enableuserfeedback_return_use_the_notification_system_if_available_if_globalthis_notificationsssestore_try_globalthis_notificationsssestore_create_type_error_title_errordata_usermessage_body_errordata_message_severity_errordata_severity_ttl_seconds_math_max_3_math_min_15_errordata_severity_errorseverity_critical_15_8_metadata_errorid_errordata_id_errortype_errordata_type_context_errordata_context_catch_notificationerror_console_warn_failed_to_show_error_notification_notificationerror_fallback_to_alert_if_errordata_severity_errorseverity_critical_errordata_severity_errorseverity_high_alert_errordata_usermessage_error_recovery_strategies_const_recoverystrategies_errortypes_network_async_errordata_network_recovery_retry_with_exponential_backoff_for_let_attempt_1_attempt')ve, errorConfig.recoveryDelay * attempt));
        // Try to fetch a simple endpoint to check connectivity
        const response = await fetch('i18n.t('ui_health')', { method: 'i18n.t('ui_head')' });
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
    return { recovered: false, suggestion: 'i18n.t('ui_try_again_with_a_longer_timeout')' };
  },
  
  [ErrorTypes.RATE_LIMIT]: async (errorData) => {
    // Rate limit recovery: wait and retry
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
    return { recovered: true, suggestion: 'i18n.t('ui_rate_limit_window_passed')' };
  },
  
  default: async (errorData) => {
    return { recovered: false, suggestion: 'i18n.t('ui_no_automatic_recovery_available')' };
  }
};

// Main error handling function
export async function handleError(error, context = {}) {
  const errorId = generateErrorId();
  const timestamp = Date.now();
  
  // Normalize error
  const normalizedError = {
    message: error.message || error.toString() || 'i18n.t('ui_unknown_error')',
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
        emit('i18n.t('ui_error_recovered')', errorData);
        
        if (errorConfig.enableConsole) {
          console.log(`Error recovei18n.t('ui_error_recovered_errorid')esult);
        }
      } else {
        errorStats.unresolved++;
        emit('i18n.t('ui_error_unresolved')', errorData);
      }
    } catch (recoveryError) {
      console.error('i18n.t('ui_error_recovery_failed')', recoveryError);
      errorStats.unresolved++;
      emit('i18n.t('ui_error_recovery_failed')', { ...errorData, recoveryError });
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
    recoveryRate: errorStats.total > 0 ? (errorStats.recovered / errorStats.total * 100).toFixed(2) + '%'i18n.t('ui_')'0%'i18n.t('ui_export_function_clearerrorhistory_errorhistory_clear_errorstats_total_0_errorstats_recovered_0_errorstats_unresolved_0_errorstats_bytype_clear_errorstats_byseverity_clear_global_error_handlers_export_function_setupglobalerrorhandlers_unhandled_promise_rejections_window_addeventlistener')'unhandledrejection'i18n.t('ui_event_handleerror_event_reason_source')'unhandledrejection'i18n.t('ui_promise_event_promise_prevent_default_behavior_only_if_we')'ve handled it
    event.preventDefault();
  });
  
  // Uncaught errors
  window.addEventListener('i18n.t('ui_error')', (event) => {
    handleError(event.error, {
      source: 'i18n.t('ui_window_error')',
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
if (typeof window !== 'i18n.t('ui_undefined')') {
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