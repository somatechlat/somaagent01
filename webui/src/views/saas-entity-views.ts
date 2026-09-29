/**
 * SAAS Entity Views - Reusable views using EntityManager
 * 
 * VIBE COMPLIANT:
 * - One component per entity type using EntityManager pattern
 * - Full 78-permission granularity preserved
 * - Lit 3.x implementation
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/entity-manager.js';

// Base view with shared styles and permission loading
abstract class BaseEntityView extends LitElement {
    static styles = css`
    :host {
      display: flex;
      height: 100vh;
      background: var(--saas-bg-page, #f5f5f5);
      font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
    }

    .sidebar {
      width: 260px;
      background: var(--saas-bg-card, #ffffff);
      border-right: 1px solid var(--saas-border-light, #e0e0e0);
      flex-shrink: 0;
    }

    .main {
      flex: 1;
      padding: 32px;
      overflow-y: auto;
    }
  `;

    @state() protected permissions: string[] = [];

    async connectedCallback() {
        super.connectedCallback();
        await this.loadPermissions();
    }

    private async loadPermissions() {
        try {
            const response = await apiClient.get('/auth/me') as { permissions?: string[] };
            this.permissions = response.permissions || [];
        } catch {
            this.permissions = [];
        }
    }
}

@customElement('saas-tenants-view')
export class SaasTenantsView extends BaseEntityView {
    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/saas/tenants"></saas-sidebar>
      </aside>
      <main class="main">
        <entity-manager
          entity="tenant"
          api-base="/api/v2/aaas"
          .permissions=${this.permissions}
        ></entity-manager>
      </main>
    `;
    }
}

@customElement('saas-users-view')
export class SaasUsersView extends BaseEntityView {
    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/admin/users"></saas-sidebar>
      </aside>
      <main class="main">
        <entity-manager
          entity="user"
          api-base="/api/v2/aaas/admin"
          .permissions=${this.permissions}
        ></entity-manager>
      </main>
    `;
    }
}

@customElement('saas-agents-view')
export class SaasAgentsView extends BaseEntityView {
    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/admin/agents"></saas-sidebar>
      </aside>
      <main class="main">
        <entity-manager
          entity="agent"
          api-base="/api/v2/aaas/admin"
          .permissions=${this.permissions}
        ></entity-manager>
      </main>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenants-view': SaasTenantsView;
        'saas-users-view': SaasUsersView;
        'saas-agents-view': SaasAgentsView;
        }
}
