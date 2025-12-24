/**
 * Eye of God Auth Store
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit Context implementation
 * - JWT token management
 * - Permission caching
 */

import { createContext } from '@lit/context';
import { LitElement, html } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { provide } from '@lit/context';

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
                throw new Error('Invalid credentials');
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

            this.authState = {
                isAuthenticated: true,
                user,
                token: data.access_token,
                expiresAt: payload.exp * 1000,
                isLoading: false,
                error: null,
            };

            this._scheduleRefresh(payload.exp * 1000);

            // Return success with redirect_path from API
            // SAAS admins (sysadmin, saas_admin) -> /select-mode
            // Regular users -> /chat
            return {
                success: true,
                redirect_path: data.redirect_path || '/chat'
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
     * Refresh the access token
     */
    private async _refreshToken() {
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

                this.authState = {
                    ...this.authState,
                    token: data.access_token,
                    expiresAt: payload?.exp ? payload.exp * 1000 : null,
                };

                if (payload?.exp) {
                    this._scheduleRefresh(payload.exp * 1000);
                }
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.logout();
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-auth-provider': SomaAuthProvider;
    }
}
