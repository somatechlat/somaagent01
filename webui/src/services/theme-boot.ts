/**
 * UI Theme boot — light by default, dark only via explicit toggle.
 * Persists choice in localStorage. No silent dark-first overrides.
 */

const STORAGE_KEY = 'soma-theme';

export type UiTheme = 'light' | 'dark';

export function getTheme(): UiTheme {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'dark' ? 'dark' : 'light';
}

export function applyTheme(theme: UiTheme): void {
    const root = document.documentElement;
    if (theme === 'dark') {
        root.setAttribute('data-theme', 'dark');
    } else {
        root.setAttribute('data-theme', 'light');
        root.removeAttribute('data-theme');
    }
    localStorage.setItem(STORAGE_KEY, theme);
    window.dispatchEvent(new CustomEvent('soma-theme-change', { detail: { theme } }));
}

export function toggleTheme(): UiTheme {
    const next: UiTheme = getTheme() === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    return next;
}

export function bootTheme(): void {
    applyTheme(getTheme());
}

declare global {
    interface Window {
        somaTheme: {
            get: typeof getTheme;
            set: typeof applyTheme;
            toggle: typeof toggleTheme;
        };
    }
}

if (typeof window !== 'undefined') {
    window.somaTheme = {
        get: getTheme,
        set: applyTheme,
        toggle: toggleTheme,
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => bootTheme(), { once: true });
    } else {
        bootTheme();
    }
}
