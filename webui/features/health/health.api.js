/**
 * Health API
 * 
 * API calls for the Health Dashboard feature.
 * Monitors service health status.
 * 
 * @module features/health/health.api
 */

import { fetchApi } from '../../core/api/client.js';
import { ENDPOINTS, buildUrl } from '../../core/api/endpoints.js';

/**
 * Fetch gateway health status
 * @returns {Promise<Object>} Health status
 */
export async function fetchGatewayHealth() {
  const response = await fetchApi(buildUrl(ENDPOINTS.HEALTH));
  
  if (!response.ok) {
    return {
      status: 'unhealthy',
      error: `HTTP ${response.status}`,
    };
  }
  
  return response.json();
}

/**
 * Fetch SomaBrain health status
 * @returns {Promise<Object>} Health status
 */
export async function fetchSomaBrainHealth() {
  try {
    const response = await fetchApi(buildUrl(ENDPOINTS.SOMABRAIN_HEALTH));
    
    if (!response.ok) {
      return {
        status: 'unhealthy',
        error: `HTTP ${response.status}`,
      };
    }
    
    return response.json();
  } catch (err) {
    return {
      status: 'offline',
      error: err.message,
    };
  }
}

/**
 * Fetch all service health statuses
 * @returns {Promise<Object>} Combined health status
 */
export async function fetchAllHealth() {
  const [gateway, somabrain] = await Promise.all([
    fetchGatewayHealth().catch(err => ({ status: 'error', error: err.message })),
    fetchSomaBrainHealth().catch(err => ({ status: 'error', error: err.message })),
  ]);
  
  return {
    gateway,
    somabrain,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Check if a service is healthy
 * @param {Object} health - Health response
 * @returns {boolean}
 */
export function isHealthy(health) {
  if (!health) return false;
  return health.status === 'healthy' || health.ok === true;
}

/**
 * Get health status color
 * @param {Object} health - Health response
 * @returns {string} 'green' | 'yellow' | 'red'
 */
export function getHealthColor(health) {
  if (!health) return 'red';
  if (isHealthy(health)) return 'green';
  if (health.status === 'degraded') return 'yellow';
  return 'red';
}

export default {
  fetchGatewayHealth,
  fetchSomaBrainHealth,
  fetchAllHealth,
  isHealthy,
  getHealthColor,
};
