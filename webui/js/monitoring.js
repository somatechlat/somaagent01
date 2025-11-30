/**
 * Monitoring (minimal, same-origin only)
 * Endpoints used:
 *   - /v1/health
 *   - /v1/somabrain/health
 */

import { fetchApi } from "./api.js";

class SystemMonitor {
  constructor() {
    this.pollingInterval = null;
    this.pollingActive = false;
    this.healthStatus = null;
    this.lastUpdate = null;
    this.callbacks = new Set();
    this.errorCount = 0;
    this.maxRetries = 3;
    this.retryDelay = 5000;
    this._somabrainErrorLogged = false;
  }

  startMonitoring(interval = 30000) {
    if (this.pollingActive) return;
    this.pollingActive = true;
    this.pollingInterval = setInterval(() => this.updateAllStatus(), interval);
    this.updateAllStatus();
  }

  stopMonitoring() {
    if (!this.pollingActive) return;
    this.pollingActive = false;
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  addCallback(cb) { this.callbacks.add(cb); }
  removeCallback(cb) { this.callbacks.delete(cb); }

  notifyCallbacks() {
    this.callbacks.forEach(cb => {
      try {
        cb({ health: this.healthStatus, lastUpdate: this.lastUpdate });
      } catch (e) {
        console.error('Error in monitoring callback:', e);
      }
    });
  }

  async updateAllStatus() {
    try {
      await Promise.all([
        this.updateHealthStatus(),
        this.checkSomabrainHealth()
      ]);
      this.lastUpdate = new Date();
      this.errorCount = 0;
      this.notifyCallbacks();
    } catch (error) {
      console.error('Error updating monitoring status:', error);
      this.errorCount++;
      if (this.errorCount <= this.maxRetries) {
        const delay = this.retryDelay * Math.pow(2, this.errorCount - 1);
        setTimeout(() => this.updateAllStatus(), delay);
      } else {
        this.stopMonitoring();
      }
    }
  }

  async updateHealthStatus() {
    try {
      const response = await fetchApi('/v1/health');
      if (response.ok) {
        const data = await response.json();
        this.healthStatus = { ...data, timestamp: new Date().toISOString() };
        this._updateSomabrainFromHealth(data);
      } else {
        this.healthStatus = { error: 'Failed to fetch health status', status: 'error', timestamp: new Date().toISOString() };
        this._setSomabrainState('unknown', 'SomaBrain status unknown', 'SomaBrain status is unknown.');
      }
    } catch (error) {
      this.healthStatus = { error: 'Failed to fetch health status', status: 'error', timestamp: new Date().toISOString() };
      this._setSomabrainState('unknown', 'SomaBrain status unknown', 'SomaBrain status is unknown.');
    }
  }

  async checkSomabrainHealth() {
    const updateStore = (state, tooltip, banner) => this._setSomabrainState(state, tooltip, banner);
    try {
      const response = await fetchApi('/v1/somabrain/health', { method: 'GET', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin' });
      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error(`SomaBrain health check failed: ${response.status}`);
      }
      const data = await response.json();
      if (data?.ready === true) {
        updateStore('normal', 'SomaBrain online', '');
      } else {
        updateStore('degraded', 'SomaBrain degraded – limited memory retrieval', 'Somabrain responses are delayed. Retrieval snippets will be limited until connectivity stabilizes.');
      }
      return data;
    } catch (error) {
      if (!this._somabrainErrorLogged) {
        console.warn('Somabrain health probe skipped/failed:', error?.message || error);
        this._somabrainErrorLogged = true;
      }
      updateStore('down', 'SomaBrain offline – degraded mode', 'Somabrain is offline. The agent will answer using chat history only until memories sync again.');
      return null;
    }
  }

  _updateSomabrainFromHealth(healthData) {
    if (!globalThis.Alpine?.store('somabrain')) return;
    if (healthData.status === 'ok') {
      this._setSomabrainState('normal', 'SomaBrain online', '');
    } else if (healthData.status === 'degraded') {
      this._setSomabrainState('degraded', 'SomaBrain degraded – limited memory retrieval', 'Somabrain responses are delayed. Retrieval snippets will be limited until connectivity stabilizes.');
    } else {
      this._setSomabrainState('down', 'SomaBrain offline – degraded mode', 'Somabrain is offline. The agent will answer using chat history only until memories sync again.');
    }
  }

  _setSomabrainState(state, tooltip, banner) {
    const store = globalThis.Alpine?.store('somabrain');
    if (!store) return;
    store.state = state;
    store.tooltip = tooltip;
    store.banner = banner;
    store.lastUpdated = Date.now();
  }
}

export const systemMonitor = new SystemMonitor();
