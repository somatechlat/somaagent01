/**
 * Infrastructure Dashboard Controller
 * Manages data loading and polling logic for the infrastructure dashboard.
 */

import { apiClient } from '../services/api-client.js';

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number | null;
  details: Record<string, any> | null;
  error: string | null;
}

export interface InfrastructureHealth {
  overall_status: string;
  timestamp: string;
  duration_ms: number;
  services: ServiceHealth[];
}

export interface RateLimitPolicy {
  id: string;
  key: string;
  description: string;
  limit: number;
  window_seconds: number;
  window_display: string;
  policy: 'HARD' | 'SOFT' | 'NONE';
  tier_overrides: Record<string, number>;
  is_active: boolean;
}

export interface DegradationStatus {
  overall_level: string;
  affected_components: string[];
  healthy_components: string[];
  total_components: number;
  timestamp: number;
  recommendations: string[];
  mitigation_actions: string[];
}

export interface ComponentHealth {
  name: string;
  healthy: boolean;
  response_time: number;
  error_rate: number;
  degradation_level: string;
  circuit_state: string;
  last_check: number;
}

export interface ServiceDependency {
  service: string;
  depends_on: string[];
  depended_by: string[];
}

export interface HistoryRecord {
  timestamp: number;
  component_name: string;
  degradation_level: string;
  healthy: boolean;
  response_time: number;
  error_rate: number;
  event_type: string;
}

// Material Symbol names for each service
export const SERVICE_ICONS: Record<string, string> = {
  postgresql: 'database',
  redis: 'bolt',
  kafka: 'mail',
  flink: 'stream',
  temporal: 'schedule',
  qdrant: 'psychology',
  keycloak: 'lock',
  lago: 'payments',
  somabrain: 'neurology',
  whisper: 'mic',
  kokoro: 'volume_up',
};

export interface InfraDashboardData {
  health: InfrastructureHealth | null;
  rateLimits: RateLimitPolicy[];
  degradation: DegradationStatus | null;
  components: ComponentHealth[];
  dependencies: ServiceDependency[];
  history: HistoryRecord[];
  loading: boolean;
  refreshing: boolean;
  lastRefresh: Date | null;
}

export interface InfraDashboardHost extends InfraDashboardData {
  requestUpdate(): void;
}

export class InfraDashboardController {
  private host: InfraDashboardHost;
  private pollInterval: number | null = null;

  constructor(host: InfraDashboardHost) {
    this.host = host;
  }

  connect(): void {
    this.fetchData();
    this.startPolling();
  }

  disconnect(): void {
    this.stopPolling();
  }

  startPolling(): void {
    this.stopPolling();
    this.pollInterval = window.setInterval(() => this.fetchHealth(), 30000);
  }

  stopPolling(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  async fetchData(): Promise<void> {
    this.host.loading = true;
    await Promise.all([this.fetchHealth(), this.fetchRateLimits(), this.fetchDegradation()]);
    this.host.loading = false;
  }

  async fetchHealth(): Promise<void> {
    try {
      this.host.refreshing = true;
      this.host.health = await apiClient.get<InfrastructureHealth>('/observability/infrastructure/health');
      this.host.lastRefresh = new Date();
    } catch (err) {
      console.error('Health fetch failed:', err);
    } finally {
      this.host.refreshing = false;
    }
  }

  async fetchRateLimits(): Promise<void> {
    try {
      const data = await apiClient.get<{ limits?: RateLimitPolicy[] }>('/core/infrastructure/ratelimits');
      this.host.rateLimits = data.limits || [];
    } catch (err) {
      console.error('Rate limits fetch failed:', err);
    }
  }

  async fetchDegradation(): Promise<void> {
    try {
      const [statusData, componentsData, historyData] = await Promise.all([
        apiClient.get<DegradationStatus>('/core/infrastructure/degradation/status'),
        apiClient.get<ComponentHealth[]>('/core/infrastructure/degradation/components'),
        apiClient.get<HistoryRecord[]>('/core/infrastructure/degradation/history?limit=50'),
      ]);
      this.host.degradation = statusData;
      this.host.components = componentsData;
      this.host.history = historyData;
    } catch (err) {
      console.error('Degradation fetch failed:', err);
    }
  }

  async seedRateLimits(): Promise<void> {
    try {
      await apiClient.post('/core/infrastructure/ratelimits/seed', {});
      await this.fetchRateLimits();
    } catch (err) {
      console.error('Seed rate limits failed:', err);
    }
  }
}
