/**
 * Health Dashboard Component
 * 
 * Displays service health status with polling.
 * 
 * @module components/health/health-dashboard
 */

import { 
  healthStore, 
  SERVICE_STATUS,
  updateServiceStatus, 
  setLoading, 
  setPolling,
  isSomaBrainOffline,
} from '../../features/health/index.js';
import { fetchAllHealth, isHealthy, getHealthColor } from '../../features/health/health.api.js';

/**
 * Health Dashboard component factory
 * @param {Object} options - Component options
 * @param {number} [options.pollInterval=30000] - Poll interval in ms
 * @returns {Object} Alpine component data
 */
export default function HealthDashboard(options = {}) {
  return {
    // State from store
    get services() { return healthStore.services; },
    get overallStatus() { return healthStore.overallStatus; },
    get lastCheck() { return healthStore.lastCheck; },
    get isLoading() { return healthStore.isLoading; },
    
    // Local state
    pollInterval: options.pollInterval ?? 30000,
    pollTimer: null,
    
    async init() {
      // Initial health check
      await this.checkHealth();
      
      // Start polling
      this.startPolling();
    },
    
    destroy() {
      this.stopPolling();
    },
    
    /**
     * Check all service health
     */
    async checkHealth() {
      setLoading(true);
      
      try {
        const health = await fetchAllHealth();
        
        // Update gateway status
        updateServiceStatus('gateway', {
          status: isHealthy(health.gateway) ? SERVICE_STATUS.HEALTHY : SERVICE_STATUS.UNHEALTHY,
          error: health.gateway.error || null,
          details: health.gateway,
        });
        
        // Update SomaBrain status
        updateServiceStatus('somabrain', {
          status: isHealthy(health.somabrain) ? SERVICE_STATUS.HEALTHY : 
                  health.somabrain.status === 'offline' ? SERVICE_STATUS.OFFLINE : SERVICE_STATUS.UNHEALTHY,
          error: health.somabrain.error || null,
          details: health.somabrain,
        });
      } catch (err) {
        console.error('Health check failed:', err);
      } finally {
        setLoading(false);
      }
    },
    
    /**
     * Start health polling
     */
    startPolling() {
      this.stopPolling();
      setPolling(true);
      
      this.pollTimer = setInterval(() => {
        this.checkHealth();
      }, this.pollInterval);
    },
    
    /**
     * Stop health polling
     */
    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
      setPolling(false);
    },
    
    /**
     * Manual refresh
     */
    async refresh() {
      await this.checkHealth();
    },
    
    /**
     * Get status badge class
     * @param {string} status - Service status
     * @returns {string} Badge class
     */
    getStatusClass(status) {
      switch (status) {
        case SERVICE_STATUS.HEALTHY: return 'badge-success';
        case SERVICE_STATUS.DEGRADED: return 'badge-warning';
        case SERVICE_STATUS.UNHEALTHY: return 'badge-error';
        case SERVICE_STATUS.OFFLINE: return 'badge-error';
        default: return '';
      }
    },
    
    /**
     * Get status text
     * @param {string} status - Service status
     * @returns {string} Status text
     */
    getStatusText(status) {
      switch (status) {
        case SERVICE_STATUS.HEALTHY: return 'Healthy';
        case SERVICE_STATUS.DEGRADED: return 'Degraded';
        case SERVICE_STATUS.UNHEALTHY: return 'Unhealthy';
        case SERVICE_STATUS.OFFLINE: return 'Offline';
        default: return 'Unknown';
      }
    },
    
    /**
     * Format last check time
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Formatted time
     */
    formatLastCheck(timestamp) {
      if (!timestamp) return 'Never';
      
      const date = new Date(timestamp);
      const now = new Date();
      const diff = Math.floor((now - date) / 1000);
      
      if (diff < 60) return 'Just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      return date.toLocaleTimeString();
    },
    
    /**
     * Check if SomaBrain is offline
     */
    get showSomaBrainBanner() {
      return isSomaBrainOffline();
    },
  };
}
