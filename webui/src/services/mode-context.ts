/**
 * Mode Context Service
 * Manages the "Eye of God" operation modes (Section 3.1)
 */
import { createContext } from '@lit-labs/context';

export const MODES = ['STD', 'TRN', 'ADM', 'DEV', 'RO', 'DGR'] as const;
export type Mode = typeof MODES[number];

export interface ModeState {
    current: Mode;
    previous?: Mode;
    reason?: string;
    timestamp: number;
}

export const modeContext = createContext<ModeState>('soma-mode');
