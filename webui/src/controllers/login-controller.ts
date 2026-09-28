/**
 * Login Controller
 *
 * Manages login API calls, token handling, navigation, and SSO flows.
 * Per SaaS Admin UIX Design - Authentication.
 */

import { googleAuthService } from '../services/google-auth-service.js';
import { keycloakService } from '../services/keycloak-service.js';

export interface LoginCredentials {
    email: string;
    password: string;
    rememberMe: boolean;
}

export interface LoginResult {
    success: boolean;
    redirectPath?: string;
    user?: unknown;
    requiresMfa?: boolean;
    mfaToken?: string;
    error?: string;
}

export interface SSOTestResult {
    success: boolean;
    message: string;
}

export interface SSOSaveResult {
    success: boolean;
    redirectUrl?: string;
    error?: string;
}

export class LoginController {
    /**
     * Authenticate with email and password.
     * If the backend requires MFA, the result will include requiresMfa and mfaToken.
     */
    async login(credentials: LoginCredentials): Promise<LoginResult> {
        const { email, password, rememberMe } = credentials;

        try {
            const response = await fetch('/api/v2/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, remember_me: rememberMe }),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                return { success: false, error: data.detail || 'Invalid credentials' };
            }

            const result = await response.json();

            if (result.requires_mfa) {
                return {
                    success: true,
                    requiresMfa: true,
                    mfaToken: result.mfa_token || '',
                };
            }

            if (result.user) {
                sessionStorage.setItem('saas_user', JSON.stringify(result.user));
            }

            const redirectPath = result.redirect_path || '/chat';
            window.location.href = redirectPath;
            return { success: true, redirectPath, user: result.user };
        } catch (err) {
            return {
                success: false,
                error: err instanceof Error ? err.message : 'Login failed',
            };
        }
    }

    /**
     * Complete login by verifying an MFA TOTP code.
     */
    async verifyMfa(code: string, _mfaToken: string): Promise<LoginResult> {
        try {
            const response = await fetch('/api/v2/auth/mfa/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code }),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                return { success: false, error: data.detail || 'Invalid MFA code' };
            }

            const result = await response.json();

            if (result.user) {
                sessionStorage.setItem('saas_user', JSON.stringify(result.user));
            }

            const redirectPath = result.redirect_path || '/chat';
            window.location.href = redirectPath;
            return { success: true, redirectPath, user: result.user };
        } catch (err) {
            return {
                success: false,
                error: err instanceof Error ? err.message : 'MFA verification failed',
            };
        }
    }

    /**
     * Redirect to Google OAuth.
     */
    startGoogleSignIn(): void {
        window.location.href = googleAuthService.getAuthUrl();
    }

    /**
     * Test an SSO identity provider configuration.
     */
    async testSSO(provider: string, config: Record<string, string>): Promise<SSOTestResult> {
        try {
            const response = await fetch('/api/v2/auth/sso/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, config }),
            });

            if (response.ok) {
                const result = await response.json();
                return {
                    success: true,
                    message: result.message || 'Connection successful! Identity provider is reachable.',
                };
            }

            const error = await response.json().catch(() => ({}));
            return {
                success: false,
                message: error.detail || 'Connection failed. Please verify your configuration.',
            };
        } catch {
            return {
                success: false,
                message: 'Network error. Please check your connection and try again.',
            };
        }
    }

    /**
     * Persist SSO configuration and return a redirect URL when applicable.
     */
    async saveSSOConfig(provider: string, config: Record<string, string>): Promise<SSOSaveResult> {
        try {
            const response = await fetch('/api/v2/auth/sso/configure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, config }),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                return { success: false, error: data.detail || 'Failed to save SSO configuration' };
            }

            if (provider === 'oidc' && config.issuer_url) {
                return { success: true, redirectUrl: keycloakService.getAuthUrl() };
            }

            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err instanceof Error ? err.message : 'Failed to save SSO configuration',
            };
        }
    }
}
