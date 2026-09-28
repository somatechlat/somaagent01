/**
 * Brain Store — SomaBrain cognitive state
 */

import { createContext } from '@lit/context';

export interface NeuromodulatorState {
    dopamine: number;
    serotonin: number;
    noradrenaline: number;
    acetylcholine: number;
}

export interface BrainState {
    connected: boolean;
    neuromodulators: NeuromodulatorState;
    adaptation: number; // 0-100
    memoryUsage: number; // vector count
    sleepStatus: 'active' | 'light' | 'deep' | 'freeze';
    lastConsolidation: string | null;
    nextScheduled: string | null;
    cognitiveLoad: 'low' | 'medium' | 'high';
}

export const brainContext = createContext<BrainStore>('brain-store');

export class BrainStore {
    private _state: BrainState = {
        connected: false,
        neuromodulators: {
            dopamine: 0,
            serotonin: 0,
            noradrenaline: 0,
            acetylcholine: 0,
        },
        adaptation: 0,
        memoryUsage: 0,
        sleepStatus: 'active',
        lastConsolidation: null,
        nextScheduled: null,
        cognitiveLoad: 'low',
    };

    private _listeners: Set<() => void> = new Set();

    get state(): Readonly<BrainState> {
        return { ...this._state, neuromodulators: { ...this._state.neuromodulators } };
    }

    subscribe(listener: () => void): () => void {
        this._listeners.add(listener);
        return () => this._listeners.delete(listener);
    }

    private _notify() {
        this._listeners.forEach(l => l());
    }

    setNeuromodulators(n: Partial<NeuromodulatorState>) {
        this._state.neuromodulators = { ...this._state.neuromodulators, ...n };
        this._notify();
    }

    setSleepStatus(status: BrainState['sleepStatus']) {
        this._state.sleepStatus = status;
        this._notify();
    }

    setCognitiveLoad(load: BrainState['cognitiveLoad']) {
        this._state.cognitiveLoad = load;
        this._notify();
    }

    setConnected(connected: boolean) {
        this._state.connected = connected;
        this._notify();
    }
}

export const brainStore = new BrainStore();
