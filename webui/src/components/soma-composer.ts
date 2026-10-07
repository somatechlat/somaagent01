/**
 * SomaAgent01 — Chat Composer (C3 rebuild)
 *
 * Auto-expanding textarea, "+" menu (composerStore attachments), mic → real
 * STT via POST /api/v2/voice/transcribe, send, queue-while-busy,
 * export / clear menu.
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state, query } from 'lit/decorators.js';
import { composerStore } from '../stores/composer-store.js';
import { apiClient } from '../services/api-client.js';
import { formatBytes } from '../utils/markdown.js';
import './soma-composer-menu.js';

export interface ComposerSendDetail {
    text: string;
    attachments: File[];
}

type MicState = 'idle' | 'recording' | 'transcribing';

@customElement('soma-composer')
export class SomaComposer extends LitElement {
    /** Host sets this while an assistant turn is streaming. */
    @property({ type: Boolean }) busy = false;
    @property({ type: String }) placeholder = 'Describe what you want the agent to do...';

    @state() private _input = '';
    @state() private _menuOpen = false;
    @state() private _attachments: File[] = [];
    @state() private _queue: ComposerSendDetail[] = [];
    @state() private _micState: MicState = 'idle';
    @state() private _micError = '';

    @query('textarea') private _textarea!: HTMLTextAreaElement;

    private _mediaRecorder: MediaRecorder | null = null;
    private _micStream: MediaStream | null = null;
    private _audioChunks: Blob[] = [];
    private _micMime = 'audio/webm';

    static styles = css`
        :host {
            display: block;
            padding: 12px 20px 16px;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        .composer {
            max-width: 760px;
            margin: 0 auto;
        }

        .input-row {
            display: flex;
            align-items: flex-end;
            gap: 8px;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-xl, 16px);
            padding: 10px 12px;
            transition: border-color 200ms ease, box-shadow 200ms ease;
        }

        .input-row:focus-within {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.14));
            box-shadow: 0 0 0 3px rgba(232, 228, 220, 0.1);
        }

        .icon-btn {
            width: 34px;
            height: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: var(--aaas-text-muted, #999999);
            cursor: pointer;
            flex-shrink: 0;
            transition: all 150ms ease;
        }

        .icon-btn .material-symbols-outlined {
            font-size: 20px;
        }

        .icon-btn:hover:not(:disabled) {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .icon-btn:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: 2px;
        }

        .icon-btn.active {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-accent, #e8e4dc);
            transform: rotate(45deg);
        }

        textarea {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--aaas-text-primary, #ffffff);
            font-size: 14px;
            line-height: 1.5;
            resize: none;
            outline: none;
            min-height: 24px;
            max-height: 168px;
            padding: 5px 2px;
            font-family: inherit;
        }

        textarea::placeholder {
            color: var(--aaas-text-muted, #999999);
        }

        .mic-btn.recording {
            background: var(--aaas-danger, #ef4444);
            color: #fff;
            animation: micPulse 1.2s ease-in-out infinite;
        }

        .mic-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        @keyframes micPulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.45); }
            50% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
        }

        .send-btn {
            width: 34px;
            height: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: var(--aaas-accent, #e8e4dc);
            border: none;
            color: var(--aaas-bg-void, #f5f5f5);
            cursor: pointer;
            flex-shrink: 0;
            transition: all 150ms ease;
        }

        .send-btn .material-symbols-outlined {
            font-size: 18px;
        }

        .send-btn:hover:not(:disabled) {
            background: var(--aaas-accent-hover, #ffffff);
            transform: scale(1.05);
        }

        .send-btn:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: 2px;
        }

        .send-btn:disabled {
            opacity: 0.45;
            cursor: not-allowed;
            transform: none;
        }

        .status-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 8px;
            min-height: 24px;
            flex-wrap: wrap;
        }

        .queue-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: var(--aaas-radius-full, 9999px);
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .queue-chip .material-symbols-outlined {
            font-size: 13px;
        }

        .queue-chip button {
            border: none;
            background: transparent;
            color: var(--aaas-text-muted, #999999);
            cursor: pointer;
            font-size: 11px;
            padding: 0 2px;
            display: inline-flex;
            align-items: center;
        }

        .queue-chip button:hover {
            color: var(--aaas-danger, #ef4444);
        }

        .queue-chip button:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: 1px;
        }

        .mic-hint {
            font-size: 12px;
            color: var(--aaas-text-muted, #999999);
        }

        .mic-hint.error {
            color: var(--aaas-danger, #ef4444);
        }

        .attachments {
            display: flex;
            gap: 6px;
            margin-bottom: 8px;
            flex-wrap: wrap;
        }

        .attachment-chip {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-md, 8px);
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1a1);
            max-width: 240px;
        }

        .attachment-chip .material-symbols-outlined {
            font-size: 14px;
            flex-shrink: 0;
        }

        .attachment-chip .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .attachment-chip .size {
            color: var(--aaas-text-muted, #999999);
            font-size: 11px;
            flex-shrink: 0;
        }

        .attachment-chip .remove {
            cursor: pointer;
            color: var(--aaas-text-muted, #999999);
            transition: color 150ms ease;
            display: inline-flex;
            align-items: center;
            background: transparent;
            border: none;
            padding: 0;
        }

        .attachment-chip .remove:hover {
            color: var(--aaas-danger, #ef4444);
        }

        .attachment-chip .remove:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: 1px;
        }

        .attachment-chip .remove .material-symbols-outlined {
            font-size: 14px;
        }

        .hint {
            font-size: 11px;
            color: var(--aaas-text-muted, #999999);
            margin-top: 6px;
            text-align: center;
        }

        .hint kbd {
            font-family: inherit;
            padding: 1px 5px;
            border-radius: 3px;
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-bg-hover, #141414);
            font-size: 10px;
        }
    `;

    private _unsubscribe?: () => void;

    /** MediaRecorder + getUserMedia available → mic can call the real STT API. */
    private get _micAvailable(): boolean {
        return (
            typeof MediaRecorder !== 'undefined' &&
            !!navigator.mediaDevices &&
            typeof navigator.mediaDevices.getUserMedia === 'function'
        );
    }

    connectedCallback() {
        super.connectedCallback();
        this._attachments = composerStore.state.attachments;
        this._unsubscribe = composerStore.subscribe(() => {
            this._attachments = composerStore.state.attachments;
        });
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._unsubscribe?.();
        this._stopMicStream();
    }

    protected updated(changed: PropertyValues) {
        // Queue-while-busy: drain one item per idle transition so the host can
        // flip `busy` back on before the next dispatch.
        if (changed.has('busy') && !this.busy && this._queue.length > 0) {
            const next = this._queue[0];
            this._queue = this._queue.slice(1);
            this._dispatchSend(next);
        }
    }

    private _onInput() {
        this._input = this._textarea.value;
        this._adjustHeight();
    }

    private _adjustHeight() {
        if (!this._textarea) return;
        this._textarea.style.height = 'auto';
        this._textarea.style.height = Math.min(this._textarea.scrollHeight, 168) + 'px';
    }

    private _onKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            this._send();
        }
    }

    private _dispatchSend(item: ComposerSendDetail) {
        this.dispatchEvent(new CustomEvent<ComposerSendDetail>('send-message', {
            detail: item,
            bubbles: true,
            composed: true,
        }));
    }

    private _send() {
        const text = this._input.trim();
        const attachments = [...this._attachments];
        if (!text && attachments.length === 0) return;

        const item: ComposerSendDetail = { text, attachments };

        if (this.busy) {
            this._queue = [...this._queue, item];
            this._clearInput();
            return;
        }

        this._dispatchSend(item);
        this._clearInput();
    }

    private _clearInput() {
        this._input = '';
        if (this._textarea) {
            this._textarea.value = '';
            this._adjustHeight();
        }
        composerStore.clearAttachments();
    }

    private _clearQueue() {
        this._queue = [];
    }

    private _toggleMenu() {
        this._menuOpen = !this._menuOpen;
        composerStore.setMenuOpen(this._menuOpen);
    }

    // ==========================================================================
    // MIC → STT (POST /api/v2/voice/transcribe)
    // ==========================================================================

    private async _toggleMic() {
        if (!this._micAvailable) return;
        if (this._micState === 'recording') {
            this._mediaRecorder?.stop();
            return;
        }
        if (this._micState === 'transcribing') return;
        await this._startRecording();
    }

    private async _startRecording() {
        this._micError = '';
        try {
            this._micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mime = MediaRecorder.isTypeSupported('audio/webm')
                ? 'audio/webm'
                : MediaRecorder.isTypeSupported('audio/mp4')
                    ? 'audio/mp4'
                    : 'audio/ogg';
            this._micMime = mime;
            this._audioChunks = [];
            const recorder = new MediaRecorder(this._micStream, { mimeType: mime });
            recorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) this._audioChunks.push(e.data);
            };
            recorder.onstop = () => {
                void this._finishRecording(mime);
            };
            recorder.onerror = () => {
                this._micState = 'idle';
                this._micError = 'Microphone recording failed';
                this._stopMicStream();
            };
            recorder.start();
            this._mediaRecorder = recorder;
            this._micState = 'recording';
        } catch (err) {
            this._micState = 'idle';
            this._micError = 'Microphone permission denied or unavailable';
            console.warn('[SomaComposer] mic start failed', err);
        }
    }

    private _stopMicStream() {
        this._micStream?.getTracks().forEach((t) => t.stop());
        this._micStream = null;
        this._mediaRecorder = null;
    }

    private async _finishRecording(mime: string) {
        this._micState = 'transcribing';
        this._stopMicStream();

        const blob = new Blob(this._audioChunks, { type: mime });
        this._audioChunks = [];
        if (blob.size === 0) {
            this._micState = 'idle';
            this._micError = 'No audio captured';
            return;
        }

        try {
            const audioBase64 = await this._blobToBase64(blob);
            const format = mime.includes('webm') ? 'webm' : mime.includes('mp4') ? 'm4a' : 'ogg';
            const result = await apiClient.post<{ text: string }>('/voice/transcribe', {
                audio_base64: audioBase64,
                format,
                language: null,
            });
            const transcript = (result?.text ?? '').trim();
            if (transcript) {
                this._input = this._input ? `${this._input} ${transcript}` : transcript;
                await this.updateComplete;
                if (this._textarea) {
                    this._textarea.value = this._input;
                    this._adjustHeight();
                }
            }
            this._micError = '';
        } catch (err) {
            console.warn('[SomaComposer] STT failed', err);
            this._micError = 'Transcription failed — check voice settings';
        } finally {
            this._micState = 'idle';
        }
    }

    private _blobToBase64(blob: Blob): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const dataUrl = String(reader.result ?? '');
                const comma = dataUrl.indexOf(',');
                resolve(comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl);
            };
            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(blob);
        });
    }

    render() {
        const micDisabled = !this._micAvailable || this._micState === 'transcribing';
        const micTitle = !this._micAvailable
            ? 'Voice input unavailable — MediaRecorder/getUserMedia not supported in this browser'
            : this._micState === 'recording'
                ? 'Stop recording and transcribe'
                : this._micState === 'transcribing'
                    ? 'Transcribing…'
                    : 'Start voice input (speech-to-text)';

        return html`
            <div class="composer">
                ${this._attachments.length > 0 ? html`
                    <div class="attachments" role="list" aria-label="Attached files">
                        ${this._attachments.map((file, i) => html`
                            <div class="attachment-chip" role="listitem">
                                <span class="material-symbols-outlined">attach_file</span>
                                <span class="name" title=${file.name}>${file.name}</span>
                                <span class="size">${formatBytes(file.size)}</span>
                                <button
                                    class="remove"
                                    type="button"
                                    aria-label=${`Remove ${file.name}`}
                                    @click=${() => composerStore.removeAttachment(i)}
                                >
                                    <span class="material-symbols-outlined">close</span>
                                </button>
                            </div>
                        `)}
                    </div>
                ` : ''}

                <div class="input-row">
                    <button
                        class="icon-btn ${this._menuOpen ? 'active' : ''}"
                        @click=${this._toggleMenu}
                        title="Menu — attach, export, clear"
                        aria-label="Composer menu"
                        aria-expanded=${this._menuOpen ? 'true' : 'false'}
                    >
                        <span class="material-symbols-outlined">add</span>
                    </button>
                    <textarea
                        placeholder=${this.placeholder}
                        .value=${this._input}
                        @input=${this._onInput}
                        @keydown=${this._onKeydown}
                        rows="1"
                        aria-label="Message"
                    ></textarea>
                    <button
                        class="icon-btn mic-btn ${this._micState === 'recording' ? 'recording' : ''}"
                        @click=${this._toggleMic}
                        ?disabled=${micDisabled}
                        title=${micTitle}
                        aria-label=${micTitle}
                    >
                        <span class="material-symbols-outlined">
                            ${this._micState === 'transcribing'
                                ? 'hourglass_top'
                                : this._micState === 'recording'
                                    ? 'mic'
                                    : 'mic_none'}
                        </span>
                    </button>
                    <button
                        class="send-btn"
                        @click=${this._send}
                        ?disabled=${!this._input.trim() && this._attachments.length === 0}
                        title=${this.busy ? 'Send (queued while the agent is running)' : 'Send message'}
                        aria-label="Send message"
                    >
                        <span class="material-symbols-outlined">arrow_upward</span>
                    </button>
                </div>

                ${this._menuOpen ? html`<soma-composer-menu></soma-composer-menu>` : ''}

                <div class="status-row">
                    ${this._queue.length > 0 ? html`
                        <span class="queue-chip" role="status">
                            <span class="material-symbols-outlined">schedule</span>
                            ${this._queue.length} queued
                            <button
                                type="button"
                                @click=${this._clearQueue}
                                title="Drop queued messages"
                                aria-label="Drop queued messages"
                            >
                                <span class="material-symbols-outlined" style="font-size:13px">close</span>
                            </button>
                        </span>
                    ` : nothing}
                    ${this._micState === 'recording' ? html`
                        <span class="mic-hint">Recording… click the mic to stop and transcribe</span>
                    ` : nothing}
                    ${this._micState === 'transcribing' ? html`
                        <span class="mic-hint">Transcribing audio…</span>
                    ` : nothing}
                    ${this._micError ? html`
                        <span class="mic-hint error" role="alert">${this._micError}</span>
                    ` : nothing}
                    ${this._queue.length === 0 && this._micState === 'idle' && !this._micError ? html`
                        <div class="hint">
                            <kbd>Enter</kbd> send · <kbd>Shift</kbd>+<kbd>Enter</kbd> newline
                        </div>
                    ` : nothing}
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-composer': SomaComposer;
    }
}
