/**
 * SaaS Admin Auth Store
 * Per SaaS Admin UIX Design Section 2.2
 * Per login-to-chat-journey design.md Section 10.1, 10.3
 *
 * VIBE COMPLIANT:
 * - Real Lit Context implementation
 * - Cookie-based auth (no localStorage JWT — XSS-safe)
 * - Permission caching
 * - Token refresh deduplication (Promise-based lock)
 * - Role-based redirect routing
 *
 * SECURITY:
 * - Access token stored in httpOnly cookie only (never localStorage)
 * - User info stored in sessionStorage (cleared when tab closes)
 * - WebSocket auth via cookie (never in URL)
 */

import { createContext } from '@lit/context';
import { LitElement, html } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { provide } from '@lit/context';
import { apiClient } from '../services/api-client.js';
import { wsClient } from '../services/websocket-client.js';

export interface User {
    id: string;
    tenant_id: string;
    username: string;
    email?: string;
    role: string;
    permissions: string[];
}

export interface AuthStateData {
    isAuthenticated: boolean;
    user: User | null;
    expiresAt: number | null;
    isLoading: boolean;
    error: string | null;
}

export const authContext = createContext<AuthStateData>('auth-context');

const USER_STORAGE_KEY = 'saas_user';

/**
 * Role priority for redirect routing.
 * Per design.md Section 6.1 - Role-Based Redirect
 */
const ROLE_PRIORITY = [
    'saas_admin',
    'tenant_sysadmin',
    'tenant_admin',
    'agent_owner',
    'developer',
    'trainer',
    'user',
    'viewer',
];

/**
 * Default route mapping for roles.
 */
const ROLE_REDIRECT_MAP: Record<string, string> = {
    saas_admin: '/select-mode',
    tenant_sysadmin: '/select-mode',
    tenant_admin: '/dashboard',
    agent_owner: '/dashboard',
};

@customElement('saas-auth-provider')
export class SaasAuthProvider extends LitElement {
    @provide({ context: authContext })
    @state()
    authState: AuthStateData = {
        isAuthenticated: false,
        user: null,
        expiresAt: null,
        isLoading: true,
        error: null,
    };

    @property({ type: Array })
    allowedRoles: string[] = [];

    private _refreshPromise: Promise<boolean> | null = null;
    private _refreshTimer: ReturnType<typeof setTimeout> | null = null;

