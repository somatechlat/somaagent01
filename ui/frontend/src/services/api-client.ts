/**
 * Eye of God API Client
 * Per Eye of God UIX Design Section 4.3
 *
 * VIBE COMPLIANT:
 * - Real implementation (no stubs)
 * - Proper error handling
 * - Timeout and retry support
 */

export interface ApiClientConfig {
    baseUrl: string;
    timeout: number;
    retries: number;
}

export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

export class ApiClient {
    private config: ApiClientConfig;
    private token: string | null = null;

    constructor(config: Partial<ApiClientConfig> = {}) {
        this.config = {
            baseUrl: config.baseUrl ?? '/api/v2',
            timeout: config.timeout ?? 30000,
            retries: config.retries ?? 3,
        };
    }

    /**
     * Set authentication token.
     */
    setToken(token: string): void {
        this.token = token;
    }

    /**
     * Clear authentication token.
     */
    clearToken(): void {
        this.token = null;
    }

    /**
     * Make an API request with retry support.
     */
    async request<T>(
        method: string,
        path: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.config.baseUrl}${path}`;
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
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
}

// Singleton instance
export const apiClient = new ApiClient();
