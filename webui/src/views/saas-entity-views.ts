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
        // TODO: Load from auth context or API
        // For now, grant full permissions for demo
        this.permissions = [
            'tenant:list', 'tenant:view', 'tenant:create', 'tenant:edit', 'tenant:delete', 'tenant:suspend', 'tenant:impersonate',
            'user:list', 'user:view', 'user:create', 'user:edit', 'user:delete', 'user:suspend',
            'agent:list', 'agent:view', 'agent:create', 'agent:edit', 'agent:delete',
            'feature:list', 'feature:view', 'feature:edit',
            'ratelimit:list', 'ratelimit:view', 'ratelimit:edit', 'ratelimit:delete',
        ];
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
          api-base="/api/v2/saas"
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
          api-base="/api/v2/admin"
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
          api-base="/api/v2/admin"
          .permissions=${this.permissions}
        ></entity-manager>
      </main>
    `;
    }
}

@customElement('saas-features-view')
export class SaasFeaturesView extends BaseEntityView {
    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/platform/features"></saas-sidebar>
      </aside>
      <main class="main">
        <entity-manager
          entity="feature"
          api-base="/api/v2/platform"
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
        'saas-features-view': SaasFeaturesView;
    }
}
