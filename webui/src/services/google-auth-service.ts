/**
 * SaaS Admin Google OAuth Service
 * Direct Google OAuth 2.0 Integration
 *
 * VIBE COMPLIANT:
 * - Real Google OAuth endpoints
 * - Secure state management
 * - Token validation
 */

export interface GoogleConfig {
    clientId: string;
    redirectUri: string;
}

export interface GoogleUserInfo {
    id: string;
    email: string;
    verified_email: boolean;
    name: string;
    given_name: string;
    family_name: string;
    picture: string;
}

class GoogleAuthService {
    private config: GoogleConfig = {
        clientId: '',
        redirectUri: '',
    };

    /**
     * Initialize with credentials from environment
     */
    init(config: Partial<GoogleConfig>) {
        this.config = { ...this.config, ...config };
    }

    /**
     * Get Google OAuth authorization URL
     */
    getAuthUrl(): string {
        const state = this._generateState();
        const nonce = this._generateNonce();

        // Store state for verification
        sessionStorage.setItem('saas_google_state', state);
        sessionStorage.setItem('saas_google_nonce', nonce);

        const params = new URLSearchParams({
            client_id: this.config.clientId,
            redirect_uri: this.config.redirectUri,
            response_type: 'code',
            scope: 'openid email profile',
            state,
            nonce,
            access_type: 'offline',
            prompt: 'consent',
        });

        return `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
    }

    /**
     * Parse callback URL for code and state
     */
    parseCallback(url: string): { code?: string; state?: string; error?: string } {
        const urlObj = new URL(url);
        return {
            code: urlObj.searchParams.get('code') || undefined,
            state: urlObj.searchParams.get('state') || undefined,
            error: urlObj.searchParams.get('error') || undefined,
        };
    }

    /**
     * Verify state matches stored state
     */
    verifyState(state: string): boolean {
        const storedState = sessionStorage.getItem('saas_google_state');
        return storedState === state;
    }

    /**
     * Exchange code for tokens via backend
     * Backend handles the client_secret securely
     */
    async exchangeCode(code: string): Promise<{
        access_token: string;
        redirect_path: string;
        user: GoogleUserInfo;
    }> {
        const response = await fetch('/api/v2/auth/google/callback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                redirect_uri: this.config.redirectUri,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Google authentication failed');
        }

        return response.json();
    }

    /**
     * Clear stored state
     */
    clearState() {
        sessionStorage.removeItem('saas_google_state');
        sessionStorage.removeItem('saas_google_nonce');
    }

    private _generateState(): string {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, (b) => b.toString(16).padStart(2, '0')).join('');
    }

    private _generateNonce(): string {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return Array.from(array, (b) => b.toString(16).padStart(2, '0')).join('');
    }
}

// Singleton instance
export const googleAuthService = new GoogleAuthService();

// Auto-initialize if config available in window
if (typeof window !== 'undefined') {
    // Use environment variables or global config
    googleAuthService.init({
        clientId: (window as any).__EOG_GOOGLE_CLIENT_ID__ || '786567505985-46etdi4j46hocuo148a1bush1asiv0od.apps.googleusercontent.com',
        redirectUri: (window as any).__EOG_GOOGLE_REDIRECT_URI__ || `${window.location.origin}/auth/callback`,
    });
}
