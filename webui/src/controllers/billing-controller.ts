/**
 * Billing Controller
 * Manages data loading for the SaaS billing dashboard.
 */

import { apiClient } from '../services/api-client.js';

export interface BillingMetrics {
  mrr: number;
  mrr_growth: number;
  arpu: number;
  churn_rate: number;
  total_tenants: number;
  paid_tenants: number;
}

export interface Invoice {
  number: string;
  amount_cents: number;
  status: 'paid' | 'pending' | 'overdue' | 'void';
  created_at: string;
}

export interface TierRevenue {
  tier: string;
  mrr: number;
  count: number;
  percentage: number;
}

export interface BillingControllerData {
  _metrics: BillingMetrics;
  _tierRevenue: TierRevenue[];
  _invoices: Invoice[];
  _isLoading: boolean;
  _error: string;
}

export interface BillingControllerHost extends BillingControllerData {
  requestUpdate(): void;
}

export class BillingController {
  private host: BillingControllerHost;

  constructor(host: BillingControllerHost) {
    this.host = host;
  }

  connect(): void {
    this.loadData();
  }

  disconnect(): void {
    // No polling to stop currently.
  }

  async loadData(): Promise<void> {
    this.host._isLoading = true;
    this.host._error = '';
    this.host.requestUpdate();

    try {
      const response = (await apiClient.get('/aaas/billing/')) as {
        metrics?: BillingMetrics;
        revenue_by_tier?: TierRevenue[];
        recent_invoices?: Invoice[];
      };

      if (response.metrics) {
        this.host._metrics = response.metrics;
      }
      if (response.revenue_by_tier) {
        this.host._tierRevenue = response.revenue_by_tier;
      }
      if (response.recent_invoices) {
        this.host._invoices = response.recent_invoices;
      }
    } catch {
      this.host._error = 'Failed to load billing data';
    } finally {
      this.host._isLoading = false;
      this.host.requestUpdate();
    }
  }
}
