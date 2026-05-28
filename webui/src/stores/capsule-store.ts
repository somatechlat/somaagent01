/**
 * Capsule Store — Capsule editing state
 */

import { createContext } from '@lit/context';

export interface CapsuleState {
    activeCapsuleId: string | null;
    editMode: 'view' | 'edit' | 'create';
    certificationStatus: 'draft' | 'certified' | 'archived' | 'pending';
    unsavedChanges: boolean;
}

export const capsuleContext = createContext<CapsuleStore>('capsule-store');

export class CapsuleStore {
    private _state: CapsuleState = {
        activeCapsuleId: null,
        editMode: 'view',
        certificationStatus: 'draft',
        unsavedChanges: false,
    };

    private _listeners: Set<() => void> = new Set();

    get state(): Readonly<CapsuleState> {
        return { ...this._state };
    }

    subscribe(listener: () => void): () => void {
        this._listeners.add(listener);
        return () => this._listeners.delete(listener);
    }

    private _notify() {
        this._listeners.forEach(l => l());
    }

    setActiveCapsule(id: string | null) {
        this._state.activeCapsuleId = id;
        this._state.unsavedChanges = false;
        this._notify();
    }

    setEditMode(mode: CapsuleState['editMode']) {
        this._state.editMode = mode;
        this._notify();
    }

    setCertificationStatus(status: CapsuleState['certificationStatus']) {
        this._state.certificationStatus = status;
        this._notify();
    }

    markUnsaved() {
        this._state.unsavedChanges = true;
        this._notify();
    }
}

export const capsuleStore = new CapsuleStore();
