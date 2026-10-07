/**
 * SOMA Entity Views - Reusable views using EntityManager
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
      background: var(--soma-bg-page, #f5f5f5);
      font-family: var(--soma-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
    }

    .sidebar {
      width: 260px;
      background: var(--soma-bg-card, #ffffff);
      border-right: 1px solid var(--soma-border-light, #e0e0e0);
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

@customElement('soma-users-view')
export class SomaUsersView extends BaseEntityView {
    render() {
        return html`
      <aside class="sidebar">
        <soma-sidebar active-route="/admin/users"></soma-sidebar>
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

@customElement('soma-agents-view')
export class SomaAgentsView extends BaseEntityView {
    render() {
        return html`
      <aside class="sidebar">
        <soma-sidebar active-route="/admin/agents"></soma-sidebar>
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
        'soma-users-view': SomaUsersView;
        'soma-agents-view': SomaAgentsView;
    }
}
