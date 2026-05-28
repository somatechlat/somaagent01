/**
 * Workspace Store — Layout state for Agent Workspace
 * VIBE COMPLIANT: Real reactive state, no mocks
 */

import { createContext } from '@lit/context';

export interface WorkspaceState {
    rightPanelOpen: boolean;
    activeSurface: string | null;
    panelWidth: number;
    composerExpanded: boolean;
    activeAgentId: string | null;
    activeConversationId: string | null;
}

export const workspaceContext = createContext<WorkspaceStore>('workspace-store');

export class WorkspaceStore {
    private _state: WorkspaceState = {
        rightPanelOpen: false,
        activeSurface: null,
        panelWidth: 400,
        composerExpanded: false,
        activeAgentId: null,
        activeConversationId: null,
    };

    private _listeners: Set<() => void> = new Set();

    get state(): Readonly<WorkspaceState> {
        return { ...this._state };
    }

    subscribe(listener: () => void): () => void {
        this._listeners.add(listener);
        return () => this._listeners.delete(listener);
    }

    private _notify() {
        this._listeners.forEach(l => l());
    }

    toggleRightPanel(surface?: string) {
        if (surface && this._state.activeSurface === surface && this._state.rightPanelOpen) {
            this._state.rightPanelOpen = false;
            this._state.activeSurface = null;
        } else {
            this._state.rightPanelOpen = true;
            this._state.activeSurface = surface || this._state.activeSurface;
        }
        this._notify();
    }

    setSurface(surface: string | null) {
        this._state.activeSurface = surface;
        this._state.rightPanelOpen = surface !== null;
        this._notify();
    }

    setPanelWidth(width: number) {
        this._state.panelWidth = Math.max(280, Math.min(600, width));
        this._notify();
    }

    setComposerExpanded(expanded: boolean) {
        this._state.composerExpanded = expanded;
        this._notify();
    }

    setActiveAgent(agentId: string | null) {
        this._state.activeAgentId = agentId;
        this._notify();
    }

    setActiveConversation(conversationId: string | null) {
        this._state.activeConversationId = conversationId;
        this._notify();
    }
}

export const workspaceStore = new WorkspaceStore();
