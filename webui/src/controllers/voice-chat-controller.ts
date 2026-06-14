/**
 * Voice Chat Controller
 *
 * Manages WebSocket connection, audio recording, and voice session state.
 */

import { apiClient } from '../services/api-client.js';

export interface VoicePersona {
    id: string;
    name: string;
    voice_id: string;
    description: string;
    is_default: boolean;
    is_active: boolean;
}

export interface PersonaListResponse {
    items: VoicePersona[];
    total: number;
}

export interface WSMessage {
    type: string;
    session_id?: string;
    text?: string;
    data?: string;
    status?: string;
    message?: string;
    duration_seconds?: number;
    turn_count?: number;
    is_final?: boolean;
    turn?: number;
    tokens?: number;
    chunk_index?: number;
}

export interface VoiceChatControllerHost {
    requestUpdate(): void;
}

export interface VoiceChatControllerOptions {
    onTranscriptAdd: (
        role: 'user' | 'assistant',
        content: string,
        isPartial?: boolean
    ) => void;
    onTranscriptUpdate: (content: string, isPartial?: boolean) => void;
}

export class VoiceChatController {
    private _host: VoiceChatControllerHost;
    private _options: VoiceChatControllerOptions;

    private _personas: VoicePersona[] = [];
    private _selectedPersona: VoicePersona | null = null;
    private _sessionId: string | null = null;
    private _sessionStatus: 'idle' | 'active' | 'completed' = 'idle';
    private _duration = 0;
    private _turnCount = 0;
    private _isLoading = false;
    private _error = '';
    private _isRecording = false;

    private _ws: WebSocket | null = null;
    private _mediaRecorder: MediaRecorder | null = null;
    private _audioBuffer: string[] = [];
    private _currentAudio: HTMLAudioElement | null = null;
    private _durationInterval?: number;

    constructor(
        host: VoiceChatControllerHost,
        options: VoiceChatControllerOptions
    ) {
        this._host = host;
        this._options = options;
    }

    get personas(): VoicePersona[] {
        return this._personas;
    }

    get selectedPersona(): VoicePersona | null {
        return this._selectedPersona;
    }

    get sessionId(): string | null {
        return this._sessionId;
    }

    get sessionStatus(): 'idle' | 'active' | 'completed' {
        return this._sessionStatus;
    }

    get duration(): number {
        return this._duration;
    }

    get turnCount(): number {
        return this._turnCount;
    }

    get isLoading(): boolean {
        return this._isLoading;
    }

    get error(): string {
        return this._error;
    }

    get isRecording(): boolean {
        return this._isRecording;
    }

    private _update(): void {
        this._host.requestUpdate();
    }

    async loadPersonas(): Promise<void> {
        this._isLoading = true;
        this._error = '';
        this._update();

        try {
            const data = await apiClient.get<PersonaListResponse>(
                '/voice/personas?active_only=true'
            );
            this._personas = data.items || [];
            this._selectedPersona =
                this._personas.find((p) => p.is_default) ||
                this._personas[0] ||
                null;
        } catch (e) {
            console.error('Failed to load voice personas:', e);
            this._error =
                'Unable to load voice personas. Please try again later.';
        }

        this._isLoading = false;
        this._update();
    }

    selectPersona(persona: VoicePersona): void {
        this._selectedPersona = persona;
        this._update();
    }

    startSession(tenantId: string): void {
        if (!this._selectedPersona) return;

        this._error = '';
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const resolvedTenantId =
            tenantId ||
            sessionStorage.getItem('saas_tenant_id') ||
            'default';
        const wsUrl = `${protocol}//${window.location.host}/ws/voice/?tenant_id=${encodeURIComponent(resolvedTenantId)}`;

        this._ws = new WebSocket(wsUrl);

        this._ws.onopen = () => {
            this._sendWS({
                type: 'start_session',
                persona_id: this._selectedPersona!.id,
            });
        };

        this._ws.onmessage = (event) => {
            try {
                const msg: WSMessage = JSON.parse(event.data);
                this._handleWSMessage(msg);
            } catch (e) {
                console.error('Invalid WebSocket message:', e);
            }
        };

        this._ws.onerror = () => {
            this._error = 'Voice connection error. Please try again.';
            this._resetSession();
        };

        this._ws.onclose = () => {
            if (this._sessionStatus === 'active') {
                this._sessionStatus = 'completed';
                this._stopDurationTimer();
            }
            this._ws = null;
            this._update();
        };

        this._isLoading = true;
        this._update();
    }

