/**
 * Chat preferences store — CS-01..CS-27 field contract.
 *
 * Persistence: localStorage key `soma_chat_prefs` (real storage, no mock).
 * The server user-preferences route is not wired; the UI must state
 * local-only persistence honestly (never claim a remote save that did not
 * happen). Live re-render is driven by the window event `soma-chat-prefs`.
 */

export type ChatDensity = 'comfortable' | 'compact' | 'tight';
export type BubbleStyle = 'glass' | 'flat' | 'minimal';
export type ReasoningVisibility = 'off' | 'collapsed' | 'expanded';
export type ReasoningStyle = 'steps' | 'prose' | 'raw';
export type ToolArgsMode = 'off' | 'collapsed' | 'expanded';

/** CS-13..20 — tool icon strip keys (one checkbox per key). */
export type ToolIconKey =
    | 'file_read'
    | 'web_search'
    | 'memory'
    | 'packages'
    | 'file_write'
    | 'code_execute'
    | 'document'
    | 'git';

export type ToolIconPrefs = Record<ToolIconKey, boolean>;

export interface ChatPrefs {
    /** CS-01 */
    density: ChatDensity;
    /** CS-02 */
    bubbleStyle: BubbleStyle;
    /** CS-03 — pixel size applied as `--skin-text-base` on the chat host. */
    fontSize: number;
    /** CS-04 */
    showTimestamps: boolean;
    /** CS-05 */
    showAvatars: boolean;
    /** CS-06 */
    showConfidence: boolean;
    /** CS-07 */
    showModelChip: boolean;
    /** CS-08 */
    showReasoning: ReasoningVisibility;
    /** CS-09 */
    reasoningStyle: ReasoningStyle;
    /** CS-10 */
    maxReasoningLines: number;
    /** CS-11 */
    showTokenUsage: boolean;
    /** CS-12 */
    showLatency: boolean;
    /** CS-13..20 */
    toolIcons: ToolIconPrefs;
    /** CS-21 */
    showToolArgs: ToolArgsMode;
    /** CS-22 */
    highlightFailures: boolean;
    /** CS-23 */
    autoExpandHitl: boolean;
    /** CS-24 */
    streamTokens: boolean;
    /** CS-25 */
    enterSends: boolean;
    /** CS-26 */
    soundOnDone: boolean;
    /** CS-27 */
    notifyOnLongJob: boolean;
}

export const CHAT_PREFS_STORAGE_KEY = 'soma_chat_prefs';
export const CHAT_PREFS_EVENT = 'soma-chat-prefs';

export const TOOL_ICON_KEYS: readonly ToolIconKey[] = [
    'file_read',
    'web_search',
    'memory',
    'packages',
    'file_write',
    'code_execute',
    'document',
    'git',
] as const;

export const TOOL_ICON_LABELS: Readonly<Record<ToolIconKey, string>> = {
    file_read: 'file_read',
    web_search: 'web_search',
    memory: 'memory',
    packages: 'packages',
    file_write: 'file_write',
    code_execute: 'code_execute',
    document: 'document',
    git: 'git',
};

export const DENSITY_OPTIONS: readonly ChatDensity[] = [
    'comfortable',
    'compact',
    'tight',
] as const;

export const BUBBLE_STYLE_OPTIONS: readonly BubbleStyle[] = [
    'glass',
    'flat',
    'minimal',
] as const;

export const REASONING_VISIBILITY_OPTIONS: readonly ReasoningVisibility[] = [
    'off',
    'collapsed',
    'expanded',
] as const;

export const REASONING_STYLE_OPTIONS: readonly ReasoningStyle[] = [
    'steps',
    'prose',
    'raw',
] as const;

export const TOOL_ARGS_OPTIONS: readonly ToolArgsMode[] = [
    'off',
    'collapsed',
    'expanded',
] as const;

/** CS-03 allowed font sizes (px). */
export const FONT_SIZE_OPTIONS: readonly number[] = [12, 13, 14, 16, 18] as const;

export const MIN_REASONING_LINES = 4;
export const MAX_REASONING_LINES = 64;
export const DEFAULT_REASONING_LINES = 12;

export const DEFAULT_CHAT_PREFS: ChatPrefs = Object.freeze({
    density: 'comfortable',
    bubbleStyle: 'glass',
    fontSize: 14,
    showTimestamps: true,
    showAvatars: true,
    showConfidence: true,
    showModelChip: true,
    showReasoning: 'collapsed',
    reasoningStyle: 'steps',
    maxReasoningLines: DEFAULT_REASONING_LINES,
    showTokenUsage: true,
    showLatency: true,
    toolIcons: Object.freeze({
        file_read: true,
        web_search: true,
        memory: true,
        packages: false,
        file_write: true,
        code_execute: false,
        document: true,
        git: false,
    }),
    showToolArgs: 'collapsed',
    highlightFailures: true,
    autoExpandHitl: true,
    streamTokens: true,
    enterSends: true,
    soundOnDone: false,
    notifyOnLongJob: true,
}) as ChatPrefs;

function clampLines(n: unknown): number {
    const v = typeof n === 'number' && Number.isFinite(n) ? Math.round(n) : DEFAULT_REASONING_LINES;
    return Math.min(MAX_REASONING_LINES, Math.max(MIN_REASONING_LINES, v));
}

