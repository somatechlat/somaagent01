/**
 * Role Badge Component
 * Displays user role with icon and color.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Reusable across views
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

const ROLE_CONFIG: Record<string, { icon: string; label: string; color: string; bg: string }> = {
    saas_admin: { icon: '🔴', label: 'SAAS Admin', color: '#dc2626', bg: '#fef2f2' },
    sysadmin: { icon: '🟠', label: 'SysAdmin', color: '#f97316', bg: '#fff7ed' },
    tenant_sysadmin: { icon: '🟠', label: 'Tenant SysAdmin', color: '#f97316', bg: '#fff7ed' },
    tenant_admin: { icon: '🟡', label: 'Tenant Admin', color: '#eab308', bg: '#fefce8' },
    admin: { icon: '🟡', label: 'Admin', color: '#eab308', bg: '#fefce8' },
    agent_owner: { icon: '🟢', label: 'Agent Owner', color: '#22c55e', bg: '#f0fdf4' },
    agent_operator: { icon: '🟢', label: 'Operator', color: '#22c55e', bg: '#f0fdf4' },
    developer: { icon: '🔵', label: 'Developer', color: '#3b82f6', bg: '#eff6ff' },
    trainer: { icon: '🟣', label: 'Trainer', color: '#a855f7', bg: '#faf5ff' },
    user: { icon: '⚪', label: 'User', color: '#6b7280', bg: '#f9fafb' },
    viewer: { icon: '⚫', label: 'Viewer', color: '#374151', bg: '#f3f4f6' },
};

@customElement('saas-role-badge')
export class SaasRoleBadge extends LitElement {
    static styles = css`
    :host {
      display: inline-flex;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 4px 10px;
      border-radius: var(--saas-radius-full, 9999px);
      font-size: var(--saas-text-xs, 11px);
      font-weight: 600;
      white-space: nowrap;
    }

    .badge.size-sm {
      padding: 2px 8px;
      font-size: 10px;
    }

    .badge.size-md {
      padding: 4px 10px;
      font-size: var(--saas-text-xs, 11px);
    }

    .badge.size-lg {
      padding: 6px 14px;
      font-size: var(--saas-text-sm, 13px);
    }

    .icon {
      font-size: inherit;
    }
  `;

    @property({ type: String }) role = 'user';
    @property({ type: String }) size: 'sm' | 'md' | 'lg' = 'md';
    @property({ type: Boolean }) showIcon = true;

    render() {
        const config = ROLE_CONFIG[this.role] || ROLE_CONFIG['user'];

        return html`
      <span class="badge size-${this.size}"
            style="background: ${config.bg}; color: ${config.color};">
        ${this.showIcon ? html`<span class="icon">${config.icon}</span>` : ''}
        ${config.label}
      </span>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-role-badge': SaasRoleBadge;
    }
}
