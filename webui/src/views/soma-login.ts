/**
 * SomaAgent Soma — Login Page
 * Per UI_SCREENS_SRS.md Section 3.1 and UI_STYLE_GUIDE.md
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - OAuth integration (Google, Keycloak SSO)
 * - Minimal white/black design
 * - SSO login modal
 * - LDAP, Active Directory, SAML, OIDC support
 */

import { LitElement, html, css } from 'lit';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

type SSOProvider = 'oidc' | 'saml' | 'ldap' | 'ad' | 'okta' | 'azure' | 'ping' | 'onelogin';

interface ProviderConfig {
    id: SSOProvider;
    name: string;
    description: string;
    icon: string;
    fields: { key: string; label: string; type: string; placeholder: string; required?: boolean }[];
}

const SSO_PROVIDERS: ProviderConfig[] = [
    {
        id: 'oidc',
        name: 'OpenID Connect',
        description: 'Connect via OIDC protocol (Keycloak, Auth0, etc.)',
        icon: 'key',
        fields: [
            { key: 'issuer_url', label: 'Issuer URL', type: 'url', placeholder: 'Issuer URL of your identity provider', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'soma-agent-client', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter client secret', required: true },
        ],
    },
    {
        id: 'saml',
        name: 'SAML 2.0',
        description: 'Enterprise SAML federation (Okta, OneLogin, etc.)',
        icon: 'security',
        fields: [
            { key: 'metadata_url', label: 'Metadata URL', type: 'url', placeholder: 'IdP metadata URL', required: true },
            { key: 'entity_id', label: 'Entity ID', type: 'text', placeholder: 'urn:soma:agent:saml', required: true },
            { key: 'acs_url', label: 'ACS URL', type: 'url', placeholder: 'ACS callback URL from your service provider config' },
        ],
    },
    {
        id: 'ldap',
        name: 'LDAP',
        description: 'Connect to OpenLDAP or similar directory',
        icon: 'folder_shared',
        fields: [
            { key: 'server_url', label: 'Server URL', type: 'url', placeholder: 'LDAP server URL', required: true },
            { key: 'base_dn', label: 'Base DN', type: 'text', placeholder: 'dc=company,dc=com', required: true },
            { key: 'bind_dn', label: 'Bind DN', type: 'text', placeholder: 'cn=admin,dc=company,dc=com', required: true },
            { key: 'bind_password', label: 'Bind Password', type: 'password', placeholder: 'Enter bind password', required: true },
            { key: 'user_filter', label: 'User Filter', type: 'text', placeholder: '(uid={username})' },
        ],
    },
    {
        id: 'ad',
        name: 'Active Directory',
        description: 'Microsoft Active Directory via LDAPS',
        icon: 'domain',
        fields: [
            { key: 'domain', label: 'Domain', type: 'text', placeholder: 'company.local', required: true },
            { key: 'server_url', label: 'Domain Controller', type: 'url', placeholder: 'Domain controller LDAPS URL', required: true },
            { key: 'service_account', label: 'Service Account', type: 'text', placeholder: 'svc-somaagent@company.local', required: true },
            { key: 'service_password', label: 'Password', type: 'password', placeholder: 'Service account password', required: true },
            { key: 'base_ou', label: 'Search Base OU', type: 'text', placeholder: 'OU=Users,DC=company,DC=local' },
        ],
    },
    {
        id: 'okta',
        name: 'Okta',
        description: 'Okta Workforce Identity Cloud',
        icon: 'verified_user',
        fields: [
            { key: 'domain', label: 'Okta Domain', type: 'text', placeholder: 'company.okta.com', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'Enter Okta Client ID', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter Okta Client Secret', required: true },
        ],
    },
    {
        id: 'azure',
        name: 'Azure AD / Entra ID',
        description: 'Microsoft Azure Active Directory',
        icon: 'cloud',
        fields: [
            { key: 'tenant_id', label: 'Tenant ID', type: 'text', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', required: true },
            { key: 'client_id', label: 'Application (Client) ID', type: 'text', placeholder: 'Enter Azure App ID', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter Azure App Secret', required: true },
        ],
    },
    {
        id: 'ping',
        name: 'PingFederate',
        description: 'Ping Identity federation server',
        icon: 'hub',
        fields: [
            { key: 'base_url', label: 'PingFederate URL', type: 'url', placeholder: 'PingFederate base URL', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'soma-agent', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter client secret', required: true },
        ],
    },
    {
        id: 'onelogin',
        name: 'OneLogin',
        description: 'OneLogin identity management',
        icon: 'login',
        fields: [
            { key: 'subdomain', label: 'Subdomain', type: 'text', placeholder: 'company', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'Enter OneLogin Client ID', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter OneLogin Client Secret', required: true },
        ],
    },
];

@customElement('soma-login')
export class SomaLogin extends LitElement {
    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: block;
            min-height: 100vh;
            font-family: var(--skin-font-sans);
            background: var(--skin-color-bg-void);
            color: var(--skin-color-text-primary);
        }

        * { box-sizing: border-box; }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: var(--skin-text-xl);
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        .login-page {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: var(--skin-space-lg);
        }

        .login-card {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            box-shadow: var(--skin-shadow-md));
            width: 100%;
            max-width: calc(var(--skin-space-2xl) * 8 + var(--skin-space-md));
            padding: calc(var(--skin-space-xl) + var(--skin-space-sm));
        }

        .brand {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
            margin-bottom: var(--skin-space-xl);
        }

        .brand-icon {
            width: calc(var(--skin-space-xl) + var(--skin-space-sm));
            height: calc(var(--skin-space-xl) + var(--skin-space-sm));
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-icon img {
            width: calc(var(--skin-space-xl) + var(--skin-space-sm));
            height: calc(var(--skin-space-xl) + var(--skin-space-sm));
            object-fit: contain;
        }

        .brand-name {
            font-size: var(--skin-text-xl);
            font-weight: var(--skin-weight-semibold);
        }

        .form-header { margin-bottom: calc(var(--skin-space-lg) + var(--skin-space-xs)); }
        .form-title { font-size: var(--skin-text-2xl); font-weight: var(--skin-weight-semibold); margin: 0 0 var(--skin-space-sm) 0; }
        .form-subtitle { font-size: var(--skin-text-base); color: var(--skin-color-text-secondary); margin: 0; }
        .form-subtitle a { color: var(--skin-color-text-primary); font-weight: var(--skin-weight-medium); text-decoration: underline; }

        .oauth-section { display: flex; flex-direction: column; gap: calc(var(--skin-space-sm) + var(--skin-space-xs)); margin-bottom: var(--skin-space-lg); }

        .oauth-btn {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-base);
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-medium);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
            font-family: var(--skin-font-sans);
        }

        .oauth-btn:hover { background: var(--skin-color-bg-hover); border-color: var(--skin-color-border-strong); }
        .oauth-btn svg { width: calc(var(--skin-space-md) + var(--skin-space-xs) * 0.5); height: calc(var(--skin-space-md) + var(--skin-space-xs) * 0.5); }

        .divider {
            display: flex;
            align-items: center;
            gap: var(--skin-space-md);
            margin: var(--skin-space-lg) 0;
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-xs);
        }
        .divider::before, .divider::after { content: ''; flex: 1; height: var(--skin-border-width); background: var(--skin-color-border); }

        .form-group { margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs)); }
        .form-label { display: flex; justify-content: space-between; font-size: var(--skin-text-sm); font-weight: var(--skin-weight-medium); color: var(--skin-color-text-secondary); margin-bottom: var(--skin-space-sm); }
        .form-label a { color: var(--skin-color-text-primary); text-decoration: none; font-weight: var(--skin-weight-normal); }

        .form-input {
            /* Typed characters must always be visible on the card. */
            color: var(--skin-color-text-primary);
            -webkit-text-fill-color: var(--skin-color-text-primary);
            caret-color: var(--skin-color-text-primary);
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-base);
            transition: border-color var(--skin-motion-fast) var(--skin-motion-ease);
            background: var(--skin-color-bg-base);
            font-family: var(--skin-font-sans);
        }
        .form-input:focus { outline: none; border-color: var(--skin-color-accent); }

        /* Kill browser autofill green/yellow wash — paint with skin tokens. */
        .form-input:-webkit-autofill,
        .form-input:-webkit-autofill:hover,
        .form-input:-webkit-autofill:focus,
        .form-input:-webkit-autofill:active {
            -webkit-box-shadow: 0 0 0 1000px var(--skin-color-bg-base) inset;
            -webkit-text-fill-color: var(--skin-color-text-primary);
            caret-color: var(--skin-color-text-primary);
            transition: background-color 5000s ease-in-out 0s;
        }
        .form-input:autofill,
        .form-input:autofill:hover,
        .form-input:autofill:focus {
            box-shadow: 0 0 0 1000px var(--skin-color-bg-base) inset;
            -webkit-text-fill-color: var(--skin-color-text-primary);
            caret-color: var(--skin-color-text-primary);
        }
        .password-wrapper { position: relative; display: flex; align-items: center; }
        .password-wrapper .form-input { padding-right: calc(var(--skin-space-xl) + var(--skin-space-sm) + var(--skin-space-xs)); }
        .toggle-password {
            position: absolute; right: calc(var(--skin-space-sm) + var(--skin-space-xs)); top: 50%; transform: translateY(-50%);
            background: none; border: none; cursor: pointer; color: var(--skin-color-text-muted); padding: var(--skin-space-xs);
            display: flex; align-items: center; justify-content: center;
        }
        .toggle-password:hover { color: var(--skin-color-accent-hover); }

        .remember-row { display: flex; align-items: center; gap: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5); margin-bottom: var(--skin-space-lg); }
        .remember-row input { width: var(--skin-space-md); height: var(--skin-space-md); accent-color: var(--skin-color-accent); cursor: pointer; }
        .remember-row label { font-size: var(--skin-text-sm); color: var(--skin-color-text-secondary); cursor: pointer; }

        .submit-btn {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-semibold);
            border: none;
            cursor: pointer;
            transition: background var(--skin-motion-fast) var(--skin-motion-ease);
            font-family: var(--skin-font-sans);
        }
        .submit-btn:hover:not(:disabled) { background: var(--skin-color-accent-hover); }
        .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .spinner {
            width: calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5); height: calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5);
            border: calc(var(--skin-border-width) * 3) solid color-mix(in srgb, var(--skin-color-accent-text) 30%, transparent);
            border-top-color: var(--skin-color-accent-text);
            border-radius: var(--skin-radius-full);
            animation: spin 0.6s linear infinite;
            display: inline-block;
            margin-right: var(--skin-space-sm);
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .error-message {
            background: color-mix(in srgb, var(--skin-color-danger) 10%, transparent);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-danger) 20%, transparent);
            border-radius: var(--skin-radius-md);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5);
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
            color: var(--skin-color-danger);
            font-size: var(--skin-text-sm);
        }

        .input-error {
            border-color: var(--skin-color-danger) !important;
        }

        .field-error {
            display: block;
            color: var(--skin-color-danger);
            font-size: var(--skin-text-xs);
            margin-top: calc(var(--skin-space-sm) * 0.75);
        }

        .footer {
            text-align: center;
            margin-top: calc(var(--skin-space-lg) + var(--skin-space-xs));
            padding-top: calc(var(--skin-space-md) + var(--skin-space-xs));
            border-top: var(--skin-border-width) solid var(--skin-color-border);
        }
        .footer-text { font-size: var(--skin-text-xs); color: var(--skin-color-text-muted); }
        .footer-text a { color: var(--skin-color-text-secondary); text-decoration: none; }

        /* ========================================
           GLASSMORPHISM SSO MODAL
           ======================================== */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: color-mix(in srgb, var(--skin-color-text-primary) 40%, transparent);
            backdrop-filter: var(--skin-glass-backdrop);
            -webkit-backdrop-filter: var(--skin-glass-backdrop);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: var(--skin-space-lg);
        }

        .modal-overlay.hidden { display: none; }

        .sso-modal {
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
            -webkit-text-fill-color: var(--skin-color-text-primary);
            backdrop-filter: var(--skin-glass-backdrop);
            -webkit-backdrop-filter: var(--skin-glass-backdrop);
            border: none;
            border-radius: 0;
            box-shadow: none;
            width: 100vw;
            max-width: 100vw;
            height: 100vh;
            max-height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .sso-header {
            padding: calc(var(--skin-space-lg) + var(--skin-space-xs)) var(--skin-space-xl) calc(var(--skin-space-md) + var(--skin-space-xs));
            border-bottom: var(--skin-border-width) solid var(--skin-color-border-subtle);
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
        }

        .sso-title-block { }

        .sso-title {
            font-size: var(--skin-text-2xl);
            font-weight: var(--skin-weight-bold);
            margin: 0 0 calc(var(--skin-space-sm) * 0.75) 0;
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }

        .sso-title .material-symbols-outlined { font-size: var(--skin-text-2xl); }

        .sso-subtitle {
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-secondary);
            margin: 0;
        }

        .sso-close {
            width: calc(var(--skin-space-xl) + var(--skin-space-xs)); height: calc(var(--skin-space-xl) + var(--skin-space-xs));
            border-radius: var(--skin-radius-md);
            border: none;
            background: color-mix(in srgb, var(--skin-color-text-primary) 4%, transparent);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background var(--skin-motion-fast) var(--skin-motion-ease);
        }
        .sso-close:hover { background: var(--skin-color-border); }

        .sso-body {
            flex: 1;
            overflow-y: auto;
            display: flex;
        }

        /* Provider List */
        .provider-list {
            width: calc(var(--skin-space-2xl) * 5 + var(--skin-space-md));
            border-right: var(--skin-border-width) solid var(--skin-color-border-subtle);
            padding: var(--skin-space-md);
            flex-shrink: 0;
            overflow-y: auto;
        }

        .provider-item {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
            padding: calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5) var(--skin-space-md);
            border-radius: var(--skin-radius-lg);
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
            margin-bottom: var(--skin-space-xs);
        }

        .provider-item:hover { background: color-mix(in srgb, var(--skin-color-text-primary) 4%, transparent); }
        .provider-item.active { background: var(--skin-color-border); }

        .provider-icon {
            width: calc(var(--skin-space-xl) + var(--skin-space-sm));
            height: calc(var(--skin-space-xl) + var(--skin-space-sm));
            border-radius: var(--skin-radius-md);
            background: color-mix(in srgb, var(--skin-color-text-primary) 4%, transparent);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .provider-icon .material-symbols-outlined { font-size: var(--skin-text-xl); }

        .provider-info { flex: 1; min-width: 0; }
        .provider-name { font-size: var(--skin-text-base); font-weight: var(--skin-weight-semibold); margin-bottom: var(--skin-space-xs); }
        .provider-desc { font-size: var(--skin-text-xs); color: var(--skin-color-text-muted); line-height: 1.3; }

        /* Config Panel */
        .config-panel {
            flex: 1;
            padding: var(--skin-space-lg) calc(var(--skin-space-lg) + var(--skin-space-xs));
            overflow-y: auto;
        }

        .config-header {
            margin-bottom: var(--skin-space-lg);
        }

        .config-title {
            font-size: var(--skin-text-xl);
            font-weight: var(--skin-weight-semibold);
            margin: 0 0 calc(var(--skin-space-sm) * 0.75) 0;
        }

        .config-desc {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            margin: 0;
        }

        .config-form {
            display: flex;
            flex-direction: column;
            gap: calc(var(--skin-space-md) + var(--skin-space-xs) * 0.5);
        }

        .config-field { }

        .config-label {
            display: block;
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            color: var(--skin-color-accent-hover);
            margin-bottom: var(--skin-space-sm);
            text-transform: uppercase;
            letter-spacing: 0.035em;
        }

        .config-label .required {
            color: var(--skin-color-danger);
            margin-left: var(--skin-space-xs);
        }

        .config-input {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-base);
            background: color-mix(in srgb, var(--skin-color-bg-base) 80%, transparent);
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
            font-family: var(--skin-font-sans);
        }

        .config-input:focus {
            outline: none;
            border-color: var(--skin-color-accent);
            background: var(--skin-color-bg-base);
            box-shadow: 0 0 0 var(--skin-focus-ring-width) color-mix(in srgb, var(--skin-color-accent) 8%, transparent);
        }

        .config-input::placeholder { color: var(--skin-color-text-muted); }

        /* Test Connection */
        .test-section {
            margin-top: var(--skin-space-lg);
            padding-top: var(--skin-space-lg);
            border-top: var(--skin-border-width) solid var(--skin-color-border-subtle);
        }

        .test-btn {
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-lg);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-base);
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-medium);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .test-btn:hover { background: var(--skin-color-bg-hover); }

        .test-btn .material-symbols-outlined { font-size: var(--skin-text-xl); }

        .test-result {
            margin-top: calc(var(--skin-space-sm) + var(--skin-space-xs));
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-sm);
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
        }

        .test-result.success { background: color-mix(in srgb, var(--skin-color-success) 18%, transparent); color: var(--skin-color-success); }
        .test-result.error { background: color-mix(in srgb, var(--skin-color-danger) 12%, transparent); color: var(--skin-color-danger); }
        .test-result.pending { background: color-mix(in srgb, var(--skin-color-warning) 22%, transparent); color: var(--skin-color-warning-text); }

        /* Modal Footer */
        .sso-footer {
            padding: calc(var(--skin-space-md) + var(--skin-space-xs)) calc(var(--skin-space-lg) + var(--skin-space-xs));
            border-top: var(--skin-border-width) solid var(--skin-color-border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: color-mix(in srgb, var(--skin-color-bg-hover) 80%, transparent);
        }

        .sso-help {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
        }

        .sso-help a { color: var(--skin-color-text-primary); font-weight: var(--skin-weight-medium); }

        .sso-actions { display: flex; gap: calc(var(--skin-space-sm) + var(--skin-space-xs)); }

        .sso-btn {
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-lg);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-semibold);
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-base);
        }

        .sso-btn:hover { background: var(--skin-color-bg-hover); }

        .sso-btn.primary {
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            border-color: var(--skin-color-accent);
        }

        .sso-btn.primary:hover { background: var(--skin-color-accent-hover); }
    `
    ];

    @state() private _email = '';
    @state() private _password = '';
    @state() private _error = '';
    @state() private _emailError = '';
    @state() private _isLoading = false;
    @state() private _rememberMe = false;
    @state() private _showPassword = false;
    @state() private _showSSOModal = false;
    @state() private _selectedProvider: SSOProvider = 'oidc';
    @state() private _testStatus: 'idle' | 'pending' | 'success' | 'error' = 'idle';
    @state() private _testMessage = '';

    /**
     * RFC 5322 compliant email validation regex.
     * Per design.md Section 1.2, 2.1 - Email Validation
     * 
     * This pattern validates:
     * - Local part: alphanumeric, dots, hyphens, underscores, plus signs
     * - Domain: alphanumeric with dots and hyphens
     * - TLD: 2+ characters
     */
    private static readonly EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

    /**
     * Validate email format per RFC 5322.
     * Per design.md Section 1.2 - Email Validation
     */
    private _validateEmail(email: string): boolean {
        if (!email) return false;
        if (email.length > 254) return false; // RFC 5321 max length
        return SomaLogin.EMAIL_REGEX.test(email);
    }

    /**
     * Handle email input with inline validation.
     */
    private _handleEmailInput(e: Event) {
        const input = e.target as HTMLInputElement;
        this._email = input.value;

        if (this._emailError && this._email) {
            this._emailError = '';
        }
    }

    /**
     * Validate email on blur.
     */
    private _handleEmailBlur() {
        if (this._email && !this._validateEmail(this._email)) {
            this._emailError = 'Please enter a valid email address';
        } else {
            this._emailError = '';
        }
    }

    render() {
        const provider = SSO_PROVIDERS.find(p => p.id === this._selectedProvider)!;

        return html`
            <div class="login-page">
                <div class="login-card">
                    <!-- Brand -->
                    <div class="brand">
                        <div class="brand-icon">
                            <img
                                src="/brand/1x/yachaq-logo-1x.png"
                                srcset="/brand/1x/yachaq-logo-1x.png 1x, /brand/2x/yachaq-logo-2x.png 2x, /brand/3x/yachaq-logo-3x.png 3x"
                                alt="YACHAQ"
                                width="40"
                                height="40"
                            />
                        </div>
                        <span class="brand-name">YACHAQ.AI</span>
                    </div>

                    <!-- Header -->
                    <div class="form-header">
                        <h2 class="form-title">Sign in</h2>
                        <p class="form-subtitle">
                            Don't have an account? <a href="/register">Get started</a>
                        </p>
                    </div>

                    ${this._error ? html`<div class="error-message">${this._error}</div>` : ''}

                    <!-- OAuth Buttons -->
                    <div class="oauth-section">
                        <button class="oauth-btn" @click=${this._handleGoogleSignIn}>
                            <svg viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                            </svg>
                            Continue with Google
                        </button>

                        <button class="oauth-btn" @click=${() => this._showSSOModal = true}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2"/>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                            </svg>
                            Enterprise SSO
                        </button>
                    </div>

                    <div class="divider">or</div>

                    <!-- Login Form -->
                    <form @submit=${this._handleLogin}>
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-input ${this._emailError ? 'input-error' : ''}" 
                                placeholder="name@company.com"
                                .value=${this._email}
                                @input=${this._handleEmailInput}
                                @blur=${this._handleEmailBlur}
                                required autocomplete="email">
                            ${this._emailError ? html`<span class="field-error">${this._emailError}</span>` : ''}
                        </div>

                        <div class="form-group">
                            <label class="form-label">Password <a href="/forgot-password">Forgot?</a></label>
                            <div class="password-wrapper">
                                <input type="${this._showPassword ? 'text' : 'password'}" class="form-input" placeholder="Enter your password"
                                    .value=${this._password}
                                    @input=${(e: Event) => this._password = (e.target as HTMLInputElement).value}
                                    required autocomplete="current-password" minlength="8">
                                <button type="button" class="toggle-password" @click=${() => this._showPassword = !this._showPassword} tabindex="-1">
                                    ${this._showPassword
                                        ? html`<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
                                        : html`<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`
                                    }
                                </button>
                            </div>
                        </div>

                        <div class="remember-row">
                            <input type="checkbox" id="remember" .checked=${this._rememberMe}
                                @change=${(e: Event) => this._rememberMe = (e.target as HTMLInputElement).checked}>
                            <label for="remember">Remember me</label>
                        </div>

                        <button type="submit" class="submit-btn" ?disabled=${this._isLoading}>
                            ${this._isLoading ? html`<span class="spinner"></span>Signing in...` : 'Sign in'}
                        </button>
                    </form>


                    <div class="footer">
                        <p class="footer-text">Powered by YACHAQ.AI</p>
                    </div>
                </div>
            </div>

            <!-- Enterprise SSO Modal -->
            <div class="modal-overlay ${this._showSSOModal ? '' : 'hidden'}" @click=${(e: Event) => e.target === e.currentTarget && (this._showSSOModal = false)}>
                <div class="sso-modal">
                    <div class="sso-header">
                        <div class="sso-title-block">
                            <h2 class="sso-title">
                                <span class="material-symbols-outlined">security</span>
                                Enterprise SSO Configuration
                            </h2>
                            <p class="sso-subtitle">Connect your organization's identity provider</p>
                        </div>
                        <button class="sso-close" @click=${() => this._showSSOModal = false}>
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="sso-body">
                        <!-- Provider List -->
                        <div class="provider-list">
                            ${SSO_PROVIDERS.map(p => html`
                                <div 
                                    class="provider-item ${this._selectedProvider === p.id ? 'active' : ''}"
                                    @click=${() => { this._selectedProvider = p.id; this._testStatus = 'idle'; }}
                                >
                                    <div class="provider-icon">
                                        <span class="material-symbols-outlined">${p.icon}</span>
                                    </div>
                                    <div class="provider-info">
                                        <div class="provider-name">${p.name}</div>
                                        <div class="provider-desc">${p.description}</div>
                                    </div>
                                </div>
                            `)}
                        </div>

                        <!-- Config Panel -->
                        <div class="config-panel">
                            <div class="config-header">
                                <h3 class="config-title">${provider.name} Configuration</h3>
                                <p class="config-desc">${provider.description}</p>
                            </div>

                            <div class="config-form">
                                ${provider.fields.map(field => html`
                                    <div class="config-field">
                                        <label class="config-label">
                                            ${field.label}
                                            ${field.required ? html`<span class="required">*</span>` : ''}
                                        </label>
                                        <input 
                                            type=${field.type} 
                                            class="config-input" 
                                            id=${`sso-${field.key}`}
                                            placeholder=${field.placeholder}
                                        >
                                    </div>
                                `)}
                            </div>

                            <div class="test-section">
                                <button class="test-btn" @click=${this._testConnection}>
                                    <span class="material-symbols-outlined">network_check</span>
                                    Test Connection
                                </button>

                                ${this._testStatus !== 'idle' ? html`
                                    <div class="test-result ${this._testStatus}">
                                        <span class="material-symbols-outlined">
                                            ${this._testStatus === 'success' ? 'check_circle' :
                    this._testStatus === 'error' ? 'error' : 'hourglass_empty'}
                                        </span>
                                        ${this._testMessage}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>

                    <div class="sso-footer">
                        <div class="sso-help">
                            Need help? Contact your administrator for SSO documentation.
                        </div>
                        <div class="sso-actions">
                            <button class="sso-btn" @click=${() => this._showSSOModal = false}>Cancel</button>
                            <button class="sso-btn primary" @click=${this._saveAndConnect}>Save & Connect</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    private async _handleLogin(e: Event) {
        e.preventDefault();
        if (!this._email || !this._password) {
            this._error = 'Please enter both email and password';
            return;
        }

        if (!this._validateEmail(this._email)) {
            this._emailError = 'Please enter a valid email address';
            return;
        }

        if (this._password.length < 8) {
            this._error = 'Password must be at least 8 characters';
            return;
        }

        this._isLoading = true;
        this._error = '';

        try {
            const response = await fetch('/api/v2/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: this._email, password: this._password, remember_me: this._rememberMe }),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                // API returns {error:{message}} — not top-level detail
                const msg =
                    data?.error?.message ||
                    data?.detail ||
                    data?.message ||
                    'Invalid credentials';
                throw new Error(msg);
            }

            const result = await response.json();
            // Cookie is httpOnly for API calls. WS auth needs the raw JWT in
            // Sec-WebSocket-Protocol (JS cannot read httpOnly cookies).
            if (result?.token) {
                try {
                    sessionStorage.setItem('soma_ws_token', result.token);
                } catch {
                    /* ignore quota */
                }
            }
            if (result.user) {
                localStorage.setItem('soma_user', JSON.stringify(result.user));
            }
            window.location.href = result.redirect_path || '/chat';
        } catch (err) {
            this._error = err instanceof Error ? err.message : 'Login failed';
        } finally {
            this._isLoading = false;
        }
    }

    private async _handleGoogleSignIn() {
        try {
            // The server OAuth router builds the authorize URL from
            // get_keycloak_config(); the browser never holds an issuer or client id.
            await apiClient.startOAuthLogin('google');
        } catch (err) {
            this._error = err instanceof Error ? err.message : 'Google sign-in failed';
        }
    }

    private async _testConnection() {
        this._testStatus = 'pending';
        this._testMessage = 'Testing connection to identity provider...';

        const provider = SSO_PROVIDERS.find(p => p.id === this._selectedProvider)!;
        const config: Record<string, string> = {};

        for (const field of provider.fields) {
            const input = this.shadowRoot?.getElementById(`sso-${field.key}`) as HTMLInputElement;
            if (input) {
                config[field.key] = input.value;
            }
        }

        try {
            const response = await fetch('/api/v2/auth/sso/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: this._selectedProvider, config }),
            });

            if (response.ok) {
                const result = await response.json();
                this._testStatus = 'success';
                this._testMessage = result.message || 'Connection successful! Identity provider is reachable.';
            } else {
                const error = await response.json().catch(() => ({}));
                this._testStatus = 'error';
                this._testMessage = error.detail || 'Connection failed. Please verify your configuration.';
            }
        } catch (err) {
            this._testStatus = 'error';
            this._testMessage = 'Network error. Please check your connection and try again.';
        }
    }

    private async _saveAndConnect() {
        const provider = SSO_PROVIDERS.find(p => p.id === this._selectedProvider)!;
        const config: Record<string, string> = {};

        for (const field of provider.fields) {
            const input = this.shadowRoot?.getElementById(`sso-${field.key}`) as HTMLInputElement;
            if (input) {
                config[field.key] = input.value;
            }
        }

        try {
            // Save SSO config to backend. The server is the only authority on
            // whether persistence exists — never claim success it did not return.
            const response = await fetch('/api/v2/auth/sso/configure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: this._selectedProvider, config }),
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok || result.success === false) {
                this._testStatus = 'error';
                this._testMessage = result.detail || result.message || 'SSO configuration was refused.';
                return;
            }
            this._testStatus = 'success';
            this._testMessage = result.message || 'SSO configuration stored.';
            this._showSSOModal = false;
            this._error = '';
        } catch {
            this._error = 'Failed to save SSO configuration';
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-login': SomaLogin;
    }
}
