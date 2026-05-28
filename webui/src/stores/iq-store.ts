/**
 * IQ Store — Agent Intelligence Quotient state
 * 3 knobs: intelligence, autonomy, resource_budget
 * Derived settings computed client-side
 */

import { createContext } from '@lit/context';

export interface IQKnobs {
    intelligence: number;   // 1-10
    autonomy: number;       // 1-10
    budget: number;         // $/turn, 0.01-1.00
}

export interface DerivedSettings {
    temperature: number;
    max_tokens: number;
    rlm_iterations: number;
    recall_limit: number;
    model_tier: 'budget' | 'standard' | 'premium' | 'flagship';
    brain_query_enabled: boolean;
    require_hitl: 'none' | 'dangerous' | 'all';
    tool_approval: 'none' | 'dangerous' | 'all';
    egress_allowed: 'none' | 'whitelist' | 'expanded' | 'unrestricted';
    token_limit: number;
    cost_tier: 'low' | 'mid' | 'high';
    thinking_budget: number;
}

export const iqContext = createContext<IQStore>('iq-store');

export class IQStore {
    private _knobs: IQKnobs = {
        intelligence: 7,
        autonomy: 5,
        budget: 0.05,
    };

    private _listeners: Set<() => void> = new Set();

    get knobs(): Readonly<IQKnobs> {
        return { ...this._knobs };
    }

    get derived(): DerivedSettings {
        return this._computeDerived(this._knobs);
    }

    subscribe(listener: () => void): () => void {
        this._listeners.add(listener);
        return () => this._listeners.delete(listener);
    }

    private _notify() {
        this._listeners.forEach(l => l());
    }

    setIntelligence(value: number) {
        this._knobs.intelligence = Math.max(1, Math.min(10, value));
        this._notify();
    }

    setAutonomy(value: number) {
        this._knobs.autonomy = Math.max(1, Math.min(10, value));
        this._notify();
    }

    setBudget(value: number) {
        this._knobs.budget = Math.max(0.01, Math.min(1.0, value));
        this._notify();
    }

    setKnobs(knobs: Partial<IQKnobs>) {
        if (knobs.intelligence !== undefined) this._knobs.intelligence = Math.max(1, Math.min(10, knobs.intelligence));
        if (knobs.autonomy !== undefined) this._knobs.autonomy = Math.max(1, Math.min(10, knobs.autonomy));
        if (knobs.budget !== undefined) this._knobs.budget = Math.max(0.01, Math.min(1.0, knobs.budget));
        this._notify();
    }

    private _computeDerived(k: IQKnobs): DerivedSettings {
        // Intelligence mapping
        const tempMap = [0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45];
        const tokenMap = [512, 1024, 1536, 2048, 2560, 3072, 3584, 4096, 6144, 8192];
        const rlmMap = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5];
        const recallMap = [10, 15, 20, 25, 30, 35, 40, 45, 50, 60];
        const tierMap: DerivedSettings['model_tier'][] = ['budget', 'budget', 'standard', 'standard', 'standard', 'premium', 'premium', 'premium', 'flagship', 'flagship'];

        // Autonomy mapping
        const hitlMap: DerivedSettings['require_hitl'][] = ['none', 'none', 'dangerous', 'dangerous', 'dangerous', 'all', 'all', 'all', 'all', 'all'];
        const approvalMap: DerivedSettings['tool_approval'][] = ['none', 'none', 'none', 'dangerous', 'dangerous', 'dangerous', 'all', 'all', 'all', 'all'];
        const egressMap: DerivedSettings['egress_allowed'][] = ['none', 'none', 'whitelist', 'whitelist', 'whitelist', 'expanded', 'expanded', 'expanded', 'unrestricted', 'unrestricted'];

        // Budget mapping
        const tokenLimitMap = [1024, 2048, 3072, 4096, 5120, 6144, 8192, 10240, 12288, 16384];
        const costTierMap: DerivedSettings['cost_tier'][] = ['low', 'low', 'low', 'mid', 'mid', 'mid', 'mid', 'high', 'high', 'high'];
        const thinkingMap = [256, 512, 512, 1024, 1024, 1536, 2048, 3072, 4096, 4096];

        const idx = Math.round(k.intelligence) - 1;
        const aidx = Math.round(k.autonomy) - 1;
        const bidx = Math.round(k.budget * 10) - 1;

        return {
            temperature: tempMap[idx] ?? 0.7,
            max_tokens: tokenMap[idx] ?? 2048,
            rlm_iterations: rlmMap[idx] ?? 3,
            recall_limit: recallMap[idx] ?? 30,
            model_tier: tierMap[idx] ?? 'standard',
            brain_query_enabled: k.intelligence >= 5,
            require_hitl: hitlMap[aidx] ?? 'dangerous',
            tool_approval: approvalMap[aidx] ?? 'dangerous',
            egress_allowed: egressMap[aidx] ?? 'whitelist',
            token_limit: tokenLimitMap[bidx] ?? 4096,
            cost_tier: costTierMap[bidx] ?? 'mid',
            thinking_budget: thinkingMap[bidx] ?? 1024,
        };
    }
}

export const iqStore = new IQStore();
