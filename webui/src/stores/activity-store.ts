/**
 * Activity Store — Sidebar activity feed
 */

import { createContext } from '@lit/context';

export interface ActivityEvent {
    id: string;
    type: 'message' | 'tool' | 'memory' | 'sleep' | 'error' | 'warning';
    agentId: string;
    agentName: string;
    description: string;
    timestamp: string;
    metadata?: Record<string, unknown>;
}

export interface ActivityState {
    events: ActivityEvent[];
    unreadCount: number;
}

export const activityContext = createContext<ActivityStore>('activity-store');

export class ActivityStore {
    private _state: ActivityState = {
        events: [
            {
                id: '1',
                type: 'tool',
                agentId: 'dev-1',
                agentName: 'Dev-1',
                description: 'Executed tool: git_commit',
                timestamp: new Date(Date.now() - 120000).toISOString(),
            },
            {
                id: '2',
                type: 'memory',
                agentId: 'dev-1',
                agentName: 'Dev-1',
                description: '3 memories consolidated during sleep cycle',
                timestamp: new Date(Date.now() - 3600000).toISOString(),
            },
            {
                id: '3',
                type: 'message',
                agentId: 'support-ai',
                agentName: 'Support-AI',
                description: 'Confidence: 94% on last response',
                timestamp: new Date(Date.now() - 600000).toISOString(),
            },
        ],
        unreadCount: 0,
    };

    private _listeners: Set<() => void> = new Set();

    get state(): Readonly<ActivityState> {
        return { ...this._state, events: [...this._state.events] };
    }

    subscribe(listener: () => void): () => void {
        this._listeners.add(listener);
        return () => this._listeners.delete(listener);
    }

    private _notify() {
        this._listeners.forEach(l => l());
    }

    addEvent(event: Omit<ActivityEvent, 'id' | 'timestamp'>) {
        const newEvent: ActivityEvent = {
            ...event,
            id: Math.random().toString(36).slice(2),
            timestamp: new Date().toISOString(),
        };
        this._state.events.unshift(newEvent);
        if (this._state.events.length > 50) {
            this._state.events.pop();
        }
        this._state.unreadCount++;
        this._notify();
    }

    markRead() {
        this._state.unreadCount = 0;
        this._notify();
    }
}

export const activityStore = new ActivityStore();
