/**
 * SomaAgent01 — Chat Composer (C3 rebuild)
 *
 * Auto-expanding textarea, "+" menu (composerStore attachments), mic → real
 * STT via POST /api/v2/voice/transcribe, send, queue-while-busy,
 * export / clear menu.
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state, query } from 'lit/decorators.js';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import { composerStore } from '../stores/composer-store.js';
import { apiClient } from '../services/api-client.js';
import { formatBytes } from '../utils/markdown.js';
import { attachmentIcon } from '../utils/file-icons.js';
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
    @state() private _previews = new Map<string, string>();
    @state() private _dragging = false;
    @state() private _queue: ComposerSendDetail[] = [];
    @state() private _micState: MicState = 'idle';
    @state() private _micError = '';

    @query('textarea') private _textarea!: HTMLTextAreaElement;

    private _mediaRecorder: MediaRecorder | null = null;
    private _micStream: MediaStream | null = null;
    private _audioChunks: Blob[] = [];
    private _micMime = 'audio/webm';

    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: block;
            padding: var(--skin-space-md) var(--skin-space-lg) var(--skin-space-md);
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: var(--skin-text-xl);
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
            max-width: 48rem;
            margin: 0 auto;
        }

        .input-row {
            display: flex;
            align-items: flex-end;
            gap: var(--skin-space-sm);
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            border-radius: var(--skin-radius-xl);
            padding: var(--skin-space-sm) var(--skin-space-md);
            transition:
                border-color var(--skin-motion-normal) var(--skin-motion-ease),
                box-shadow var(--skin-motion-normal) var(--skin-motion-ease);
        }

        .input-row:focus-within {
            border-color: var(--skin-color-border-strong);
            box-shadow: 0 0 0 var(--skin-focus-ring-width) color-mix(in srgb, var(--skin-focus-ring) 18%, transparent);
        }

        .icon-btn {
            width: var(--skin-space-xl);
            height: var(--skin-space-xl);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--skin-radius-full);
            background: transparent;
            border: none;
            color: var(--skin-color-text-muted);
            cursor: pointer;
            flex-shrink: 0;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .icon-btn .material-symbols-outlined {
            font-size: var(--skin-text-xl);
        }

        .icon-btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-secondary);
        }

        .icon-btn:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .icon-btn.active {
            background: var(--skin-color-bg-active);
            color: var(--skin-color-accent);
            transform: rotate(45deg);
        }

        textarea {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--skin-color-text-primary);
            font-size: var(--skin-text-base);
            line-height: var(--skin-leading-normal);
            resize: none;
            outline: none;
            min-height: var(--skin-space-lg);
            max-height: 10.5rem;
            padding: var(--skin-space-xs) 2px;
            font-family: inherit;
        }

        textarea::placeholder {
            color: var(--skin-color-text-muted);
        }

        .mic-btn.recording {
            background: var(--skin-color-danger);
            color: var(--skin-color-text-inverse);
            animation: micPulse 1.2s ease-in-out infinite;
        }

        .mic-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        @keyframes micPulse {
            0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--skin-color-danger) 45%, transparent); }
            50% { box-shadow: 0 0 0 var(--skin-space-sm) color-mix(in srgb, var(--skin-color-danger) 0%, transparent); }
        }

        .send-btn {
            width: var(--skin-space-xl);
            height: var(--skin-space-xl);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-accent);
            border: none;
            color: var(--skin-color-accent-text);
            cursor: pointer;
            flex-shrink: 0;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .send-btn .material-symbols-outlined {
            font-size: var(--skin-text-lg);
        }

        .send-btn:hover:not(:disabled) {
            background: var(--skin-color-accent-hover);
            transform: scale(1.05);
        }

        .send-btn:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .send-btn:disabled {
            opacity: 0.45;
            cursor: not-allowed;
            transform: none;
        }

        @media (prefers-reduced-motion: reduce) {
            .mic-btn.recording {
                animation: none;
            }
            .send-btn:hover:not(:disabled) {
                transform: none;
            }
            .icon-btn,
            .send-btn,
            .input-row {
                transition: none;
            }
        }

        .status-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--skin-space-sm);
            margin-top: var(--skin-space-sm);
            min-height: var(--skin-space-lg);
            flex-wrap: wrap;
        }

        .queue-chip {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-bg-hover);
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
        }

        .queue-chip .material-symbols-outlined {
            font-size: var(--skin-text-xs);
        }

        .queue-chip button {
            border: none;
            background: transparent;
            color: var(--skin-color-text-muted);
            cursor: pointer;
            font-size: var(--skin-text-xs);
            padding: 0 2px;
            display: inline-flex;
            align-items: center;
        }

        .queue-chip button:hover {
            color: var(--skin-color-danger);
        }

        .queue-chip button:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .mic-hint {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-muted);
        }

        .mic-hint.error {
            color: var(--skin-color-danger);
        }

        .attachments {
            display: flex;
            gap: var(--skin-space-xs);
            margin-bottom: var(--skin-space-sm);
            flex-wrap: wrap;
        }

        .attachment-chip {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            background: var(--skin-color-bg-hover);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            max-width: 17.5rem;
        }

        .attachment-chip .file-icon {
            width: var(--skin-space-xl);
            height: var(--skin-space-xl);
            border-radius: var(--skin-radius-md);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--skin-color-bg-active);
            color: var(--skin-color-text-primary);
            flex-shrink: 0;
        }

        .attachment-chip .file-icon .material-symbols-outlined {
            font-size: var(--skin-text-lg);
        }

        .dropzone {
            border: var(--skin-border-width) dashed transparent;
            border-radius: var(--skin-radius-lg);
            transition:
                border-color var(--skin-motion-fast) var(--skin-motion-ease),
                background var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .dropzone.dragging {
            border-color: var(--skin-color-accent);
            background: color-mix(in srgb, var(--skin-color-accent) 8%, transparent);
        }

        .attachment-chip .material-symbols-outlined {
            font-size: var(--skin-text-sm);
            flex-shrink: 0;
        }

        .attachment-chip .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .attachment-chip .size {
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-xs);
            flex-shrink: 0;
        }

        .attachment-chip .remove {
            cursor: pointer;
            color: var(--skin-color-text-muted);
            transition: color var(--skin-motion-fast) var(--skin-motion-ease);
            display: inline-flex;
            align-items: center;
            background: transparent;
            border: none;
            padding: 0;
        }

        .attachment-chip .remove:hover {
            color: var(--skin-color-danger);
        }

        .attachment-chip .remove:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .attachment-chip .remove .material-symbols-outlined {
            font-size: var(--skin-text-sm);
        }

        .hint {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            margin-top: var(--skin-space-xs);
            text-align: center;
        }

        .hint kbd {
            font-family: inherit;
            padding: 1px var(--skin-space-xs);
            border-radius: var(--skin-radius-sm);
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            background: var(--skin-color-bg-hover);
            font-size: var(--skin-text-xs);
        }
    `,
    ];

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
            <div
                class="composer dropzone ${this._dragging ? 'dragging' : ''}"
                @dragover=${(e: DragEvent) => {
                    e.preventDefault();
                    if (!this._dragging) this._dragging = true;
                }}
                @dragleave=${(e: DragEvent) => {
                    if (e.currentTarget === e.target) this._dragging = false;
                }}
                @drop=${(e: DragEvent) => {
                    e.preventDefault();
                    this._dragging = false;
                    const files = e.dataTransfer?.files;
                    if (files && files.length > 0) {
                        Array.from(files).forEach((f) => composerStore.addAttachment(f));
                    }
                }}
            >
                ${this._attachments.length > 0 ? html`
                    <div class="attachments" role="list" aria-label="Attached files">
                        ${this._attachments.map((file, i) => html`
                            <div class="attachment-chip" role="listitem">
                                <span class="file-icon" aria-hidden="true">
                                    <span class="material-symbols-outlined">${attachmentIcon(file.name, file.type)}</span>
                                </span>
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
                        class="icon-btn"
                        data-testid="composer-files"
                        @click=${() => {
                            this.dispatchEvent(new CustomEvent('soma-open-files', {
                                bubbles: true,
                                composed: true,
                            }));
                        }}
                        title="Files"
                        aria-label="Open files"
                    >
                        <span class="material-symbols-outlined">folder_open</span>
                    </button>
                    <button
                        class="icon-btn ${this._menuOpen ? 'active' : ''}"
                        @click=${this._toggleMenu}
                        title="Upload files"
                        aria-label="Upload files"
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

                ${this._menuOpen
                    ? html`<soma-composer-menu
                          @soma-menu-close=${() => {
                              this._menuOpen = false;
                              composerStore.setMenuOpen(false);
                          }}
                      ></soma-composer-menu>`
                    : ''}

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
                                <span class="material-symbols-outlined">close</span>
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
