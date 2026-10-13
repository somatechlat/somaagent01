/**
 * i18n — SOMA-UI-I18N-001 (UI-wide internationalization).
 *
 * Law: real catalogs only. No mocks. No emojis in any locale.
 * Keys: `domain.camelCase` (I18N-02). Catalogs en/es must stay in parity (I18N-03).
 * Missing key (I18N-10): show the key in dev; English fallback in prod + log.
 * Locale persistence: `soma_locale` (one source). `<html lang>` tracks the locale (I18N-05).
 * Live switch — no reload. Components re-render via `onLocaleChange`.
 */
import en from './en.json';
import es from './es.json';

export type Locale = 'en' | 'es';

export const SUPPORTED_LOCALES: readonly Locale[] = ['en', 'es'] as const;
export const DEFAULT_LOCALE: Locale = 'en';
export const LOCALE_STORAGE_KEY = 'soma_locale';
export const LOCALE_CHANGE_EVENT = 'soma-locale-change';

type Catalog = Record<string, string>;

const CATALOGS: Record<Locale, Catalog> = {
    en: en as Catalog,
    es: es as Catalog,
};

const listeners = new Set<(locale: Locale) => void>();

function isLocale(value: unknown): value is Locale {
    return typeof value === 'string' && (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

function readStoredLocale(): Locale | null {
    try {
        const direct = localStorage.getItem(LOCALE_STORAGE_KEY);
        if (isLocale(direct)) return direct;
        // One source going forward: migrate the earlier Interface pref if present.
        const raw = localStorage.getItem('soma_interface');
        if (raw) {
            const prefs = JSON.parse(raw) as { language?: unknown };
            if (isLocale(prefs.language)) return prefs.language;
        }
    } catch {
        /* storage blocked — fall through to default */
    }
    return null;
}

function persistLocale(locale: Locale): void {
    try {
        localStorage.setItem(LOCALE_STORAGE_KEY, locale);
    } catch {
        /* storage blocked — session-only locale */
    }
}

function applyHtmlLang(locale: Locale): void {
    if (typeof document !== 'undefined') {
        document.documentElement.lang = locale;
    }
}

function interpolate(template: string, params?: Record<string, string | number>): string {
    if (!params) return template;
    return template.replace(/\{(\w+)\}/g, (match, name: string) => {
        const value = params[name];
        return value === undefined ? match : String(value);
    });
}

let currentLocale: Locale = readStoredLocale() ?? DEFAULT_LOCALE;
persistLocale(currentLocale);
applyHtmlLang(currentLocale);

/** Translate `key` in the active locale. Optional `{name}` params are substituted. */
export function t(key: string, params?: Record<string, string | number>): string {
    const active = CATALOGS[currentLocale]?.[key];
    if (active !== undefined) {
        return interpolate(active, params);
    }
    if (import.meta.env.DEV) {
        return key;
    }
    console.warn(`[i18n] missing key "${key}" (locale=${currentLocale})`);
    const fallback = CATALOGS[DEFAULT_LOCALE][key];
    return fallback === undefined ? key : interpolate(fallback, params);
}

/** Active locale code (`en` | `es`). */
export function getLocale(): Locale {
    return currentLocale;
}

/**
 * Switch the live locale. Persists to `soma_locale`, sets `<html lang>`,
 * notifies listeners (I18N-05). Unknown codes fall back to `en`.
 */
export function setLocale(next: string): Locale {
    const locale = isLocale(next) ? next : DEFAULT_LOCALE;
    if (!isLocale(next)) {
        console.warn(`[i18n] unsupported locale "${next}" — falling back to ${DEFAULT_LOCALE}`);
    }
    const changed = locale !== currentLocale;
    currentLocale = locale;
    persistLocale(locale);
    applyHtmlLang(locale);
    if (changed) {
        for (const listener of [...listeners]) {
            listener(locale);
        }
        if (typeof window !== 'undefined') {
            window.dispatchEvent(
                new CustomEvent<Locale>(LOCALE_CHANGE_EVENT, { detail: locale }),
            );
        }
    }
    return currentLocale;
}

/** Subscribe to locale changes. Returns an unsubscribe function. */
export function onLocaleChange(listener: (locale: Locale) => void): () => void {
    listeners.add(listener);
    return () => {
        listeners.delete(listener);
    };
}
