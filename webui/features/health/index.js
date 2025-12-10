/**
 * Health Feature Module
 * 
 * Public API for the Health Dashboard feature.
 * Re-exports store and API functions.
 * 
 * @module features/health
 */

import * as store from './health.store.js';
import * as api from './health.api.js';

// Re-export store functions
export const {
  healthStore,
  SERVICE_STATUS,
  updateServiceStatus,
  setLoading,
  setError,
  setPolling,
  isSomaBrainOffline,
  isAnyServiceDegraded,
  getServiceStatus,
  onHealthChange,
} = store;

// Re-export API functions
export const {
  fetchGatewayHealth,
  fetchSomaBrainHealth,
  fetchAllHealth,
  isHealthy,
  getHealthColor,
} = api;

export default {
  store,
  api,
};