    connectedCallback() {
        super.connectedCallback();
        this._initializeAuth();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this._refreshTimer) {
            clearTimeout(this._refreshTimer);
        }
    }

    render() {
        return html`<slot></slot>`;
    }

    /**
     * Initialize auth state from sessionStorage and validate cookie.
     */
    private async _initializeAuth() {
        try {
            // Try to validate existing cookie auth by fetching current user
            const user = await apiClient.get<User>('/auth/me');
            const userJson = sessionStorage.getItem(USER_STORAGE_KEY);
            const storedUser = userJson ? (JSON.parse(userJson) as User) : null;

            if (user) {
                this.authState = {
                    isAuthenticated: true,
                    user: storedUser ?? user,
                    expiresAt: null,
                    isLoading: false,
                    error: null,
                };
                // Schedule proactive refresh every 10 minutes
                this._scheduleRefresh(600000);
                return;
            }
        } catch {
            // Cookie auth invalid or expired
        }

        // No valid cookie auth — clear any stale sessionStorage
        sessionStorage.removeItem(USER_STORAGE_KEY);
        this.authState = {
            isAuthenticated: false,
            user: null,
            expiresAt: null,
            isLoading: false,
            error: null,
        };
    }

    /**
     * Login with credentials
     * Returns result object with success flag and redirect_path for role-based routing
     * Per design.md Section 6.1 - Role-Based Redirect
     */
    async login(username: string, password: string): Promise<{ success: boolean; redirect_path?: string; error?: string }> {
        this.authState = { ...this.authState, isLoading: true, error: null };

        try {
            const response = await fetch('/api/v2/auth/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Invalid credentials');
            }

            const data = await response.json();

            // Fetch user info (cookie is now set automatically)
            const user = await apiClient.get<User>('/auth/me');

            if (!user) {
                throw new Error('Failed to fetch user info');
            }

            sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));

            this.authState = {
                isAuthenticated: true,
                user,
                expiresAt: data.expires_in ? Date.now() + data.expires_in * 1000 : null,
                isLoading: false,
                error: null,
            };

            if (data.expires_in) {
                this._scheduleRefresh(data.expires_in * 1000);
            }

            const redirectPath = data.redirect_path || this.getDefaultRoute(user.permissions);

            return {
                success: true,
                redirect_path: redirectPath
            };

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Login failed';
            this.authState = {
                ...this.authState,
                isLoading: false,
                error: errorMessage,
            };
            return { success: false, error: errorMessage };
        }
    }

    /**
     * Get default route based on user roles.
     * Per design.md Section 6.1 - Role-Based Redirect
     *
     * Priority order:
     * 1. saas_admin, tenant_sysadmin -> /select-mode
     * 2. tenant_admin, agent_owner -> /dashboard
     * 3. developer, trainer, user, viewer -> /chat
     */
    getDefaultRoute(roles: string[]): string {
        for (const role of ROLE_PRIORITY) {
            if (roles.includes(role)) {
                return ROLE_REDIRECT_MAP[role] || '/chat';
            }
        }
        return '/chat';
    }

    /**
     * Validate return URL is same-origin.
     * Per design.md Section 6.2 - Return URL Same-Origin Validation
     *
     * Security: Only allow redirects to same-origin URLs to prevent open redirect attacks.
     */
    validateReturnUrl(returnUrl: string | null): string | null {
        if (!returnUrl) return null;

        try {
            const url = new URL(returnUrl, window.location.origin);
            // Only allow same-origin URLs
            if (url.origin === window.location.origin) {
                return url.pathname + url.search + url.hash;
            }
            console.warn(`[Auth] Rejected non-same-origin return URL: ${returnUrl}`);
            return null;
        } catch {
            // Invalid URL - reject
            console.warn(`[Auth] Rejected invalid return URL: ${returnUrl}`);
            return null;
        }
    }

    /**
     * Logout and clear state
     */
    async logout() {
        try {
            await apiClient.post('/auth/logout', {});
        } catch {
            // Best-effort logout
        }

        sessionStorage.removeItem(USER_STORAGE_KEY);
        if (this._refreshTimer) {
            clearTimeout(this._refreshTimer);
            this._refreshTimer = null;
        }

        this.authState = {
            isAuthenticated: false,
            user: null,
            expiresAt: null,
            isLoading: false,
            error: null,
        };

        wsClient.disconnect();

        // Redirect to login
        window.location.href = '/login';
    }

    /**
     * Check if user has specific permission
     */
    hasPermission(permission: string): boolean {
        return this.authState.user?.permissions.includes(permission) ?? false;
    }

    /**
     * Check if user has any of the specified roles
     */
    hasRole(...roles: string[]): boolean {
        const userRole = this.authState.user?.role;
        return userRole ? roles.includes(userRole) : false;
    }

    /**
     * Schedule token refresh before expiration
     */
    private _scheduleRefresh(expiresInMs: number) {
        if (this._refreshTimer) {
            clearTimeout(this._refreshTimer);
        }
        const refreshBuffer = 60000; // 1 minute before expiry
        const refreshIn = Math.max(expiresInMs - refreshBuffer, 30000); // At least 30s

        this._refreshTimer = setTimeout(() => this._refreshToken(), refreshIn);
    }

    /**
     * Refresh the access token with deduplication.
     * Per design.md Section 10.5 - Token Refresh Deduplication
     *
     * Uses Promise-based lock to ensure only one refresh request at a time.
     * Concurrent callers will await the same Promise.
     */
    private async _refreshToken(): Promise<boolean> {
        if (this._refreshPromise) {
            console.log('[Auth] Token refresh already in progress, waiting...');
            return this._refreshPromise;
        }

        this._refreshPromise = this._doRefreshToken();

        try {
            return await this._refreshPromise;
        } finally {
            this._refreshPromise = null;
        }
    }

    /**
     * Internal token refresh implementation.
     * Cookie-based: refresh_token is read from httpOnly cookie by backend.
     */
    private async _doRefreshToken(): Promise<boolean> {
        try {
            const response = await fetch('/api/v2/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
            });

            if (response.ok) {
                const data = await response.json();

                if (data.expires_in) {
                    this._scheduleRefresh(data.expires_in * 1000);
                }

                console.log('[Auth] Token refreshed successfully');
                return true;
            } else {
                console.warn('[Auth] Token refresh failed, logging out');
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('[Auth] Token refresh error:', error);
            this.logout();
            return false;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-auth-provider': SaasAuthProvider;
    }
}
