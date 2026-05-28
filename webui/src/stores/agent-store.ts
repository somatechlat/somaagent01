/**
 * Agent Store — Active agent state, profiles, presets
 * VIBE COMPLIANT: Real reactive state, no mocks
 */

import { createContext } from '@lit/context';

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
        profiles: [
            { id: 'default', name: 'Default', description: 'General purpose assistant', system_prompt: 'You are a helpful assistant.' },
            { id: 'developer', name: 'Developer', description: 'Code-focused, concise', system_prompt: 'You are an expert software developer. Be concise, write clean code, explain your reasoning.' },
            { id: 'researcher', name: 'Researcher', description: 'Deep research with citations', system_prompt: 'You are a thorough researcher. Provide citations, explore edge cases, and validate assumptions.' },
            { id: 'security', name: 'Security Auditor', description: 'Security-focused analysis', system_prompt: 'You are a security analyst. Think like an attacker, identify vulnerabilities, suggest mitigations.' },
            { id: 'creative', name: 'Creative', description: 'Brainstorming and creative writing', system_prompt: 'You are a creative partner. Brainstorm freely, explore unconventional ideas, and iterate rapidly.' },
        ],
        presets: [
            { id: 'max-power', name: 'Max Power', provider: 'anthropic', model: 'claude-3-opus-20240229', temperature: 0.7, max_tokens: 4096, context_length: 200000 },
            { id: 'balanced', name: 'Balanced', provider: 'anthropic', model: 'claude-3-sonnet-20240229', temperature: 0.5, max_tokens: 2048, context_length: 200000 },
            { id: 'cost-efficient', name: 'Cost Efficient', provider: 'openai', model: 'gpt-4o-mini', temperature: 0.3, max_tokens: 1024, context_length: 128000 },
        ],
        activeProfileId: 'default',
        activePresetId: 'balanced',
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
            const { apiClient } = await import('../services/api-client.js');
            const res = await apiClient.get(`/agents/${agentId}`) as AgentState['currentAgent'];
            this.setCurrentAgent(res);
        } catch (e) {
            console.error('[AgentStore] Failed to load agent:', e);
        }
    }
}

export const agentStore = new AgentStore();
