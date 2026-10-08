/**
 * SomaAgent Soma — Chat Workspace (Agent Zero parity)
 *
 * 3-column workspace shell:
 *   Left  — brand, New Chat, searchable conversation list (rename/delete/export),
 *           user card (/auth/me), nav to Memory / Settings only (IA-001)
 *   Center — topbar (title, model, pause/stop/reset), message stream + tool
 *           timeline, welcome empty state, composer
 *   Right  — the one surface registry (`soma-right-panel`, UI-X-01…08)
 *
 * Transport: WebSocket /ws/v2/chat/:id + REST /chat/conversations*.
 * Dark-first, AAAS token palette. No mocks, no placeholders.
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state, query } from 'lit/decorators.js';
import { WebSocketClient } from '../services/websocket-client.js';
import { apiClient } from '../services/api-client.js';
import type { ToolCallStep, ToolStepStatus } from '../components/soma-tool-timeline.js';
import { iqStore } from '../stores/iq-store.js';
import type { ComposerSendDetail } from '../components/soma-composer.js';
import type { ChatControlAction, ConnectionStatus } from '../components/soma-chat-topbar.js';
import { formatRelative } from '../utils/markdown.js';
import '../components/soma-message.js';
import '../components/soma-tool-timeline.js';
import '../components/soma-chat-topbar.js';
import '../components/soma-composer.js';
import '../components/soma-right-panel.js';
import '../components/soma-status-dot.js';
import '../components/soma-glass-modal.js';
import '../components/soma-agent-iq.js';
import type { StatusDotState } from '../components/soma-status-dot.js';

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
    /** Present only when the server sent a count. Never defaulted to 0. */
    messageCount?: number;
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

type AgentMode = 'STD' | 'TRN' | 'ADM' | 'DEV' | 'RO' | 'DGR';

const ICON = (name: string, size = 20) =>
    html`<span class="material-symbols-outlined" style="font-size:${size}px" aria-hidden="true">${name}</span>`;

