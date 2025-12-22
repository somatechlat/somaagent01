/**
 * SomaStack UI - Status Indicator Component
 * Version: 1.0.0
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('statusIndicator', (config = {}) => ({
    service: config.service || '',
    showTooltip: false,
    
    get status() {
      return Alpine.store('status').getService(this.service);
    },
    
    get health() {
      return this.status.health;
    },
    
    get dotClass() {
      return `status__dot--${this.health}`;
    },
    
    get isPulsing() {
      return this.health === 'healthy';
    },
    
    formatTime(date) {
      if (!date) return 'Never';
      
      const now = new Date();
      const diff = now - new Date(date);
      
      if (diff < 60000) {
        return 'Just now';
      }
      if (diff < 3600000) {
        const mins = Math.floor(diff / 60000);
        return `${mins}m ago`;
      }
      if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
      }
      
      return new Date(date).toLocaleString();
    },
    
    get lastCheckedFormatted() {
      return this.formatTime(this.status.lastChecked);
    },
    
    get latency() {
      return this.status.latencyMs;
    },
    
    get details() {
      return this.status.details || {};
    },
    
    refresh() {
      Alpine.store('status').checkHealth(this.service);
    }
  }));
});