    private _handleWSMessage(msg: WSMessage): void {
        switch (msg.type) {
            case 'connected':
                this._sessionId = msg.session_id || null;
                this._update();
                break;
            case 'session_started':
                this._sessionStatus = 'active';
                this._duration = 0;
                this._turnCount = 0;
                this._isLoading = false;
                this._startDurationTimer();
                this._update();
                break;
            case 'status':
                break;
            case 'transcription':
                if (msg.text) {
                    this._turnCount = msg.turn || this._turnCount + 1;
                    this._options.onTranscriptAdd('user', msg.text, false);
                    this._update();
                }
                break;
            case 'response_start':
                this._audioBuffer = [];
                this._options.onTranscriptAdd('assistant', '...', true);
                break;
            case 'audio_chunk':
                if (msg.data) {
                    this._audioBuffer.push(msg.data);
                }
                break;
            case 'response_end':
                if (msg.text) {
                    this._options.onTranscriptUpdate(msg.text, false);
                }
                this._playAudioBuffer();
                break;
            case 'session_ended':
                this._sessionStatus = 'completed';
                this._stopDurationTimer();
                this._closeWebSocket();
                this._update();
                break;
            case 'error':
                this._error = msg.message || 'Voice session error.';
                this._update();
                break;
        }
    }

    endSession(): void {
        this._sendWS({ type: 'end_session' });
        this._closeWebSocket();
        this._stopRecording();
        this._stopDurationTimer();
        this._sessionStatus = 'completed';
        this._update();
    }

    private _resetSession(): void {
        this._closeWebSocket();
        this._stopRecording();
        this._stopDurationTimer();
        this._sessionStatus = 'idle';
        this._sessionId = null;
        this._isLoading = false;
        this._update();
    }

    destroy(): void {
        this._closeWebSocket();
        this._stopRecording();
        this._stopDurationTimer();
    }

    private _sendWS(payload: object): void {
        if (this._ws?.readyState === WebSocket.OPEN) {
            this._ws.send(JSON.stringify(payload));
        }
    }

    private _closeWebSocket(): void {
        if (this._ws) {
            this._ws.close();
            this._ws = null;
        }
    }

    private _startDurationTimer(): void {
        this._stopDurationTimer();
        this._durationInterval = window.setInterval(() => {
            this._duration += 1;
            this._update();
        }, 1000);
    }

    private _stopDurationTimer(): void {
        if (this._durationInterval) {
            clearInterval(this._durationInterval);
            this._durationInterval = undefined;
        }
    }

    formatDuration(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    handleRecordingStart(stream: MediaStream): void {
        if (!stream || !this._ws) return;

        this._isRecording = true;
        this._error = '';
        this._update();

        try {
            const mimeType = MediaRecorder.isTypeSupported('audio/webm')
                ? 'audio/webm'
                : MediaRecorder.isTypeSupported('audio/mp4')
                  ? 'audio/mp4'
                  : '';
            this._mediaRecorder = mimeType
                ? new MediaRecorder(stream, { mimeType })
                : new MediaRecorder(stream);

            this._mediaRecorder.ondataavailable = async (event: BlobEvent) => {
                if (event.data && event.data.size > 0) {
                    const base64 = await this._blobToBase64(event.data);
                    this._sendWS({
                        type: 'audio_chunk',
                        data: base64,
                        format: this._formatFromMimeType(
                            this._mediaRecorder?.mimeType || 'webm'
                        ),
                    });
                }
            };

            this._mediaRecorder.start(250);
        } catch (err) {
            console.error('MediaRecorder error:', err);
            this._error = 'Could not start audio recording.';
            this._isRecording = false;
            this._update();
        }
    }

    handleRecordingStop(): void {
        this._stopRecording();
    }

    private _stopRecording(): void {
        this._isRecording = false;
        if (
            this._mediaRecorder &&
            this._mediaRecorder.state !== 'inactive'
        ) {
            try {
                this._mediaRecorder.stop();
            } catch {
                // ignore
            }
        }
        this._mediaRecorder = null;
        this._update();
    }

    private _blobToBase64(blob: Blob): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                const result = reader.result as string;
                const base64 = result.split(',')[1] || '';
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    private _formatFromMimeType(mimeType: string): string {
        if (mimeType.includes('mp4')) return 'mp4';
        if (mimeType.includes('webm')) return 'webm';
        if (mimeType.includes('ogg')) return 'ogg';
        if (mimeType.includes('wav')) return 'wav';
        return 'webm';
    }

    private _playAudioBuffer(): void {
        if (this._audioBuffer.length === 0) return;

        try {
            const byteCharacters = atob(this._audioBuffer.join(''));
            const byteNumbers = new Array(byteCharacters.length)
                .fill(0)
                .map((_, i) => byteCharacters.charCodeAt(i));
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'audio/mpeg' });
            const url = URL.createObjectURL(blob);

            this._currentAudio = new Audio(url);
            this._currentAudio.onended = () => {
                URL.revokeObjectURL(url);
            };
            this._currentAudio.play().catch((err) => {
                console.warn('Audio playback failed:', err);
            });
        } catch (err) {
            console.error('Failed to play audio response:', err);
        }
    }
}
