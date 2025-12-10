/**
 * Health Store
 * 
 * Centralized state management for the Health Dashboard feature.
 * 
 * @module features/health/health.store
 */

import { createStore, subscribe } from '../../core/state/store.js';

/**
 * Service status types
 */
export const SERVICE_STATUS = Object.freeze({
  HEALTHY: 'healthy',
  DEGRADED: 'degraded',
  UNHEALTHY: 'unhealthy',
  OFFLINE: 'offline',
  UNKNOWN: 'unknown',
});

/**
 * Initial health state
 */
const initialState = {
  // Service statuses
  services: {
    gateway: { status: SERVICE_STATUS.UNKNOWN, lastCheck: null, error: null },
    somabrain: { status: SERVICE_STATUS.UNKNOWN, lastCheck: null, error: null },
  },
  
  // Overall status
  overallStatus: SERVICE_STATUS.UNKNOWN,
  
  // Last check timestamp
  lastCheck: null,
  
  // Polling state
  isPolling: false,
  pollInterval: 30000, // 30 seconds
  
  // UI state
  isLoading: false,
  error: null,
};

/**
 * Health store instance
 */
export const healthStore = createStore('health', initialState, {
  persist: false,
});

/**
 * Update service status
 * @param {string} serviceName - Service name
 * @param {Object} status - Status object
 */
export function updateServiceStatus(serviceName, status) {
  healthStore.services = {
    ...healthStore.services,
    [serviceName]: {
      ...status,
      lastCheck: new Date().toISOString(),
    },
  };
  
  // Update overall status
  updateOverallStatus();
}

/**
 * Update overall status based on all services
 */
function updateOverallStatus() {
  const statuses = Object.values(healthStore.services);
  
  if (statuses.every(s => s.status === SERVICE_STATUS.HEALTHY)) {
    healthStore.overallStatus = SERVICE_STATUS.HEALTHY;
  } else if (statuses.some(s => s.status === SERVICE_STATUS.UNHEALTHY || s.status === SERVICE_STATUS.OFFLINE)) {
    healthStore.overallStatus = SERVICE_STATUS.UNHEALTHY;
  } else if (statuses.some(s => s.status === SERVICE_STATUS.DEGRADED)) {
    healthStore.overallStatus = SERVICE_STATUS.DEGRADED;
  } else {
    healthStore.overallStatus = SERVICE_STATUS.UNKNOWN;
  }
  
  healthStore.lastCheck = new Date().toISOString();
}

/**
 * Set loading state
 * @param {boolean} loading - Loading state
 */
export function setLoading(loading) {
  healthStore.isLoading = loading;
}

/**
 * Set error state
 * @param {string|null} error - Error message
 */
export function setError(error) {
  healthStore.error = error;
}

/**
 * Set polling state
 * @param {boolean} polling - Polling state
 */
export function setPolling(polling) {
  healthStore.isPolling = polling;
}

/**
 * Check if SomaBrain is offline
 * @returns {boolean}
 */
export function isSomaBrainOffline() {
  const status = healthStore.services.somabrain?.status;
  return status === SERVICE_STATUS.OFFLINE || status === SERVICE_STATUS.UNHEALTHY;
}

/**
 * Check if any service is degraded
 * @returns {boolean}
 */
export function isAnyServiceDegraded() {
  return healthStore.overallStatus !== SERVICE_STATUS.HEALTHY;
}

/**
 * Get service status
 * @param {string} serviceName - Service name
 * @returns {Object} Service status
 */
export function getServiceStatus(serviceName) {
  return healthStore.services[serviceName] || { status: SERVICE_STATUS.UNKNOWN };
}

/**
 * Subscribe to health changes
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function onHealthChange(callback) {
  return subscribe('health', callback);
}

export default {
  store: healthStore,
  SERVICE_STATUS,
  updateServiceStatus,
  setLoading,
  setError,
  setPolling,
  isSomaBrainOffline,
  isAnyServiceDegraded,
  getServiceStatus,
  onHealthChange,
};
