/**
 * Agent Store — Active agent state, profiles, presets
 * VIBE COMPLIANT: Real reactive state, no mocks
 */

import { createContext } from '@lit/context';
import { apiClient } from '../services/api-client.js';

export interface AgentProfile {
    id: string;
    name: string;
    description: string;
    system_prompt: string;
    icon?: string;
}

export interface ModelPreset {
    id: string;
    name: string;
    provider: string;
    model: string;
    temperature: number;
    max_tokens: number;
    context_length: number;
}

export interface AgentState {
    currentAgent: {
        id: string;
        name: string;
        description: string;
        status: 'active' | 'paused' | 'archived' | 'error';
        iq_level: number;
        skin_id?: string;
    } | null;
    profiles: AgentProfile[];
    presets: ModelPreset[];
    activeProfileId: string | null;
    activePresetId: string | null;
}

export const agentContext = createContext<AgentStore>('agent-store');

export class AgentStore {
    private _state: AgentState = {
        currentAgent: null,
        profiles: [],
        presets: [],
        activeProfileId: null,
        activePresetId: null,
    };

    private _listeners: Set<() => void> = new Set();

    get state(): Readonly<AgentState> {
        return { ...this._state, profiles: [...this._state.profiles], presets: [...this._state.presets] };
    }

    subscribe(listener: () => void): () => void {
        this._listeners.add(listener);
        return () => this._listeners.delete(listener);
    }

    private _notify() {
        this._listeners.forEach(l => l());
    }

    setCurrentAgent(agent: AgentState['currentAgent']) {
        this._state.currentAgent = agent;
        this._notify();
    }

    setActiveProfile(profileId: string) {
        this._state.activeProfileId = profileId;
        this._notify();
    }

    setActivePreset(presetId: string) {
        this._state.activePresetId = presetId;
        this._notify();
    }

    addProfile(profile: AgentProfile) {
        this._state.profiles.push(profile);
        this._notify();
    }

    addPreset(preset: ModelPreset) {
        this._state.presets.push(preset);
        this._notify();
    }

    async loadAgent(agentId: string) {
        try {
            const res = await apiClient.get(`/agents/${agentId}`) as AgentState['currentAgent'];
            this.setCurrentAgent(res);
        } catch (e) {
            console.error('[AgentStore] Failed to load agent:', e);
        }
    }
}

export const agentStore = new AgentStore();
