/**
 * SomaStack UI - Stats Card Component
 * Version: 1.0.0
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('statsCard', (config = {}) => ({
    value: config.value || 0,
    previousValue: config.previousValue || null,
    label: config.label || '',
    icon: config.icon || 'chart',
    format: config.format || 'number',
    precision: config.precision || 1,
    
    init() {
      // Animate value on load if desired
    },
    
    get formattedValue() {
      return this.formatNumber(this.value);
    },
    
    formatNumber(num) {
      if (num === null || num === undefined) return '—';
      
      if (this.format === 'percent') {
        return `${num.toFixed(this.precision)}%`;
      }
      
      if (this.format === 'currency') {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(num);
      }
      
      if (this.format === 'duration') {
        return this.formatDuration(num);
      }
      
      // Default number formatting with K/M/B suffixes
      if (Math.abs(num) >= 1e9) {
        return (num / 1e9).toFixed(this.precision) + 'B';
      }
      if (Math.abs(num) >= 1e6) {
        return (num / 1e6).toFixed(this.precision) + 'M';
      }
      if (Math.abs(num) >= 1e3) {
        return (num / 1e3).toFixed(this.precision) + 'K';
      }
      
      return num.toLocaleString();
    },
    
    formatDuration(ms) {
      if (ms < 1000) return `${ms}ms`;
      if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
      if (ms < 3600000) return `${Math.floor(ms / 60000)}m`;
      return `${(ms / 3600000).toFixed(1)}h`;
    },
    
    get trend() {
      if (this.previousValue === null || this.previousValue === 0) {
        return { direction: 'neutral', percent: 0 };
      }
      
      const change = ((this.value - this.previousValue) / this.previousValue) * 100;
      
      return {
        direction: change > 0 ? 'up' : change < 0 ? 'down' : 'neutral',
        percent: Math.abs(change).toFixed(1)
      };
    },
    
    get trendClass() {
      const dir = this.trend.direction;
      return {
        'stats-card__trend--up': dir === 'up',
        'stats-card__trend--down': dir === 'down',
        'stats-card__trend--neutral': dir === 'neutral'
      };
    },
    
    get trendIcon() {
      const dir = this.trend.direction;
      if (dir === 'up') return '↑';
      if (dir === 'down') return '↓';
      return '→';
    },
    
    get trendPercent() {
      return this.trend.percent;
    },
    
    setValue(newValue, newPreviousValue = null) {
      if (newPreviousValue !== null) {
        this.previousValue = newPreviousValue;
      } else {
        this.previousValue = this.value;
      }
      this.value = newValue;
    }
  }));
});
