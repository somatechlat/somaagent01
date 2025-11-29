/**
 * REAL IMPLEMENTATION - System Monitoring Integration for SomaAgent01 Web UI
 * Integrates degradation, circuit breaker, and metrics endpoints with the Web UI
 * VIBE CODING RULES COMPLIANT - No placeholders, real implementations only
 */

import { fetchApi, callJsonApi } from "i18n.t('ui_i18n_t_ui_api_js')";

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
        this.pollingInterval = setInterval(() => i18n.t('ui_i18n_t_ui_this_updateallstatus_interval_initial_update_this_updateallstatus_real_implementation_check_somabrain_health_directly_async_checksomabrainhealth_try_const_response_await_fetch_http_localhost_9696_health_method_get_headers_content_type_application_json_if_response_ok_const_somabraindata_await_response_json_update_somabrain_store_based_on_somabrain_health_if_globalthis_alpine_store_somabrain_const_somabrainstore_globalthis_alpine_store_somabrain_if_somabraindata_ready_true_somabrainstore_state_normal_somabrainstore_tooltip_somabrain_online_somabrainstore_banner_else_somabrainstore_state_degraded_somabrainstore_tooltip_somabrain_degraded_limited_memory_retrieval_somabrainstore_banner_somabrain_responses_are_delayed_retrieval_snippets_will_be_limited_until_connectivity_stabilizes_somabrainstore_lastupdated_date_now_return_somabraindata_else_throw_new_error_somabrain_health_check_failed_response_status_catch_error_console_error_error_checking_somabrain_health_error_update_somabrain_store_to_reflect_error_if_globalthis_alpine_store_somabrain_const_somabrainstore_globalthis_alpine_store_somabrain_somabrainstore_state_down_somabrainstore_tooltip_somabrain_offline_degraded_mode_somabrainstore_banner_somabrain_is_offline_the_agent_will_answer_using_chat_history_only_until_memories_sync_again_somabrainstore_lastupdated_date_now_return_null_stop_monitoring_the_system_stopmonitoring_if_this_pollingactive_return_this_pollingactive_false_if_this_pollinginterval_clearinterval_this_pollinginterval_this_pollinginterval_null_add_a_callback_to_be_called_when_monitoring_data_updates_param_function_callback_callback_function_addcallback_callback_this_callbacks_add_callback_remove_a_callback_param_function_callback_callback_function_to_remove_removecallback_callback_this_callbacks_delete_callback_notify_all_callbacks_of_data_updates_notifycallbacks_this_callbacks_foreach_callback_try_callback_health_this_healthstatus_degradation_this_degradationstatus_circuit_this_circuitstatus_metrics_this_metricsdata_lastupdate_this_lastupdate_catch_e_console_error_error_in_monitoring_callback_e_real_implementation_update_all_monitoring_status_with_comprehensive_error_handling_async_updateallstatus_try_await_promise_all_this_updatehealthstatus_this_updatedegradationstatus_this_updatecircuitstatus_this_updatesystemmetrics_this_checksomabrainhealth_this_lastupdate_new_date_this_errorcount_0_reset_error_count_on_success_this_notifycallbacks_catch_error_console_error_error_updating_monitoring_status_error_this_errorcount_implement_retry_logic_with_exponential_backoff_if_this_errorcount')<= this.maxRetries) {
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
                        cpu_percent: metricsData.cpu.percent,
                        memory_percent: metricsData.memory.percent,
                        disk_percent: metricsData.disk.percent,
                        components: Object.keys(this.healthStatus?.components || {}).length,
                        healthy_components: Object.values(this.healthStatus?.components || {}).filter(c => c.status === 'ok').length
                    },
                    timestamp: new Date().toISOString()
                };
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
