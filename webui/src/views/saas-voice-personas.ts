/**
 * Voice Personas View
 * 
 * VIBE COMPLIANT - Lit View
 * Manage voice personas for tenant.
 * Uses voice-persona-card and voice-config-panel components.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

// Import components
import '../components/voice-persona-card.js';
import '../components/voice-config-panel.js';
import '../components/saas-glass-modal.js';
import '../components/saas-sidebar.js';

interface VoicePersona {
    id: string;
    name: string;
    description: string;
    voice_id: string;
    voice_speed: number;
    stt_model: string;
    stt_language: string;
    llm_config_id: string | null;
    llm_config_name: string | null;
    llm_provider: string | null;
    system_prompt: string;
    temperature: number;
    max_tokens: number;
    turn_detection_enabled: boolean;
    turn_detection_threshold: number;
    silence_duration_ms: number;
    is_active: boolean;
    is_default: boolean;
}

@customElement('saas-voice-personas')
export class SaasVoicePersonas extends LitElement {
    static styles = css`
        :host {
            display: flex;
            min-height: 100vh;
            background: var(--saas-bg, #f8fafc);
            color: var(--saas-text, #1e293b);
        }

        .main-content {
            flex: 1;
            padding: 24px 32px;
            margin-left: 260px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--saas-text, #1e293b);
            margin: 0;
        }

        .create-btn {
            background: var(--saas-primary, #3b82f6);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }

        .create-btn:hover {
            background: var(--saas-primary-hover, #2563eb);
            transform: translateY(-1px);
        }

        .personas-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }

        .empty-state {
            grid-column: 1 / -1;
            text-align: center;
            padding: 60px;
            background: var(--saas-surface, white);
            border-radius: 12px;
            border: 2px dashed var(--saas-border, #e2e8f0);
        }

        .empty-state h3 {
            font-size: 18px;
            margin-bottom: 8px;
            color: var(--saas-text, #1e293b);
        }

        .empty-state p {
            color: var(--saas-text-dim, #64748b);
            margin-bottom: 20px;
        }

        .modal-header {
            margin-bottom: 20px;
        }

        .modal-header h2 {
            font-size: 20px;
            font-weight: 600;
            margin: 0 0 8px 0;
        }

        .modal-header p {
            color: var(--saas-text-dim, #64748b);
            font-size: 14px;
            margin: 0;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .form-group.full {
            grid-column: 1 / -1;
        }

        label {
            font-size: 13px;
            font-weight: 500;
            color: var(--saas-text-dim, #64748b);
        }

        input, textarea {
            padding: 10px 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
            border-radius: 6px;
            font-size: 14px;
            background: var(--saas-bg, #f8fafc);
            color: var(--saas-text, #1e293b);
        }

        input:focus, textarea:focus {
            outline: none;
            border-color: var(--saas-primary, #3b82f6);
        }

        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid var(--saas-border, #e2e8f0);
        }

        .btn {
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-secondary {
            background: var(--saas-surface, white);
            border: 1px solid var(--saas-border, #e2e8f0);
            color: var(--saas-text, #1e293b);
        }

        .btn-primary {
            background: var(--saas-primary, #3b82f6);
            border: 1px solid var(--saas-primary, #3b82f6);
            color: white;
        }

        .loading {
            display: flex;
            justify-content: center;
            padding: 40px;
        }
    `;

    @state() private personas: VoicePersona[] = [];
    @state() private loading = true;
    @state() private showCreateModal = false;
    @state() private showEditModal = false;
    @state() private editingPersona: VoicePersona | null = null;
    @state() private newPersona = { name: '', description: '' };

    connectedCallback() {
        super.connectedCallback();
        this._loadPersonas();
    }

    private async _loadPersonas() {
        this.loading = true;
        try {
            const response = await fetch('/api/v2/voice/personas');
            if (response.ok) {
                const data = await response.json();
                this.personas = data.items || data || [];
            }
        } catch (e) {
            console.error('Failed to load personas:', e);
            // Demo data for development
            this.personas = [
                {
                    id: '1',
                    name: 'Customer Support',
                    description: 'Friendly and helpful support agent',
                    voice_id: 'af_heart',
                    voice_speed: 1.0,
                    stt_model: 'tiny',
                    stt_language: 'en',
                    llm_config_id: '1',
                    llm_config_name: 'llama-3.3-70b',
                    llm_provider: 'groq',
                    system_prompt: 'You are a helpful customer support agent.',
                    temperature: 0.7,
                    max_tokens: 1024,
                    turn_detection_enabled: true,
                    turn_detection_threshold: 0.5,
                    silence_duration_ms: 500,
                    is_active: true,
                    is_default: true,
                },
                {
                    id: '2',
                    name: 'Sales Assistant',
                    description: 'Professional sales representative',
                    voice_id: 'af_bella',
                    voice_speed: 1.1,
                    stt_model: 'small',
                    stt_language: 'en',
                    llm_config_id: '2',
                    llm_config_name: 'claude-3-sonnet',
                    llm_provider: 'anthropic',
                    system_prompt: 'You are a professional sales assistant.',
                    temperature: 0.8,
                    max_tokens: 2048,
                    turn_detection_enabled: true,
                    turn_detection_threshold: 0.6,
                    silence_duration_ms: 600,
                    is_active: true,
                    is_default: false,
                },
            ];
        }
        this.loading = false;
    }

    render() {
        return html`
            <saas-sidebar></saas-sidebar>
            
            <div class="main-content">
                <div class="header">
                    <h1>🎙️ Voice Personas</h1>
                    <button class="create-btn" @click=${() => this.showCreateModal = true}>
                        + Create Persona
                    </button>
                </div>

                ${this.loading ? html`
                    <div class="loading">Loading...</div>
                ` : html`
                    <div class="personas-grid">
                        ${this.personas.length === 0 ? html`
                            <div class="empty-state">
                                <h3>No Voice Personas</h3>
                                <p>Create your first voice persona to get started with AgentVoice Vox.</p>
                                <button class="create-btn" @click=${() => this.showCreateModal = true}>
                                    + Create Persona
                                </button>
                            </div>
                        ` : this.personas.map(persona => html`
                            <voice-persona-card
                                .persona=${persona}
                                @persona-edit=${(e: CustomEvent) => this._handleEdit(e.detail.persona)}
                                @persona-duplicate=${(e: CustomEvent) => this._handleDuplicate(e.detail.persona)}
                                @persona-set-default=${(e: CustomEvent) => this._handleSetDefault(e.detail.persona)}
                                @persona-delete=${(e: CustomEvent) => this._handleDelete(e.detail.persona)}
                            ></voice-persona-card>
                        `)}
                    </div>
                `}
            </div>

            ${this.showCreateModal ? html`
                <saas-glass-modal 
                    size="large"
                    @close=${() => this.showCreateModal = false}
                >
                    <div class="modal-header">
                        <h2>Create Voice Persona</h2>
                        <p>Configure a new voice persona for your agents.</p>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Name</label>
                            <input type="text" placeholder="e.g. Customer Support"
                                .value=${this.newPersona.name}
                                @input=${(e: Event) => this.newPersona = { ...this.newPersona, name: (e.target as HTMLInputElement).value }}
                            />
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group full">
                            <label>Description</label>
                            <textarea placeholder="Brief description of this persona..."
                                .value=${this.newPersona.description}
                                @input=${(e: Event) => this.newPersona = { ...this.newPersona, description: (e.target as HTMLTextAreaElement).value }}
                            ></textarea>
                        </div>
                    </div>

                    <voice-config-panel></voice-config-panel>

                    <div class="modal-actions">
                        <button class="btn btn-secondary" @click=${() => this.showCreateModal = false}>Cancel</button>
                        <button class="btn btn-primary" @click=${this._handleCreate}>Create Persona</button>
                    </div>
                </saas-glass-modal>
            ` : ''}
        `;
    }

    private _handleEdit(persona: VoicePersona) {
        this.editingPersona = persona;
        this.showEditModal = true;
    }

    private _handleDuplicate(persona: VoicePersona) {
        const newPersona = { ...persona, id: '', name: `${persona.name} (Copy)`, is_default: false };
        this.editingPersona = newPersona;
        this.showCreateModal = true;
    }

    private async _handleSetDefault(persona: VoicePersona) {
        try {
            await fetch(`/api/v2/voice/personas/${persona.id}/set-default`, { method: 'POST' });
            this._loadPersonas();
        } catch (e) {
            // Update locally for demo
            this.personas = this.personas.map(p => ({ ...p, is_default: p.id === persona.id }));
        }
    }

    private async _handleDelete(persona: VoicePersona) {
        if (!confirm(`Delete "${persona.name}"?`)) return;
        try {
            await fetch(`/api/v2/voice/personas/${persona.id}`, { method: 'DELETE' });
            this._loadPersonas();
        } catch (e) {
            // Remove locally for demo
            this.personas = this.personas.filter(p => p.id !== persona.id);
        }
    }

    private async _handleCreate() {
        const configPanel = this.shadowRoot?.querySelector('voice-config-panel') as any;
        const config = configPanel?.getConfig() || {};

        const payload = {
            name: this.newPersona.name,
            description: this.newPersona.description,
            ...config,
        };

        try {
            const response = await fetch('/api/v2/voice/personas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (response.ok) {
                this.showCreateModal = false;
                this._loadPersonas();
            }
        } catch (e) {
            // Add locally for demo
            this.personas = [...this.personas, { ...payload, id: String(Date.now()), is_active: true, is_default: false } as VoicePersona];
            this.showCreateModal = false;
        }

        this.newPersona = { name: '', description: '' };
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-voice-personas': SaasVoicePersonas;
    }
}
