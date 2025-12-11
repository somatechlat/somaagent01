/**
 * Agent Control Panel Component
 * Implements restart/pause/resume controls and cognitive state display
 * Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6
 */

import { fetchApi } from '../../core/api/client.js';
import { ENDPOINTS } from '../../core/api/endpoints.js';

/**
 * Agent Control Panel Alpine Component
 */
export function createAgentControlPanel() {
  return {
    // State
    agentStatus: 'unknown', // running, paused, stopped, error
    cognitiveState: {
      dopamine: 0.5,
      serotonin: 0.5,
      noradrenaline: 0.5,
      acetylcholine: 0.5
    },
    isLoading: false,
    error: null,
    lastUpdate: null,
    pollInterval: null,
    
    // Computed
    get statusColor() {
      const colors = {
        running: 'var(--success)',
        paused: 'var(--warning)',
        stopped: 'var(--text-muted)',
        error: 'var(--error)',
        unknown: 'var(--text-muted)'
      };
      return colors[this.agentStatus] || colors.unknown;
    },
    
    get statusIcon() {
      const icons = {
        running: 'play_circle',
        paused: 'pause_circle',
        stopped: 'stop_circle',
        error: 'error',
        unknown: 'help'
      };
      return icons[this.agentStatus] || icons.unknown;
    },
    
    get canPause() {
      return this.agentStatus === 'running';
    },
    
    get canResume() {
      return this.agentStatus === 'paused';
    },
    
    get canRestart() {
      return this.agentStatus !== 'unknown';
    },
    
    // Lifecycle
    init() {
      this.fetchStatus();
      this.startPolling();
    },
    
    destroy() {
      this.stopPolling();
    },
    
    // Polling
    startPolling(interval = 10000) {
      this.stopPolling();
      this.pollInterval = setInterval(() => this.fetchStatus(), interval);
    },
    
    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }
    },
    
    // API Methods
    async fetchStatus() {
      try {
        const health = await fetchApi(ENDPOINTS.HEALTH);
        this.agentStatus = health.agent_status || 'running';
        this.lastUpdate = new Date();
        this.error = null;
        
        // Fetch cognitive state if available
        await this.fetchCognitiveState();
      } catch (err) {
        this.error = err.message;
        this.agentStatus = 'error';
      }
    },
    
    async fetchCognitiveState() {
      try {
        // Try to fetch neuromodulator state from SomaBrain
        const response = await fetchApi('/v1/cognitive/state');
        if (response && response.neuromodulators) {
          this.cognitiveState = {
            dopamine: response.neuromodulators.dopamine || 0.5,
            serotonin: response.neuromodulators.serotonin || 0.5,
            noradrenaline: response.neuromodulators.noradrenaline || 0.5,
            acetylcholine: response.neuromodulators.acetylcholine || 0.5
          };
        }
      } catch (err) {
        // Cognitive state endpoint may not be available
        console.debug('Cognitive state not available:', err.message);
      }
    },
    
    async pauseAgent() {
      if (!this.canPause) return;
      
      this.isLoading = true;
      try {
        await fetchApi('/v1/agent/pause', { method: 'POST' });
        this.agentStatus = 'paused';
        this.$dispatch('agent:paused');
      } catch (err) {
        this.error = err.message;
      } finally {
        this.isLoading = false;
      }
    },
    
    async resumeAgent() {
      if (!this.canResume) return;
      
      this.isLoading = true;
      try {
        await fetchApi('/v1/agent/resume', { method: 'POST' });
        this.agentStatus = 'running';
        this.$dispatch('agent:resumed');
      } catch (err) {
        this.error = err.message;
      } finally {
        this.isLoading = false;
      }
    },
    
    async restartAgent() {
      if (!this.canRestart) return;
      
      if (!confirm('Are you sure you want to restart the agent? This will interrupt any ongoing tasks.')) {
        return;
      }
      
      this.isLoading = true;
      try {
        await fetchApi('/v1/agent/restart', { method: 'POST' });
        this.agentStatus = 'running';
        this.$dispatch('agent:restarted');
      } catch (err) {
        this.error = err.message;
      } finally {
        this.isLoading = false;
      }
    },
    
    // Helpers
    formatNeuromodulator(value) {
      return Math.round(value * 100) + '%';
    },
    
    getNeuromodulatorColor(value) {
      if (value < 0.3) return 'var(--error)';
      if (value < 0.5) return 'var(--warning)';
      if (value < 0.7) return 'var(--success)';
      return 'var(--accent-primary)';
    },
    
    getNeuromodulatorLabel(key) {
      const labels = {
        dopamine: 'Dopamine (Motivation)',
        serotonin: 'Serotonin (Mood)',
        noradrenaline: 'Noradrenaline (Focus)',
        acetylcholine: 'Acetylcholine (Learning)'
      };
      return labels[key] || key;
    }
  };
}

/**
 * Register Alpine component
 */
export function registerAgentControlPanel() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('agentControlPanel', createAgentControlPanel);
  }
}

export default createAgentControlPanel;
