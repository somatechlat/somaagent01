/**
 * SomaAgent SaaS — Chat Workspace (Agent Zero parity)
 *
 * 3-column workspace shell:
 *   Left  — brand, New Chat, searchable conversation list (rename/delete/export),
 *           user card (/auth/me), nav to Memory / Models / Channels / Settings
 *   Center — topbar (title, model, pause/stop/reset), message stream + tool
 *           timeline, welcome empty state, composer
 *   Right  — canvas rail: Memory / Files / Channel panels (real APIs)
 *
 * Transport: WebSocket /ws/v2/chat/:id + REST /chat/conversations*.
 * Dark-first, AAAS token palette. No mocks, no placeholders.
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state, query } from 'lit/decorators.js';
import { WebSocketClient } from '../services/websocket-client.js';
import { apiClient } from '../services/api-client.js';
import type { ToolCallStep, ToolStepStatus } from '../components/saas-tool-timeline.js';
import type { ComposerSendDetail } from '../components/saas-composer.js';
import type { ChatControlAction, ConnectionStatus } from '../components/saas-chat-topbar.js';
import { formatRelative } from '../utils/markdown.js';
import '../components/saas-message.js';
import '../components/saas-tool-timeline.js';
import '../components/saas-chat-topbar.js';
import '../components/saas-composer.js';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    confidence?: number;
    streaming?: boolean;
    tools?: ToolCallStep[];
    stopped?: boolean;
    error?: string;
    attachments?: { name: string; type?: string; size?: number }[];
}

export interface Conversation {
    id: string;
    title: string;
    lastMessage: string;
    updatedAt: string;
    messageCount: number;
}

interface ToolCallPayload {
    conversation_id?: string;
    response_id?: string;
    iteration?: number;
    index?: number;
    tool_call_id?: string | null;
    name?: string;
    arguments_delta?: string;
    arguments?: Record<string, unknown> | null;
    result?: unknown;
    ok?: boolean;
    error?: string | null;
    duration_ms?: number;
    status?: string;
}

interface MemoryItem {
    id: string;
    type: string;
    content: string;
    summary?: string;
    tags?: string[];
    score?: number;
    timestamp?: string;
}

interface ChannelItem {
    id: string;
    kind: string;
    status: string;
    capsule_id?: string | null;
}

type AgentMode = 'STD' | 'TRN' | 'ADM' | 'DEV' | 'RO' | 'DGR';
type CanvasTab = 'memory' | 'files' | 'channel';

const ICON = (name: string, size = 20) =>
    html`<span class="material-symbols-outlined" style="font-size:${size}px" aria-hidden="true">${name}</span>`;

@customElement('saas-chat')
export class SaasChat extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--aaas-bg-void, #f5f5f5);
            font-family: var(--aaas-font-sans, 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--aaas-text-primary, #ffffff);
            overflow: hidden;
        }

        * {
            box-sizing: border-box;
        }

        *:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: 2px;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        button {
            font: inherit;
            cursor: pointer;
            border: none;
            background: transparent;
            color: inherit;
        }

        input, textarea, select {
            font: inherit;
        }

        /* =========================
           LEFT SIDEBAR
           ========================= */
        .sidebar {
            width: 272px;
            background: var(--aaas-bg-sidebar, #ffffff);
            border-right: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            min-height: 0;
        }

        .sidebar-header {
            padding: 16px 16px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 0;
        }

        .brand-icon {
            width: 32px;
            height: 32px;
            background: var(--aaas-accent, #e8e4dc);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .brand-icon svg {
            width: 16px;
            height: 16px;
            stroke: var(--aaas-bg-void, #f5f5f5);
            fill: none;
        }

        .brand-name {
            font-size: 15px;
            font-weight: 600;
            letter-spacing: -0.01em;
        }

        .new-chat-btn {
            margin: 4px 16px 12px;
            padding: 10px 14px;
            border-radius: var(--aaas-radius-md, 8px);
            background: var(--aaas-accent, #e8e4dc);
            color: var(--aaas-bg-void, #f5f5f5);
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: background 150ms ease, transform 150ms ease;
            width: calc(100% - 32px);
        }

        .new-chat-btn:hover {
            background: var(--aaas-accent-hover, #ffffff);
        }

        .new-chat-btn .material-symbols-outlined {
            font-size: 18px;
        }

        .search-wrap {
            padding: 0 16px 10px;
            position: relative;
        }

        .search-wrap .material-symbols-outlined {
            position: absolute;
            left: 26px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 16px;
            color: var(--aaas-text-muted, #999999);
            pointer-events: none;
        }

        .search-input {
            width: 100%;
            padding: 8px 10px 8px 34px;
            border-radius: var(--aaas-radius-md, 8px);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-bg-card, #1e1e1e);
            color: var(--aaas-text-primary, #ffffff);
            font-size: 13px;
            outline: none;
            transition: border-color 150ms ease;
        }

        .search-input:focus {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.16));
        }

        .search-input::placeholder {
            color: var(--aaas-text-muted, #999999);
        }

        .conversations-section {
            padding: 0 8px;
            flex: 1;
            overflow-y: auto;
            min-height: 0;
        }

        .section-label {
            font-size: 10px;
            text-transform: uppercase;
            color: var(--aaas-text-muted, #999999);
            padding: 10px 10px 6px;
            font-weight: 600;
            letter-spacing: 0.08em;
        }

        .conversation-item {
            position: relative;
            padding: 9px 10px;
            border-radius: var(--aaas-radius-md, 8px);
            cursor: pointer;
            transition: background 120ms ease;
            margin-bottom: 2px;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }

        .conversation-item:hover,
        .conversation-item:focus-within {
            background: var(--aaas-bg-hover, #141414);
        }

        .conversation-item.active {
            background: var(--aaas-bg-active, #1a1a1a);
        }

        .conversation-item .conv-body {
            flex: 1;
            min-width: 0;
        }

        .conversation-title {
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--aaas-text-primary, #ffffff);
        }

        .conversation-meta {
            font-size: 11px;
            color: var(--aaas-text-muted, #999999);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .conv-actions {
            display: flex;
            gap: 2px;
            opacity: 0;
            transition: opacity 120ms ease;
            flex-shrink: 0;
        }

        .conversation-item:hover .conv-actions,
        .conversation-item:focus-within .conv-actions {
            opacity: 1;
        }

        .conv-action {
            width: 26px;
            height: 26px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--aaas-text-muted, #999999);
            transition: background 120ms ease, color 120ms ease;
        }

        .conv-action:hover {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-text-primary, #ffffff);
        }

        .conv-action.danger:hover {
            color: var(--aaas-danger, #ef4444);
        }

        .conv-action .material-symbols-outlined {
            font-size: 15px;
        }

        .rename-row {
            display: flex;
            gap: 4px;
            align-items: center;
            width: 100%;
        }

        .rename-input {
            flex: 1;
            min-width: 0;
            padding: 3px 6px;
            border-radius: 4px;
            border: 1px solid var(--aaas-info, #3b82f6);
            background: var(--aaas-bg-card, #1e1e1e);
            color: var(--aaas-text-primary, #ffffff);
            font-size: 12px;
            outline: none;
        }

        .rename-confirm {
            color: var(--aaas-success, #22c55e);
            width: 22px;
            height: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
        }

        .rename-confirm:hover { background: rgba(34,197,94,0.15); }

        .skeleton-list {
            padding: 4px 10px;
        }

        .skeleton-row {
            height: 46px;
            border-radius: var(--aaas-radius-md, 8px);
            background: linear-gradient(90deg, var(--aaas-bg-hover, #141414) 25%, var(--aaas-bg-active, #1a1a1a) 50%, var(--aaas-bg-hover, #141414) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.4s ease-in-out infinite;
            margin-bottom: 6px;
        }

        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .empty-list {
            padding: 24px 14px;
            text-align: center;
            color: var(--aaas-text-muted, #999999);
            font-size: 12px;
            line-height: 1.55;
        }

        /* Nav links */
        .nav-links {
            padding: 8px 12px;
            border-top: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .nav-link {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 10px;
            border-radius: var(--aaas-radius-md, 8px);
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
            cursor: pointer;
            transition: background 120ms ease, color 120ms ease;
            width: 100%;
            text-align: left;
        }

        .nav-link:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .nav-link .material-symbols-outlined {
            font-size: 18px;
            width: 20px;
            text-align: center;
        }

        /* User card */
        .user-section {
            padding: 12px 16px;
            border-top: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .user-avatar {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            background: var(--aaas-bg-active, #1a1a1a);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            flex-shrink: 0;
        }

        .user-info {
            flex: 1;
            min-width: 0;
        }

        .user-name {
            font-size: 13px;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .user-role {
            font-size: 11px;
            color: var(--aaas-text-muted, #999999);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .logout-btn {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            background: transparent;
            border: none;
            color: var(--aaas-text-muted, #999999);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 120ms ease;
        }

        .logout-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-danger, #ef4444);
        }

        /* =========================
           MAIN COLUMN
           ========================= */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
            min-width: 0;
            background: var(--aaas-bg-void, #f5f5f5);
        }

        .header {
            padding: 12px 24px;
            background: var(--aaas-bg-void, #f5f5f5);
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            align-items: center;
            gap: 16px;
            flex-shrink: 0;
        }

        .header saas-chat-topbar {
            flex: 1;
            min-width: 0;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }

        /* Mode selector */
        .mode-selector {
            position: relative;
        }

        .mode-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: var(--aaas-radius-md, 8px);
            background: var(--aaas-surface, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            font-size: 12px;
            font-weight: 500;
            color: var(--aaas-text-secondary, #a1a1a1);
            cursor: pointer;
            transition: all 120ms ease;
        }

        .mode-btn:hover {
            background: var(--aaas-surface-hover, #1a1a1a);
        }

        .mode-badge {
            padding: 2px 6px;
            border-radius: 4px;
            background: var(--aaas-accent, #e8e4dc);
            color: var(--aaas-bg-void, #f5f5f5);
            font-size: 10px;
            font-weight: 700;
        }

        .mode-dropdown {
            position: absolute;
            top: calc(100% + 6px);
            right: 0;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-lg, 12px);
            box-shadow: var(--aaas-shadow-lg, 0 8px 24px rgba(0,0,0,0.6));
            min-width: 240px;
            z-index: 100;
            overflow: hidden;
            display: none;
            padding: 4px;
        }

        .mode-dropdown.open {
            display: block;
        }

        .mode-option {
            padding: 10px 12px;
            cursor: pointer;
            border-radius: var(--aaas-radius-md, 8px);
            transition: background 120ms ease;
            border: none;
            width: 100%;
            text-align: left;
            background: transparent;
            color: inherit;
        }

        .mode-option:hover {
            background: var(--aaas-bg-hover, #141414);
        }

        .mode-option.active {
            background: var(--aaas-bg-active, #1a1a1a);
        }

        .mode-option.locked {
            opacity: 0.45;
            cursor: not-allowed;
        }

        .mode-option-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 2px;
        }

        .mode-option-title {
            font-size: 13px;
            font-weight: 500;
            color: var(--aaas-text-primary, #ffffff);
        }

        .mode-option-desc {
            font-size: 11px;
            color: var(--aaas-text-muted, #999999);
        }

        .lock-icon {
            font-size: 12px;
            color: var(--aaas-text-muted, #999999);
        }

        /* Messages */
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 28px 24px 16px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            scroll-behavior: smooth;
        }

        @media (prefers-reduced-motion: reduce) {
            .messages { scroll-behavior: auto; }
        }

        /* Welcome / empty state */
        .welcome {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px 24px;
            gap: 8px;
        }

        .welcome-icon {
            width: 64px;
            height: 64px;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
        }

        .welcome-icon .material-symbols-outlined {
            font-size: 30px;
            color: var(--aaas-accent, #e8e4dc);
        }

        .welcome h2 {
            margin: 0;
            font-size: 22px;
            font-weight: 600;
            letter-spacing: -0.02em;
        }

        .welcome p {
            margin: 0;
            color: var(--aaas-text-secondary, #a1a1a1);
            max-width: 440px;
            line-height: 1.6;
            font-size: 14px;
        }

        .welcome-actions {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-top: 22px;
            width: 100%;
            max-width: 520px;
        }

        .welcome-action {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 14px;
            border-radius: var(--aaas-radius-lg, 12px);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-bg-card, #1e1e1e);
            cursor: pointer;
            text-align: left;
            transition: border-color 150ms ease, background 150ms ease, transform 150ms ease;
            color: inherit;
            font: inherit;
        }

        .welcome-action:hover {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.16));
            background: var(--aaas-bg-hover, #141414);
            transform: translateY(-1px);
        }

        .welcome-action .material-symbols-outlined {
            font-size: 20px;
            color: var(--aaas-accent, #e8e4dc);
            margin-top: 1px;
        }

        .welcome-action .wa-title {
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 2px;
        }

        .welcome-action .wa-desc {
            font-size: 11px;
            color: var(--aaas-text-muted, #999999);
            line-height: 1.45;
        }

        /* Message skeletons */
        .msg-skeleton {
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-width: 70%;
        }

        .msg-skeleton .bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, var(--aaas-bg-hover, #141414) 25%, var(--aaas-bg-active, #1a1a1a) 50%, var(--aaas-bg-hover, #141414) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.4s ease-in-out infinite;
        }

        .msg-skeleton .bar.short { width: 40%; }
        .msg-skeleton .bar.mid { width: 72%; }

        /* =========================
           RIGHT CANVAS
           ========================= */
        .right-canvas {
            display: flex;
            flex-direction: row;
            border-left: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-bg-sidebar, #ffffff);
            height: 100vh;
            flex-shrink: 0;
        }

        .right-canvas:not(.open) {
            width: 48px;
        }

        .right-canvas.open {
            width: 320px;
        }

        .canvas-rail {
            width: 48px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            padding: 12px 0;
            border-right: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .rail-btn {
            width: 36px;
            height: 36px;
            border-radius: var(--aaas-radius-md, 8px);
            border: none;
            background: transparent;
            cursor: pointer;
            color: var(--aaas-text-muted, #999999);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            transition: background 120ms ease, color 120ms ease;
        }

        .rail-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .rail-btn.active {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-accent, #e8e4dc);
        }

        .rail-btn .material-symbols-outlined {
            font-size: 20px;
        }

        .canvas-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }

        .canvas-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 14px;
            font-weight: 600;
            font-size: 13px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            text-transform: capitalize;
            flex-shrink: 0;
        }

        .canvas-header .icon-btn {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--aaas-text-muted, #999999);
        }

        .canvas-header .icon-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .canvas-body {
            padding: 12px;
            overflow: auto;
            flex: 1;
            min-height: 0;
        }

        .canvas-hint {
            font-size: 12px;
            color: var(--aaas-text-muted, #999999);
            line-height: 1.55;
            padding: 4px 2px 12px;
        }

        .canvas-search {
            width: 100%;
            padding: 7px 10px;
            border-radius: var(--aaas-radius-md, 8px);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-bg-card, #1e1e1e);
            color: var(--aaas-text-primary, #ffffff);
            font-size: 12px;
            outline: none;
            margin-bottom: 10px;
        }

        .canvas-search:focus {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.16));
        }

        .memory-card {
            padding: 10px;
            border-radius: var(--aaas-radius-md, 8px);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-bg-card, #1e1e1e);
            margin-bottom: 8px;
        }

        .memory-card .type {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--aaas-accent, #e8e4dc);
            font-weight: 600;
            margin-bottom: 4px;
        }

        .memory-card .content {
            font-size: 12px;
            line-height: 1.5;
            color: var(--aaas-text-secondary, #a1a1a1);
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .memory-card .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-top: 6px;
        }

        .tag-chip {
            font-size: 10px;
            padding: 1px 7px;
            border-radius: 9999px;
            background: var(--aaas-bg-void, #f5f5f5);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            color: var(--aaas-text-muted, #999999);
        }

        .file-row {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 10px;
            border-radius: var(--aaas-radius-md, 8px);
            margin-bottom: 4px;
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .file-row:hover {
            background: var(--aaas-bg-hover, #141414);
        }

        .file-row .material-symbols-outlined {
            font-size: 16px;
            color: var(--aaas-text-muted, #999999);
        }

        .file-row .fname {
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .file-row .fsize {
            font-size: 10px;
            color: var(--aaas-text-muted, #999999);
            flex-shrink: 0;
        }

        .channel-row {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            border-radius: var(--aaas-radius-md, 8px);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-bg-card, #1e1e1e);
            margin-bottom: 8px;
            font-size: 12px;
        }

        .channel-kind {
            text-transform: capitalize;
            flex: 1;
            color: var(--aaas-text-primary, #ffffff);
            font-weight: 500;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            flex-shrink: 0;
            background: var(--aaas-text-muted, #999999);
        }

        .status-dot.ok { background: var(--aaas-success, #22c55e); }
        .status-dot.err { background: var(--aaas-danger, #ef4444); }
        .status-dot.warn { background: var(--aaas-warning, #f59e0b); }

        .panel-skeleton .srow {
            height: 56px;
            border-radius: var(--aaas-radius-md, 8px);
            background: linear-gradient(90deg, var(--aaas-bg-hover, #141414) 25%, var(--aaas-bg-active, #1a1a1a) 50%, var(--aaas-bg-hover, #141414) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.4s ease-in-out infinite;
            margin-bottom: 8px;
        }

        /* Agent selector */
        .agent-select {
            padding: 5px 8px;
            border-radius: var(--aaas-radius-md, 8px);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-surface, #141414);
            color: var(--aaas-text-primary, #ffffff);
            font-size: 12px;
            outline: none;
            max-width: 160px;
        }

        /* Scrollbars */
        .conversations-section::-webkit-scrollbar,
        .messages::-webkit-scrollbar,
        .canvas-body::-webkit-scrollbar {
            width: 6px;
        }

        .conversations-section::-webkit-scrollbar-thumb,
        .messages::-webkit-scrollbar-thumb,
        .canvas-body::-webkit-scrollbar-thumb {
            background: var(--aaas-border-light, rgba(255,255,255,0.08));
            border-radius: 3px;
        }

        /* Responsive */
        @media (max-width: 960px) {
            .sidebar {
                width: 220px;
            }
            .right-canvas.open {
                width: 260px;
            }
            .welcome-actions {
                grid-template-columns: 1fr;
            }
        }
    `;

    @property({ type: String }) sessionId = '';
    @state() private _messages: ChatMessage[] = [];
    @state() private _conversations: Conversation[] = [];
    @state() private _conversationsLoading = true;
    @state() private _messagesLoading = false;
    @state() private _isStreaming = false;
    @state() private _streamContent = '';
    @state() private _activeTools: ToolCallStep[] = [];
    @state() private _paused = false;
    @state() private _currentMode: AgentMode = 'STD';
    @state() private _showModeDropdown = false;
    @state() private _activeConversationId = '';
    @state() private _wsConnected = false;
    @state() private _wsEverConnected = false;
    @state() private _wsReconnecting = false;
    @state() private _connectionStatus: ConnectionStatus = 'ok';
    @state() private _agents: { id: string; name: string; description: string; capsule_id?: string }[] = [];
    @state() private _selectedAgentId = '';
    @state() private _modelLabel = '';
    @state() private _chatTitle = 'New conversation';
    @state() private _userName = 'User';
    @state() private _userRole = 'Member';
    @state() private _userInitials = 'U';
    @state() private _showRightPanel = false;
    @state() private _rightPanelTab: CanvasTab = 'memory';
    @state() private _convFilter = '';
    @state() private _renamingId = '';
    @state() private _renameDraft = '';

    @state() private _memories: MemoryItem[] = [];
    @state() private _memoryLoading = false;
    @state() private _memoryQuery = '';

    @state() private _channels: ChannelItem[] = [];
    @state() private _channelsLoading = false;

    @query('.messages') private _messagesContainer!: HTMLElement;
    @query('.rename-input') private _renameInput!: HTMLInputElement;

    private _wsClient: WebSocketClient | null = null;
    private _turnStopped = false;
    private _activeResponseId = '';
    private _reconnectBannerTimer = 0;
    private _connectionChipTimer = 0;
    private _lastErrorMessage = '';

    private _modes = [
        { id: 'STD', name: 'Standard', desc: 'Normal operation', locked: false },
        { id: 'DEV', name: 'Developer', desc: 'Debug tools, logs', locked: false },
        { id: 'TRN', name: 'Training', desc: 'Cognitive parameters', locked: true },
        { id: 'ADM', name: 'Admin', desc: 'Agent configuration', locked: true },
        { id: 'RO', name: 'Read-Only', desc: 'View only, no actions', locked: false },
        { id: 'DGR', name: 'Degraded', desc: 'Limited tools, resilience budget (governor)', locked: false },
    ];

    private _brainHealthTimer = 0;

    async connectedCallback() {
        super.connectedCallback();
        await this._loadUser();
        await this._loadAgents();
        await this._loadConversations();
        document.addEventListener('click', this._handleOutsideClick);
        void this._pollBrainConnector();
        this._brainHealthTimer = window.setInterval(() => void this._pollBrainConnector(), 15000);
        window.addEventListener('keydown', this._onGlobalKeydown);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this._wsClient) {
            this._wsClient.disconnect();
            this._wsClient = null;
        }
        document.removeEventListener('click', this._handleOutsideClick);
        window.removeEventListener('keydown', this._onGlobalKeydown);
        window.clearTimeout(this._reconnectBannerTimer);
        window.clearTimeout(this._connectionChipTimer);
    }

    protected updated(changed: PropertyValues) {
        if (changed.has('_renamingId') && this._renamingId && this._renameInput) {
            this._renameInput.focus();
            this._renameInput.select();
        }
    }

    private _onGlobalKeydown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
            this._showModeDropdown = false;
            if (this._renamingId) {
                this._renamingId = '';
                this._renameDraft = '';
            }
        }
    };

    private _handleOutsideClick = (e: Event) => {
        const target = e.target as HTMLElement;
        if (!target.closest('.mode-selector')) {
            this._showModeDropdown = false;
        }
    };

    // ==========================================================================
    // DATA LOADING (real APIs only)
    // ==========================================================================


    /**
     * Availability banner is driven by the agent SomaBrain connector circuit
     * (admin/core/somabrain_connector.py) — not a raw browser probe of SomaBrain.
     */
    private async _pollBrainConnector(): Promise<void> {
        try {
            const h = await apiClient.get<{
                connected: boolean;
                circuit: string;
                last_error?: string | null;
            }>('/core/brain-connector');
            if (h && h.connected && h.circuit === 'closed') {
                this._connectionStatus = 'ok';
                this._wsReconnecting = false;
            } else if (h && h.circuit === 'open') {
                this._connectionStatus = 'degraded';
            } else {
                this._connectionStatus = 'reconnecting';
            }
            this.requestUpdate();
        } catch {
            // Keep last state on poll failure; do not spam the banner.
        }
    }

    private async _loadUser() {
        try {
            const me = await apiClient.get<{ name?: string; username?: string; email?: string; role?: string }>(
                '/auth/me',
            );
            const name = me.name || me.username || me.email || 'User';
            this._userName = name;
            this._userRole = me.role || 'Member';
            this._userInitials = name
                .split(/\s+/)
                .map((p) => p[0])
                .join('')
                .slice(0, 2)
                .toUpperCase() || 'U';
        } catch {
            this._userName = 'User';
            this._userInitials = 'U';
        }
    }

    private async _loadAgents(): Promise<void> {
        try {
            const data = await apiClient.get<{ agents: { agent_id: string; name: string; description: string; capsule_id?: string }[]; total: number }>('/agents/');
            const agents = (data.agents || []).map((agent) => ({
                id: agent.agent_id,
                name: agent.name,
                description: agent.description,
                capsule_id: agent.capsule_id,
            }));
            this._agents = agents;

            const params = new URLSearchParams(window.location.search);
            const queryAgentId = params.get('agent');
            if (queryAgentId && agents.some((a) => a.id === queryAgentId)) {
                this._selectedAgentId = queryAgentId;
            } else if (agents.length === 1) {
                this._selectedAgentId = agents[0].id;
            } else if (agents.length > 1 && !this._selectedAgentId) {
                this._selectedAgentId = agents[0].id;
            }

            if (this._selectedAgentId) {
                this._connectWebSocket();
            }
        } catch (error) {
            console.error('[SaasChat] Failed to load agents:', error);
        }
    }

    private async _loadConversations(): Promise<void> {
        this._conversationsLoading = true;
        try {
            const response = await apiClient.get('/chat/conversations');
            const items = Array.isArray(response)
                ? response
                : (response as { data?: Conversation[] }).data || [];

            this._conversations = items.map((conv: Record<string, unknown>) => ({
                id: String(conv.id ?? ''),
                title: (conv.title as string) ?? 'Untitled',
                lastMessage: (conv.last_message as string) ?? '',
                updatedAt: (conv.updated_at as string) ?? '',
                messageCount: (conv.message_count as number) ?? 0,
            }));
        } catch (error) {
            console.error('[SaasChat] Failed to load conversations:', error);
            this._conversations = [];
        } finally {
            this._conversationsLoading = false;
        }
    }

    private async _createConversation(agentId: string): Promise<string | null> {
        try {
            const data = await apiClient.post<{ id?: string }>('/chat/conversations', {
                agent_id: agentId,
            });
            return data?.id ?? null;
        } catch (error) {
            console.error('[SaasChat] Failed to create conversation:', error);
            return null;
        }
    }

    private async _renameConversation(id: string, title: string) {
        const trimmed = title.trim();
        if (!trimmed) return;
        try {
            await apiClient.patch(`/chat/conversations/${id}`, { title: trimmed });
            this._conversations = this._conversations.map((c) =>
                c.id === id ? { ...c, title: trimmed } : c,
            );
            if (id === this._activeConversationId) {
                this._chatTitle = trimmed;
            }
        } catch (error) {
            console.error('[SaasChat] Rename failed:', error);
        } finally {
            this._renamingId = '';
            this._renameDraft = '';
        }
    }

    private async _deleteConversation(id: string) {
        try {
            await apiClient.delete(`/chat/conversations/${id}`);
            this._conversations = this._conversations.filter((c) => c.id !== id);
            if (id === this._activeConversationId) {
                this._activeConversationId = '';
                this._messages = [];
                this._chatTitle = 'New conversation';
            }
        } catch (error) {
            console.error('[SaasChat] Delete failed:', error);
        }
    }

    private async _exportConversation(conv: Conversation) {
        let messages: unknown[] = [];
        if (conv.id === this._activeConversationId) {
            messages = this._messages;
        } else {
            try {
                const response = await apiClient.get(`/chat/conversations/${conv.id}/messages`);
                const items = Array.isArray(response)
                    ? response
                    : (response as { data?: unknown[] }).data || [];
                messages = items;
            } catch {
                messages = [];
            }
        }
        const blob = new Blob(
            [
                JSON.stringify(
                    {
                        conversation_id: conv.id,
                        title: conv.title,
                        exported_at: new Date().toISOString(),
                        messages,
                    },
                    null,
                    2,
                ),
            ],
            { type: 'application/json' },
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `soma-chat-${conv.id || 'export'}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // ==========================================================================
    // RIGHT CANVAS PANELS
    // ==========================================================================

    private _openRightPanel(tab: CanvasTab) {
        if (this._showRightPanel && this._rightPanelTab === tab) {
            this._showRightPanel = false;
            return;
        }
        this._rightPanelTab = tab;
        this._showRightPanel = true;
        if (tab === 'memory') void this._loadMemories();
        if (tab === 'channel') void this._loadChannels();
    }

    private async _loadMemories() {
        this._memoryLoading = true;
        try {
            const response = (await apiClient.get('/memory/')) as {
                memories?: Array<{
                    text?: string;
                    content?: string | Record<string, unknown>;
                    coord?: string;
                    score?: number;
                    created_at?: string;
                    kind?: string;
                }>;
                total?: number;
            };
            const hits = Array.isArray(response?.memories) ? response.memories : [];
            this._memories = hits.map((raw, index) => {
                const payload = typeof raw.content === 'object' && raw.content !== null ? raw.content : null;
                const text =
                    raw.text ||
                    (typeof raw.content === 'string' ? raw.content : '') ||
                    (payload ? String((payload as Record<string, unknown>).text ?? '') : '');
                return {
                    id: raw.coord || `mem-${index}`,
                    type: String(raw.kind || 'episodic'),
                    content: text,
                    score: typeof raw.score === 'number' ? raw.score : 0,
                    timestamp: raw.created_at || new Date().toISOString(),
                } as MemoryItem;
            });
        } catch {
            this._memories = [];
        } finally {
            this._memoryLoading = false;
        }
    }

    private async _searchMemories() {
        const q = this._memoryQuery.trim();
        if (!q) {
            await this._loadMemories();
            return;
        }
        this._memoryLoading = true;
        try {
            const response = (await apiClient.post('/memory/recall', {
                query: q,
                top_k: 20,
            })) as {
                memories?: Array<{
                    text?: string;
                    content?: string | Record<string, unknown>;
                    coord?: string;
                    score?: number;
                    created_at?: string;
                    kind?: string;
                }>;
            };
            const hits = Array.isArray(response?.memories) ? response.memories : [];
            this._memories = hits.map((raw, index) => {
                const payload = typeof raw.content === 'object' && raw.content !== null ? raw.content : null;
                const text =
                    raw.text ||
                    (typeof raw.content === 'string' ? raw.content : '') ||
                    (payload ? String((payload as Record<string, unknown>).text ?? '') : '');
                return {
                    id: raw.coord || `mem-${index}`,
                    type: String(raw.kind || 'episodic'),
                    content: text,
                    score: typeof raw.score === 'number' ? raw.score : 0,
                    timestamp: raw.created_at || new Date().toISOString(),
                } as MemoryItem;
            });
        } catch {
            this._memories = [];
        } finally {
            this._memoryLoading = false;
        }
    }

    private async _loadChannels() {
        this._channelsLoading = true;
        const normalize = (response: unknown): ChannelItem[] => {
            if (Array.isArray(response)) return response as ChannelItem[];
            const obj = response as { channels?: ChannelItem[] } | null;
            if (obj && Array.isArray(obj.channels)) return obj.channels;
            return [];
        };
        try {
            // Prefer the settings namespace; fall back to the bridges endpoint
            // that saas-settings-channels uses.
            try {
                const response = await apiClient.get('/bridges/channels');
                this._channels = normalize(response);
            } catch {
                const response = await apiClient.get('/bridges/channels');
                this._channels = normalize(response);
            }
        } catch {
            // Fail closed to an empty state — never invent channel data.
            this._channels = [];
        } finally {
            this._channelsLoading = false;
        }
    }

    private _conversationFiles(): { name: string; type?: string; size?: number }[] {
        const seen = new Set<string>();
        const files: { name: string; type?: string; size?: number }[] = [];
        for (const msg of this._messages) {
            for (const a of msg.attachments ?? []) {
                if (!seen.has(a.name)) {
                    seen.add(a.name);
                    files.push(a);
                }
            }
        }
        return files;
    }

    // ==========================================================================
    // WEBSOCKET
    // ==========================================================================

    private _connectWebSocket(): void {
        if (this._wsClient) {
            this._wsClient.disconnect();
            this._wsClient = null;
        }

        const agent = this._agents.find((a) => a.id === this._selectedAgentId);
        if (!agent) return;

        const wsId = agent.capsule_id || agent.id;
        if (!wsId) return;

        this._wsClient = new WebSocketClient({ url: `/ws/v2/chat/${wsId}` });

        this._wsClient.on('chat.message', (data) => {
            this._handleIncomingMessage(data as ChatMessage);
        });
        this._wsClient.on('chat.delta', (data) => {
            this._handleStreamDelta(data as { delta?: string; content?: string; response_id?: string });
        });
        this._wsClient.on('chat.done', (data) => {
            this._handleStreamDone(data as { content?: string; confidence?: number; response_id?: string });
        });
        this._wsClient.on('tool.call', (data) => {
            this._handleToolCall(data as ToolCallPayload);
        });
        this._wsClient.on('tool.delta', (data) => {
            this._handleToolDelta(data as ToolCallPayload);
        });
        this._wsClient.on('tool.done', (data) => {
            this._handleToolDone(data as ToolCallPayload);
        });
        this._wsClient.on('tool.approval_request', (data) => {
            this._handleToolApprovalRequest(data as ToolCallPayload);
        });
        this._wsClient.on('title_update', (data) => {
            const payload = data as { title?: string; conversation_id?: string };
            if (payload?.title) {
                this._chatTitle = payload.title;
            }
        });
        this._wsClient.on('connected', (data) => {
            this._wsConnected = true;
            this._wsEverConnected = true;
            this._wsReconnecting = false;
            this._connectionStatus = 'ok';
            window.clearTimeout(this._reconnectBannerTimer);
            window.clearTimeout(this._connectionChipTimer);
            const payload = data as { iq_tier?: string; agent_id?: string; tools_available?: number } | undefined;
            if (payload?.iq_tier) {
                this._modelLabel = payload.iq_tier;
            }
        });
        this._wsClient.on('disconnected', () => {
            this._wsConnected = false;
            // Debounce the degraded chip so a single blip doesn't flash it.
            window.clearTimeout(this._reconnectBannerTimer);
            window.clearTimeout(this._connectionChipTimer);
            this._reconnectBannerTimer = window.setTimeout(() => {
                if (!this._wsConnected) {
                    this._wsReconnecting = true;
                    this._connectionStatus = 'reconnecting';
                }
            }, 1200);
        });
        // WebSocketClient emits 'error' for BOTH socket errors (Event) and
        // gateway `error` messages ({code, message}). Distinguish by shape.
        this._wsClient.on('error', (data) => {
            const payload = data as { message?: string; code?: string } | undefined;
            if (payload && typeof payload === 'object' && typeof payload.message === 'string') {
                const msg = payload.message || 'Chat stream error';
                // Do not spam identical errors (e.g. reconnect storms).
                if (this._lastErrorMessage !== msg) {
                    this._lastErrorMessage = msg;
                    this._pushInlineError(msg);
                }
                this._isStreaming = false;
                return;
            }
            // Raw socket Event — wait for the debounce chip instead of hard error.
            if (this._wsEverConnected) {
                window.clearTimeout(this._connectionChipTimer);
                this._connectionChipTimer = window.setTimeout(() => {
                    if (!this._wsConnected) {
                        this._connectionStatus = 'degraded';
                    }
                }, 2500);
            }
        });

        this._wsClient.connect();
    }

    private async _ensureWebSocket(): Promise<boolean> {
        if (!this._wsClient) return false;
        if (this._wsClient.connected) return true;

        this._wsClient.connect();

        return new Promise((resolve) => {
            const unsubscribe = this._wsClient!.on('connected', () => {
                unsubscribe();
                resolve(true);
            });
            const timeout = setTimeout(() => {
                unsubscribe();
                resolve(false);
            }, 5000);
            void timeout;
        });
    }

    // ==========================================================================
    // STREAM HANDLERS
    // ==========================================================================

    private _handleIncomingMessage(msg: ChatMessage) {
        this._isStreaming = false;
        this._streamContent = '';
        this._messages = [...this._messages, msg];
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private _handleStreamDelta(chunk: { delta?: string; content?: string; response_id?: string }) {
        if (this._turnStopped) return;
        if (chunk?.response_id) {
            if (this._activeResponseId && this._activeResponseId !== chunk.response_id) return;
            this._activeResponseId = chunk.response_id;
        }
        if (this._paused) return;
        const delta = chunk.delta ?? chunk.content ?? '';
        this._streamContent += delta;
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private _handleStreamDone(chunk: { content?: string; confidence?: number; response_id?: string }) {
        if (
            this._turnStopped ||
            (chunk?.response_id && this._activeResponseId && chunk.response_id !== this._activeResponseId)
        ) {
            this._streamContent = '';
            this._activeTools = [];
            this._activeResponseId = '';
            this._isStreaming = false;
            this._turnStopped = false;
            return;
        }
        const message: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: chunk.content ?? this._streamContent,
            timestamp: new Date().toISOString(),
            confidence: chunk.confidence,
            tools: this._activeTools.length > 0 ? [...this._activeTools] : undefined,
        };
        this._streamContent = '';
        this._activeTools = [];
        this._activeResponseId = '';
        this._handleIncomingMessage(message);
    }

    private _finalizeStreamedMessage(stopped: boolean) {
        const content = this._streamContent;
        const tools = this._activeTools.length > 0 ? [...this._activeTools] : undefined;
        this._streamContent = '';
        this._activeTools = [];
        this._isStreaming = false;
        if (content || tools) {
            this._messages = [
                ...this._messages,
                {
                    id: `msg-${Date.now()}`,
                    role: 'assistant',
                    content,
                    timestamp: new Date().toISOString(),
                    stopped,
                    tools,
                },
            ];
            this.updateComplete.then(() => this._scrollToBottom());
        }
    }

    /**
     * Inline error attached to the last message (or a system row).
     * Never a global blinking banner — this keeps "internal error" spam gone.
     */
    private _pushInlineError(content: string) {
        const last = this._messages[this._messages.length - 1];
        if (last && last.role === 'assistant') {
            this._messages = [
                ...this._messages.slice(0, -1),
                { ...last, error: last.error ? `${last.error} · ${content}` : content },
            ];
            return;
        }
        this._messages = [
            ...this._messages,
            {
                id: `msg-${Date.now()}`,
                role: 'system',
                content: '',
                error: content,
                timestamp: new Date().toISOString(),
            },
        ];
        this.updateComplete.then(() => this._scrollToBottom());
    }

    // ==========================================================================
    // TOOL TIMELINE
    // ==========================================================================

    private _toolStepKey(p: ToolCallPayload): string {
        if (p.tool_call_id) return p.tool_call_id;
        return `idx:${p.iteration ?? 0}:${p.index ?? 0}`;
    }

    private _findToolStep(p: ToolCallPayload): number {
        const key = this._toolStepKey(p);
        return this._activeTools.findIndex(
            (s) =>
                s.id === key ||
                (p.tool_call_id && s.id === p.tool_call_id) ||
                (p.index != null && s.index === p.index && (p.iteration == null || s.iteration === p.iteration)),
        );
    }

    private _upsertToolStep(p: ToolCallPayload, status: ToolStepStatus): ToolCallStep[] {
        const key = this._toolStepKey(p);
        const idx = this._findToolStep(p);
        const next = [...this._activeTools];
        if (idx >= 0) {
            next[idx] = {
                ...next[idx],
                name: p.name ?? next[idx].name,
                status,
                iteration: p.iteration ?? next[idx].iteration,
                index: p.index ?? next[idx].index,
                arguments: (p.arguments ?? next[idx].arguments) as Record<string, unknown> | null,
            };
            return next;
        }
        next.push({
            id: key,
            name: p.name ?? 'tool',
            status,
            iteration: p.iteration,
            index: p.index,
            arguments: (p.arguments ?? null) as Record<string, unknown> | null,
            argumentsText: '',
        });
        return next;
    }

    private _handleToolCall(p: ToolCallPayload) {
        if (this._turnStopped) return;
        this._activeTools = this._upsertToolStep(p, 'executing');
    }

    private _handleToolDelta(p: ToolCallPayload) {
        if (this._turnStopped) return;
        const key = this._toolStepKey(p);
        const next = this._upsertToolStep(p, 'executing');
        const idx = next.findIndex((s) => s.id === key || (p.index != null && s.index === p.index));
        if (idx >= 0) {
            const step = { ...next[idx] };
            step.argumentsText = (step.argumentsText ?? '') + (p.arguments_delta ?? '');
            try {
                step.arguments = JSON.parse(step.argumentsText) as Record<string, unknown>;
            } catch {
                // incomplete JSON mid-stream — keep raw text only
            }
            next[idx] = step;
        }
        this._activeTools = next;
    }

    private _handleToolDone(p: ToolCallPayload) {
        const status = (p.status as ToolStepStatus) || (p.ok ? 'executed' : 'error');
        const next = this._upsertToolStep(p, status);
        const key = this._toolStepKey(p);
        const idx = next.findIndex((s) => s.id === key || (p.tool_call_id && s.id === p.tool_call_id));
        if (idx >= 0) {
            next[idx] = {
                ...next[idx],
                name: p.name ?? next[idx].name,
                result: p.result,
                ok: p.ok,
                error: p.error ?? null,
                durationMs: p.duration_ms,
                arguments: (p.arguments ?? next[idx].arguments) as Record<string, unknown> | null,
                status,
            };
        }
        this._activeTools = next;
    }

    private _handleToolApprovalRequest(p: ToolCallPayload) {
        const next = this._upsertToolStep(p, 'approval_required');
        const key = this._toolStepKey(p);
        const idx = next.findIndex((s) => s.id === key);
        if (idx >= 0) {
            next[idx] = {
                ...next[idx],
                name: p.name ?? next[idx].name,
                arguments: (p.arguments ?? next[idx].arguments) as Record<string, unknown> | null,
                status: 'approval_required',
            };
        }
        this._activeTools = next;
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private _onToolApproval(e: CustomEvent<{ toolCallId: string; name: string; approved: boolean }>) {
        e.stopPropagation();
        if (!this._wsClient?.connected) {
            this._pushInlineError('Cannot send tool approval — WebSocket disconnected');
            return;
        }
        this._wsClient.send({
            type: 'tool.approval',
            payload: {
                conversation_id: this._activeConversationId,
                tool_call_id: e.detail.toolCallId,
                name: e.detail.name,
                approved: e.detail.approved,
            },
        });
    }

    // ==========================================================================
    // CHAT CONTROLS
    // ==========================================================================

    private _onChatControl(e: CustomEvent<{ action: ChatControlAction }>) {
        e.stopPropagation();
        const action = e.detail?.action;
        switch (action) {
            case 'pause':
                this._paused = true;
                break;
            case 'resume':
                this._paused = false;
                break;
            case 'stop':
                this._stopTurn();
                break;
            case 'reset':
                void this._resetChat();
                break;
            case 'nudge':
                if (this._wsClient?.connected && this._activeConversationId) {
                    this._wsClient.send({
                        type: 'chat.nudge',
                        payload: { conversation_id: this._activeConversationId },
                    });
                }
                break;
            default:
                break;
        }
    }

    private _stopTurn() {
        if (!this._isStreaming) return;
        this._turnStopped = true;
        this._paused = false;
        this._finalizeStreamedMessage(true);
    }

    private async _resetChat() {
        this._stopTurn();
        this._messages = [];
        this._streamContent = '';
        this._activeTools = [];
        this._paused = false;
        this._chatTitle = 'New conversation';
        if (this._selectedAgentId) {
            const conversationId = await this._createConversation(this._selectedAgentId);
            if (conversationId) {
                this._activeConversationId = conversationId;
                await this._loadConversations();
            } else {
                this._pushInlineError('Failed to reset conversation');
            }
        } else {
            this._activeConversationId = '';
        }
    }

    private _onClearChat() {
        this._messages = [];
        this._streamContent = '';
        this._activeTools = [];
    }

    private _onExportChat() {
        if (this._messages.length === 0) {
            this._pushInlineError('Nothing to export yet');
            return;
        }
        const payload = this._messages.map((m) => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp,
            tools: m.tools ?? [],
            attachments: m.attachments ?? [],
        }));
        const blob = new Blob(
            [
                JSON.stringify(
                    {
                        conversation_id: this._activeConversationId,
                        title: this._chatTitle,
                        exported_at: new Date().toISOString(),
                        messages: payload,
                    },
                    null,
                    2,
                ),
            ],
            { type: 'application/json' },
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `soma-chat-${this._activeConversationId || 'export'}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // ==========================================================================
    // SEND
    // ==========================================================================

    private _onComposerSend(e: CustomEvent<ComposerSendDetail>) {
        e.stopPropagation();
        const detail = e.detail;
        if (!detail || (!detail.text?.trim() && (!detail.attachments || detail.attachments.length === 0))) {
            return;
        }
        if (this._isStreaming) {
            this._pushInlineError('Still finishing the previous turn — message not sent');
            return;
        }
        this._isStreaming = true;
        void this._deliverUserMessage(detail);
    }

    private async _deliverUserMessage(detail: ComposerSendDetail) {
        const content = detail.text.trim();
        if (!content && (!detail.attachments || detail.attachments.length === 0)) {
            this._isStreaming = false;
            return;
        }

        const wsReady = await this._ensureWebSocket();
        if (!wsReady) {
            this._isStreaming = false;
            this._pushInlineError('Not connected — message not sent');
            return;
        }

        let conversationId = this._activeConversationId;
        if (!conversationId && this._selectedAgentId) {
            const newId = await this._createConversation(this._selectedAgentId);
            conversationId = newId || '';
            if (!conversationId) {
                this._isStreaming = false;
                this._pushInlineError('Failed to create conversation — message not sent');
                return;
            }
            this._activeConversationId = conversationId;
            await this._loadConversations();
        }
        if (!conversationId) {
            this._isStreaming = false;
            this._pushInlineError('No active conversation — message not sent');
            return;
        }

        const userMessage: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: 'user',
            content,
            timestamp: new Date().toISOString(),
            attachments:
                detail.attachments?.map((f) => ({ name: f.name, type: f.type, size: f.size })) ?? [],
        };
        this._messages = [...this._messages, userMessage];
        this._turnStopped = false;
        this._paused = false;
        this._streamContent = '';
        this._activeTools = [];
        this._lastErrorMessage = '';

        this.updateComplete.then(() => this._scrollToBottom());

        try {
            this._wsClient?.send({
                type: 'chat.message',
                payload: {
                    content,
                    conversation_id: conversationId,
                    mode: this._currentMode,
                    attachments: userMessage.attachments,
                },
            });
        } catch (error) {
            console.error('Failed to send message:', error);
            this._isStreaming = false;
            this._pushInlineError('Failed to send message');
        }
    }

    // ==========================================================================
    // CONVERSATION NAV
    // ==========================================================================

    private async _startNewChat() {
        this._messages = [];
        this._streamContent = '';
        this._activeTools = [];
        this._isStreaming = false;
        this._chatTitle = 'New conversation';
        this._activeConversationId = '';
        if (this._selectedAgentId) {
            const conversationId = await this._createConversation(this._selectedAgentId);
            if (conversationId) {
                this._activeConversationId = conversationId;
                await this._loadConversations();
                this.updateComplete.then(() => {
                    const input = this.renderRoot.querySelector('saas-composer') as HTMLElement | null;
                    input?.shadowRoot?.querySelector('textarea')?.focus();
                });
            }
        }
    }

    private async _selectConversation(id: string) {
        if (id === this._activeConversationId && this._messages.length > 0) return;
        this._activeConversationId = id;
        const conv = this._conversations.find((c) => c.id === id);
        if (conv) this._chatTitle = conv.title;
        await this._loadConversationMessages(id);
    }

    private async _loadConversationMessages(conversationId: string): Promise<void> {
        this._messagesLoading = true;
        try {
            const response = await apiClient.get(`/chat/conversations/${conversationId}/messages`);
            const items = Array.isArray(response)
                ? response
                : (response as { data?: ChatMessage[] }).data || [];

            this._messages = items.map((msg: Record<string, unknown>) => ({
                id: String(msg.id ?? `msg-${Date.now()}`),
                role: (msg.role as ChatMessage['role']) ?? 'assistant',
                content: String(msg.content ?? ''),
                timestamp: String(msg.created_at ?? msg.timestamp ?? ''),
                confidence: (msg.metadata as { confidence?: number } | undefined)?.confidence,
            }));
            this.updateComplete.then(() => this._scrollToBottom());
        } catch (error) {
            console.error('[SaasChat] Failed to load messages:', error);
            this._messages = [];
        } finally {
            this._messagesLoading = false;
        }
    }

    private _scrollToBottom() {
        if (this._messagesContainer) {
            this._messagesContainer.scrollTop = this._messagesContainer.scrollHeight;
        }
    }

    private _navigate(path: string) {
        window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route: path } }));
    }

    private _logout() {
        localStorage.removeItem('saas_auth_token');
        localStorage.removeItem('saas_user');
        localStorage.removeItem('saas_keycloak_token');
        sessionStorage.removeItem('saas_auth_state');
        sessionStorage.removeItem('saas_auth_nonce');
        window.location.href = '/login';
    }

    // ==========================================================================
    // RENDER
    // ==========================================================================

    private get filteredConversations(): Conversation[] {
        const q = this._convFilter.trim().toLowerCase();
        if (!q) return this._conversations;
        return this._conversations.filter(
            (c) =>
                c.title.toLowerCase().includes(q) ||
                (c.lastMessage ?? '').toLowerCase().includes(q),
        );
    }

    private get modeLabel(): string {
        return this._modes.find((m) => m.id === this._currentMode)?.name ?? this._currentMode;
    }

    render() {
        return html`
            ${this._renderSidebar()}
            ${this._renderMain()}
            ${this._renderCanvas()}
        `;
    }

    /* ---------- LEFT SIDEBAR ---------- */

    private _renderSidebar() {
        const filtered = this.filteredConversations;
        return html`
            <aside class="sidebar" aria-label="Conversations">
                <div class="sidebar-header">
                    <div class="brand">
                        <div class="brand-icon">
                            <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <rect x="3" y="3" width="7" height="7" rx="1"/>
                                <rect x="14" y="3" width="7" height="7" rx="1"/>
                                <rect x="14" y="14" width="7" height="7" rx="1"/>
                                <rect x="3" y="14" width="7" height="7" rx="1"/>
                            </svg>
                        </div>
                        <span class="brand-name">SomaAgent</span>
                    </div>
                </div>

                <button class="new-chat-btn" @click=${this._startNewChat} title="New conversation">
                    ${ICON('add_comment', 18)} New Chat
                </button>

                <div class="search-wrap">
                    ${ICON('search', 16)}
                    <input
                        class="search-input"
                        type="search"
                        placeholder="Search conversations"
                        aria-label="Search conversations"
                        .value=${this._convFilter}
                        @input=${(e: Event) => {
                            this._convFilter = (e.target as HTMLInputElement).value;
                        }}
                    />
                </div>

                <div class="conversations-section">
                    <div class="section-label">Conversations</div>
                    ${this._conversationsLoading
                        ? html`
                              <div class="skeleton-list" aria-hidden="true">
                                  <div class="skeleton-row"></div>
                                  <div class="skeleton-row"></div>
                                  <div class="skeleton-row"></div>
                              </div>
                          `
                        : filtered.length === 0
                            ? html`
                                  <div class="empty-list">
                                      ${this._convFilter
                                          ? 'No conversations match your search.'
                                          : 'No conversations yet. Start a new chat to begin.'}
                                  </div>
                              `
                            : filtered.map((conv) => this._renderConversationRow(conv))}
                </div>

                <nav class="nav-links" aria-label="Workspace">
                    <button class="nav-link" @click=${() => this._navigate('/memory')}>
                        ${ICON('psychology', 18)} Memory
                    </button>
                    <button class="nav-link" @click=${() => this._navigate('/settings/models')}>
                        ${ICON('memory', 18)} Models
                    </button>
                    <button class="nav-link" @click=${() => this._navigate('/settings/channels')}>
                        ${ICON('forum', 18)} Channels
                    </button>
                    <button class="nav-link" @click=${() => this._navigate('/settings')}>
                        ${ICON('settings', 18)} Settings
                    </button>
                </nav>

                <div class="user-section">
                    <div class="user-avatar" aria-hidden="true">${this._userInitials}</div>
                    <div class="user-info">
                        <div class="user-name" title=${this._userName}>${this._userName}</div>
                        <div class="user-role">${this._userRole}</div>
                    </div>
                    <button class="logout-btn" @click=${this._logout} title="Logout" aria-label="Logout">
                        ${ICON('logout', 18)}
                    </button>
                </div>
            </aside>
        `;
    }

    private _renderConversationRow(conv: Conversation) {
        const isActive = conv.id === this._activeConversationId;
        const renaming = this._renamingId === conv.id;

        return html`
            <div
                class="conversation-item ${isActive ? 'active' : ''}"
                role="button"
                tabindex="0"
                @click=${() => !renaming && this._selectConversation(conv.id)}
                @keydown=${(e: KeyboardEvent) => {
                    if ((e.key === 'Enter' || e.key === ' ') && !renaming) {
                        e.preventDefault();
                        void this._selectConversation(conv.id);
                    }
                }}
                aria-current=${isActive ? 'true' : 'false'}
            >
                <div class="conv-body">
                    ${renaming
                        ? html`
                              <div class="rename-row" @click=${(e: Event) => e.stopPropagation()}>
                                  <input
                                      class="rename-input"
                                      .value=${this._renameDraft}
                                      @input=${(e: Event) => {
                                          this._renameDraft = (e.target as HTMLInputElement).value;
                                      }}
                                      @keydown=${(e: KeyboardEvent) => {
                                          if (e.key === 'Enter') {
                                              e.preventDefault();
                                              void this._renameConversation(conv.id, this._renameDraft);
                                          } else if (e.key === 'Escape') {
                                              e.preventDefault();
                                              e.stopPropagation();
                                              this._renamingId = '';
                                              this._renameDraft = '';
                                          }
                                      }}
                                      aria-label="Conversation title"
                                  />
                                  <button
                                      class="rename-confirm"
                                      title="Save"
                                      aria-label="Save rename"
                                      @click=${() => void this._renameConversation(conv.id, this._renameDraft)}
                                  >
                                      ${ICON('check', 14)}
                                  </button>
                              </div>
                          `
                        : html`
                              <div class="conversation-title">${conv.title || 'Untitled'}</div>
                              <div class="conversation-meta">
                                  ${formatRelative(conv.updatedAt) || '—'}
                                  ${conv.messageCount ? html` · ${conv.messageCount} msg` : nothing}
                              </div>
                          `}
                </div>
                ${!renaming
                    ? html`
                          <div class="conv-actions">
                              <button
                                  class="conv-action"
                                  title="Rename"
                                  aria-label="Rename conversation"
                                  @click=${(e: Event) => {
                                      e.stopPropagation();
                                      this._renamingId = conv.id;
                                      this._renameDraft = conv.title;
                                  }}
                              >
                                  ${ICON('edit', 15)}
                              </button>
                              <button
                                  class="conv-action"
                                  title="Export"
                                  aria-label="Export conversation"
                                  @click=${(e: Event) => {
                                      e.stopPropagation();
                                      this._exportConversation(conv);
                                  }}
                              >
                                  ${ICON('download', 15)}
                              </button>
                              <button
                                  class="conv-action danger"
                                  title="Delete"
                                  aria-label="Delete conversation"
                                  @click=${(e: Event) => {
                                      e.stopPropagation();
                                      if (confirm(`Delete “${conv.title || 'Untitled'}”?`)) {
                                          void this._deleteConversation(conv.id);
                                      }
                                  }}
                              >
                                  ${ICON('delete', 15)}
                              </button>
                          </div>
                      `
                    : nothing}
            </div>
        `;
    }

    /* ---------- CENTER ---------- */

    private _renderMain() {
        return html`
            <main class="main">
                <header class="header">
                    <saas-chat-topbar
                        .title=${this._chatTitle}
                        .modelLabel=${this._modelLabel}
                        .busy=${this._isStreaming}
                        .paused=${this._paused}
                        .canNudge=${this._isStreaming}
                        .connectionStatus=${this._connectionStatus}
                        @saas-chat-control=${this._onChatControl}
                    ></saas-chat-topbar>

                    <div class="header-right">
                        ${this._agents.length > 1
                            ? html`
                                  <select
                                      class="agent-select"
                                      aria-label="Select agent"
                                      @change=${this._handleAgentSelect}
                                  >
                                      ${this._agents.map(
                                          (agent) => html`
                                              <option
                                                  value=${agent.id}
                                                  ?selected=${agent.id === this._selectedAgentId}
                                              >
                                                  ${agent.name}
                                              </option>
                                          `,
                                      )}
                                  </select>
                              `
                            : nothing}

                        <div class="mode-selector">
                            <button
                                class="mode-btn"
                                @click=${this._toggleModeDropdown}
                                aria-haspopup="listbox"
                                aria-expanded=${this._showModeDropdown ? 'true' : 'false'}
                                title="Agent mode"
                            >
                                <span class="mode-badge">${this._currentMode}</span>
                                ${this.modeLabel}
                                ${ICON('expand_more', 14)}
                            </button>
                            <div
                                class="mode-dropdown ${this._showModeDropdown ? 'open' : ''}"
                                role="listbox"
                                aria-label="Agent mode"
                            >
                                ${this._modes.map(
                                    (mode) => html`
                                        <button
                                            class="mode-option ${mode.id === this._currentMode
                                                ? 'active'
                                                : ''} ${mode.locked ? 'locked' : ''}"
                                            role="option"
                                            aria-selected=${mode.id === this._currentMode ? 'true' : 'false'}
                                            ?disabled=${mode.locked}
                                            @click=${() => this._selectMode(mode.id as AgentMode, mode.locked)}
                                        >
                                            <div class="mode-option-header">
                                                <span
                                                    class="mode-badge"
                                                    style=${mode.id === this._currentMode
                                                        ? 'background:var(--aaas-accent,#1a1a1a);color:var(--aaas-text-inverse,#ffffff)'
                                                        : 'background:var(--aaas-bg-void,#f5f5f5);color:var(--aaas-text-muted,#999999)'}
                                                    >${mode.id}</span
                                                >
                                                <span class="mode-option-title">${mode.name}</span>
                                                ${mode.locked
                                                    ? html`<span class="lock-icon">${ICON('lock', 12)}</span>`
                                                    : nothing}
                                            </div>
                                            <div class="mode-option-desc">${mode.desc}</div>
                                        </button>
                                    `,
                                )}
                            </div>
                        </div>
                    </div>
                </header>

                <div class="messages" @tool-approval=${this._onToolApproval} role="log" aria-live="polite">
                    ${this._messagesLoading
                        ? html`
                              <div class="msg-skeleton" aria-hidden="true">
                                  <div class="bar mid"></div>
                                  <div class="bar"></div>
                                  <div class="bar short"></div>
                              </div>
                          `
                        : this._messages.length === 0 && !this._isStreaming
                            ? this._renderWelcome()
                            : html`
                                  ${this._messages.map((msg) => this._renderMessage(msg))}
                                  ${this._isStreaming
                                      ? html`
                                            <saas-message
                                                message-role="assistant"
                                                .text=${this._streamContent}
                                                .tools=${this._activeTools}
                                                .streaming=${!this._paused}
                                            ></saas-message>
                                        `
                                      : nothing}
                              `}
                </div>

                <saas-composer
                    .busy=${this._isStreaming}
                    .placeholder=${this._selectedAgentId
                        ? 'Describe what you want the agent to do…'
                        : 'Select an agent to start chatting'}
                    @send-message=${this._onComposerSend}
                    @clear-chat=${this._onClearChat}
                    @export-chat=${this._onExportChat}
                ></saas-composer>
            </main>
        `;
    }

    private _renderWelcome() {
        const firstName =
            this._userName && this._userName !== 'User' ? `, ${this._userName.split(' ')[0]}` : '';
        return html`
            <div class="welcome">
                <div class="welcome-icon">${ICON('chat', 30)}</div>
                <h2>Hello${firstName}</h2>
                <p>
                    Start a conversation with your Soma agent — tools, memory, and Capsule skills
                    are live.
                </p>
                <div class="welcome-actions">
                    <button class="welcome-action" @click=${() => this._startNewChat()}>
                        ${ICON('add_comment', 20)}
                        <span>
                            <div class="wa-title">New chat</div>
                            <div class="wa-desc">Spin up a fresh conversation with the agent</div>
                        </span>
                    </button>
                    <button class="welcome-action" @click=${() => this._navigate('/memory')}>
                        ${ICON('psychology', 20)}
                        <span>
                            <div class="wa-title">Memory</div>
                            <div class="wa-desc">Browse cognitive memories and recall</div>
                        </span>
                    </button>
                    <button class="welcome-action" @click=${() => this._navigate('/settings/models')}>
                        ${ICON('tune', 20)}
                        <span>
                            <div class="wa-title">Models</div>
                            <div class="wa-desc">Pick the chat provider and model tier</div>
                        </span>
                    </button>
                    <button class="welcome-action" @click=${() => this._navigate('/settings/channels')}>
                        ${ICON('forum', 20)}
                        <span>
                            <div class="wa-title">Channels</div>
                            <div class="wa-desc">WhatsApp / Telegram Capsule bridges</div>
                        </span>
                    </button>
                </div>
            </div>
        `;
    }

    private _renderMessage(msg: ChatMessage) {
        return html`
            <saas-message
                message-role=${msg.role}
                .text=${msg.content}
                .timestamp=${msg.timestamp}
                .tools=${msg.tools ?? []}
                .attachments=${msg.attachments ?? []}
                .stopped=${!!msg.stopped}
                .confidence=${msg.confidence}
                .error=${msg.error ?? ''}
            ></saas-message>
        `;
    }

    /* ---------- RIGHT CANVAS ---------- */

    private _renderCanvas() {
        return html`
            <aside class="right-canvas ${this._showRightPanel ? 'open' : ''}" aria-label="Workspace canvas">
                <div class="canvas-rail">
                    <button
                        class="rail-btn ${this._rightPanelTab === 'memory' && this._showRightPanel ? 'active' : ''}"
                        title="Memory"
                        aria-label="Memory panel"
                        @click=${() => this._openRightPanel('memory')}
                    >
                        ${ICON('psychology', 20)}
                    </button>
                    <button
                        class="rail-btn ${this._rightPanelTab === 'files' && this._showRightPanel ? 'active' : ''}"
                        title="Files"
                        aria-label="Files panel"
                        @click=${() => this._openRightPanel('files')}
                    >
                        ${ICON('folder', 20)}
                    </button>
                    <button
                        class="rail-btn ${this._rightPanelTab === 'channel' && this._showRightPanel ? 'active' : ''}"
                        title="Channel"
                        aria-label="Channel panel"
                        @click=${() => this._openRightPanel('channel')}
                    >
                        ${ICON('forum', 20)}
                    </button>
                </div>
                ${this._showRightPanel
                    ? html`
                          <div class="canvas-panel">
                              <div class="canvas-header">
                                  <span>${this._rightPanelTab}</span>
                                  <button
                                      class="icon-btn"
                                      title="Close panel"
                                      aria-label="Close panel"
                                      @click=${() => (this._showRightPanel = false)}
                                  >
                                      ${ICON('close', 16)}
                                  </button>
                              </div>
                              <div class="canvas-body">
                                  ${this._rightPanelTab === 'memory'
                                      ? this._renderMemoryPanel()
                                      : nothing}
                                  ${this._rightPanelTab === 'files' ? this._renderFilesPanel() : nothing}
                                  ${this._rightPanelTab === 'channel'
                                      ? this._renderChannelPanel()
                                      : nothing}
                              </div>
                          </div>
                      `
                    : nothing}
            </aside>
        `;
    }

    private _renderMemoryPanel() {
        return html`
            <input
                class="canvas-search"
                type="search"
                placeholder="Search memories…"
                aria-label="Search memories"
                .value=${this._memoryQuery}
                @input=${(e: Event) => {
                    this._memoryQuery = (e.target as HTMLInputElement).value;
                }}
                @keydown=${(e: KeyboardEvent) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        void this._searchMemories();
                    }
                }}
            />
            <div class="canvas-hint">
                Cognitive memory (Brain + SFM).
                <button
                    style="color:var(--aaas-info,#3b82f6);background:none;border:none;padding:0;cursor:pointer;text-decoration:underline;font:inherit"
                    @click=${() => this._navigate('/memory')}
                >
                    Open full dashboard
                </button>
            </div>
            ${this._memoryLoading
                ? html`
                      <div class="panel-skeleton" aria-hidden="true">
                          <div class="srow"></div>
                          <div class="srow"></div>
                          <div class="srow"></div>
                      </div>
                  `
                : this._memories.length === 0
                    ? html`<div class="canvas-hint">No memories yet.</div>`
                    : this._memories.slice(0, 20).map(
                          (m) => html`
                              <div class="memory-card">
                                  <div class="type">${m.type || 'memory'}</div>
                                  <div class="content">${m.summary || m.content}</div>
                                  ${m.tags && m.tags.length > 0
                                      ? html`
                                            <div class="tags">
                                                ${m.tags.slice(0, 4).map((t) => html`<span class="tag-chip">${t}</span>`)}
                                            </div>
                                        `
                                      : nothing}
                              </div>
                          `,
                      )}
        `;
    }

    private _renderFilesPanel() {
        const files = this._conversationFiles();
        return html`
            <div class="canvas-hint">
                Attachments and workdir files for this conversation.
            </div>
            ${files.length === 0
                ? html`<div class="canvas-hint">No files attached to this conversation yet.</div>`
                : files.map(
                      (f) => html`
                          <div class="file-row">
                              ${ICON('draft', 16)}
                              <span class="fname" title=${f.name}>${f.name}</span>
                              <span class="fsize">${f.size ? `${Math.max(1, Math.round(f.size / 1024))} KB` : ''}</span>
                          </div>
                      `,
                  )}
        `;
    }

    private _renderChannelPanel() {
        return html`
            <div class="canvas-hint">
                WhatsApp / Telegram Capsule channels.
                <button
                    style="color:var(--aaas-info,#3b82f6);background:none;border:none;padding:0;cursor:pointer;text-decoration:underline;font:inherit"
                    @click=${() => this._navigate('/settings/channels')}
                >
                    Configure
                </button>
            </div>
            ${this._channelsLoading
                ? html`
                      <div class="panel-skeleton" aria-hidden="true">
                          <div class="srow"></div>
                          <div class="srow"></div>
                      </div>
                  `
                : this._channels.length === 0
                    ? html`<div class="canvas-hint">No channels configured.</div>`
                    : this._channels.map((c) => {
                          const status = (c.status ?? '').toLowerCase();
                          const dotClass =
                              status === 'ok' || status === 'connected' || status === 'active'
                                  ? 'ok'
                                  : status === 'error' || status === 'failed'
                                      ? 'err'
                                      : 'warn';
                          return html`
                              <div class="channel-row">
                                  <span class="status-dot ${dotClass}" title=${c.status}></span>
                                  <span class="channel-kind">${c.kind}</span>
                                  <span style="color:var(--aaas-text-muted,#6b6b6b);font-size:11px">${c.status}</span>
                              </div>
                          `;
                      })}
        `;
    }

    /* ---------- misc handlers ---------- */

    private _toggleModeDropdown(e: Event) {
        e.stopPropagation();
        this._showModeDropdown = !this._showModeDropdown;
    }

    private _selectMode(mode: AgentMode, locked: boolean) {
        if (locked) return;
        this._currentMode = mode;
        this._showModeDropdown = false;
    }

    private _handleAgentSelect(e: Event) {
        const select = e.target as HTMLSelectElement;
        const agentId = select.value;
        if (agentId && agentId !== this._selectedAgentId) {
            this._selectedAgentId = agentId;
            this._activeConversationId = '';
            this._messages = [];
            this._chatTitle = 'New conversation';
            this._connectWebSocket();
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-chat': SaasChat;
    }
}
