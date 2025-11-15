/**
 * System Monitoring Integration for SomaAgent01 Web UI
 * Integrates degradation, circuit breaker, and metrics endpoints with the Web UI
 */

import { fetchApi, callJsonApi } from '/js/api.js';

class SystemMonitor {
    constructor() {
        this.pollingInterval = null;
        this.pollingActive = false;
        this.degradationStatus = null;
        this.circuitStatus = null;
        this.metricsData = null;
        this.lastUpdate = null;
        this.callbacks = new Set();
    }

    /**
     * Start monitoring the system
     * @param {number} interval - Polling interval in milliseconds (default: 30000)
     */
    startMonitoring(interval = 30000) {
        if (this.pollingActive) return;
        
        this.pollingActive = true;
        this.pollingInterval = setInterval(() => {
            this.updateAllStatus();
        }, interval);
        
        // Initial update
        this.updateAllStatus();
    }

    /**
     * Stop monitoring the system
     */
    stopMonitoring() {
        if (!this.pollingActive) return;
        
        this.pollingActive = false;
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * Add a callback to be called when monitoring data updates
     * @param {Function} callback - Callback function
     */
    addCallback(callback) {
        this.callbacks.add(callback);
    }

    /**
     * Remove a callback
     * @param {Function} callback - Callback function to remove
     */
    removeCallback(callback) {
        this.callbacks.delete(callback);
    }

    /**
     * Notify all callbacks of data updates
     */
    notifyCallbacks() {
        this.callbacks.forEach(callback => {
            try {
                callback({
                    degradation: this.degradationStatus,
                    circuit: this.circuitStatus,
                    metrics: this.metricsData,
                    lastUpdate: this.lastUpdate
                });
            } catch (e) {
                console.error('Error in monitoring callback:', e);
            }
        });
    }

    /**
     * Update all monitoring status
     */
    async updateAllStatus() {
        try {
            await Promise.all([
                this.updateDegradationStatus(),
                this.updateCircuitStatus(),
                this.updateMetricsData()
            ]);
            
            this.lastUpdate = new Date();
            this.notifyCallbacks();
        } catch (error) {
            console.error('Error updating monitoring status:', error);
        }
    }

    /**
     * Update degradation status
     */
    async updateDegradationStatus() {
        try {
            const response = await fetchApi('/v1/degradation/status');
            if (response.ok) {
                this.degradationStatus = await response.json();
            } else {
                console.error('Degradation status request failed:', response.status);
                this.degradationStatus = { error: 'Failed to fetch degradation status' };
            }
        } catch (error) {
            console.error('Error fetching degradation status:', error);
            this.degradationStatus = { error: 'Failed to fetch degradation status' };
        }
    }

    /**
     * Update circuit breaker status
     */
    async updateCircuitStatus() {
        try {
            const response = await fetchApi('/v1/circuit/status');
            if (response.ok) {
                this.circuitStatus = await response.json();
            } else {
                console.error('Circuit status request failed:', response.status);
                this.circuitStatus = { error: 'Failed to fetch circuit status' };
            }
        } catch (error) {
            console.error('Error fetching circuit status:', error);
            this.circuitStatus = { error: 'Failed to fetch circuit status' };
        }
    }

    /**
     * Update metrics data
     */
    async updateMetricsData() {
        try {
            const response = await fetchApi('/v1/metrics/system');
            if (response.ok) {
                this.metricsData = await response.json();
            } else {
                console.error('Metrics request failed:', response.status);
                this.metricsData = { error: 'Failed to fetch metrics' };
            }
        } catch (error) {
            console.error('Error fetching metrics:', error);
            this.metricsData = { error: 'Failed to fetch metrics' };
        }
    }

    /**
     * Get current degradation status
     */
    getDegradationStatus() {
        return this.degradationStatus;
    }

    /**
     * Get current circuit breaker status
     */
    getCircuitStatus() {
        return this.circuitStatus;
    }

    /**
     * Get current metrics data
     */
    getMetricsData() {
        return this.metricsData;
    }

    /**
     * Get system health summary
     */
    getHealthSummary() {
        const issues = [];
        
        if (this.degradationStatus) {
            if (this.degradationStatus.overall_level !== 'none') {
                issues.push({
                    type: 'degradation',
                    level: this.degradationStatus.overall_level,
                    message: `System degradation: ${this.degradationStatus.overall_level}`
                });
            }
        }
        
        if (this.circuitStatus && !this.circuitStatus.error) {
            // Check if any circuit breakers are open
            if (this.circuitStatus.circuits) {
                Object.entries(this.circuitStatus.circuits).forEach(([name, circuit]) => {
                    if (circuit.state === 'OPEN') {
                        issues.push({
                            type: 'circuit',
                            level: 'critical',
                            message: `Circuit breaker open: ${name}`
                        });
                    }
                });
            }
        }
        
        if (this.metricsData && !this.metricsData.error) {
            // Check for high resource usage
            if (this.metricsData.cpu && this.metricsData.cpu.percent > 80) {
                issues.push({
                    type: 'resource',
                    level: 'warning',
                    message: `High CPU usage: ${this.metricsData.cpu.percent.toFixed(1)}%`
                });
            }
            
            if (this.metricsData.memory && this.metricsData.memory.percent > 80) {
                issues.push({
                    type: 'resource',
                    level: 'warning',
                    message: `High memory usage: ${this.metricsData.memory.percent.toFixed(1)}%`
                });
            }
        }
        
        return {
            healthy: issues.length === 0,
            issues: issues,
            lastUpdate: this.lastUpdate
        };
    }
}

// Create global instance
const systemMonitor = new SystemMonitor();

// Export for use in other modules
export { systemMonitor, SystemMonitor };

// Auto-start monitoring when DOM is ready
if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // Start monitoring with 30-second intervals
        systemMonitor.startMonitoring(30000);
        
        // Integrate with existing Alpine store if available
        if (window.Alpine && window.Alpine.store) {
            // Create a monitoring store
            window.Alpine.store('monitoring', {
                degradation: null,
                circuit: null,
                metrics: null,
                healthSummary: null,
                lastUpdate: null,
                
                init() {
                    // Add callback to update Alpine store
                    systemMonitor.addCallback((data) => {
                        this.degradation = data.degradation;
                        this.circuit = data.circuit;
                        this.metrics = data.metrics;
                        this.healthSummary = systemMonitor.getHealthSummary();
                        this.lastUpdate = data.lastUpdate;
                    });
                }
            });
        }
    });
}