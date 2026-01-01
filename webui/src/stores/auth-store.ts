/**
 * Eye of God Auth Store
 * Per Eye of God UIX Design Section 2.2
 * Per login-to-chat-journey design.md Section 10.1, 10.3
 *
 * VIBE COMPLIANT:
 * - Real Lit Context implementation
 * - JWT token management
 * - Permission caching
 * - Token refresh deduplication (Promise-based lock)
 * - Role-based redirect routing
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
    token: string | null;
    expiresAt: number | null;
    isLoading: boolean;
    error: string | null;
}

export const authContext = createContext<AuthStateData>('auth-context');

const AUTH_STORAGE_KEY = 'eog_auth_token';
const USER_STORAGE_KEY = 'eog_user';

/**
 * Role priority for redirect routing.
 * Per design.md Section 6.1 - Role-Based Redirect
 */
const ROLE_REDIRECT_MAP: Record<string, string> = {
    'saas_admin': '/select-mode',
    'tenant_sysadmin': '/select-mode',
    'tenant_admin': '/dashboard',
    'agent_owner': '/dashboard',
    'developer': '/chat',
    'trainer': '/chat',
    'user': '/chat',
    'viewer': '/chat',
};

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

@customElement('soma-auth-provider')
export class SomaAuthProvider extends LitElement {
    @provide({ context: authContext })
    @state()
    authState: AuthStateData = {
        isAuthenticated: false,
        user: null,
        token: null,
        expiresAt: null,
        isLoading: true,
        error: null,
    };

    /**
     * Token refresh deduplication lock.
     * Per design.md Section 10.5 - Only one refresh request at a time.
     */
    private _refreshPromise: Promise<boolean> | null = null;

    connectedCallback() {
        super.connectedCallback();
        this._initializeAuth();
    }

    render() {
        return html`<slot></slot>`;
    }

    /**
     * Initialize auth state from storage
     */
    private async _initializeAuth() {
        try {
            const token = localStorage.getItem(AUTH_STORAGE_KEY);
            const userJson = localStorage.getItem(USER_STORAGE_KEY);

            if (token && userJson) {
                const user = JSON.parse(userJson) as User;
                const payload = this._decodeToken(token);

                if (payload && payload.exp * 1000 > Date.now()) {
                    this.authState = {
                        isAuthenticated: true,
                        user,
                        token,
                        expiresAt: payload.exp * 1000,
                        isLoading: false,
                        error: null,
                    };

                    apiClient.setToken(token);
                    wsClient.setToken(token);

                    // Schedule token refresh
                    this._scheduleRefresh(payload.exp * 1000);
                    return;
                }
            }

            this.authState = {
                ...this.authState,
                isLoading: false,
            };
        } catch (error) {
            console.error('Auth initialization failed:', error);
            this.authState = {
                ...this.authState,
                isLoading: false,
                error: 'Failed to initialize authentication',
            };
        }
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
            const payload = this._decodeToken(data.access_token);

            // Fetch user info
            const userResponse = await fetch('/api/v2/auth/me', {
                headers: { 'Authorization': `Bearer ${data.access_token}` },
            });

            const user = await userResponse.json() as User;

            if (!payload) {
                throw new Error('Invalid token');
            }

            // Store in localStorage
            localStorage.setItem(AUTH_STORAGE_KEY, data.access_token);
            localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));

            apiClient.setToken(data.access_token);
            wsClient.setToken(data.access_token);

            this.authState = {
                isAuthenticated: true,
                user,
                token: data.access_token,
                expiresAt: payload.exp * 1000,
                isLoading: false,
                error: null,
            };

            this._scheduleRefresh(payload.exp * 1000);

            // Determine redirect path from API response or compute from roles
            // Per design.md Section 6.1 - Role-Based Redirect
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
    logout() {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);

        this.authState = {
            isAuthenticated: false,
            user: null,
            token: null,
            expiresAt: null,
            isLoading: false,
            error: null,
        };

        apiClient.clearToken();
        wsClient.setToken(null);
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
     * Decode JWT payload (without verification - server does that)
     */
    private _decodeToken(token: string): { sub: string; exp: number;[key: string]: unknown } | null {
        try {
            const base64Payload = token.split('.')[1];
            return JSON.parse(atob(base64Payload));
        } catch {
            return null;
        }
    }

    /**
     * Schedule token refresh before expiration
     */
    private _scheduleRefresh(expiresAt: number) {
        const refreshBuffer = 60000; // 1 minute before expiry
        const refreshIn = expiresAt - Date.now() - refreshBuffer;

        if (refreshIn > 0) {
            setTimeout(() => this._refreshToken(), refreshIn);
        }
    }

    /**
     * Refresh the access token with deduplication.
     * Per design.md Section 10.5 - Token Refresh Deduplication
     * 
     * Uses Promise-based lock to ensure only one refresh request at a time.
     * Concurrent callers will await the same Promise.
     */
    private async _refreshToken(): Promise<boolean> {
        // If refresh already in progress, return existing promise
        if (this._refreshPromise) {
            console.log('[Auth] Token refresh already in progress, waiting...');
            return this._refreshPromise;
        }

        // Create new refresh promise
        this._refreshPromise = this._doRefreshToken();
        
        try {
            return await this._refreshPromise;
        } finally {
            // Clear the lock after completion
            this._refreshPromise = null;
        }
    }

    /**
     * Internal token refresh implementation.
     */
    private async _doRefreshToken(): Promise<boolean> {
        try {
            const response = await fetch('/api/v2/auth/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authState.token}`,
                },
            });

            if (response.ok) {
                const data = await response.json();
                const payload = this._decodeToken(data.access_token);

                localStorage.setItem(AUTH_STORAGE_KEY, data.access_token);

                apiClient.setToken(data.access_token);
                wsClient.setToken(data.access_token);

                this.authState = {
                    ...this.authState,
                    token: data.access_token,
                    expiresAt: payload?.exp ? payload.exp * 1000 : null,
                };

                if (payload?.exp) {
                    this._scheduleRefresh(payload.exp * 1000);
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
        'soma-auth-provider': SomaAuthProvider;
    }
}
