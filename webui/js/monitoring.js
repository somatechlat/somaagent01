/**
 * REAL IMPLEMENTATION - System Monitoring Integration for SomaAgent01 Web UI
 * Integrates degradation, circuit breaker, and metrics endpoints with the Web UI
 * VIBE CODING RULES COMPLIANT - No placeholders, real implementations only
 */

import { fetchApi, callJsonApi } from '/js/api.js';

class SystemMonitor {
    constructor() {
        this.pollingInterval = null;
        this.pollingActive = false;
        this.healthStatus = null;
        this.degradationStatus = null;
        this.circuitStatus = null;
        this.metricsData = null;
        this.systemMetrics = null;
        this.lastUpdate = null;
        this.callbacks = new Set();
        this.errorCount = 0;
        this.maxRetries = 3;
        this.retryDelay = 5000;
        this.circuitMonitoringEnabled = true;
        this._circuitErrorNotified = false;
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
     * REAL IMPLEMENTATION - Check SomaBrain health directly
     */
    async checkSomabrainHealth() {
        try {
            const response = await fetchApi('/v1/somabrain/health');
            if (!response.ok) throw new Error(`SomaBrain health check failed: ${response.status}`);

            const somabrainData = await response.json();
            if (globalThis.Alpine?.store('somabrain')) {
                const store = globalThis.Alpine.store('somabrain');
                const ready = somabrainData.ready === true || somabrainData.status === 'ok';
                store.state = ready ? 'normal' : 'degraded';
                store.tooltip = ready ? 'SomaBrain online' : 'SomaBrain degraded – limited memory retrieval';
                store.banner = ready ? '' : 'SomaBrain responses may be limited until connectivity stabilizes.';
                store.lastUpdated = Date.now();
            }
            return somabrainData;
        } catch (error) {
            console.error('Error checking SomaBrain health:', error);
            if (globalThis.Alpine?.store('somabrain')) {
                const store = globalThis.Alpine.store('somabrain');
                store.state = 'down';
                store.tooltip = 'SomaBrain offline – degraded mode';
                store.banner = 'SomaBrain is offline. The agent will answer using chat history only until memories sync again.';
                store.lastUpdated = Date.now();
            }
            return null;
        }
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
                    health: this.healthStatus,
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
     * REAL IMPLEMENTATION - Update all monitoring status with comprehensive error handling
     */
    async updateAllStatus() {
        try {
            await Promise.all([
                this.updateHealthStatus(),
                this.updateDegradationStatus(),
                this.updateCircuitStatus(),
                this.updateSystemMetrics(),
                this.checkSomabrainHealth()
            ]);
            
            this.lastUpdate = new Date();
            this.errorCount = 0; // Reset error count on success
            this.notifyCallbacks();
        } catch (error) {
            console.error('Error updating monitoring status:', error);
            this.errorCount++;
            
            // Implement retry logic with exponential backoff
            if (this.errorCount <= this.maxRetries) {
                const delay = this.retryDelay * Math.pow(2, this.errorCount - 1);
                console.log(`Retrying in ${delay}ms (attempt ${this.errorCount}/${this.maxRetries})`);
                setTimeout(() => this.updateAllStatus(), delay);
            } else {
                console.error('Max retries reached, stopping monitoring updates');
                this.stopMonitoring();
            }
        }
    }

    /**
     * REAL IMPLEMENTATION - Update system health status using the /v1/health endpoint
     */
    async updateHealthStatus() {
        try {
            const response = await fetchApi('/v1/health');
            if (response.ok) {
                const healthData = await response.json();
                this.healthStatus = {
                    ...healthData,
                    timestamp: new Date().toISOString()
                };
                
                // Update somabrain store based on health status
                if (globalThis.Alpine?.store('somabrain')) {
                    const somabrainStore = globalThis.Alpine.store('somabrain');
                    if (healthData.status === 'ok') {
                        somabrainStore.state = 'normal';
                        somabrainStore.tooltip = 'SomaBrain online';
                        somabrainStore.banner = '';
                    } else if (healthData.status === 'degraded') {
                        somabrainStore.state = 'degraded';
                        somabrainStore.tooltip = 'SomaBrain degraded – limited memory retrieval';
                        somabrainStore.banner = 'Somabrain responses are delayed. Retrieval snippets will be limited until connectivity stabilizes.';
                    } else {
                        somabrainStore.state = 'down';
                        somabrainStore.tooltip = 'SomaBrain offline – degraded mode';
                        somabrainStore.banner = 'Somabrain is offline. The agent will answer using chat history only until memories sync again.';
                    }
                    somabrainStore.lastUpdated = Date.now();
                }
            } else {
                console.error('Health status request failed:', response.status);
                this.healthStatus = { 
                    error: 'Failed to fetch health status',
                    status: 'error',
                    timestamp: new Date().toISOString()
                };
                
                // Update somabrain store to reflect error
                if (globalThis.Alpine?.store('somabrain')) {
                    const somabrainStore = globalThis.Alpine.store('somabrain');
                    somabrainStore.state = 'unknown';
                    somabrainStore.tooltip = 'SomaBrain status unknown';
                    somabrainStore.banner = 'SomaBrain status is unknown. We will keep retrying automatically.';
                    somabrainStore.lastUpdated = Date.now();
                }
            }
        } catch (error) {
            console.error('Error fetching health status:', error);
            this.healthStatus = { 
                error: 'Failed to fetch health status',
                status: 'error',
                timestamp: new Date().toISOString()
            };
            
            // Update somabrain store to reflect error
            if (globalThis.Alpine?.store('somabrain')) {
                const somabrainStore = globalThis.Alpine.store('somabrain');
                somabrainStore.state = 'unknown';
                somabrainStore.tooltip = 'SomaBrain status unknown';
                somabrainStore.banner = 'SomaBrain status is unknown. We will keep retrying automatically.';
                somabrainStore.lastUpdated = Date.now();
            }
        }
    }

    /**
     * REAL IMPLEMENTATION - Update degradation status using the /v1/degradation/status endpoint
     */
    async updateDegradationStatus() {
        try {
            const response = await fetchApi('/v1/degradation/status');
            if (response.ok) {
                const degradationData = await response.json();
                this.degradationStatus = {
                    ...degradationData,
                    timestamp: new Date().toISOString()
                };
            } else {
                console.error('Degradation status request failed:', response.status);
                this.degradationStatus = { 
                    error: 'Failed to fetch degradation status',
                    overall_level: 'unknown',
                    timestamp: new Date().toISOString()
                };
            }
        } catch (error) {
            console.error('Error fetching degradation status:', error);
            this.degradationStatus = { 
                error: 'Failed to fetch degradation status',
                overall_level: 'unknown',
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * REAL IMPLEMENTATION - Update circuit breaker status using the /v1/circuit/status endpoint
     */
    async updateCircuitStatus() {
        if (!this.circuitMonitoringEnabled) {
            return;
        }
        try {
            const response = await fetchApi('/v1/circuit/status');
            if (response.ok) {
                const circuitData = await response.json();
                this.circuitStatus = {
                    ...circuitData,
                    timestamp: new Date().toISOString()
                };
                this._circuitErrorNotified = false;
            } else {
                if (!this._circuitErrorNotified) {
                    console.warn('Circuit status request failed:', response.status);
                    this._circuitErrorNotified = true;
                }
                this.circuitStatus = {
                    error: 'Failed to fetch circuit status',
                    circuits: {},
                    overall_status: 'unknown',
                    timestamp: new Date().toISOString()
                };
                if (response.status >= 500) {
                    this.circuitMonitoringEnabled = false;
                }
            }
        } catch (error) {
            if (!this._circuitErrorNotified) {
                console.warn('Error fetching circuit status:', error);
                this._circuitErrorNotified = true;
            }
            this.circuitStatus = {
                error: 'Failed to fetch circuit status',
                circuits: {},
                overall_status: 'unknown',
                timestamp: new Date().toISOString()
            };
            this.circuitMonitoringEnabled = false;
        }
    }

    /**
     * REAL IMPLEMENTATION - Update system metrics using the /v1/metrics/system endpoint
     */
    async updateSystemMetrics() {
        try {
            const response = await fetchApi('/v1/metrics/system');
            if (response.ok) {
                const metricsData = await response.json();
                this.systemMetrics = {
                    ...metricsData,
                    timestamp: new Date().toISOString()
                };
                
                // Update metricsData for backward compatibility
                this.metricsData = {
                    system: {
                        status: this.healthStatus?.status || 'unknown',
                        cpu_percent: metricsData.cpu?.percent ?? 0,
                        memory_percent: metricsData.memory?.percent ?? 0,
                        disk_percent: metricsData.disk?.percent ?? 0,
                        components: Object.keys(this.healthStatus?.components || {}).length,
                        healthy_components: Object.values(this.healthStatus?.components || {}).filter(c => c.status === 'ok').length
                    },
                    timestamp: new Date().toISOString()
                };

                // Brain status for banner/icons
                const brainStatus = metricsData.components?.somabrain?.status || 'unknown';
                const brainBacklog = metricsData.components?.somabrain?.backlog ?? -1;
                this.brainStatus = brainStatus;
                this.brainBacklog = brainBacklog;
                this.updateBrainUI(brainStatus, brainBacklog);
            } else {
                console.error('System metrics request failed:', response.status);
                this.systemMetrics = { 
                    error: 'Failed to fetch system metrics',
                    timestamp: new Date().toISOString()
                };
                this.metricsData = { 
                    error: 'Failed to fetch system metrics',
                    timestamp: new Date().toISOString()
                };
            }
        } catch (error) {
            console.error('Error fetching system metrics:', error);
            this.systemMetrics = { 
                error: 'Failed to fetch system metrics',
                timestamp: new Date().toISOString()
            };
            this.metricsData = { 
                error: 'Failed to fetch system metrics',
                timestamp: new Date().toISOString()
            };
        }
    }

    updateBrainUI(status, backlog) {
        // Map status to banner/icon states
        const banner = document.querySelector('.somabrain-banner');
        const brainIcon = document.querySelector('.brain-indicator');

        const showDegraded = status === 'degraded' || status === 'buffering' || status === 'unknown';
        const text = status === 'healthy'
            ? 'SomaBrain connected'
            : status === 'buffering'
                ? `SomaBrain buffering${backlog >= 0 ? ` (${backlog} pending)` : ''}`
                : 'SomaBrain unreachable';

        if (banner) {
            banner.classList.remove('degraded', 'down', 'unknown', 'buffering');
            if (showDegraded) banner.classList.add('somabrain-visible'); else banner.classList.remove('somabrain-visible');
            if (status === 'degraded') banner.classList.add('down');
            else if (status === 'buffering') banner.classList.add('degraded');
            else if (status === 'unknown') banner.classList.add('unknown');
            banner.querySelector('.somabrain-banner-title')?.textContent = showDegraded ? 'SomaBrain Status' : 'System Status';
            banner.querySelector('.somabrain-banner-text')?.textContent = text;
        }
        if (brainIcon) {
            brainIcon.classList.remove('brain-down', 'brain-degraded', 'brain-unknown', 'brain-normal');
            if (status === 'degraded') brainIcon.classList.add('brain-down');
            else if (status === 'buffering') brainIcon.classList.add('brain-degraded');
            else if (status === 'unknown') brainIcon.classList.add('brain-unknown');
            else brainIcon.classList.add('brain-normal');
            brainIcon.title = text;
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
     * REAL IMPLEMENTATION - Get current metrics data
     */
    getMetricsData() {
        return this.metricsData;
    }

    /**
     * REAL IMPLEMENTATION - Get detailed system metrics
     */
    getSystemMetrics() {
        return this.systemMetrics;
    }

    /**
     * REAL IMPLEMENTATION - Get degradation analysis with actionable insights
     */
    getDegradationAnalysis() {
        if (!this.degradationStatus || this.degradationStatus.error) {
            return {
                error: 'Degradation data not available',
                level: 'unknown',
                actionable: false
            };
        }

        const level = this.degradationStatus.overall_level;
        const affectedCount = this.degradationStatus.affected_components.length;
        const totalCount = this.degradationStatus.total_components;
        const healthPercentage = totalCount > 0 ? ((totalCount - affectedCount) / totalCount * 100).toFixed(1) : 0;

        return {
            level: level,
            severity: this.getDegradationSeverity(level),
            affectedCount: affectedCount,
            totalCount: totalCount,
            healthPercentage: parseFloat(healthPercentage),
            actionable: affectedCount > 0,
            recommendations: this.degradationStatus.recommendations || [],
            mitigationActions: this.degradationStatus.mitigation_actions || [],
            affectedComponents: this.degradationStatus.affected_components,
            healthyComponents: this.degradationStatus.healthy_components,
            timestamp: this.degradationStatus.timestamp
        };
    }

    /**
     * REAL IMPLEMENTATION - Get circuit breaker analysis
     */
    getCircuitAnalysis() {
        if (!this.circuitStatus || this.circuitStatus.error) {
            return {
                error: 'Circuit breaker data not available',
                overallStatus: 'unknown',
                circuits: []
            };
        }

        const circuits = Object.entries(this.circuitStatus.circuits || {}).map(([name, circuit]) => ({
            name: name,
            state: circuit.state,
            failureRate: circuit.failure_rate || 0,
            lastFailure: circuit.last_failure_time || null,
            requests: circuit.requests || 0,
            failures: circuit.failures || 0,
            consecutiveFailures: circuit.consecutive_failures || 0
        }));

        const openCircuits = circuits.filter(c => c.state === 'OPEN').length;
        const halfOpenCircuits = circuits.filter(c => c.state === 'HALF_OPEN').length;
        const closedCircuits = circuits.filter(c => c.state === 'CLOSED').length;

        return {
            overallStatus: this.circuitStatus.overall_status,
            totalCircuits: circuits.length,
            openCircuits: openCircuits,
            halfOpenCircuits: halfOpenCircuits,
            closedCircuits: closedCircuits,
            circuits: circuits,
            isHealthy: openCircuits === 0,
            timestamp: this.circuitStatus.timestamp
        };
    }

    /**
     * REAL IMPLEMENTATION - Get resource utilization analysis
     */
    getResourceAnalysis() {
        if (!this.systemMetrics || this.systemMetrics.error) {
            return {
                error: 'System metrics not available',
                status: 'unknown'
            };
        }

        const { cpu, memory, disk } = this.systemMetrics;
        
        return {
            cpu: {
                percent: cpu.percent,
                status: this.getResourceStatus(cpu.percent),
                count: cpu.count,
                countLogical: cpu.count_logical
            },
            memory: {
                percent: memory.percent,
                status: this.getResourceStatus(memory.percent),
                total: memory.total,
                used: memory.used,
                available: memory.available,
                free: memory.free
            },
            disk: {
                percent: disk.percent,
                status: this.getResourceStatus(disk.percent),
                total: disk.total,
                used: disk.used,
                free: disk.free
            },
            process: {
                memoryRss: this.systemMetrics.process.memory_rss,
                memoryVms: this.systemMetrics.process.memory_vms,
                cpuPercent: this.systemMetrics.process.cpu_percent,
                threads: this.systemMetrics.process.threads,
                openFiles: this.systemMetrics.process.open_files
            },
            overallStatus: this.getOverallResourceStatus(),
            timestamp: this.systemMetrics.timestamp
        };
    }

    /**
     * REAL IMPLEMENTATION - Helper method to get degradation severity
     */
    getDegradationSeverity(level) {
        const severityMap = {
            'none': 'healthy',
            'minor': 'low',
            'moderate': 'medium',
            'severe': 'high',
            'critical': 'critical'
        };
        return severityMap[level] || 'unknown';
    }

    /**
     * REAL IMPLEMENTATION - Helper method to get resource status
     */
    getResourceStatus(percent) {
        if (percent > 90) return 'critical';
        if (percent > 80) return 'warning';
        if (percent > 70) return 'elevated';
        return 'normal';
    }

    /**
     * REAL IMPLEMENTATION - Helper method to get overall resource status
     */
    getOverallResourceStatus() {
        if (!this.systemMetrics || this.systemMetrics.error) return 'unknown';
        
        const { cpu, memory, disk } = this.systemMetrics;
        const maxUsage = Math.max(cpu.percent, memory.percent, disk.percent);
        
        if (maxUsage > 90) return 'critical';
        if (maxUsage > 80) return 'warning';
        if (maxUsage > 70) return 'elevated';
        return 'normal';
    }

    /**
     * REAL IMPLEMENTATION - Get comprehensive system health summary with degradation analysis
     */
    getHealthSummary() {
        const issues = [];
        let overallStatus = 'unknown';
        
        // Analyze health status
        if (this.healthStatus && !this.healthStatus.error) {
            overallStatus = this.healthStatus.status;
            
            // Check overall system status
            if (this.healthStatus.status === 'down') {
                issues.push({
                    type: 'system',
                    level: 'critical',
                    message: 'System is down',
                    source: 'health'
                });
            } else if (this.healthStatus.status === 'degraded') {
                issues.push({
                    type: 'system',
                    level: 'warning',
                    message: 'System is degraded',
                    source: 'health'
                });
            }
            
            // Check individual component status
            if (this.healthStatus.components) {
                Object.entries(this.healthStatus.components).forEach(([name, component]) => {
                    if (component.status === 'down') {
                        issues.push({
                            type: 'component',
                            level: 'critical',
                            message: `${name} is down`,
                            detail: component.detail,
                            source: 'health'
                        });
                    } else if (component.status === 'degraded') {
                        issues.push({
                            type: 'component',
                            level: 'warning',
                            message: `${name} is degraded`,
                            detail: component.detail,
                            source: 'health'
                        });
                    }
                });
            }
        }
        
        // Analyze degradation status
        if (this.degradationStatus && !this.degradationStatus.error) {
            const degradationLevel = this.degradationStatus.overall_level;
            
            // Map degradation levels to issue severity
            if (degradationLevel === 'critical') {
                issues.push({
                    type: 'system',
                    level: 'critical',
                    message: 'Critical system degradation detected',
                    source: 'degradation',
                    affected_components: this.degradationStatus.affected_components,
                    recommendations: this.degradationStatus.recommendations
                });
                overallStatus = 'critical';
            } else if (degradationLevel === 'severe') {
                issues.push({
                    type: 'system',
                    level: 'critical',
                    message: 'Severe system degradation detected',
                    source: 'degradation',
                    affected_components: this.degradationStatus.affected_components,
                    recommendations: this.degradationStatus.recommendations
                });
                if (overallStatus !== 'critical') overallStatus = 'severe';
            } else if (degradationLevel === 'moderate') {
                issues.push({
                    type: 'system',
                    level: 'warning',
                    message: 'Moderate system degradation detected',
                    source: 'degradation',
                    affected_components: this.degradationStatus.affected_components,
                    recommendations: this.degradationStatus.recommendations
                });
                if (overallStatus === 'ok') overallStatus = 'degraded';
            } else if (degradationLevel === 'minor') {
                issues.push({
                    type: 'system',
                    level: 'info',
                    message: 'Minor system degradation detected',
                    source: 'degradation',
                    affected_components: this.degradationStatus.affected_components,
                    recommendations: this.degradationStatus.recommendations
                });
            }
        }
        
        // Analyze circuit breaker status
        if (this.circuitStatus && !this.circuitStatus.error) {
            if (this.circuitStatus.circuits) {
                Object.entries(this.circuitStatus.circuits).forEach(([name, circuit]) => {
                    if (circuit.state === 'OPEN') {
                        issues.push({
                            type: 'circuit',
                            level: 'critical',
                            message: `${name} circuit breaker is open`,
                            source: 'circuit',
                            detail: `Circuit is open, blocking requests to ${name}`
                        });
                        overallStatus = 'critical';
                    } else if (circuit.state === 'HALF_OPEN') {
                        issues.push({
                            type: 'circuit',
                            level: 'warning',
                            message: `${name} circuit breaker is half-open`,
                            source: 'circuit',
                            detail: `Circuit is testing ${name} service recovery`
                        });
                        if (overallStatus === 'ok') overallStatus = 'degraded';
                    }
                });
            }
        }
        
        // Analyze system metrics
        if (this.systemMetrics && !this.systemMetrics.error) {
            const { cpu, memory, disk } = this.systemMetrics;
            
            // Check CPU usage
            if (cpu.percent > 90) {
                issues.push({
                    type: 'resource',
                    level: 'critical',
                    message: `High CPU usage: ${cpu.percent.toFixed(1)}%`,
                    source: 'metrics',
                    detail: 'System CPU utilization is critically high'
                });
                if (overallStatus === 'ok') overallStatus = 'degraded';
            } else if (cpu.percent > 80) {
                issues.push({
                    type: 'resource',
                    level: 'warning',
                    message: `High CPU usage: ${cpu.percent.toFixed(1)}%`,
                    source: 'metrics',
                    detail: 'System CPU utilization is elevated'
                });
            }
            
            // Check memory usage
            if (memory.percent > 90) {
                issues.push({
                    type: 'resource',
                    level: 'critical',
                    message: `High memory usage: ${memory.percent.toFixed(1)}%`,
                    source: 'metrics',
                    detail: 'System memory utilization is critically high'
                });
                if (overallStatus === 'ok') overallStatus = 'degraded';
            } else if (memory.percent > 80) {
                issues.push({
                    type: 'resource',
                    level: 'warning',
                    message: `High memory usage: ${memory.percent.toFixed(1)}%`,
                    source: 'metrics',
                    detail: 'System memory utilization is elevated'
                });
            }
            
            // Check disk usage
            if (disk.percent > 90) {
                issues.push({
                    type: 'resource',
                    level: 'critical',
                    message: `High disk usage: ${disk.percent.toFixed(1)}%`,
                    source: 'metrics',
                    detail: 'System disk utilization is critically high'
                });
                if (overallStatus === 'ok') overallStatus = 'degraded';
            } else if (disk.percent > 80) {
                issues.push({
                    type: 'resource',
                    level: 'warning',
                    message: `High disk usage: ${disk.percent.toFixed(1)}%`,
                    source: 'metrics',
                    detail: 'System disk utilization is elevated'
                });
            }
        }
        
        // Sort issues by severity
        const severityOrder = { critical: 0, warning: 1, info: 2 };
        issues.sort((a, b) => severityOrder[a.level] - severityOrder[b.level]);
        
        return {
            healthy: overallStatus === 'ok',
            overallStatus: overallStatus,
            degradationLevel: this.degradationStatus?.overall_level || 'unknown',
            issues: issues,
            affectedComponents: this.degradationStatus?.affected_components || [],
            healthyComponents: this.degradationStatus?.healthy_components || [],
            totalComponents: this.degradationStatus?.total_components || 0,
            recommendations: this.degradationStatus?.recommendations || [],
            mitigationActions: this.degradationStatus?.mitigation_actions || [],
            systemMetrics: this.systemMetrics,
            lastUpdate: this.lastUpdate
        };
    }
}

// Create global instance
const systemMonitor = new SystemMonitor();

// Export for use in other modules
export { systemMonitor, SystemMonitor };

// Auto-start monitoring when DOM is ready and Alpine is initialized
if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // Wait for Alpine to be initialized before starting monitoring
        const waitForAlpine = setInterval(() => {
            if (window.Alpine && window.Alpine.store && window.Alpine.store('monitoring')) {
                clearInterval(waitForAlpine);
                
                // Get the monitoring store
                const monitoringStore = window.Alpine.store('monitoring');
                
                // Add callback to update Alpine store
                systemMonitor.addCallback((data) => {
                    // Update the monitoring store with comprehensive data
                    monitoringStore.degradation = data.degradation;
                    monitoringStore.circuit = data.circuit;
                    monitoringStore.metrics = data.metrics;
                    monitoringStore.healthSummary = systemMonitor.getHealthSummary();
                    monitoringStore.lastUpdate = data.lastUpdate;
                    
                    // Update detailed analysis data
                    monitoringStore.healthStatus = monitoringStore.healthSummary?.overallStatus || 'unknown';
                    monitoringStore.degradationLevel = data.degradation?.overall_level || 'none';
                    monitoringStore.circuitBreakerStatus = data.circuit?.overall_status || 'unknown';
                    monitoringStore.systemMetrics = {
                        cpu: systemMonitor.getSystemMetrics()?.cpu?.percent || 0,
                        memory: systemMonitor.getSystemMetrics()?.memory?.percent || 0,
                        disk: systemMonitor.getSystemMetrics()?.disk?.percent || 0
                    };
                    monitoringStore.healthSummary = monitoringStore.healthSummary || {
                        healthy: 0,
                        degraded: 0,
                        critical: 0
                    };
                    monitoringStore.degradationAnalysis = systemMonitor.getDegradationAnalysis();
                    monitoringStore.circuitAnalysis = systemMonitor.getCircuitAnalysis();
                    monitoringStore.resourceAnalysis = systemMonitor.getResourceAnalysis();
                });
                
                // Start monitoring with 30-second intervals
                systemMonitor.startMonitoring(30000);
                
                console.log('✅ Degradation monitoring started successfully');
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(() => {
            clearInterval(waitForAlpine);
            console.warn('⚠️ Alpine store not found, starting monitoring anyway');
            systemMonitor.startMonitoring(30000);
        }, 5000);
    });
}
