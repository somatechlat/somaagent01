/**
 * Phase 3: Health Banner Component
 * Displays memory WAL lag and system health alerts
 */

import { API } from "/static/config.js";

class HealthBanner {
    constructor(container) {
        this.container = container;
        this.currentHealth = {};
        this.lastCheck = 0;
        
        // Health thresholds
        this.thresholds = {
            wal_lag_warning: 10,      // seconds
            wal_lag_critical: 30,     // seconds
            outbox_warning: 50,       // pending messages
            outbox_critical: 100      // pending messages
        };
        
        this.init();
    }
    
    init() {
        this.createBanner();
        this.startHealthCheck();
        
        // Listen for visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // no-op; no polling to stop
            } else {
                // Trigger a one-shot refresh when tab becomes visible
                this.performHealthCheck();
            }
        });
    }
    
    createBanner() {
        const banner = document.createElement('div');
        banner.id = 'memory-health-banner';
        banner.className = 'memory-health-banner hidden';
        banner.innerHTML = `
            <div class="health-content">
                <div class="health-icon">
                    <span class="icon-indicator"></span>
                </div>
                <div class="health-message">
                    <span class="health-text"></span>
                    <span class="health-details"></span>
                </div>
                <div class="health-actions">
                    <button class="health-refresh">Refresh</button>
                    <button class="health-dismiss">×</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(banner);
        this.bannerElement = banner;
        
        // Event listeners
        banner.querySelector('.health-refresh').addEventListener('click', () => {
            this.performHealthCheck();
        });
        
        banner.querySelector('.health-dismiss').addEventListener('click', () => {
            this.hideBanner();
        });
    }
    
    async startHealthCheck() {
        // One-shot initial check; no periodic polling (SSE-only directive)
        await this.performHealthCheck();
    }
    
    async performHealthCheck() {
        try {
            const response = await fetch(`${API.BASE}${API.HEALTH}`);
            const health = await response.json();
            
            this.currentHealth = health;
            this.lastCheck = Date.now();
            
            const memoryIssues = this.analyzeMemoryHealth(health);
            
            if (memoryIssues.length > 0) {
                this.showBanner(memoryIssues[0]); // Show most severe
            } else {
                this.hideBanner();
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.showBanner({
                level: 'error',
                message: 'Health check unavailable',
                details: `Connection error: ${error.message}`
            });
        }
    }
    
    analyzeMemoryHealth(health) {
        const issues = [];
        
        // Check WAL lag
        if (health.components?.memory_wal_lag) {
            const lag = health.components.memory_wal_lag.lag_seconds;
            if (lag >= this.thresholds.wal_lag_critical) {
                issues.push({
                    level: 'critical',
                    message: 'Memory sync critical',
                    details: `WAL lag: ${lag.toFixed(1)}s (exceeds ${this.thresholds.wal_lag_critical}s)`
                });
            } else if (lag >= this.thresholds.wal_lag_warning) {
                issues.push({
                    level: 'warning',
                    message: 'Memory sync delayed',
                    details: `WAL lag: ${lag.toFixed(1)}s`
                });
            }
        }
        
        // Check outbox backlog
        if (health.components?.memory_write_outbox) {
            const pending = health.components.memory_write_outbox.pending;
            if (pending >= this.thresholds.outbox_critical) {
                issues.push({
                    level: 'critical',
                    message: 'Memory backlog critical',
                    details: `${pending} pending writes`
                });
            } else if (pending >= this.thresholds.outbox_warning) {
                issues.push({
                    level: 'warning',
                    message: 'Memory backlog elevated',
                    details: `${pending} pending writes`
                });
            }
        }
        
        // Check component health
        const memoryComponents = ['memory_write_outbox', 'memory_replicator', 'memory_dlq'];
        memoryComponents.forEach(component => {
            if (health.components?.[component]?.status === 'down') {
                issues.push({
                    level: 'error',
                    message: `${component} unavailable`,
                    details: health.components[component].detail || 'Service down'
                });
            } else if (health.components?.[component]?.status === 'degraded') {
                issues.push({
                    level: 'warning',
                    message: `${component} degraded`,
                    details: health.components[component].detail || 'Performance issues'
                });
            }
        });
        
        return issues.sort((a, b) => {
            const severity = { critical: 3, error: 2, warning: 1 };
            return (severity[b.level] || 0) - (severity[a.level] || 0);
        });
    }
    
    showBanner(issue) {
        if (!this.bannerElement) return;
        
        const banner = this.bannerElement;
        const icon = banner.querySelector('.icon-indicator');
        const message = banner.querySelector('.health-text');
        const details = banner.querySelector('.health-details');
        
        // Set content
        message.textContent = issue.message;
        details.textContent = issue.details;
        
        // Set styling based on level
        banner.className = `memory-health-banner ${issue.level}`;
        icon.textContent = this.getIcon(issue.level);
        
        // Show banner
        banner.classList.remove('hidden');
    }
    
    hideBanner() {
        if (this.bannerElement) {
            this.bannerElement.classList.add('hidden');
        }
    }
    
    getIcon(level) {
        const icons = {
            critical: '⚠️',
            error: '❌',
            warning: '⚠️'
        };
        return icons[level] || 'ℹ️';
    }
    
    // API for other components
    getCurrentHealth() {
        return this.currentHealth;
    }
    
    forceHealthCheck() {
        return this.performHealthCheck();
    }
}

// CSS for health banner
const healthStyles = `
.memory-health-banner {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    padding: 12px 16px;
    font-size: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

.memory-health-banner.hidden {
    transform: translateY(-100%);
    opacity: 0;
}

.memory-health-banner.critical {
    background: #fee;
    color: #c53030;
    border-bottom: 2px solid #e53e3e;
}

.memory-health-banner.error {
    background: #fed7d7;
    color: #c53030;
}

.memory-health-banner.warning {
    background: #fffbeb;
    color: #b7791f;
}

.health-content {
    display: flex;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
    gap: 12px;
}

.health-icon {
    flex-shrink: 0;
}

.health-message {
    flex: 1;
    min-width: 0;
}

.health-text {
    font-weight: 600;
    margin-right: 8px;
}

.health-details {
    font-size: 12px;
    opacity: 0.8;
}

.health-actions {
    display: flex;
    gap: 8px;
    align-items: center;
}

.health-actions button {
    background: transparent;
    border: 1px solid currentColor;
    color: inherit;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
}

.health-actions button:hover {
    background: rgba(0,0,0,0.1);
}

@media (max-width: 768px) {
    .memory-health-banner {
        padding: 8px 12px;
        font-size: 12px;
    }
    
    .health-content {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }
}
`;

// Inject styles
if (!document.getElementById('memory-health-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'memory-health-styles';
    styleSheet.textContent = healthStyles;
    document.head.appendChild(styleSheet);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize health banner if UI is loaded
    if (typeof window !== 'undefined') {
        window.memoryHealthBanner = new HealthBanner(document.body);
    }
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HealthBanner };
}