@customElement('soma-chat')
export class SomaChat extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--aaas-bg-void, #0A0A0A);
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
            background: var(--aaas-bg-sidebar, #111111);
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
            background: var(--aaas-accent, #3B82F6);
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
            background: var(--aaas-accent, #3B82F6);
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
            background: var(--aaas-accent-hover, #2563EB);
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
            background: var(--aaas-bg-card, #1A1A1A);
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
            background: var(--aaas-bg-card, #1A1A1A);
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
            background: var(--aaas-bg-void, #0A0A0A);
        }

        .header {
            padding: 12px 24px;
            background: var(--aaas-bg-void, #0A0A0A);
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            align-items: center;
            gap: 16px;
            flex-shrink: 0;
        }

        .header soma-chat-topbar {
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
            background: var(--aaas-accent, #3B82F6);
            color: var(--aaas-bg-void, #f5f5f5);
            font-size: 10px;
            font-weight: 700;
        }

        .mode-dropdown {
            position: absolute;
            top: calc(100% + 6px);
            right: 0;
            background: var(--aaas-bg-card, #1A1A1A);
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
            display: flex;
            flex-direction: column;
            gap: 14px;
            padding: 18px 20px 12px;
        }

        @media (prefers-reduced-motion: reduce) {
            .messages { scroll-behavior: auto; }
        }

        /* Welcome / empty state — A0-merged enterprise */
        .welcome {
            display: flex;
            flex-direction: column;
            gap: 1.35rem;
            width: min(100%, 960px);
            margin: 0 auto;
            padding: 2.5rem 1.5rem 2rem;
        }

        .welcome-hero {
            text-align: center;
            padding-top: 1.5rem;
        }

        .welcome-hero h2 {
            margin: 0;
            font-size: clamp(1.85rem, 3.2vw, 2.45rem);
            font-weight: 500;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #FF4D00 0%, #FF7A3D 55%, #FF4D00 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .welcome-hero p {
            margin: 0.45rem 0 0;
            font-size: 1.15rem;
            color: var(--aaas-text-secondary, #a1a1aa);
        }

        .welcome-banner {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid color-mix(in srgb, #f59e0b 35%, transparent);
            background: color-mix(in srgb, #f59e0b 12%, transparent);
            font-size: 13px;
            color: var(--aaas-text-bright, #f8fafc);
        }

        .wb-action {
            margin-left: auto;
            border: 0;
            border-radius: 8px;
            padding: 6px 12px;
            background: #FF4D00;
            color: #fff;
            cursor: pointer;
            font-size: 12px;
        }

        .wb-dismiss {
            border: 0;
            background: transparent;
            color: inherit;
            cursor: pointer;
            opacity: 0.7;
        }

        .welcome-quick {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
        }

        .wq-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 18px 12px;
            border-radius: 8px;
            border: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.06));
            background: color-mix(in srgb, var(--aaas-bg-card, #1a1a1a) 88%, transparent);
            color: var(--aaas-text-bright, #f8fafc);
            cursor: pointer;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }

        .wq-card:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 77, 0, 0.55);
            box-shadow:
                0 1px 0 rgba(255, 255, 255, 0.06) inset,
                0 16px 36px rgba(255, 77, 0, 0.2);
        }

        .wq-card .material-symbols-outlined {
            font-size: 22px;
            color: #FF4D00;
        }

        .wq-glow {
            box-shadow:
                0 0 0 1px rgba(16, 185, 129, 0.35),
                0 0 24px rgba(16, 185, 129, 0.18);
        }

        .wq-label {
            font-size: 13px;
            font-weight: 500;
        }

        .welcome-section {
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 16px;
            padding: 16px 18px;
            background: rgba(18, 18, 18, 0.5);
            backdrop-filter: blur(18px) saturate(125%);
            -webkit-backdrop-filter: blur(18px) saturate(125%);
            box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset;
        }

        .ws-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .ws-head h3 {
            margin: 0;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            color: var(--aaas-text-secondary, #a1a1aa);
        }

        .ws-link {
            border: 0;
            background: transparent;
            color: #FF4D00;
            cursor: pointer;
            font-size: 12px;
        }

        .ws-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }

        .ws-card {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding: 14px;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.07);
            background: rgba(10, 10, 10, 0.45);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }

        .ws-card-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--aaas-text-bright, #f8fafc);
        }

        .ws-card-desc {
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1aa);
            line-height: 1.4;
            min-height: 2.6em;
        }

        .ws-cta {
            align-self: flex-start;
            margin-top: 4px;
            border: 0;
            border-radius: 8px;
            padding: 7px 12px;
            background: #FF4D00;
            color: #fff;
            cursor: pointer;
            font-size: 12px;
        }

        .ws-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 4px;
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1aa);
        }

        .ws-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #22c55e;
        }

        .sys-rows {
            display: grid;
            gap: 10px;
        }

        .sys-row {
            display: grid;
            grid-template-columns: 48px 1fr auto;
            gap: 10px;
            align-items: center;
        }

        .sys-name {
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1aa);
        }

        .sys-track {
            height: 8px;
            border-radius: 999px;
            background: color-mix(in srgb, var(--aaas-border-light, rgba(255, 255, 255, 0.08)) 80%, transparent);
            overflow: hidden;
        }

        .sys-fill {
            display: block;
            height: 100%;
            border-radius: inherit;
        }

        .sys-val {
            font-size: 12px;
            font-variant-numeric: tabular-nums;
            color: var(--aaas-text-secondary, #a1a1aa);
            white-space: nowrap;
        }

        .welcome-footer {
            text-align: center;
            font-size: 11px;
            color: var(--aaas-text-secondary, #71717a);
            padding: 8px 0 16px;
        }



        .dock {
            border-top: 1px solid rgba(255, 255, 255, 0.07);
            background: rgba(10, 10, 10, 0.78);
            backdrop-filter: blur(22px) saturate(130%);
            -webkit-backdrop-filter: blur(22px) saturate(130%);
            box-shadow: 0 -12px 40px rgba(0, 0, 0, 0.35);
        }

        .dock-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            min-height: 48px;
            padding: 0 12px 0 14px;
            cursor: pointer;
            user-select: none;
        }

        .dock-vitals {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            min-width: 0;
            overflow: hidden;
        }

        .vital {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 11px;
            color: #94A3B8;
            white-space: nowrap;
        }

        .vital em {
            font-style: normal;
            color: #C4C4C4;
        }

        .vital em.memory-queued-chip {
            color: #F59E0B;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            border: 1px solid rgba(245, 158, 11, 0.45);
            border-radius: 999px;
            padding: 0 6px;
        }

        .vital.text {
            font-variant-numeric: tabular-nums;
        }

        .vital.pulse {
            color: #FF7A3D;
        }

        .dock-knobs-preview {
            font-size: 11px;
            color: #FF7A3D;
            font-variant-numeric: tabular-nums;
            padding: 3px 8px;
            border-radius: 999px;
            background: rgba(255, 77, 0, 0.12);
            border: 1px solid rgba(255, 77, 0, 0.28);
        }

        .dock-handle {
            border: 0;
            background: rgba(255, 77, 0, 0.16);
            color: #FF4D00;
            width: 34px;
            height: 34px;
            border-radius: 10px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .dock-panel {
            display: grid;
            grid-template-rows: 0fr;
            transition: grid-template-rows 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        .dock.open .dock-panel {
            grid-template-rows: 1fr;
        }

        .dock-panel-inner {
            overflow: hidden;
            min-height: 0;
        }

        .dock.open .dock-panel-inner {
            padding: 0 14px 14px;
        }

        .dock-panel-head {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0 0 10px;
            color: #FFFFFF;
            font-size: 13px;
        }

        .dock-status-row {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .dock-panel-head .muted {
            color: #94A3B8;
            font-size: 11px;
        }

        .dock-panel-head .spacer {
            flex: 1;
        }

        .dock-x {
            border: 0;
            background: transparent;
            color: #94A3B8;
            cursor: pointer;
            display: inline-flex;
            padding: 4px;
        }
        .chat-foot {
            display: flex;
            align-items: center;
            gap: 12px;
            height: 28px;
            padding: 0 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            background: rgba(10, 10, 10, 0.7);
            backdrop-filter: blur(18px) saturate(120%);
            -webkit-backdrop-filter: blur(18px) saturate(120%);
            font-size: 11px;
            color: #64748B;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
            overflow: hidden;
        }

        .foot-spacer {
            flex: 1;
        }

        .foot-link {
            border: 0;
            background: transparent;
            color: #FF4D00;
            cursor: pointer;
            font-size: 11px;
        }

        .del-body {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            padding: 8px 8px 4px;
            text-align: center;
        }

        .del-icon {
            width: 56px;
            height: 56px;
            border-radius: 16px;
            display: grid;
            place-items: center;
            background: rgba(255, 77, 0, 0.14);
            color: #FF4D00;
            border: 1px solid rgba(255, 77, 0, 0.35);
        }

        .del-text {
            margin: 0;
            font-size: 15px;
            color: #FFFFFF;
            line-height: 1.45;
        }

        .del-sub {
            margin: 0;
            font-size: 12.5px;
            color: #B0B8C4;
            line-height: 1.45;
        }

        .del-check {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 6px;
            font-size: 12.5px;
            color: #94A3B8;
            cursor: pointer;
            user-select: none;
        }

        .del-check input {
            accent-color: #FF4D00;
            width: 15px;
            height: 15px;
            cursor: pointer;
        }

        .del-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            width: 100%;
            padding: 4px 2px 2px;
        }

        .del-btn {
            border: 0;
            border-radius: 12px;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 560;
            cursor: pointer;
            transition: transform 140ms ease, background 140ms ease, border-color 140ms ease;
        }

        .del-btn.ghost {
            background: rgba(255, 255, 255, 0.06);
            color: #E5E5E5;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .del-btn.ghost:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .del-btn.danger {
            background: linear-gradient(135deg, #FF4D00 0%, #E64500 100%);
            color: #FFFFFF;
            box-shadow: 0 8px 20px rgba(255, 77, 0, 0.28);
        }

        .del-btn.danger:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 28px rgba(255, 77, 0, 0.36);
        }

        .chat-header-slim {
            display: flex;
            flex-direction: column;
            gap: 0;
            padding: 8px 14px 6px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            background: rgba(10, 10, 10, 0.72);
            backdrop-filter: blur(20px) saturate(130%);
            -webkit-backdrop-filter: blur(20px) saturate(130%);
        }

        .chat-title-row {
            display: flex;
            align-items: center;
            gap: 8px;
            min-height: 28px;
        }

        .chat-title {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--aaas-text-bright, #F8FAFC);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 42ch;
        }

        .model-chip {
            font-size: 11px;
            padding: 2px 10px;
            border-radius: 999px;
            background: rgba(255, 77, 0, 0.12);
            border: 1px solid rgba(255, 77, 0, 0.35);
            color: #FFB088;
            white-space: nowrap;
        }

        .turn-state {
            font-size: 11px;
            color: var(--aaas-text-secondary, #a1a1aa);
        }

        .title-spacer {
            flex: 1;
        }

        .hdr-btn {
            border: 0;
            background: transparent;
            color: var(--aaas-text-secondary, #a1a1aa);
            cursor: pointer;
            display: inline-flex;
            padding: 4px;
            border-radius: 6px;
        }

        .hdr-btn:hover {
            background: color-mix(in srgb, var(--aaas-border-light, rgba(255,255,255,0.08)) 80%, transparent);
            color: var(--aaas-text-bright, #f8fafc);
        }

        .memory-ghost {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 4px;
            font-size: 11px;
            color: var(--aaas-text-secondary, #71717a);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .ghost-link {
            border: 0;
            background: transparent;
            color: #FF4D00;
            cursor: pointer;
            font-size: 11px;
            padding: 0;
        }

        .chat-top-strip {
            display: flex;
            align-items: center;
            gap: 10px;
            height: 40px;
            padding: 0 14px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.06));
            background: var(--aaas-bg-card, #141414);
            width: 100%;
        }

        .strip-brand {
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: var(--aaas-text-bright, #f8fafc);
        }

        .strip-clock {
            font-size: 12px;
            font-variant-numeric: tabular-nums;
            color: var(--aaas-text-secondary, #a1a1aa);
            margin-left: 8px;
        }

        .strip-spacer {
            flex: 1;
        }

        .sidebar-toggle-hint {
            border: 0;
            background: transparent;
            color: var(--aaas-text-secondary, #a1a1aa);
            cursor: pointer;
            display: inline-flex;
            padding: 4px;
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
            background: var(--aaas-bg-sidebar, #111111);
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

        /* The registry owns its own rail + content chrome. */
        .canvas-panel soma-right-panel {
            flex: 1;
            min-height: 0;
            display: flex;
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
        .messages::-webkit-scrollbar {
            width: 6px;
        }

        .conversations-section::-webkit-scrollbar-thumb,
        .messages::-webkit-scrollbar-thumb {
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
    @state() private _conversationsError = '';
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
    @state() private _userRole = '';
    @state() private _userInitials = 'U';
    @state() private _turnLanes: Record<string, number> | null = null;
    @state() private _memoryHits: { text?: string; score?: number | null; kind?: string | null }[] = [];
    @state() private _contextTokens = 0;
    @state() private _showRightPanel = false;
    @state() private _convFilter = '';
    @state() private _renamingId = '';
    @state() private _renameDraft = '';
    @state() private _brainDot: StatusDotState = 'idle';
    @state() private _brainTooltip = 'Brain · Status unavailable';
    @state() private _memoryDot: StatusDotState = 'idle';
    @state() private _memoryTooltip = 'Memory · Status unavailable';
    @state() private _memoryQueued = false;
    @state() private _sysCpu: { percent: number; cores: number } | null = null;
    @state() private _sysRam: { usedMb: number; totalMb: number; percent: number } | null = null;
    @state() private _channels: { id: string; kind: string; name: string; connected: boolean }[] = [];
    @state() private _channelsLoaded = false;
    @state() private _welcomeWarning = '';
    @state() private _pendingDelete: { id: string; title: string } | null = null;
    @state() private _deleteSkipConfirm = localStorage.getItem('soma_skip_delete_confirm') === '1';
    @state() private _deleteDontAsk = false;
    @state() private _knobPanelOpen = false;
    @state() private _knobCapsuleId = '';
    @state() private _iqPreview: { iq: number; auto: number } | null = null;
    private _iqUnsub: (() => void) | null = null;

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

    async connectedCallback() {
        super.connectedCallback();
        await this._loadUser();
        await this._loadAgents();
        void this._loadIqForAgent();
        await this._loadConversations();
        document.addEventListener('click', this._handleOutsideClick);
        // One health read on connect. No auto-poll: a poll interval is
        // latency policy and must come from a named setting.
        void this._pollBrainConnector();
        this._syncIqPreview();
        this._iqUnsub = iqStore.subscribe(() => this._syncIqPreview());
        void this._loadSystemDiagnostics();
        void this._loadChannels();
        void this._loadMemoryStatus();
        window.addEventListener('keydown', this._onGlobalKeydown);
    }

    disconnectedCallback() {
        this._iqUnsub?.();
        this._iqUnsub = null;
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
        if ((e as KeyboardEvent).key === 'Escape' && this._knobPanelOpen) { this._knobPanelOpen = false; }
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
    private async _loadIqForAgent(): Promise<void> {
        const agent = this._agents.find((a) => a.id === this._selectedAgentId);
        const capsuleId = agent?.capsule_id;
        if (!capsuleId) return;
        try {
            const payload = await apiClient.get<{
                knobs?: Record<string, unknown>;
                derived?: Record<string, unknown>;
            }>(`/core/agentiq/${capsuleId}`);
            iqStore.setFromServer(payload.knobs as never, payload.derived as never);
            iqStore.markSaved();
            this._syncIqPreview();
        } catch {
            /* dock shows — until AgentIQ is reachable */
        }
    }

    private _syncIqPreview(): void {
        const knobs = iqStore.knobs;
        if (!knobs) return;
        this._iqPreview = {
            iq: knobs.intelligence_level,
            auto: knobs.autonomy_level,
        };
    }

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
                this._brainDot = 'ok';
                this._brainTooltip = 'Brain · Connected';
                this._welcomeWarning = '';
            } else if (h && h.circuit === 'open') {
                this._connectionStatus = 'degraded';
                this._brainDot = 'warn';
                this._brainTooltip = 'Brain · Degraded';
                this._welcomeWarning = 'Brain connector degraded';
            } else {
                this._connectionStatus = 'reconnecting';
                this._brainDot = 'pending';
                this._brainTooltip = 'Brain · Connecting…';
                this._welcomeWarning = 'Brain connector disconnected';
            }
            this.requestUpdate();
        } catch {
            // Keep last state on poll failure; do not spam the banner.
        }
    }

    private async _loadSystemDiagnostics(): Promise<void> {
        try {
            const d = await apiClient.get<{
                system?: { cpu_percent?: number; cpu_count?: number };
                memory?: { total_mb?: number; available_mb?: number; percent_used?: number };
            }>('/somabrain/admin/diagnostics');
            const cpu = d?.system;
            const mem = d?.memory;
            if (cpu && typeof cpu.cpu_percent === 'number') {
                this._sysCpu = {
                    percent: cpu.cpu_percent,
                    cores: cpu.cpu_count ?? 0,
                };
            }
            if (mem && typeof mem.percent_used === 'number' && mem.total_mb) {
                const usedMb = (mem.total_mb - (mem.available_mb ?? 0)) || 0;
                this._sysRam = {
                    usedMb,
                    totalMb: mem.total_mb,
                    percent: mem.percent_used,
                };
            }
            this.requestUpdate();
        } catch {
            // Diagnostics optional — hide the System block. Never invent meters.
        }
    }

    private async _loadMemoryStatus(): Promise<void> {
        try {
            const rows = await apiClient.get<{ memories?: unknown[]; total?: number }>('/memory/');
            const ok = !!(rows && Array.isArray(rows.memories));
            if (ok) {
                this._memoryDot = 'ok';
                this._memoryTooltip = 'Memory ready';
                this._memoryQueued = false;
            }
            this.requestUpdate();
        } catch {
            // Honest degradation: memory down never blocks chat. Writes queue
            // in the agent WAL until the brain recovers (T-6).
            this._memoryDot = 'warn';
            this._memoryTooltip =
                'Memory unavailable — messages are queued and will sync when connected';
            this._memoryQueued = true;
        }
    }

    private async _loadChannels(): Promise<void> {
        try {
            const data = await apiClient.get<
                { channels?: { id?: string; kind?: string; name?: string; status?: string }[] } | { id?: string; kind?: string; name?: string; status?: string }[]
            >('/bridges/channels');
            const list = Array.isArray(data) ? data : (data.channels ?? []);
            this._channels = list.map((c, i) => ({
                id: c.id ?? String(i),
                kind: (c.kind ?? '').toLowerCase(),
                name: c.name ?? c.kind ?? 'channel',
                connected: (c.status ?? '').toLowerCase() === 'active' || (c.status ?? '').toLowerCase() === 'connected',
            }));
            this._channelsLoaded = true;
            this.requestUpdate();
        } catch {
            this._channelsLoaded = false;
        }
    }

    private async _loadUser() {
        try {
            const me = await apiClient.get<{ name?: string; username?: string; email?: string; role?: string }>(
                '/auth/me',
            );
            const name = me.name || me.username || me.email || 'User';
            this._userName = name;
            this._userRole = me.role ?? '';
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
                this._persistSelectedAgentId();
                this._connectWebSocket();
            }
        } catch (error) {
            console.error('[SomaChat] Failed to load agents:', error);
        }
    }

    /** The cognitive panel (soma-cognitive-panel.ts:736+) reads
     *  sessionStorage 'soma_agent_id' first, then localStorage — same key.
     *  Persist here so the panel can act on the agent this chat selected. */
    private _persistSelectedAgentId(): void {
        if (!this._selectedAgentId) return;
        sessionStorage.setItem('soma_agent_id', this._selectedAgentId);
    }

    private async _loadConversations(): Promise<void> {
        this._conversationsLoading = true;
        this._conversationsError = '';
        try {
            const response = await apiClient.get<unknown>('/chat/conversations');
            // apiClient unwraps paginated_response → { items, total, … }.
            // A raw array is also accepted. Never invent rows from an empty parse.
            const items: Record<string, unknown>[] = Array.isArray(response)
                ? (response as Record<string, unknown>[])
                : ((response as { items?: Record<string, unknown>[]; data?: Record<string, unknown>[] })
                      ?.items ??
                  (response as { data?: Record<string, unknown>[] })?.data ??
                  []);

            this._conversations = items.map((conv) => ({
                id: String(conv.id ?? ''),
                // No invented titles. A missing title renders as a dash.
                title: typeof conv.title === 'string' ? conv.title : '',
                lastMessage: typeof conv.last_message === 'string' ? conv.last_message : '',
                updatedAt: typeof conv.updated_at === 'string' ? conv.updated_at : '',
                messageCount: typeof conv.message_count === 'number' ? conv.message_count : undefined,
            }));
        } catch (error) {
            // Failure is not "no conversations".
            console.error('[SomaChat] Failed to load conversations:', error);
            this._conversations = [];
            this._conversationsError = 'Failed to load conversations. The request did not succeed.';
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
            console.error('[SomaChat] Failed to create conversation:', error);
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
            console.error('[SomaChat] Rename failed:', error);
        } finally {
            this._renamingId = '';
            this._renameDraft = '';
        }
    }

    private async _deleteConversation(id: string) {
        // Optimistic remove so the row disappears immediately.
        const prev = this._conversations;
        this._conversations = prev.filter((c) => c.id !== id);
        if (id === this._activeConversationId) {
            this._activeConversationId = '';
            this._messages = [];
            this._streamContent = '';
            this._isStreaming = false;
            this._chatTitle = 'New conversation';
        }
        try {
            await apiClient.delete(`/chat/conversations/${id}`);
            await this._loadConversations();
        } catch (error) {
            console.error('[SomaChat] Delete failed:', error);
            this._conversations = prev;
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
    // RIGHT RAIL — the single surface registry (UI-X-01…08)
    // ==========================================================================

    private _toggleRightPanel() {
        this._showRightPanel = !this._showRightPanel;
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
        this._wsClient.on('chat.turn_meta', (data) => {
            this._handleTurnMeta(data as {
                model?: string;
                lanes?: Record<string, number>;
                memory_hits?: { text?: string; score?: number | null; kind?: string | null }[];
                context_tokens?: number;
            });
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
            const payload = data as {
                iq_tier?: string;
                agent_id?: string;
                tools_available?: number;
                iq?: { knobs?: Record<string, unknown>; derived?: Record<string, unknown> } | undefined;
            } | undefined;
            // AgentIQ: take knobs/derived only if the server sent them. Never
            // recompute in the browser — and never synthesize derived fields
            // from the handshake. `iq_tier` is a tier string, not a model name
            // and not a DerivedSettings value; the AgentIQ API (verified 200)
            // is the only source for derived settings. The active model is
            // announced by `chat.turn_meta.model`, not by the handshake.
            if (payload?.iq) {
                iqStore.setFromServer(
                    (payload.iq.knobs as never) ?? null,
                    (payload.iq.derived as never) ?? null,
                );
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
        // A missing client is a client that has not been built yet, not a
        // refusal. Build it rather than reporting "not connected".
        if (!this._wsClient) {
            this._connectWebSocket();
        }
        if (!this._wsClient) return false;
        if (this._wsClient.connected) return true;

        return new Promise((resolve) => {
            // Subscribe BEFORE connecting. A connection that completes before
            // the listener is attached is missed, and the caller then waits the
            // full timeout for an event that already happened.
            const ws = this._wsClient!;
            const unsubscribe = ws.on('connected', () => {
                clearTimeout(timer);
                unsubscribe();
                resolve(true);
            });
            const timer = setTimeout(() => {
                unsubscribe();
                resolve(false);
            }, 5000);
            ws.connect();
        });
    }

    // ==========================================================================
    // STREAM HANDLERS
    // ==========================================================================

    private _handleIncomingMessage(msg: ChatMessage) {
        // Only a real chat row may land in the transcript. The WS also carries
        // metadata frames whose payload is not a ChatMessage; treating one as a
        // message would clear the live stream and push an empty bubble.
        if (!msg || typeof msg !== 'object' || (msg.role !== 'user' && msg.role !== 'assistant' && msg.role !== 'system')) {
            return;
        }
        this._isStreaming = false;
        this._streamContent = '';
        this._activeResponseId = '';
        this._messages = [...this._messages, { ...msg, content: msg.content ?? '' }];
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private _handleStreamDelta(chunk: { delta?: string; content?: string; response_id?: string }) {
        if (this._turnStopped) return;
        if (chunk?.response_id) {
            // A different response id while nothing is buffered is a new turn,
            // not a stale frame: adopt it. While text is buffered, ignore a
            // foreign id so two turns cannot interleave in one bubble.
            if (this._activeResponseId && this._activeResponseId !== chunk.response_id) {
                if (this._streamContent) return;
            }
            this._activeResponseId = chunk.response_id;
        }
        if (this._paused) return;
        const delta = chunk.delta ?? chunk.content ?? '';
        this._streamContent += delta;
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private _handleStreamDone(chunk: { content?: string; confidence?: number; response_id?: string }) {
        const foreign =
            !!chunk?.response_id &&
            !!this._activeResponseId &&
            chunk.response_id !== this._activeResponseId;
        // A done for another response must not swallow the tokens already
        // streamed for this one. Commit what we have; only a stopped turn
        // discards its buffer.
        if (this._turnStopped && !this._streamContent) {
            this._streamContent = '';
            this._activeTools = [];
            this._activeResponseId = '';
            this._isStreaming = false;
            this._turnStopped = false;
            return;
        }
        if (foreign && !this._streamContent && !chunk.content) {
            this._activeTools = [];
            this._isStreaming = false;
            return;
        }
        const content = chunk.content ?? this._streamContent;
        const message: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content,
            // Server message time is not in the stream frame. A client-clock
            // stamp presented as message time is a lie — leave it empty and
            // the bubble renders no time (history rows carry created_at).
            timestamp: '',
            confidence: chunk.confidence,
            tools: this._activeTools.length > 0 ? [...this._activeTools] : undefined,
        };
        this._streamContent = '';
        this._activeTools = [];
        this._activeResponseId = '';
        this._isStreaming = false;
        this._turnStopped = false;
        this._messages = [...this._messages, message];
        this.updateComplete.then(() => this._scrollToBottom());
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
                    timestamp: '',
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
                timestamp: '',
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

    /**
     * Turn metadata the orchestrator emits after model selection and
     * 5-lane context build (`chat.turn_meta`). The model actually in use,
     * the lane allocation, and what memory recall returned — never guessed
     * in the browser.
     */
    private _handleTurnMeta(p: {
        model?: string;
        lanes?: Record<string, number>;
        memory_hits?: { text?: string; score?: number | null; kind?: string | null }[];
        context_tokens?: number;
    }) {
        if (p.model) {
            this._modelLabel = p.model;
        }
        this._turnLanes = p.lanes ?? null;
        this._memoryHits = Array.isArray(p.memory_hits) ? p.memory_hits : [];
        this._contextTokens = typeof p.context_tokens === 'number' ? p.context_tokens : 0;
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
                this._sendChatControl('chat.pause');
                break;
            case 'resume':
                this._paused = false;
                this._sendChatControl('chat.resume');
                break;
            case 'stop':
                this._stopTurn();
                break;
            case 'reset':
                void this._resetChat();
                break;
            case 'nudge':
                this._sendChatControl('chat.nudge');
                break;
            default:
                break;
        }
    }

    /**
     * Forward a chat control to the gateway over the live WebSocket.
     *
     * The gateway already implements `chat.pause` / `chat.resume` /
     * `chat.nudge` / `chat.stop` / `chat.reset`
     * (`services/gateway/consumers/chat.py`, `CONTROL_MSG_TYPES`). A control
     * that only mutates local state is a lie: the turn keeps running on the
     * server while the UI pretends it stopped. Every control MUST reach the
     * transport.
     *
     * Fails loud when there is no socket: the user is told the control could
     * not be applied, rather than being shown a state the server never heard.
     */
    private _sendChatControl(type: 'chat.pause' | 'chat.resume' | 'chat.nudge' | 'chat.stop' | 'chat.reset') {
        if (!this._wsClient?.connected) {
            this._pushInlineError(`Cannot send ${type} — WebSocket disconnected`);
            return;
        }
        this._wsClient.send({
            type,
            payload: { conversation_id: this._activeConversationId || undefined },
        });
    }

    private _stopTurn() {
        // Tell the gateway first: cancelling only the local buffer leaves the
        // model turn running server-side. `chat.stop` is fail-closed on the
        // server (no-op when idle) so this is safe to send even when unsure.
        this._sendChatControl('chat.stop');
        if (!this._isStreaming) return;
        this._turnStopped = true;
        this._paused = false;
        this._finalizeStreamedMessage(true);
    }

    private async _resetChat() {
        this._stopTurn();
        // Clear the server-side conversation stream state too, not just the
        // local transcript (`chat.reset` in the gateway control handler).
        this._sendChatControl('chat.reset');
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
            // Client send-time is not the server message time. History rows
            // carry created_at; a live bubble shows no clock instead of one.
            timestamp: '',
            attachments:
                detail.attachments?.map((f) => ({ name: f.name, type: f.type, size: f.size })) ?? [],
        };
        this._messages = [...this._messages, userMessage];
        this._turnStopped = false;
        this._paused = false;
        this._streamContent = '';
        this._activeTools = [];
        this._activeResponseId = '';
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
                    const input = this.renderRoot.querySelector('soma-composer') as HTMLElement | null;
                    input?.shadowRoot?.querySelector('textarea')?.focus();
                });
            }
        }
    }

    private async _selectConversation(id: string) {
        this._activeConversationId = id;
        const conv = this._conversations.find((c) => c.id === id);
        this._chatTitle = conv?.title || 'Conversation';
        this._streamContent = '';
        this._isStreaming = false;
        await this._loadConversationMessages(id);
    }

    private async _loadConversationMessages(conversationId: string): Promise<void> {
        this._messagesLoading = true;
        try {
            const response = await apiClient.get<unknown>(`/chat/conversations/${conversationId}/messages`);
            // apiClient unwraps paginated_response → { items, total, … }.
            // A raw array is also accepted. Do NOT read .data — that key is
            // stripped by the unwrap and made every open conversation blank.
            const raw: Record<string, unknown>[] = Array.isArray(response)
                ? (response as Record<string, unknown>[])
                : ((response as { items?: Record<string, unknown>[]; data?: Record<string, unknown>[] })
                      ?.items ??
                  (response as { data?: Record<string, unknown>[] })?.data ??
                  []);

            this._messages = raw.map((msg: Record<string, unknown>) => {
                const meta = msg.metadata;
                const metaObj =
                    meta && typeof meta === 'object' ? (meta as Record<string, unknown>) : null;
                return {
                    id: String(msg.id ?? `msg-${Date.now()}`),
                    role: (msg.role as ChatMessage['role']) ?? 'assistant',
                    content: String(msg.content ?? ''),
                    timestamp: String(msg.created_at ?? msg.timestamp ?? ''),
                    confidence: metaObj?.confidence as number | undefined,
                };
            });
            this.updateComplete.then(() => this._scrollToBottom());
        } catch (error) {
            console.error('[SomaChat] Failed to load messages:', error);
            // Keep the previous transcript on a failed reload — do not wipe the UI.
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
        window.dispatchEvent(new CustomEvent('soma-navigate', { detail: { route: path } }));
    }

    private async _logout() {
        // SECURITY: the session lives in httpOnly cookies. Clearing storage
        // does not end it — `checkAuth()` reads the cookie and would sign the
        // user straight back in. POST /auth/logout first so the server deletes
        // the cookies, then clear client residue and leave.
        try {
            await apiClient.logout();
        } catch (err) {
            console.error('[SomaChat] server logout failed', err);
        }
        localStorage.removeItem('soma_auth_token');
        localStorage.removeItem('soma_user');
        localStorage.removeItem('soma_keycloak_token');
        sessionStorage.removeItem('soma_auth_state');
        sessionStorage.removeItem('soma_auth_nonce');
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
            ${this._renderDeleteConfirm()}
        `;
    }

    private _renderDeleteConfirm() {
        const d = this._pendingDelete;
        return html`
            <soma-glass-modal
                size="sm"
                .open=${!!d}
                title="Delete conversation"
                subtitle="This cannot be undone"
                @soma-modal-close=${() => (this._pendingDelete = null)}
            >
                <div class="del-body">
                    <div class="del-icon">${ICON('delete_forever', 28)}</div>
                    <p class="del-text">
                        Delete <strong>${d?.title || 'this conversation'}</strong>?
                    </p>
                    <p class="del-sub">The chat transcript and local history will be removed.</p>
                    <label class="del-check">
                        <input
                            type="checkbox"
                            .checked=${this._deleteDontAsk}
                            @change=${(e: Event) => {
                                this._deleteDontAsk = (e.target as HTMLInputElement).checked;
                            }}
                        />
                        <span>Don’t ask again</span>
                    </label>
                </div>
                <div slot="footer" class="del-actions">
                    <button class="del-btn ghost" @click=${() => (this._pendingDelete = null)}>Cancel</button>
                    <button
                        class="del-btn danger"
                        @click=${() => {
                            const id = this._pendingDelete?.id;
                            if (this._deleteDontAsk) {
                                this._deleteSkipConfirm = true;
                                try {
                                    localStorage.setItem('soma_skip_delete_confirm', '1');
                                } catch {
                                    /* storage blocked — session-only skip */
                                }
                            }
                            this._pendingDelete = null;
                            if (id) void this._deleteConversation(id);
                        }}
                    >
                        Delete
                    </button>
                </div>
            </soma-glass-modal>
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
                        : this._conversationsError
                            ? html`<div class="empty-list" data-control="conversations-error">${this._conversationsError}</div>`
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
                              <div class="conversation-title">${conv.title || '—'}</div>
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
                                      if (this._deleteSkipConfirm) {
                                          void this._deleteConversation(conv.id);
                                          return;
                                      }
                                      this._deleteDontAsk = false;
                                      this._pendingDelete = {
                                          id: conv.id,
                                          title: conv.title || 'this conversation',
                                      };
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
                <div class="messages" @tool-approval=${this._onToolApproval} role="log" aria-live="polite">
                    ${this._messagesLoading
                        ? html`
                              <div class="msg-skeleton" aria-hidden="true">
                                  <div class="bar mid"></div>
                                  <div class="bar"></div>
                                  <div class="bar short"></div>
                              </div>
                          `
                        : this._messages.length === 0 &&
                            !this._isStreaming &&
                            !this._messagesLoading &&
                            !this._activeConversationId
                            ? this._renderWelcome()
                            : html`
                                  ${this._messages.map((msg) => this._renderMessage(msg))}
                                  ${this._isStreaming
                                      ? html`
                                            <soma-message
                                                message-role="assistant"
                                                .text=${this._streamContent}
                                                .tools=${this._activeTools}
                                                .streaming=${!this._paused}
                                            ></soma-message>
                                        `
                                      : nothing}
                              `}
                </div>

                <soma-composer
                    .busy=${this._isStreaming}
                    .placeholder=${this._selectedAgentId
                        ? 'Message Soma…'
                        : 'Select an agent to start chatting'}
                    @send-message=${this._onComposerSend}
                    @clear-chat=${this._onClearChat}
                    @export-chat=${this._onExportChat}
                ></soma-composer>

                <footer class="dock ${this._knobPanelOpen ? 'open' : ''}" data-control="chat-footer">
                    <div class="dock-bar" @click=${() => (this._knobPanelOpen = !this._knobPanelOpen)}>
                        <div class="dock-vitals">
                            <span class="vital" title=${this._brainTooltip}>
                                <soma-status-dot kind="brain" state=${this._brainDot} title=${this._brainTooltip} label="brain"></soma-status-dot>
                                <em>Brain</em>
                            </span>
                            <span class="vital" title=${this._connectionStatus === 'ok' ? 'Sync · Connected' : 'Sync · Degraded'}>
                                <soma-status-dot
                                    kind="sync"
                                    state=${this._connectionStatus === 'ok' ? 'ok' : this._connectionStatus === 'degraded' ? 'warn' : 'pending'}
                                    title=${this._connectionStatus === 'ok' ? 'Sync · Connected' : this._connectionStatus === 'degraded' ? 'Sync · Degraded' : 'Sync · Reconnecting'}
                                    label="sync"
                                ></soma-status-dot>
                                <em>Sync</em>
                            </span>
                            <span class="vital" title=${this._memoryTooltip}>
                                <soma-status-dot kind="memory" state=${this._memoryDot} title=${this._memoryTooltip} label="memory"></soma-status-dot>
                                <em>Memory</em>
                                ${this._memoryQueued
                                    ? html`<em class="memory-queued-chip" title=${this._memoryTooltip}>queued</em>`
                                    : nothing}
                            </span>
                            ${this._memoryHits.length
                                ? html`<span class="vital text" title="Recall this turn">🧠 ${this._memoryHits.length}</span>`
                                : nothing}
                            ${this._contextTokens
                                ? html`<span class="vital text" title="Context tokens">⎘ ${this._contextTokens}</span>`
                                : nothing}
                            ${this._modelLabel
                                ? html`<span class="vital text" title="Model">${this._modelLabel}</span>`
                                : nothing}
                            ${this._isStreaming
                                ? html`<span class="vital text pulse">● working</span>`
                                : nothing}
                        </div>
                        <span
                            class="dock-knobs-preview"
                            title="Live from AgentIQ · Capsule.persona_config.knobs"
                            data-control="iq-preview"
                            >${this._iqPreview
                                ? html`IQ ${this._iqPreview.iq} · AUTO ${this._iqPreview.auto}`
                                : html`IQ —`}</span
                        >
                        <button
                            class="dock-handle"
                            aria-expanded=${this._knobPanelOpen ? 'true' : 'false'}
                            aria-label=${this._knobPanelOpen ? 'Hide agent knobs' : 'Show agent knobs'}
                            @click=${(e: Event) => {
                                e.stopPropagation();
                                this._knobPanelOpen = !this._knobPanelOpen;
                            }}
                        >
                            ${ICON(this._knobPanelOpen ? 'expand_more' : 'expand_less', 18)}
                        </button>
                    </div>

                    <div class="dock-panel" aria-hidden=${this._knobPanelOpen ? 'false' : 'true'}>
                        <div class="dock-panel-inner">
                            <div class="dock-panel-head">
                                <strong>Agent knobs</strong>
                                <span class="dock-status-row">
                                    <soma-status-dot kind="brain" state=${this._brainDot} title=${this._brainTooltip} label="brain"></soma-status-dot>
                                    <soma-status-dot
                                        kind="sync"
                                        state=${this._connectionStatus === 'ok' ? 'ok' : this._connectionStatus === 'degraded' ? 'warn' : 'pending'}
                                        title="sync"
                                        label="sync"
                                    ></soma-status-dot>
                                    <soma-status-dot kind="memory" state=${this._memoryDot} title=${this._memoryTooltip} label="memory"></soma-status-dot>
                                    <span class="muted">${this._brainTooltip}</span>
                                </span>
                                <span class="muted">tune live · saved to Capsule</span>
                                <span class="spacer"></span>
                                <button class="dock-x" aria-label="Close knobs" @click=${() => (this._knobPanelOpen = false)}>
                                    ${ICON('close', 16)}
                                </button>
                            </div>
                            <soma-agent-iq
                                .capsuleId=${this._knobCapsuleId ||
                                    this._agents.find((a) => a.id === this._selectedAgentId)?.capsule_id ||
                                    ''}
                                @click=${(e: Event) => e.stopPropagation()}
                            ></soma-agent-iq>
                        </div>
                    </div>
                </footer>
            </main>
        `;
    }

    private _renderWelcome() {
        const firstName =
            this._userName && this._userName !== 'User' ? `, ${this._userName.split(' ')[0]}` : '';
        const start = (text: string) => {
            void this._startNewChat().then(() => {
                const input = this.renderRoot.querySelector('soma-composer') as HTMLElement & {
                    text?: string;
                } | null;
                if (input) {
                    input.text = text;
                    input.focus?.();
                }
            });
        };
        const channelCards = [
            { kind: 'telegram', label: 'Telegram', desc: 'Chat on Telegram wherever you are.' },
            { kind: 'whatsapp', label: 'WhatsApp', desc: 'Send and receive WhatsApp messages.' },
            { kind: 'email', label: 'Email', desc: 'Let Soma read and send emails on your behalf.' },
        ];
        const known = new Map(this._channels.map((c) => [c.kind, c]));
        return html`
            <div class="welcome">
                <div class="welcome-hero">
                    <h2>Hello! I'm Soma</h2>
                    <p>How can I help you today?</p>
                </div>

                ${this._welcomeWarning
                    ? html`
                          <div class="welcome-banner" role="status">
                              <span class="wb-icon">${ICON('warning', 18)}</span>
                              <span class="wb-text">${this._welcomeWarning}</span>
                              <button class="wb-action" @click=${() => this._navigate('/settings')}>Open Settings</button>
                              <button class="wb-dismiss" title="Dismiss" aria-label="Dismiss" @click=${() => (this._welcomeWarning = '')}>
                                  ${ICON('close', 16)}
                              </button>
                          </div>
                      `
                    : nothing}

                <div class="welcome-quick" role="navigation" aria-label="Quick actions">
                    <button class="wq-card" @click=${() => this._toggleRightPanel()}>
                        ${ICON('folder_open', 22)}
                        <span class="wq-label">Files</span>
                    </button>
                    <button class="wq-card" @click=${() => this._navigate('/settings/tools')}>
                        ${ICON('extension', 22)}
                        <span class="wq-label">Modules</span>
                    </button>
                    <button class="wq-card" @click=${() => this._startNewChat()}>
                        ${ICON('add_comment', 22)}
                        <span class="wq-label">New chat</span>
                    </button>
                </div>

                ${this._channelsLoaded
                    ? html`
                          <section class="welcome-section" aria-label="Connect channels">
                              <div class="ws-head">
                                  <h3>Connect channels</h3>
                                  <button class="ws-link" @click=${() => this._navigate('/settings/channels')}>Manage ›</button>
                              </div>
                              <div class="ws-cards">
                                  ${channelCards.map((ch) => {
                                      const row = known.get(ch.kind);
                                      const unconfigured = !row || !row.connected;
                                      return html`
                                          <div class="ws-card">
                                              <div class="ws-card-title">${ch.label}</div>
                                              <div class="ws-card-desc">${ch.desc}</div>
                                              ${unconfigured
                                                  ? html`<button
                                                        class="ws-cta"
                                                        @click=${() => this._navigate('/settings/channels')}
                                                    >
                                                        Connect
                                                    </button>`
                                                  : html`<span class="ws-chip"><i class="ws-dot"></i> Connected</span>`}
                                          </div>
                                      `;
                                  })}
                              </div>
                          </section>
                      `
                    : nothing}

                ${this._sysRam || this._sysCpu
                    ? html`
                          <section class="welcome-section" aria-label="System">
                              <div class="ws-head">
                                  <h3>System</h3>
                              </div>
                              <div class="sys-rows">
                                  ${this._sysRam
                                      ? html`
                                            <div class="sys-row">
                                                <span class="sys-name">RAM</span>
                                                <span class="sys-track"
                                                    ><span
                                                        class="sys-fill"
                                                        style="width:${Math.min(100, Math.max(0, this._sysRam.percent))}%;background:${this._sysRam.percent >= 85
                                                            ? '#EF4444'
                                                            : this._sysRam.percent >= 70
                                                              ? '#F59E0B'
                                                              : 'linear-gradient(90deg,#10B981,#34D399)'}"
                                                    ></span
                                                ></span>
                                                <span class="sys-val"
                                                    >${Math.round(this._sysRam.percent)}% · ${(this._sysRam.usedMb / 1024).toFixed(1)} / ${(
                                                        this._sysRam.totalMb / 1024
                                                    ).toFixed(1)} GB</span
                                                >
                                            </div>
                                        `
                                      : nothing}
                                  ${this._sysCpu
                                      ? html`
                                            <div class="sys-row">
                                                <span class="sys-name">CPU</span>
                                                <span class="sys-track"
                                                    ><span
                                                        class="sys-fill"
                                                        style="width:${Math.min(100, Math.max(0, this._sysCpu.percent))}%;background:${this._sysCpu.percent >= 85
                                                            ? '#ef4444'
                                                            : this._sysCpu.percent >= 70
                                                              ? '#f59e0b'
                                                              : '#22c55e'}"
                                                    ></span
                                                ></span>
                                                <span class="sys-val"
                                                    >${Math.round(this._sysCpu.percent)}%${this._sysCpu.cores ? ` · ${this._sysCpu.cores} cores` : ''}</span
                                                >
                                            </div>
                                        `
                                      : nothing}
                              </div>
                          </section>
                      `
                    : nothing}

                <div class="welcome-footer">SomaTech · Cognitive AI Agent</div>
            </div>
        `;
    }

    private _renderMessage(msg: ChatMessage) {
        return html`
            <soma-message
                message-role=${msg.role}
                .text=${msg.content}
                .timestamp=${msg.timestamp}
                .tools=${msg.tools ?? []}
                .attachments=${msg.attachments ?? []}
                .stopped=${!!msg.stopped}
                .confidence=${msg.confidence}
                .error=${msg.error ?? ''}
            ></soma-message>
        `;
    }

    /* ---------- RIGHT RAIL (UI-X-01…08) ---------- */

    /**
     * The chat view does NOT own a second rail. All eight right-rail surfaces
     * (Files, Tools, Browser, Editor, Debug, Capsule, Brain, Desktop) live in
     * the one typed registry at `soma-right-panel`. The previous
     * memory|files|channel rail here was a competing, partial surface set and
     * has been deleted (SOMA-01-UIUX-001 §6, REQ-UIX-020).
     */
    private _renderCanvas() {
        return html`
            <aside class="right-canvas ${this._showRightPanel ? 'open' : ''}" aria-label="Surface rail">
                <div class="canvas-rail">
                    <button
                        class="rail-btn ${this._showRightPanel ? 'active' : ''}"
                        title="Surfaces"
                        aria-label="Toggle surface rail"
                        aria-pressed=${this._showRightPanel ? 'true' : 'false'}
                        @click=${this._toggleRightPanel}
                    >
                        ${ICON('dock_to_right', 20)}
                    </button>
                </div>
                ${this._showRightPanel
                    ? html`
                          <div class="canvas-panel">
                              <soma-right-panel></soma-right-panel>
                          </div>
                      `
                    : nothing}
            </aside>
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
            this._persistSelectedAgentId();
            this._activeConversationId = '';
            this._messages = [];
            this._chatTitle = 'New conversation';
            this._connectWebSocket();
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-chat': SomaChat;
    }
}
