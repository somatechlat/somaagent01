/**
 * SomaStack Unified UI Design System - Status Store
 * 
 * Document ID: SOMASTACK-UI-STATUS-STORE
 * Version: 1.0.0
 * 
 * Alpine.js store for service health monitoring.
 * 
 * Requirements: FR-SI-001 through FR-SI-007
 */

/**
 * Default health endpoints for SomaStack services
 * Requirement: FR-SI-006
 */
const DEFAULT_ENDPOINTS = {
  somabrain: { url: '/api/somabrain/health', port: 9696, path: '/health' },
  somamemory: { url: '/api/somamemory/healthz', port: 9595, path: '/healthz' },
  somaagent: { url: '/v1/health', port: 21016, path: '/v1/health' }
};

/**
 * Health status enum
 * Requirement: FR-SI-001
 */
const HealthStatus = {
  HEALTHY: 'healthy',
  DEGRADED: 'degraded',
  DOWN: 'down',
  UNKNOWN: 'unknown'
};

/**
 * Format relative time
 * 
 * @param {Date} date - Date to format
 * @returns {string} Relative time string
 */
function formatRelativeTime(date) {
  if (!date) return 'never';
  
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  
  if (diffSec < 5) return 'just now';
  if (diffSec < 60) return `${diffSec}s ago`;
  
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}h ago`;
  
  const diffDay = Math.floor(diffHour / 24);
  return `${diffDay}d ago`;
}

/**
 * Register the status store with Alpine.js
 * 
 * Usage:
 *   Alpine.store('status').services.somabrain.health
 *   Alpine.store('status').checkAllServices()
 */
function registerStatusStore(Alpine) {
  Alpine.store('status', {
    // State
    services: {},
    isPolling: false,
    pollIntervalMs: 5000, // Requirement: FR-SI-002 - update within 5 seconds
    pollIntervalId: null,
    
    /**
     * Initialize store on Alpine start
     */
    init() {
      // Initialize service status objects
      Object.keys(DEFAULT_ENDPOINTS).forEach(name => {
        this.services[name] = {
          name: name,
          health: HealthStatus.UNKNOWN,
          lastChecked: null,
          latencyMs: 0,
          details: {}
        };
      });
      
      // Start polling
      this.startPolling();
    },
    
    /**
     * Check health of a single service
     * Requirement: FR-SI-006
     * 
     * @param {string} serviceName - Service identifier
     * @param {string} endpoint - Health check URL
     * @returns {Promise<void>}
     */
    async checkHealth(serviceName, endpoint) {
      const startTime = performance.now();
      
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(endpoint, {
          method: 'GET',
          signal: controller.signal,
          headers: {
            'Accept': 'application/json'
          }
        });
        
        clearTimeout(timeoutId);
        
        const latency = Math.round(performance.now() - startTime);
        
        if (!response.ok) {
          this.services[serviceName] = {
            name: serviceName,
            health: HealthStatus.DEGRADED,
            lastChecked: new Date(),
            latencyMs: latency,
            details: { error: `HTTP ${response.status}` }
          };
          return;
        }
        
        const data = await response.json();
        
        // Determine health status from response
        let health = HealthStatus.HEALTHY;
        if (data.ok === false || data.status === 'unhealthy') {
          health = HealthStatus.DEGRADED;
        }
        
        this.services[serviceName] = {
          name: serviceName,
          health: health,
          lastChecked: new Date(),
          latencyMs: latency,
          details: data.components || data.details || {}
        };
        
      } catch (error) {
        const latency = Math.round(performance.now() - startTime);
        
        this.services[serviceName] = {
          name: serviceName,
          health: error.name === 'AbortError' ? HealthStatus.DOWN : HealthStatus.DOWN,
          lastChecked: new Date(),
          latencyMs: latency,
          details: { error: error.message }
        };
      }
    },
    
    /**
     * Check health of all configured services
     * Requirement: FR-SI-006, FR-SI-007
     * 
     * @returns {Promise<void>}
     */
    async checkAllServices() {
      const checks = Object.entries(DEFAULT_ENDPOINTS).map(([name, config]) => {
        return this.checkHealth(name, config.url);
      });
      
      await Promise.all(checks);
    },
    
    /**
     * Start health polling
     * Requirement: FR-SI-002
     */
    startPolling() {
      if (this.isPolling) return;
      
      this.isPolling = true;
      
      // Initial check
      this.checkAllServices();
      
      // Set up interval
      this.pollIntervalId = setInterval(() => {
        this.checkAllServices();
      }, this.pollIntervalMs);
    },
    
    /**
     * Stop health polling
     */
    stopPolling() {
      if (this.pollIntervalId) {
        clearInterval(this.pollIntervalId);
        this.pollIntervalId = null;
      }
      this.isPolling = false;
    },
    
    /**
     * Set poll interval
     * 
     * @param {number} ms - Interval in milliseconds (min 1000)
     */
    setPollInterval(ms) {
      this.pollIntervalMs = Math.max(1000, ms);
      
      if (this.isPolling) {
        this.stopPolling();
        this.startPolling();
      }
    },
    
    /**
     * Get service status
     * 
     * @param {string} serviceName - Service identifier
     * @returns {object} Service status object
     */
    getService(serviceName) {
      return this.services[serviceName] || {
        name: serviceName,
        health: HealthStatus.UNKNOWN,
        lastChecked: null,
        latencyMs: 0,
        details: {}
      };
    },
    
    /**
     * Get formatted last checked time
     * Requirement: FR-SI-003
     * 
     * @param {string} serviceName - Service identifier
     * @returns {string} Relative time string
     */
    getLastCheckedFormatted(serviceName) {
      const service = this.services[serviceName];
      return formatRelativeTime(service?.lastChecked);
    },
    
    /**
     * Computed: Overall system health
     * 
     * @returns {string} Overall health status
     */
    get overallHealth() {
      const statuses = Object.values(this.services).map(s => s.health);
      
      if (statuses.some(s => s === HealthStatus.DOWN)) {
        return HealthStatus.DOWN;
      }
      if (statuses.some(s => s === HealthStatus.DEGRADED)) {
        return HealthStatus.DEGRADED;
      }
      if (statuses.every(s => s === HealthStatus.HEALTHY)) {
        return HealthStatus.HEALTHY;
      }
      return HealthStatus.UNKNOWN;
    },
    
    /**
     * Computed: Count of healthy services
     */
    get healthyCount() {
      return Object.values(this.services).filter(s => s.health === HealthStatus.HEALTHY).length;
    },
    
    /**
     * Computed: Total service count
     */
    get totalCount() {
      return Object.keys(this.services).length;
    },
    
    /**
     * Add custom service endpoint
     * 
     * @param {string} name - Service name
     * @param {string} url - Health check URL
     */
    addService(name, url) {
      DEFAULT_ENDPOINTS[name] = { url };
      this.services[name] = {
        name: name,
        health: HealthStatus.UNKNOWN,
        lastChecked: null,
        latencyMs: 0,
        details: {}
      };
    },
    
    /**
     * Remove service from monitoring
     * 
     * @param {string} name - Service name
     */
    removeService(name) {
      delete DEFAULT_ENDPOINTS[name];
      delete this.services[name];
    }
  });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { registerStatusStore, HealthStatus, formatRelativeTime };
}

// Auto-register if Alpine is available
if (typeof Alpine !== 'undefined') {
  registerStatusStore(Alpine);
}
