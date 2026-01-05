/**
 * SaaS Admin Voice Store
 * Per SaaS Admin UIX Design Section 5.1
 *
 * VIBE COMPLIANT:
 * - Real Lit Context implementation
 * - State machine for voice states
 * - Provider abstraction
 */

import { createContext } from '@lit/context';
import { LitElement, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { provide } from '@lit/context';

/**
 * Voice provider types.
 */
export type VoiceProvider = 'local' | 'agentvoicebox' | 'none';

/**
 * Voice state machine states.
 */
export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

/**
 * Voice configuration.
 */
export interface VoiceConfig {
    provider: VoiceProvider;
    language: string;
    sttModel: string;
    ttsVoice: string;
    ttsSpeed: number;
    vadEnabled: boolean;
    vadThreshold: number;
    agentVoiceBoxUrl?: string;
    agentVoiceBoxToken?: string;
}

/**
 * Voice state data.
 */
export interface VoiceStateData {
    state: VoiceState;
    provider: VoiceProvider;
    config: VoiceConfig;
    transcript: string;
    interimTranscript: string;
    audioLevel: number;
    isMuted: boolean;
    error: string | null;
    sessionId: string | null;
}

// Default configuration
const DEFAULT_CONFIG: VoiceConfig = {
    provider: 'local',
    language: 'en-US',
    sttModel: 'whisper-base',
    ttsVoice: 'am_onyx',
    ttsSpeed: 1.0,
    vadEnabled: true,
    vadThreshold: 0.5,
};

// Initial state
const INITIAL_STATE: VoiceStateData = {
    state: 'idle',
    provider: 'local',
    config: DEFAULT_CONFIG,
    transcript: '',
    interimTranscript: '',
    audioLevel: 0,
    isMuted: false,
    error: null,
    sessionId: null,
};

export const voiceContext = createContext<VoiceStateData>('voice-state');

@customElement('saas-voice-provider')
export class SaasVoiceProvider extends LitElement {
    @provide({ context: voiceContext })
    @property({ attribute: false })
    state: VoiceStateData = { ...INITIAL_STATE };

    private _mediaStream: MediaStream | null = null;
    private _audioContext: AudioContext | null = null;
    private _analyser: AnalyserNode | null = null;
    private _animationFrame: number | null = null;

    /**
     * Initialize voice with selected provider.
     */
    async initialize(provider: VoiceProvider): Promise<boolean> {
        try {
            this.state = {
                ...this.state,
                provider,
                config: { ...this.state.config, provider },
                error: null,
            };

            if (provider === 'none') {
                return true;
            }

            // Request microphone permission
            this._mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });

            // Set up audio analysis
            this._audioContext = new AudioContext();
            this._analyser = this._audioContext.createAnalyser();
            this._analyser.fftSize = 256;

            const source = this._audioContext.createMediaStreamSource(this._mediaStream);
            source.connect(this._analyser);

            this._startAudioLevelMonitor();

            return true;
        } catch (error) {
            this.state = {
                ...this.state,
                state: 'error',
                error: `Failed to initialize voice: ${error}`,
            };
            return false;
        }
    }

    /**
     * Start listening for voice input.
     */
    async startListening(): Promise<void> {
        if (this.state.state !== 'idle') {
            return;
        }

        this.state = {
            ...this.state,
            state: 'listening',
            transcript: '',
            interimTranscript: '',
        };

        this.dispatchEvent(new CustomEvent('voice-start', {
            bubbles: true,
            composed: true,
        }));
    }

    /**
     * Stop listening and process input.
     */
    async stopListening(): Promise<void> {
        if (this.state.state !== 'listening') {
            return;
        }

        this.state = { ...this.state, state: 'processing' };

        // In a real implementation, this would send audio to STT
        // For now, simulate processing
        this.dispatchEvent(new CustomEvent('voice-stop', {
            bubbles: true,
            composed: true,
            detail: { transcript: this.state.transcript },
        }));
    }

    /**
     * Speak text using TTS.
     */
    async speak(text: string): Promise<void> {
        if (this.state.state === 'speaking') {
            return;
        }

        this.state = { ...this.state, state: 'speaking' };

        // Use Web Speech API as fallback for local provider
        if (this.state.provider === 'local' && 'speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = this.state.config.ttsSpeed;
            utterance.lang = this.state.config.language;

            utterance.onend = () => {
                this.state = { ...this.state, state: 'idle' };
                this.dispatchEvent(new CustomEvent('voice-speak-end', {
                    bubbles: true,
                    composed: true,
                }));
            };

            speechSynthesis.speak(utterance);
        } else {
            // AgentVoiceBox provider would stream audio
            this.state = { ...this.state, state: 'idle' };
        }
    }

    /**
     * Cancel current operation.
     */
    cancel(): void {
        if (this.state.state === 'speaking') {
            speechSynthesis.cancel();
        }

        this.state = {
            ...this.state,
            state: 'idle',
            interimTranscript: '',
        };
    }

    /**
     * Toggle mute state.
     */
    toggleMute(): void {
        this.state = {
            ...this.state,
            isMuted: !this.state.isMuted,
        };

        if (this._mediaStream) {
            this._mediaStream.getAudioTracks().forEach(track => {
                track.enabled = !this.state.isMuted;
            });
        }
    }

    /**
     * Update configuration.
     */
    updateConfig(config: Partial<VoiceConfig>): void {
        this.state = {
            ...this.state,
            config: { ...this.state.config, ...config },
        };
    }

    /**
     * Update transcript from external source.
     */
    updateTranscript(text: string, isFinal: boolean): void {
        if (isFinal) {
            this.state = {
                ...this.state,
                transcript: this.state.transcript + text,
                interimTranscript: '',
            };
        } else {
            this.state = {
                ...this.state,
                interimTranscript: text,
            };
        }
    }

    /**
     * Clean up resources.
     */
    async cleanup(): Promise<void> {
        if (this._animationFrame) {
            cancelAnimationFrame(this._animationFrame);
        }

        if (this._mediaStream) {
            this._mediaStream.getTracks().forEach(track => track.stop());
        }

        if (this._audioContext) {
            await this._audioContext.close();
        }

        this.state = { ...INITIAL_STATE };
    }

    private _startAudioLevelMonitor(): void {
        if (!this._analyser) return;

        const dataArray = new Uint8Array(this._analyser.frequencyBinCount);

        const update = () => {
            if (!this._analyser) return;

            this._analyser.getByteFrequencyData(dataArray);
            const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
            const normalized = average / 255;

            this.state = {
                ...this.state,
                audioLevel: normalized,
            };

            this._animationFrame = requestAnimationFrame(update);
        };

        update();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.cleanup();
    }

    render() {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-voice-provider': SaasVoiceProvider;
    }
}
