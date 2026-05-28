/**
 * Composer Store — Chat composer state
 */

import { createContext } from '@lit/context';

export interface ComposerState {
    attachments: File[];
    activeSkills: string[];
    historyOpen: boolean;
    contextOpen: boolean;
    menuOpen: boolean;
}

export const composerContext = createContext<ComposerStore>('composer-store');

export class ComposerStore {
    private _state: ComposerState = {
        attachments: [],
        activeSkills: [],
        historyOpen: false,
        contextOpen: false,
        menuOpen: false,
    };

    private _listeners: Set<() => void> = new Set();

    get state(): Readonly<ComposerState> {
        return { ...this._state, attachments: [...this._state.attachments], activeSkills: [...this._state.activeSkills] };
    }

    subscribe(listener: () => void): () => void {
        this._listeners.add(listener);
        return () => this._listeners.delete(listener);
    }

    private _notify() {
        this._listeners.forEach(l => l());
    }

    addAttachment(file: File) {
        this._state.attachments.push(file);
        this._notify();
    }

    removeAttachment(index: number) {
        this._state.attachments.splice(index, 1);
        this._notify();
    }

    clearAttachments() {
        this._state.attachments = [];
        this._notify();
    }

    toggleSkill(skill: string) {
        const idx = this._state.activeSkills.indexOf(skill);
        if (idx >= 0) {
            this._state.activeSkills.splice(idx, 1);
        } else {
            this._state.activeSkills.push(skill);
        }
        this._notify();
    }

    setMenuOpen(open: boolean) {
        this._state.menuOpen = open;
        this._notify();
    }

    setHistoryOpen(open: boolean) {
        this._state.historyOpen = open;
        this._notify();
    }

    setContextOpen(open: boolean) {
        this._state.contextOpen = open;
        this._notify();
    }
}

export const composerStore = new ComposerStore();
