/**
 * Voice Personas View
 *
 * VIBE COMPLIANT - Lit View
 * Manage voice personas for tenant using real voice API endpoints.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

// Import components
import '../components/voice-persona-card.js';
import '../components/voice-config-panel.js';
import '../components/saas-glass-modal.js';
import '../components/saas-sidebar.js';

interface LLMOption {
    id: string;
    name: string;
    provider: string;
}

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

interface PaginatedPersonas {
    items: VoicePersona[];
    total: number;
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

        .btn-primary:disabled {
            background: #93c5fd;
            cursor: not-allowed;
        }

        .loading {
            display: flex;
            justify-content: center;
            padding: 40px;
        }

        .error-banner {
            margin-bottom: 16px;
            padding: 12px 16px;
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
            border-radius: 8px;
            font-size: 14px;
        }
    `;

    @state() private personas: VoicePersona[] = [];
    @state() private llmOptions: LLMOption[] = [];
    @state() private voiceOptions: string[] = [];
    @state() private loading = true;
    @state() private saving = false;
    @state() private showModal = false;
    @state() private editingPersona: VoicePersona | null = null;
    @state() private basePersona = { name: '', description: '', is_active: true };
    @state() private error = '';

    connectedCallback() {
        super.connectedCallback();
        this._loadData();
    }

    private async _loadData() {
        this.loading = true;
        await Promise.all([
            this._loadPersonas(),
            this._loadLLMOptions(),
            this._loadVoiceOptions(),
        ]);
        this.loading = false;
    }

    private async _loadPersonas() {
        try {
            const data = await apiClient.get<PaginatedPersonas>(
                '/voice/personas?active_only=true'
            );
            this.personas = data.items || [];
        } catch (e) {
            console.error('Failed to load personas:', e);
            this.error = 'Unable to load voice personas.';
        }
    }

    private async _loadLLMOptions() {
        try {
            const data = await apiClient.get<{ items: LLMOption[]; total: number }>(
                '/voice/llm-configs?model_type=chat'
            );
            this.llmOptions = data.items || [];
        } catch (e) {
            console.error('Failed to load LLM configs:', e);
            this.llmOptions = [];
        }
    }

    private async _loadVoiceOptions() {
        try {
            const data = await apiClient.get<{ items: { voice_id: string; name: string }[]; total: number }>(
                '/voice/models'
            );
            this.voiceOptions = (data.items || []).map((m) => m.voice_id);
        } catch (e) {
            console.error('Failed to load voice models:', e);
            // Fail closed: an unreachable voice catalog is empty, not a guess.
            this.voiceOptions = [];
        }
    }

    private _openCreate() {
        this.editingPersona = null;
        this.basePersona = { name: '', description: '', is_active: true };
        this.showModal = true;
    }

    private _handleEdit(persona: VoicePersona) {
        this.editingPersona = { ...persona };
        this.basePersona = {
            name: persona.name,
            description: persona.description,
            is_active: persona.is_active,
        };
        this.showModal = true;
    }

    private _handleDuplicate(persona: VoicePersona) {
        this.editingPersona = null;
        this.basePersona = {
            name: `${persona.name} (Copy)`,
            description: persona.description,
            is_active: persona.is_active,
        };
        this.showModal = true;
    }

    private async _handleSetDefault(persona: VoicePersona) {
        try {
            await apiClient.post(`/voice/personas/${persona.id}/set-default`, {});
            await this._loadPersonas();
        } catch (e) {
            console.error('Failed to set default persona:', e);
            this.error = 'Failed to set default persona.';
        }
    }

    private async _handleDelete(persona: VoicePersona) {
        if (!confirm(`Delete "${persona.name}"?`)) return;
        try {
            await apiClient.delete(`/voice/personas/${persona.id}`);
            await this._loadPersonas();
        } catch (e) {
            console.error('Failed to delete persona:', e);
            this.error = 'Failed to delete persona.';
        }
    }

    private _getConfigPanel() {
        return this.shadowRoot?.querySelector('voice-config-panel') as any;
    }

    private async _handleSave() {
        const configPanel = this._getConfigPanel();
        const config = configPanel?.getConfig() || {};

        const payload: Record<string, unknown> = {
            name: this.basePersona.name,
            description: this.basePersona.description,
            ...config,
            llm_config_id: config.llm_config_id || null,
        };

        this.saving = true;
        this.error = '';
        try {
            if (this.editingPersona) {
                await apiClient.put(`/voice/personas/${this.editingPersona.id}`, payload);
            } else {
                await apiClient.post('/voice/personas', payload);
            }
            this.showModal = false;
            this.basePersona = { name: '', description: '', is_active: true };
            this.editingPersona = null;
            await this._loadPersonas();
        } catch (e) {
            console.error('Failed to save persona:', e);
            this.error = 'Failed to save persona. Please check your input and try again.';
        }
        this.saving = false;
    }

    private _modalTitle() {
        return this.editingPersona ? 'Edit Voice Persona' : 'Create Voice Persona';
    }

    render() {
        return html`
            <saas-sidebar></saas-sidebar>

            <div class="main-content">
                <div class="header">
                    <h1>
                        <span class="material-symbols-outlined">record_voice_over</span>
                        Voice Personas
                    </h1>
                    <button class="create-btn" @click=${this._openCreate}>
                        <span class="material-symbols-outlined">add</span>
                        Create Persona
                    </button>
                </div>

                ${this.error ? html`<div class="error-banner">${this.error}</div>` : ''}

                ${this.loading
                    ? html`<div class="loading">Loading...</div>`
                    : html`
                          <div class="personas-grid">
                              ${this.personas.length === 0
                                  ? html`
                                        <div class="empty-state">
                                            <h3>No Voice Personas</h3>
                                            <p>Create your first voice persona to get started with AgentVoice Vox.</p>
                                            <button class="create-btn" @click=${this._openCreate}>
                                                <span class="material-symbols-outlined">add</span>
                                                Create Persona
                                            </button>
                                        </div>
                                    `
                                  : this.personas.map(
                                        (persona) => html`
                                            <voice-persona-card
                                                .persona=${persona}
                                                @persona-edit=${(e: CustomEvent) =>
                                                    this._handleEdit(e.detail.persona)}
                                                @persona-duplicate=${(e: CustomEvent) =>
                                                    this._handleDuplicate(e.detail.persona)}
                                                @persona-set-default=${(e: CustomEvent) =>
                                                    this._handleSetDefault(e.detail.persona)}
                                                @persona-delete=${(e: CustomEvent) =>
                                                    this._handleDelete(e.detail.persona)}
                                            ></voice-persona-card>
                                        `
                                    )}
                          </div>
                      `}
            </div>

            ${this.showModal
                ? html`
                      <saas-glass-modal size="large" @close=${() => (this.showModal = false)}>
                          <div class="modal-header">
                              <h2>${this._modalTitle()}</h2>
                              <p>Configure voice persona settings for your agents.</p>
                          </div>

                          <div class="form-row">
                              <div class="form-group">
                                  <label>Name</label>
                                  <input
                                      type="text"
                                      placeholder="e.g. Customer Support"
                                      .value=${this.basePersona.name}
                                      @input=${(e: Event) =>
                                          (this.basePersona = {
                                              ...this.basePersona,
                                              name: (e.target as HTMLInputElement).value,
                                          })}
                                  />
                              </div>
                              <div class="form-group">
                                  <label>Status</label>
                                  <select
                                      .value=${this.basePersona.is_active ? 'active' : 'inactive'}
                                      @change=${(e: Event) =>
                                          (this.basePersona = {
                                              ...this.basePersona,
                                              is_active:
                                                  (e.target as HTMLSelectElement).value ===
                                                  'active',
                                          })}
                                  >
                                      <option value="active">Active</option>
                                      <option value="inactive">Inactive</option>
                                  </select>
                              </div>
                          </div>

                          <div class="form-row">
                              <div class="form-group full">
                                  <label>Description</label>
                                  <textarea
                                      placeholder="Brief description of this persona..."
                                      .value=${this.basePersona.description}
                                      @input=${(e: Event) =>
                                          (this.basePersona = {
                                              ...this.basePersona,
                                              description: (
                                                  e.target as HTMLTextAreaElement
                                              ).value,
                                          })}
                                  ></textarea>
                              </div>
                          </div>

                          <voice-config-panel
                              .config=${this.editingPersona}
                              .llmOptions=${this.llmOptions}
                              .voiceOptions=${this.voiceOptions}
                          ></voice-config-panel>

                          <div class="modal-actions">
                              <button
                                  class="btn btn-secondary"
                                  @click=${() => (this.showModal = false)}
                                  ?disabled=${this.saving}
                              >
                                  Cancel
                              </button>
                              <button
                                  class="btn btn-primary"
                                  @click=${this._handleSave}
                                  ?disabled=${this.saving || !this.basePersona.name.trim()}
                              >
                                  ${this.saving ? 'Saving...' : 'Save Persona'}
                              </button>
                          </div>
                      </saas-glass-modal>
                  `
                : ''}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-voice-personas': SaasVoicePersonas;
    }
}
