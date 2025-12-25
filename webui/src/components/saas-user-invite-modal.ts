/**
 * User Invite Modal Component
 * Modal for inviting new users to the tenant.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Django Ninja API integration
 *
 * PERSONAS APPLIED:
 * - 🎨 UX Consultant: Role preview, agent selection
 * - 🔒 Security Auditor: Role permission display
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

interface RoleDefinition {
    code: string;
    label: string;
    icon: string;
    color: string;
    description: string;
    canAccess: string[];
    cannotAccess: string[];
}

interface AgentOption {
    id: string;
    name: string;
    slug: string;
    status: 'active' | 'paused';
}

const ROLES: RoleDefinition[] = [
    {
        code: 'sysadmin',
        label: 'SysAdmin',
        icon: '🟠',
        color: '#f97316',
        description: 'Full tenant access',
        canAccess: ['All modes', 'All agents', 'Billing', 'Settings'],
        cannotAccess: [],
    },
    {
        code: 'admin',
        label: 'Admin',
        icon: '🟡',
        color: '#eab308',
        description: 'Manage users and agents',
        canAccess: ['STD mode', 'ADM mode', 'All agents', 'User management'],
        cannotAccess: ['Billing', 'API keys'],
    },
    {
        code: 'developer',
        label: 'Developer',
        icon: '🔵',
        color: '#3b82f6',
        description: 'Development and debugging',
        canAccess: ['STD mode', 'DEV mode', 'Assigned agents', 'Logs'],
        cannotAccess: ['User management', 'Billing', 'Cognitive settings'],
    },
    {
        code: 'trainer',
        label: 'Trainer',
        icon: '🟣',
        color: '#a855f7',
        description: 'Tune agent behavior',
        canAccess: ['STD mode', 'TRN mode', 'Assigned agents', 'Neuromodulators'],
        cannotAccess: ['User management', 'Billing', 'Debug console'],
    },
    {
        code: 'user',
        label: 'User',
        icon: '⚪',
        color: '#6b7280',
        description: 'Standard agent access',
        canAccess: ['STD mode', 'Assigned agents', 'Chat', 'Memory'],
        cannotAccess: ['Settings', 'User management', 'Billing'],
    },
    {
        code: 'viewer',
        label: 'Viewer',
        icon: '⚫',
        color: '#374151',
        description: 'Read-only access',
        canAccess: ['View chat history', 'View memory'],
        cannotAccess: ['Send messages', 'Settings', 'Any write operations'],
    },
];

@customElement('saas-user-invite-modal')
export class SaasUserInviteModal extends LitElement {
    static styles = css`
    :host {
      display: block;
    }

    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }

    .modal {
      background: var(--saas-bg-card, #ffffff);
      border-radius: var(--saas-radius-lg, 12px);
      width: 100%;
      max-width: 500px;
      max-height: 90vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--saas-spacing-md, 16px) var(--saas-spacing-lg, 24px);
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .modal-title {
      font-size: var(--saas-text-lg, 18px);
      font-weight: 600;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .close-btn {
      background: none;
      border: none;
      font-size: 24px;
      color: var(--saas-text-muted, #999999);
      cursor: pointer;
      padding: 0;
    }

    .modal-content {
      padding: var(--saas-spacing-lg, 24px);
      overflow-y: auto;
    }

    .form-group {
      margin-bottom: var(--saas-spacing-md, 16px);
    }

    .form-label {
      display: block;
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      color: var(--saas-text-primary, #1a1a1a);
      margin-bottom: 4px;
    }

    .form-label .required {
      color: #dc2626;
    }

    .form-input {
      width: 100%;
      padding: 10px 12px;
      background: var(--saas-bg-input, #ffffff);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-base, 14px);
      color: var(--saas-text-primary, #1a1a1a);
      box-sizing: border-box;
    }

    .form-input:focus {
      outline: none;
      border-color: var(--saas-accent, #2563eb);
    }

    .form-error {
      font-size: var(--saas-text-xs, 11px);
      color: #dc2626;
      margin-top: 4px;
    }

    /* Role Selector */
    .role-selector {
      display: flex;
      flex-wrap: wrap;
      gap: var(--saas-spacing-sm, 8px);
      margin-bottom: var(--saas-spacing-md, 16px);
    }

    .role-option {
      padding: 8px 16px;
      border: 2px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-md, 8px);
      background: var(--saas-bg-card, #ffffff);
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .role-option:hover {
      border-color: var(--saas-text-muted, #999999);
    }

    .role-option.selected {
      border-color: var(--saas-accent, #2563eb);
      background: rgba(37, 99, 235, 0.05);
    }

    .role-name {
      font-weight: 500;
    }

    /* Role Preview */
    .role-preview {
      background: var(--saas-bg-surface, #fafafa);
      border-radius: var(--saas-radius-md, 8px);
      padding: var(--saas-spacing-md, 16px);
      margin-bottom: var(--saas-spacing-md, 16px);
    }

    .role-header {
      display: flex;
      align-items: center;
      gap: var(--saas-spacing-sm, 8px);
      margin-bottom: var(--saas-spacing-sm, 8px);
    }

    .role-title {
      font-weight: 600;
      font-size: var(--saas-text-md, 16px);
    }

    .role-desc {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-secondary, #666666);
      margin-bottom: var(--saas-spacing-sm, 8px);
    }

    .access-list {
      font-size: var(--saas-text-xs, 11px);
    }

    .access-list h4 {
      font-weight: 600;
      margin: 4px 0;
    }

    .access-list ul {
      margin: 0;
      padding-left: 20px;
      color: var(--saas-text-secondary, #666666);
    }

    .access-can { color: #22c55e; }
    .access-cannot { color: #dc2626; }

    /* Agent Selection */
    .agent-list {
      max-height: 150px;
      overflow-y: auto;
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-md, 8px);
    }

    .agent-item {
      display: flex;
      align-items: center;
      gap: var(--saas-spacing-sm, 8px);
      padding: var(--saas-spacing-sm, 8px) var(--saas-spacing-md, 16px);
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .agent-item:last-child {
      border-bottom: none;
    }

    .agent-item input {
      margin: 0;
    }

    .agent-name {
      font-size: var(--saas-text-sm, 13px);
    }

    .agent-status {
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-muted, #999999);
    }

    /* Modal Footer */
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: var(--saas-spacing-sm, 8px);
      padding: var(--saas-spacing-md, 16px) var(--saas-spacing-lg, 24px);
      border-top: 1px solid var(--saas-border, #e0e0e0);
    }

    .btn {
      padding: 10px 20px;
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-primary {
      background: var(--saas-accent, #2563eb);
      color: white;
      border: none;
    }

    .btn-primary:hover {
      background: #1d4ed8;
    }

    .btn-primary:disabled {
      background: #93c5fd;
      cursor: not-allowed;
    }

    .btn-secondary {
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
      border: 1px solid var(--saas-border, #e0e0e0);
    }

    .btn-secondary:hover {
      background: var(--saas-bg-surface, #fafafa);
    }
  `;

    @property({ type: Boolean }) open = false;
    @property({ type: Array }) agents: AgentOption[] = [];

    @state() private email = '';
    @state() private selectedRole = 'user';
    @state() private selectedAgents: Set<string> = new Set();
    @state() private submitting = false;
    @state() private error = '';

    private _getSelectedRoleInfo(): RoleDefinition {
        return ROLES.find(r => r.code === this.selectedRole) || ROLES[4];
    }

    private _handleSubmit() {
        if (!this.email || !this.email.includes('@')) {
            this.error = 'Please enter a valid email address';
            return;
        }

        this.submitting = true;
        this.dispatchEvent(new CustomEvent('invite', {
            detail: {
                email: this.email,
                role: this.selectedRole,
                agentIds: Array.from(this.selectedAgents),
            },
            bubbles: true,
            composed: true,
        }));
    }

    private _handleClose() {
        this.email = '';
        this.selectedRole = 'user';
        this.selectedAgents = new Set();
        this.error = '';
        this.dispatchEvent(new CustomEvent('close'));
    }

    private _toggleAgent(agentId: string) {
        const newSet = new Set(this.selectedAgents);
        if (newSet.has(agentId)) {
            newSet.delete(agentId);
        } else {
            newSet.add(agentId);
        }
        this.selectedAgents = newSet;
    }

    render() {
        if (!this.open) return null;

        const roleInfo = this._getSelectedRoleInfo();

        return html`
      <div class="modal-backdrop" @click=${(e: Event) => e.target === e.currentTarget && this._handleClose()}>
        <div class="modal">
          <div class="modal-header">
            <span class="modal-title">Invite New User</span>
            <button class="close-btn" @click=${this._handleClose}>×</button>
          </div>

          <div class="modal-content">
            <div class="form-group">
              <label class="form-label">Email Address <span class="required">*</span></label>
              <input class="form-input" type="email" placeholder="user@example.com"
                     .value=${this.email}
                     @input=${(e: Event) => { this.email = (e.target as HTMLInputElement).value; this.error = ''; }}>
              ${this.error ? html`<div class="form-error">${this.error}</div>` : ''}
            </div>

            <div class="form-group">
              <label class="form-label">Role <span class="required">*</span></label>
              <div class="role-selector">
                ${ROLES.map(role => html`
                  <div class="role-option ${this.selectedRole === role.code ? 'selected' : ''}"
                       @click=${() => this.selectedRole = role.code}>
                    <span class="role-name">${role.icon} ${role.label}</span>
                  </div>
                `)}
              </div>
            </div>

            <div class="role-preview">
              <div class="role-header">
                <span style="font-size: 24px;">${roleInfo.icon}</span>
                <span class="role-title">${roleInfo.label}</span>
              </div>
              <div class="role-desc">${roleInfo.description}</div>
              <div class="access-list">
                <h4 class="access-can">✅ Can access:</h4>
                <ul>
                  ${roleInfo.canAccess.map(item => html`<li>${item}</li>`)}
                </ul>
                ${roleInfo.cannotAccess.length > 0 ? html`
                  <h4 class="access-cannot">❌ Cannot access:</h4>
                  <ul>
                    ${roleInfo.cannotAccess.map(item => html`<li>${item}</li>`)}
                  </ul>
                ` : ''}
              </div>
            </div>

            ${this.selectedRole !== 'sysadmin' && this.agents.length > 0 ? html`
              <div class="form-group">
                <label class="form-label">Agent Access</label>
                <div class="agent-list">
                  ${this.agents.map(agent => html`
                    <label class="agent-item">
                      <input type="checkbox" 
                             ?checked=${this.selectedAgents.has(agent.id)}
                             @change=${() => this._toggleAgent(agent.id)}>
                      <span class="agent-name">${agent.name}</span>
                      <span class="agent-status">(${agent.status})</span>
                    </label>
                  `)}
                </div>
              </div>
            ` : ''}
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click=${this._handleClose}>Cancel</button>
            <button class="btn btn-primary" ?disabled=${this.submitting || !this.email}
                    @click=${this._handleSubmit}>
              ${this.submitting ? 'Sending...' : 'Send Invite'}
            </button>
          </div>
        </div>
      </div>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-user-invite-modal': SaasUserInviteModal;
    }
}
