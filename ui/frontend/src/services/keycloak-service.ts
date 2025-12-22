/**
 * Eye of God Keycloak Service
 * Per Eye of God UIX Design - Authentication
 *
 * VIBE COMPLIANT:
 * - Real Keycloak OIDC integration
 * - Token management
 * - Refresh token handling
 */

export interface KeycloakConfig {
    url: string;
    realm: string;
    clientId: string;
}

export interface KeycloakToken {
    access_token: string;
    refresh_token: string;
    id_token: string;
    token_type: string;
    expires_in: number;
    refresh_expires_in: number;
}

export interface KeycloakUserInfo {
    sub: string;
    preferred_username: string;
    email?: string;
    email_verified?: boolean;
    name?: string;
    given_name?: string;
    family_name?: string;
    realm_access?: {
        roles: string[];
    };
    resource_access?: Record<string, { roles: string[] }>;
}

class KeycloakService {
    private config: KeycloakConfig = {
        url: '/auth',
        realm: 'somaagent',
        clientId: 'eye-of-god',
    };

    private token: KeycloakToken | null = null;
    private refreshTimeoutId: ReturnType<typeof setTimeout> | null = null;

    /**
     * Initialize the service with config
     */
    init(config: Partial<KeycloakConfig>) {
        this.config = { ...this.config, ...config };

        // Check for stored token
        const storedToken = localStorage.getItem('eog_keycloak_token');
        if (storedToken) {
            try {
                this.token = JSON.parse(storedToken);
                this._scheduleRefresh();
            } catch {
                localStorage.removeItem('eog_keycloak_token');
            }
        }
    }

    /**
     * Get authorization URL for OIDC login
     */
    getAuthUrl(redirectUri?: string): string {
        const redirect = redirectUri || `${window.location.origin}/auth/callback`;
        const nonce = this._generateNonce();
        const state = this._generateState();

        // Store state for verification
        sessionStorage.setItem('eog_auth_state', state);
        sessionStorage.setItem('eog_auth_nonce', nonce);

        const params = new URLSearchParams({
            client_id: this.config.clientId,
            redirect_uri: redirect,
            response_type: 'code',
            scope: 'openid profile email',
            state,
            nonce,
        });

        return `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/auth?${params}`;
    }

    /**
     * Exchange authorization code for tokens
     */
    async exchangeCode(code: string, redirectUri?: string): Promise<KeycloakToken> {
        const redirect = redirectUri || `${window.location.origin}/auth/callback`;

        const response = await fetch(
            `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/token`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    grant_type: 'authorization_code',
                    client_id: this.config.clientId,
                    code,
                    redirect_uri: redirect,
                }),
            }
        );

        if (!response.ok) {
            throw new Error('Failed to exchange code for token');
        }

        this.token = await response.json();
        this._storeToken();
        this._scheduleRefresh();

        return this.token;
    }

    /**
     * Refresh the access token
     */
    async refreshToken(): Promise<KeycloakToken | null> {
        if (!this.token?.refresh_token) {
            return null;
        }

        try {
            const response = await fetch(
                `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/token`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({
                        grant_type: 'refresh_token',
                        client_id: this.config.clientId,
                        refresh_token: this.token.refresh_token,
                    }),
                }
            );

            if (!response.ok) {
                this.logout();
                return null;
            }

            this.token = await response.json();
            this._storeToken();
            this._scheduleRefresh();

            return this.token;
        } catch {
            this.logout();
            return null;
        }
    }

    /**
     * Get user info from Keycloak
     */
    async getUserInfo(): Promise<KeycloakUserInfo | null> {
        if (!this.token?.access_token) {
            return null;
        }

        const response = await fetch(
            `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/userinfo`,
            {
                headers: { 'Authorization': `Bearer ${this.token.access_token}` },
            }
        );

        if (!response.ok) {
            return null;
        }

        return response.json();
    }

    /**
     * Logout and revoke tokens
     */
    async logout(): Promise<void> {
        if (this.refreshTimeoutId) {
            clearTimeout(this.refreshTimeoutId);
        }

        if (this.token?.refresh_token) {
            try {
                await fetch(
                    `${this.config.url}/realms/${this.config.realm}/protocol/openid-connect/logout`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: new URLSearchParams({
                            client_id: this.config.clientId,
                            refresh_token: this.token.refresh_token,
                        }),
                    }
                );
            } catch {
                // Continue with local logout even if server logout fails
            }
        }

        this.token = null;
        localStorage.removeItem('eog_keycloak_token');
        localStorage.removeItem('eog_auth_token');
        localStorage.removeItem('eog_user');
        sessionStorage.removeItem('eog_auth_state');
        sessionStorage.removeItem('eog_auth_nonce');
    }

    /**
     * Get current access token
     */
    getAccessToken(): string | null {
        return this.token?.access_token || null;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated(): boolean {
        return !!this.token?.access_token;
    }

    /**
     * Parse hash fragment for implicit flow tokens
     */
    parseCallback(urlOrHash: string): { code?: string; state?: string; error?: string } {
        const params = new URLSearchParams(
            urlOrHash.includes('?') ? urlOrHash.split('?')[1] : urlOrHash.replace('#', '')
        );

        return {
            code: params.get('code') || undefined,
            state: params.get('state') || undefined,
            error: params.get('error') || undefined,
        };
    }

    /**
     * Verify state parameter
     */
    verifyState(state: string): boolean {
        const storedState = sessionStorage.getItem('eog_auth_state');
        return storedState === state;
    }

    // Private methods

    private _storeToken(): void {
        if (this.token) {
            localStorage.setItem('eog_keycloak_token', JSON.stringify(this.token));
            localStorage.setItem('eog_auth_token', this.token.access_token);
        }
    }

    private _scheduleRefresh(): void {
        if (this.refreshTimeoutId) {
            clearTimeout(this.refreshTimeoutId);
        }

        if (!this.token?.expires_in) {
            return;
        }

        // Refresh 60 seconds before expiry
        const refreshIn = (this.token.expires_in - 60) * 1000;

        if (refreshIn > 0) {
            this.refreshTimeoutId = setTimeout(() => {
                this.refreshToken();
            }, refreshIn);
        }
    }

    private _generateNonce(): string {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return Array.from(array, b => b.toString(16).padStart(2, '0')).join('');
    }

    private _generateState(): string {
        return this._generateNonce();
    }
}

export const keycloakService = new KeycloakService();
