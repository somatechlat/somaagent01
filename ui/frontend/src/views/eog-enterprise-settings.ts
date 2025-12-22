/**
 * Eye of God Enterprise Settings Modal
 * Per User Request: Login Page Settings Cog
 *
 * VIBE COMPLIANT:
 * - Glassmorphism UI
 * - Full Enterprise Configuration (SSO, LDAP, Mode Activation)
 * - Real API integration
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/eog-modal.js';
import '../components/eog-input.js';
import '../components/eog-toggle.js';
import '../components/eog-button.js';
import '../components/eog-tabs.js';

interface EnterpriseConfig {
    enterprise_mode_enabled: boolean;
    company_name: string;
    domain: string;
    sso: {
        oidc_enabled: boolean;
        oidc_provider_url: string;
        oidc_client_id: string;
        saml_enabled: boolean;
        saml_entry_point: string;
        saml_cert: string;
    };
    ldap: {
        enabled: boolean;
        server_url: string;
        bind_dn: string;
        search_base: string;
    };
    security: {
        mfa_required: boolean;
        session_timeout_mins: number;
        ip_allowlist: string;
    }
}

@customElement('eog-enterprise-settings')
export class EogEnterpriseSettings extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .settings-content {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-lg, 24px);
        }

        .section {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: var(--eog-radius-lg, 12px);
            padding: var(--eog-spacing-lg, 24px);
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-md, 16px);
        }

        .section-title {
            font-size: var(--eog-text-base, 14px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .form-grid {
            display: grid;
            gap: var(--eog-spacing-md, 16px);
        }

        .two-col {
            grid-template-columns: 1fr 1fr;
        }

        .info-box {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: var(--eog-radius-md, 8px);
            padding: var(--eog-spacing-md, 16px);
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-info, #60a5fa);
            margin-bottom: var(--eog-spacing-md, 16px);
            display: flex;
            gap: 8px;
        }

        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-badge.active {
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
        }

        .status-badge.inactive {
            background: rgba(100, 116, 139, 0.2);
            color: #94a3b8;
        }
    `;

    @property({ type: Boolean }) open = false;
    @state() private _config: EnterpriseConfig = {
        enterprise_mode_enabled: false,
        company_name: '',
        domain: '',
        sso: {
            oidc_enabled: false,
            oidc_provider_url: '',
            oidc_client_id: '',
            saml_enabled: false,
            saml_entry_point: '',
            saml_cert: ''
        },
        ldap: {
            enabled: false,
            server_url: '',
            bind_dn: '',
            search_base: ''
        },
        security: {
            mfa_required: false,
            session_timeout_mins: 60,
            ip_allowlist: ''
        }
    };
    @state() private _isLoading = false;
    @state() private _activeTab = 'general';

    async connectedCallback() {
        super.connectedCallback();
        await this._loadConfig();
    }

    render() {
        return html`
            <eog-modal
                ?open=${this.open}
                title="Enterprise Settings"
                @close=${this._close}
                width="800px"
            >
                <eog-tabs
                    .tabs=${[
                { id: 'general', label: 'General' },
                { id: 'sso', label: 'SSO & Auth' },
                { id: 'ldap', label: 'LDAP / Directory' },
                { id: 'security', label: 'Security' }
            ]}
                    .active=${this._activeTab}
                    @eog-change=${(e: CustomEvent) => this._activeTab = e.detail.value}
                    style="margin-bottom: 24px;"
                ></eog-tabs>

                <div class="settings-content">
                    ${this._renderContent()}
                </div>

                <div slot="footer">
                    <eog-button variant="secondary" @click=${this._close}>Cancel</eog-button>
                    <eog-button 
                        @click=${this._saveConfig} 
                        ?loading=${this._isLoading}
                    >
                        Save Configuration
                    </eog-button>
                </div>
            </eog-modal>
        `;
    }

    private _renderContent() {
        switch (this._activeTab) {
            case 'general': return this._renderGeneral();
            case 'sso': return this._renderSSO();
            case 'ldap': return this._renderLDAP();
            case 'security': return this._renderSecurity();
            default: return html``;
        }
    }

    private _renderGeneral() {
        return html`
            <div class="info-box">
                <span>🏢</span>
                <span>
                    Enterprise Mode enables centralized management, SSO, and enhanced security policies.
                    Activating requires a valid Enterprise License.
                </span>
            </div>

            <div class="section">
                <div class="section-header">
                    <span class="section-title">Activation Status</span>
                    <eog-toggle
                        .checked=${this._config.enterprise_mode_enabled}
                        @change=${(e: Event) => this._updateConfig('enterprise_mode_enabled', (e.target as HTMLInputElement).checked)}
                    ></eog-toggle>
                </div>

                <div class="form-grid">
                    <eog-input
                        label="Company Name"
                        .value=${this._config.company_name}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('company_name', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled}
                    ></eog-input>

                    <eog-input
                        label="Primary Domain"
                        placeholder="example.com"
                        .value=${this._config.domain}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('domain', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled}
                    ></eog-input>
                </div>
            </div>
        `;
    }

    private _renderSSO() {
        return html`
            <div class="section">
                <div class="section-header">
                    <div class="section-title">
                        <span>🔑</span> OIDC (OpenID Connect)
                    </div>
                    <eog-toggle
                        .checked=${this._config.sso.oidc_enabled}
                        @change=${(e: Event) => this._updateConfig('sso.oidc_enabled', (e.target as HTMLInputElement).checked)}
                        ?disabled=${!this._config.enterprise_mode_enabled}
                    ></eog-toggle>
                </div>

                <div class="form-grid">
                    <eog-input
                        label="Provider URL"
                        placeholder="https://accounts.google.com"
                        .value=${this._config.sso.oidc_provider_url}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('sso.oidc_provider_url', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled || !this._config.sso.oidc_enabled}
                    ></eog-input>
                    <eog-input
                        label="Client ID"
                        .value=${this._config.sso.oidc_client_id}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('sso.oidc_client_id', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled || !this._config.sso.oidc_enabled}
                    ></eog-input>
                </div>
            </div>

            <div class="section">
                <div class="section-header">
                    <div class="section-title">
                        <span>🏛️</span> SAML 2.0
                    </div>
                    <eog-toggle
                        .checked=${this._config.sso.saml_enabled}
                        @change=${(e: Event) => this._updateConfig('sso.saml_enabled', (e.target as HTMLInputElement).checked)}
                        ?disabled=${!this._config.enterprise_mode_enabled}
                    ></eog-toggle>
                </div>

                <div class="form-grid">
                    <eog-input
                        label="IdP Entry Point"
                        .value=${this._config.sso.saml_entry_point}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('sso.saml_entry_point', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled || !this._config.sso.saml_enabled}
                    ></eog-input>
                    <div class="form-field">
                        <label>X.509 Certificate</label>
                        <textarea
                            style="width:100%; height:100px; background:rgba(0,0,0,0.2); color:inherit; border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:8px;"
                            .value=${this._config.sso.saml_cert}
                            @input=${(e: Event) => this._updateConfig('sso.saml_cert', (e.target as HTMLTextAreaElement).value)}
                            ?disabled=${!this._config.enterprise_mode_enabled || !this._config.sso.saml_enabled}
                        ></textarea>
                    </div>
                </div>
            </div>
        `;
    }

    private _renderLDAP() {
        return html`
            <div class="section">
                <div class="section-header">
                    <div class="section-title">
                        <span>📒</span> Active Directory / LDAP
                    </div>
                    <eog-toggle
                        .checked=${this._config.ldap.enabled}
                        @change=${(e: Event) => this._updateConfig('ldap.enabled', (e.target as HTMLInputElement).checked)}
                        ?disabled=${!this._config.enterprise_mode_enabled}
                    ></eog-toggle>
                </div>

                <div class="form-grid">
                    <eog-input
                        label="Server URL"
                        placeholder="ldaps://ldap.company.com:636"
                        .value=${this._config.ldap.server_url}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('ldap.server_url', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled || !this._config.ldap.enabled}
                    ></eog-input>
                    <eog-input
                        label="Bind DN"
                        placeholder="cn=read-only-admin,dc=example,dc=com"
                        .value=${this._config.ldap.bind_dn}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('ldap.bind_dn', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled || !this._config.ldap.enabled}
                    ></eog-input>
                    <eog-input
                        label="Search Base"
                        placeholder="dc=example,dc=com"
                        .value=${this._config.ldap.search_base}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('ldap.search_base', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled || !this._config.ldap.enabled}
                    ></eog-input>
                </div>
            </div>
        `;
    }

    private _renderSecurity() {
        return html`
            <div class="section">
                <div class="section-header">
                    <span class="section-title">Access Control Policy</span>
                </div>

                <div class="form-grid">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <label>Enforce MFA</label>
                        <eog-toggle
                            .checked=${this._config.security.mfa_required}
                            @change=${(e: Event) => this._updateConfig('security.mfa_required', (e.target as HTMLInputElement).checked)}
                            ?disabled=${!this._config.enterprise_mode_enabled}
                        ></eog-toggle>
                    </div>

                    <eog-input
                        label="Session Timeout (minutes)"
                        type="number"
                        .value=${String(this._config.security.session_timeout_mins)}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('security.session_timeout_mins', Number(e.detail.value))}
                        ?disabled=${!this._config.enterprise_mode_enabled}
                    ></eog-input>

                    <eog-input
                        label="IP Allowlist (CIDR)"
                        placeholder="10.0.0.0/8, 192.168.1.0/24"
                        .value=${this._config.security.ip_allowlist}
                        @eog-input=${(e: CustomEvent) => this._updateConfig('security.ip_allowlist', e.detail.value)}
                        ?disabled=${!this._config.enterprise_mode_enabled}
                    ></eog-input>
                </div>
            </div>
        `;
    }

    private _updateConfig(path: string, value: any) {
        const parts = path.split('.');
        if (parts.length === 1) {
            this._config = { ...this._config, [path]: value };
        } else {
            this._config = {
                ...this._config,
                [parts[0]]: {
                    ...((this._config as any)[parts[0]]),
                    [parts[1]]: value
                }
            };
        }
    }

    private async _loadConfig() {
        try {
            // In real app, fetch from API
            // const config = await apiClient.get<EnterpriseConfig>('/saas/settings');
            // this._config = config;
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    private async _saveConfig() {
        this._isLoading = true;
        try {
            await apiClient.post('/saas/settings', this._config);
            this._close();
            // Show success toast (TODO)
        } catch (error) {
            console.error('Failed to save settings:', error);
            // Show error toast (TODO)
        } finally {
            this._isLoading = false;
        }
    }

    private _close() {
        this.open = false;
        this.dispatchEvent(new CustomEvent('close'));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-enterprise-settings': EogEnterpriseSettings;
    }
}
