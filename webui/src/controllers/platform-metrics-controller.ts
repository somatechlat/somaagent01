/**
 * Platform Metrics Controller
 * Manages data loading and polling for the platform metrics dashboard.
 */

import { apiClient } from '../services/api-client.js';

export interface MetricSnapshot {
  gateway: {
    requests_total: number;
    requests_per_minute: number;
    latency_p50_ms: number;
    latency_p95_ms: number;
    latency_p99_ms: number;
    error_rate: number;
  };
  llm: {
    calls_total: number;
    input_tokens_total: number;
    output_tokens_total: number;
    avg_latency_ms: number;
    cost_estimate_usd: number;
    models: Record<string, { calls: number; tokens: number }>;
  };
  tools: {
    executions_total: number;
    success_rate: number;
    avg_duration_ms: number;
    by_tool: Record<string, { calls: number; success_rate: number; avg_ms: number }>;
  };
  memory: {
    operations_total: number;
    wal_lag_seconds: number;
    persistence_avg_ms: number;
    policy_decisions: number;
  };
  system: {
    uptime_seconds: number;
    cpu_percent: number;
    memory_bytes: number;
  };
}

export interface SLAStatus {
  name: string;
  target: number;
  actual: number;
  status: 'ok' | 'warning' | 'critical';
}

export interface PlatformMetricsData {
  metrics: MetricSnapshot | null;
  sla: SLAStatus[];
  loading: boolean;
  lastRefresh: Date | null;
}

export interface PlatformMetricsHost extends PlatformMetricsData {
  requestUpdate(): void;
}

export class PlatformMetricsController {
  private host: PlatformMetricsHost;
  private pollInterval: number | null = null;

  constructor(host: PlatformMetricsHost) {
    this.host = host;
  }

  connect(): void {
    this.fetchMetrics();
    this.startPolling();
  }

  disconnect(): void {
    this.stopPolling();
  }

  startPolling(): void {
    this.stopPolling();
    this.pollInterval = window.setInterval(() => this.fetchMetrics(), 30000);
  }

  stopPolling(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  async fetchMetrics(): Promise<void> {
    try {
      const [metricsData, slaData] = await Promise.all([
        apiClient.get<MetricSnapshot>('/core/observability/snapshot'),
        apiClient.get<SLAStatus[]>('/core/observability/sla'),
      ]);

      this.host.metrics = metricsData;
      this.host.sla = slaData;
      this.host.lastRefresh = new Date();
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      this.host.metrics = null;
      this.host.sla = [];
    } finally {
      this.host.loading = false;
      this.host.requestUpdate();
    }
  }
}
