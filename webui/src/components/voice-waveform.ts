/**
 * Voice Waveform Component
 * 
 * VIBE COMPLIANT - Lit Component
 * Real-time audio visualization for voice sessions.
 * 
 * 7-Persona Implementation:
 * - 🏗️ Django Architect: WebSocket ready
 * - 🔒 Security Auditor: MediaStream permission handling
 * - 📈 PM: Clear visual feedback
 * - 🧪 QA Engineer: Fallback for no mic
 * - 📚 Technical Writer: Clear documentation
 * - ⚡ Performance Lead: requestAnimationFrame optimization
 * - 🌍 i18n Specialist: Accessible labels
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('voice-waveform')
export class VoiceWaveform extends LitElement {
    static styles = css`
        :host {
            display: block;
            width: 100%;
        }

        .waveform-container {
            position: relative;
            height: 80px;
            background: var(--saas-bg, #f8fafc);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--saas-border, #e2e8f0);
        }

        canvas {
            width: 100%;
            height: 100%;
        }

        .status-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--saas-text-dim, #64748b);
            font-size: 14px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }

        .status-dot.listening {
            background: #22c55e;
        }

        .status-dot.processing {
            background: #f59e0b;
        }

        .status-dot.speaking {
            background: #3b82f6;
        }

        .status-dot.idle {
            background: #94a3b8;
            animation: none;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }

        .controls {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 12px;
        }

        .control-btn {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: all 0.2s ease;
        }

        .control-btn.mic {
            background: var(--saas-primary, #3b82f6);
            color: white;
        }

        .control-btn.mic:hover {
            background: var(--saas-primary-hover, #2563eb);
            transform: scale(1.05);
        }

        .control-btn.mic.active {
            background: #ef4444;
            animation: pulse 1s infinite;
        }

        .control-btn.stop {
            background: var(--saas-surface, white);
            border: 1px solid var(--saas-border, #e2e8f0);
            color: var(--saas-text, #1e293b);
        }

        .control-btn.stop:hover {
            background: var(--saas-bg, #f8fafc);
        }
    `;

    @property({ type: String }) status: 'idle' | 'listening' | 'processing' | 'speaking' = 'idle';
    @property({ type: Boolean }) showControls = true;

    @state() private isRecording = false;
    @state() private audioContext: AudioContext | null = null;
    @state() private analyser: AnalyserNode | null = null;
    @state() private animationId: number | null = null;

    private canvas!: HTMLCanvasElement;
    private canvasCtx!: CanvasRenderingContext2D;

    firstUpdated() {
        this.canvas = this.shadowRoot!.querySelector('canvas')!;
        this.canvasCtx = this.canvas.getContext('2d')!;
        this._drawIdleWaveform();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._stopVisualization();
    }

    private _drawIdleWaveform() {
        const { width, height } = this.canvas.getBoundingClientRect();
        this.canvas.width = width * 2;
        this.canvas.height = height * 2;
        this.canvasCtx.scale(2, 2);

        this.canvasCtx.fillStyle = 'var(--saas-bg, #f8fafc)';
        this.canvasCtx.fillRect(0, 0, width, height);

        // Draw flat line
        this.canvasCtx.strokeStyle = 'var(--saas-border, #e2e8f0)';
        this.canvasCtx.lineWidth = 2;
        this.canvasCtx.beginPath();
        this.canvasCtx.moveTo(0, height / 2);
        this.canvasCtx.lineTo(width, height / 2);
        this.canvasCtx.stroke();
    }

    private _startVisualization(stream: MediaStream) {
        this.audioContext = new AudioContext();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;

        const source = this.audioContext.createMediaStreamSource(stream);
        source.connect(this.analyser);

        this._draw();
    }

    private _draw() {
        if (!this.analyser) return;

        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        this.analyser.getByteTimeDomainData(dataArray);

        const { width, height } = this.canvas.getBoundingClientRect();
        this.canvasCtx.fillStyle = 'rgba(248, 250, 252, 0.3)';
        this.canvasCtx.fillRect(0, 0, width, height);

        this.canvasCtx.lineWidth = 2;
        this.canvasCtx.strokeStyle = this.isRecording ? '#3b82f6' : '#94a3b8';
        this.canvasCtx.beginPath();

        const sliceWidth = width / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = (v * height) / 2;

            if (i === 0) {
                this.canvasCtx.moveTo(x, y);
            } else {
                this.canvasCtx.lineTo(x, y);
            }
            x += sliceWidth;
        }

        this.canvasCtx.lineTo(width, height / 2);
        this.canvasCtx.stroke();

        this.animationId = requestAnimationFrame(() => this._draw());
    }

    private _stopVisualization() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        this._drawIdleWaveform();
    }

    private async _toggleRecording() {
        if (this.isRecording) {
            this.isRecording = false;
            this.status = 'idle';
            this._stopVisualization();
            this.dispatchEvent(new CustomEvent('recording-stop'));
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.isRecording = true;
                this.status = 'listening';
                this._startVisualization(stream);
                this.dispatchEvent(new CustomEvent('recording-start', { detail: { stream } }));
            } catch (e) {
                console.error('Mic permission denied:', e);
                this.dispatchEvent(new CustomEvent('mic-error', { detail: { error: e } }));
            }
        }
    }

    render() {
        const statusLabels = {
            idle: 'Ready',
            listening: 'Listening...',
            processing: 'Processing...',
            speaking: 'Speaking...',
        };

        return html`
            <div class="waveform-container">
                <canvas></canvas>
                <div class="status-overlay">
                    <span class="status-dot ${this.status}"></span>
                    <span>${statusLabels[this.status]}</span>
                </div>
            </div>

            ${this.showControls ? html`
                <div class="controls">
                    <button 
                        class="control-btn mic ${this.isRecording ? 'active' : ''}"
                        @click=${this._toggleRecording}
                        aria-label=${this.isRecording ? 'Stop recording' : 'Start recording'}
                    >
                        ${this.isRecording ? '⏹️' : '🎙️'}
                    </button>
                </div>
            ` : ''}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'voice-waveform': VoiceWaveform;
    }
}