function oneOf<T extends string>(value: unknown, allowed: readonly T[], fallback: T): T {
    return typeof value === 'string' && (allowed as readonly string[]).includes(value)
        ? (value as T)
        : fallback;
}

function bool(value: unknown, fallback: boolean): boolean {
    return typeof value === 'boolean' ? value : fallback;
}

function normalizeToolIcons(raw: unknown): ToolIconPrefs {
    const src = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>;
    const out = {} as ToolIconPrefs;
    for (const key of TOOL_ICON_KEYS) {
        out[key] = bool(src[key], DEFAULT_CHAT_PREFS.toolIcons[key]);
    }
    return out;
}

/**
 * Coerce untrusted stored JSON into a complete ChatPrefs.
 * Unknown keys are dropped; missing keys fall back to defaults.
 */
export function normalizeChatPrefs(raw: unknown): ChatPrefs {
    const src = (raw && typeof raw === 'object' ? raw : {}) as Partial<ChatPrefs>;
    const fontRaw = src.fontSize;
    const font =
        typeof fontRaw === 'number' && (FONT_SIZE_OPTIONS as readonly number[]).includes(fontRaw)
            ? fontRaw
            : DEFAULT_CHAT_PREFS.fontSize;

    return {
        density: oneOf(src.density, DENSITY_OPTIONS, DEFAULT_CHAT_PREFS.density),
        bubbleStyle: oneOf(src.bubbleStyle, BUBBLE_STYLE_OPTIONS, DEFAULT_CHAT_PREFS.bubbleStyle),
        fontSize: font,
        showTimestamps: bool(src.showTimestamps, DEFAULT_CHAT_PREFS.showTimestamps),
        showAvatars: bool(src.showAvatars, DEFAULT_CHAT_PREFS.showAvatars),
        showConfidence: bool(src.showConfidence, DEFAULT_CHAT_PREFS.showConfidence),
        showModelChip: bool(src.showModelChip, DEFAULT_CHAT_PREFS.showModelChip),
        showReasoning: oneOf(
            src.showReasoning,
            REASONING_VISIBILITY_OPTIONS,
            DEFAULT_CHAT_PREFS.showReasoning,
        ),
        reasoningStyle: oneOf(
            src.reasoningStyle,
            REASONING_STYLE_OPTIONS,
            DEFAULT_CHAT_PREFS.reasoningStyle,
        ),
        maxReasoningLines: clampLines(src.maxReasoningLines),
        showTokenUsage: bool(src.showTokenUsage, DEFAULT_CHAT_PREFS.showTokenUsage),
        showLatency: bool(src.showLatency, DEFAULT_CHAT_PREFS.showLatency),
        toolIcons: normalizeToolIcons(src.toolIcons),
        showToolArgs: oneOf(src.showToolArgs, TOOL_ARGS_OPTIONS, DEFAULT_CHAT_PREFS.showToolArgs),
        highlightFailures: bool(src.highlightFailures, DEFAULT_CHAT_PREFS.highlightFailures),
        autoExpandHitl: bool(src.autoExpandHitl, DEFAULT_CHAT_PREFS.autoExpandHitl),
        streamTokens: bool(src.streamTokens, DEFAULT_CHAT_PREFS.streamTokens),
        enterSends: bool(src.enterSends, DEFAULT_CHAT_PREFS.enterSends),
        soundOnDone: bool(src.soundOnDone, DEFAULT_CHAT_PREFS.soundOnDone),
        notifyOnLongJob: bool(src.notifyOnLongJob, DEFAULT_CHAT_PREFS.notifyOnLongJob),
    };
}

/** Read prefs from localStorage. Corrupt or absent storage → defaults. */
export function loadChatPrefs(): ChatPrefs {
    try {
        const raw = localStorage.getItem(CHAT_PREFS_STORAGE_KEY);
        if (!raw) return normalizeChatPrefs(null);
        return normalizeChatPrefs(JSON.parse(raw) as unknown);
    } catch {
        return normalizeChatPrefs(null);
    }
}

/**
 * Persist prefs to localStorage and return the normalized copy that was
 * written. Throws if storage is unavailable (caller surfaces the failure).
 */
export function saveChatPrefs(prefs: ChatPrefs): ChatPrefs {
    const normalized = normalizeChatPrefs(prefs);
    localStorage.setItem(CHAT_PREFS_STORAGE_KEY, JSON.stringify(normalized));
    return normalized;
}

/** Drop stored prefs and return a fresh copy of the defaults. */
export function resetChatPrefs(): ChatPrefs {
    try {
        localStorage.removeItem(CHAT_PREFS_STORAGE_KEY);
    } catch {
        // Storage may be blocked; defaults still apply in-memory.
    }
    return normalizeChatPrefs(null);
}

/** Broadcast saved prefs so open chat / composer / message trees re-render live. */
export function emitChatPrefs(prefs: ChatPrefs): void {
    window.dispatchEvent(
        new CustomEvent<ChatPrefs>(CHAT_PREFS_EVENT, {
            detail: normalizeChatPrefs(prefs),
        }),
    );
}

/** Convenience: load at boot without forcing a write. */
export function getChatPrefs(): ChatPrefs {
    return loadChatPrefs();
}
