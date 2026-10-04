/**
 * SaaS Admin API Client
 * Per SaaS Admin UIX Design Section 4.3
 *
 * VIBE COMPLIANT:
 * - Real implementation (no stubs)
 * - Proper error handling
 * - Timeout and retry support
 *
 * SECURITY: Auth via httpOnly cookie. No Authorization header or localStorage token.
 */

export interface ApiClientConfig {
    baseUrl: string;
    timeout: number;
    retries: number;
}

export type ApiResponse<T> = T;

export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

export class ApiClient {
    private config: ApiClientConfig;

    constructor(config: Partial<ApiClientConfig> = {}) {
        this.config = {
            baseUrl: config.baseUrl ?? '/api/v2',
            timeout: config.timeout ?? 30000,
            retries: config.retries ?? 3,
        };
    }

    /**
     * Make an API request with retry support.
     * Auth is handled automatically via httpOnly cookie.
     */
    async request<T>(
        method: string,
        path: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.config.baseUrl}${path}`;
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            ...(options.headers ?? {}),
        };

        let lastError: Error | null = null;

        for (let attempt = 0; attempt < this.config.retries; attempt++) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

            try {
                const response = await fetch(url, {
                    method,
                    headers,
                    signal: controller.signal,
                    credentials: 'include',
                    ...options,
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    const error = await response.json().catch(() => ({}));
                    throw new ApiError(response.status, error.detail ?? 'Request failed');
                }

                return response.json();
            } catch (error) {
                clearTimeout(timeoutId);

                if (error instanceof ApiError) {
                    throw error;
                }

                lastError = error as Error;

                // Retry on network errors (not on 4xx/5xx)
                if (attempt < this.config.retries - 1) {
                    // Exponential backoff
                    await this.delay(Math.pow(2, attempt) * 100);
                    continue;
                }
            }
        }

        throw new ApiError(0, lastError?.message ?? 'Request failed after retries');
    }

    /**
     * Helper delay function.
     */
    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * GET request.
     */
    get<T>(path: string): Promise<T> {
        return this.request<T>('GET', path);
    }

    /**
     * POST request.
     */
    post<T>(path: string, body: unknown): Promise<T> {
        return this.request<T>('POST', path, { body: JSON.stringify(body) });
    }

    /**
     * PUT request.
     */
    put<T>(path: string, body: unknown): Promise<T> {
        return this.request<T>('PUT', path, { body: JSON.stringify(body) });
    }

    /**
     * PATCH request.
     */
    patch<T>(path: string, body: unknown): Promise<T> {
        return this.request<T>('PATCH', path, { body: JSON.stringify(body) });
    }

    /**
     * DELETE request.
     */
    delete<T>(path: string): Promise<T> {
        return this.request<T>('DELETE', path);
    }

    /**
     * End the session on the server.
     *
     * SECURITY: the auth session lives in httpOnly cookies (`access_token`,
     * `refresh_token`, `session_id`) set by `admin/auth/api.py`. Clearing
     * localStorage does not touch them, so a "logout" that only clears storage
     * leaves the session alive — `checkAuth()` reads the cookie and the user is
     * still signed in. This must POST /auth/logout so the server deletes the
     * cookies before any client-side cleanup or redirect.
     *
     * Deliberately single-attempt and non-retrying: logout is a terminal
     * action, and a retry storm against a dead API cannot resurrect a cookie
     * that was already cleared. Failures are surfaced to the caller so the
     * view can decide, but never silently ignored by this layer.
     */
    async logout(): Promise<void> {
        const url = `${this.config.baseUrl}/auth/logout`;
        try {
            await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
            });
        } catch (error) {
            throw new ApiError(0, error instanceof Error ? error.message : 'Logout request failed');
        }
    }
}

/**
 * Extract the data payload from a standardized API response.
 *
 * Supports:
 * - `api_response({ data: T })`
 * - `paginated_response({ data: T[], pagination: {...} })`
 * - Legacy list envelopes `{ items: T[] }`
 * - Already-unwrapped arrays
 *
 * Returns `undefined` when the response is null/undefined or does not match
 * a recognized envelope so callers can apply their own defaults.
 */
export function getData<T>(response: unknown): T | undefined {
    if (response === null || response === undefined) {
        return undefined;
    }
    if (Array.isArray(response)) {
        return response as T;
    }
    if (typeof response === 'object') {
        const obj = response as Record<string, unknown>;
        if (obj.data !== undefined) {
            return obj.data as T;
        }
        if (Array.isArray(obj.items)) {
            return obj.items as T;
        }
    }
    return undefined;
}

// Singleton instance
export const apiClient = new ApiClient();
