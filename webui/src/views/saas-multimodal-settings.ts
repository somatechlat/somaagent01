/**
 * Multimodal Settings Dashboard
 * Configure agent multimodal capabilities and providers.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses /api/v2/agents/{id}/multimodal-config endpoint
 * - Permission: agent:update, agent:configure_*
 * - Per SRS-MULTIMODAL.md Section 6
 *
 * 7-Persona Implementation:
 * - 📈 PM: Capability toggles and tier gating
 * - 🏗️ Architect: Provider configuration
 * - 🔒 Security: Quota enforcement messaging
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state, property } from 'lit/decorators.js';

interface MultimodalConfig {
    image_enabled: boolean;
    image_quality: 'standard' | 'hd';
    image_style: 'vivid' | 'natural';
    diagram_enabled: boolean;
    diagram_format: 'svg' | 'png';
    diagram_theme: 'default' | 'dark' | 'forest' | 'neutral';
    screenshot_enabled: boolean;
    screenshot_width: number;
    screenshot_height: number;
    screenshot_full_page: boolean;
    video_enabled: boolean;
    vision_enabled: boolean;
    chat_model_vision: boolean;
    browser_model_vision: boolean;
    image_provider: string;
    diagram_provider: string;
    screenshot_provider: string;
}

interface QuotaUsage {
    images: { current: number; limit: number };
    diagrams: { current: number; limit: number };
    screenshots: { current: number; limit: number };
    video_minutes: { current: number; limit: number };
}

@customElement('saas-multimodal-settings')
export class SaasMultimodalSettings extends LitElement {
    static styles = css`
    :host {
      display: flex;
      height: 100vh;
      background: var(--saas-bg-page, #0f0f0f);
      font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
      color: #fff;
    }

    * { box-sizing: border-box; }

    .sidebar { width: 260px; flex-shrink: 0; }
    .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

    .header {
      padding: 20px 32px;
      border-bottom: 1px solid #222;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: #888; margin: 4px 0 0 0; }

    .btn {
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid #333;
      background: #1a1a1a;
      color: #fff;
      transition: all 0.15s;
    }

    .btn:hover { background: #262626; }
    .btn-primary { background: #22c55e; border-color: #22c55e; color: #000; }
    .btn-primary:hover { background: #16a34a; }

    .content { flex: 1; overflow-y: auto; padding: 32px; }

    /* Quota Bar */
    .quota-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 32px;
    }

    .quota-card {
      background: #1a1a1a;
      border: 1px solid #222;
      border-radius: 12px;
      padding: 16px;
    }

    .quota-label { font-size: 12px; color: #888; margin-bottom: 8px; }
    .quota-value { font-size: 18px; font-weight: 600; margin-bottom: 8px; }

    .quota-bar {
      height: 4px;
      background: #333;
      border-radius: 2px;
      overflow: hidden;
    }

    .quota-fill { height: 100%; border-radius: 2px; transition: width 0.3s; }
    .quota-fill.low { background: #22c55e; }
    .quota-fill.medium { background: #eab308; }
    .quota-fill.high { background: #ef4444; }

    /* Sections */
    .section {
      background: #1a1a1a;
      border: 1px solid #222;
      border-radius: 12px;
      margin-bottom: 24px;
      overflow: hidden;
    }

    .section-header {
      padding: 16px 20px;
      border-bottom: 1px solid #222;
      font-weight: 600;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .section-content { padding: 20px; }

    /* Capability Row */
    .capability-row {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      padding: 16px 0;
      border-bottom: 1px solid #222;
    }

    .capability-row:last-child { border-bottom: none; }

    .capability-info { flex: 1; }
    .capability-name { font-size: 14px; font-weight: 500; margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }
    .capability-desc { font-size: 12px; color: #888; margin-bottom: 8px; }

    .capability-options {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .capability-option {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #888;
    }

    .capability-option select {
      padding: 6px 10px;
      background: #0d0d0d;
      border: 1px solid #333;
      border-radius: 6px;
      color: #fff;
      font-size: 12px;
    }

    .capability-toggle { margin-left: 16px; }

    /* Toggle */
    .toggle-switch {
      position: relative;
      width: 44px;
      height: 24px;
    }

    .toggle-switch input { opacity: 0; width: 0; height: 0; }

    .toggle-slider {
      position: absolute;
      inset: 0;
      background: #333;
      border-radius: 24px;
      cursor: pointer;
      transition: 0.3s;
    }

    .toggle-slider:before {
      content: "";
      position: absolute;
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background: white;
      border-radius: 50%;
      transition: 0.3s;
    }

    input:checked + .toggle-slider { background: #22c55e; }
    input:checked + .toggle-slider:before { transform: translateX(20px); }

    /* Provider Grid */
    .provider-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }

    .provider-card {
      background: #0d0d0d;
      border: 1px solid #222;
      border-radius: 10px;
      padding: 16px;
    }

    .provider-name { font-size: 13px; font-weight: 500; margin-bottom: 8px; }
    .provider-type { font-size: 11px; color: #666; margin-bottom: 12px; }

    .provider-select {
      width: 100%;
      padding: 8px 12px;
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 6px;
      color: #fff;
      font-size: 12px;
    }

    .tag {
      font-size: 9px;
      font-weight: 600;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }

    .tag-enterprise { background: #7c3aed; color: #fff; }
    .tag-billable { background: #fef3c7; color: #92400e; }

    .loading { display: flex; justify-content: center; padding: 60px; color: #666; }
  `;

    @property({ type: String }) agentId = '';

    @state() private config: MultimodalConfig = {
        image_enabled: true,
        image_quality: 'standard',
        image_style: 'vivid',
        diagram_enabled: true,
        diagram_format: 'svg',
        diagram_theme: 'default',
        screenshot_enabled: true,
        screenshot_width: 1920,
        screenshot_height: 1080,
        screenshot_full_page: true,
        video_enabled: false,
        vision_enabled: true,
        chat_model_vision: true,
        browser_model_vision: true,
        image_provider: 'dalle3',
        diagram_provider: 'mermaid',
        screenshot_provider: 'playwright',
    };

    @state() private quotas: QuotaUsage = {
        images: { current: 312, limit: 500 },
        diagrams: { current: 234, limit: 1000 },
        screenshots: { current: 158, limit: 1000 },
        video_minutes: { current: 0, limit: 10 },
    };

    @state() private loading = false;
    @state() private saving = false;

    connectedCallback() {
        super.connectedCallback();
        this.loadConfig();
    }

    private getAuthHeaders(): HeadersInit {
        const token = localStorage.getItem('auth_token');
        return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
    }

    private async loadConfig() {
        if (!this.agentId) return;
        this.loading = true;
        try {
            const res = await fetch(`/api/v2/agents/${this.agentId}/multimodal-config`, { headers: this.getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                this.config = { ...this.config, ...data.config };
                this.quotas = data.quotas || this.quotas;
            }
        } catch (e) {
            console.error('Failed to load multimodal config:', e);
        } finally {
            this.loading = false;
        }
    }

    private async saveConfig() {
        this.saving = true;
        try {
            const res = await fetch(`/api/v2/agents/${this.agentId || 'current'}/multimodal-config`, {
                method: 'PUT',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(this.config),
            });
            if (res.ok) {
                // Show success toast
                console.log('Multimodal config saved');
            }
        } catch (e) {
            console.error('Failed to save:', e);
        } finally {
            this.saving = false;
        }
    }

    private getQuotaClass(current: number, limit: number): string {
        const pct = (current / limit) * 100;
        if (pct >= 80) return 'high';
        if (pct >= 50) return 'medium';
        return 'low';
    }

    private updateConfig(key: keyof MultimodalConfig, value: unknown) {
        this.config = { ...this.config, [key]: value };
    }

    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/settings/multimodal"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">🎨 Multimodal Settings</h1>
            <p class="header-subtitle">Configure image, diagram, and screenshot generation</p>
          </div>
          <button class="btn btn-primary" ?disabled=${this.saving} @click=${() => this.saveConfig()}>
            ${this.saving ? 'Saving...' : '💾 Save Changes'}
          </button>
        </header>

        <div class="content">
          <!-- Quota Usage -->
          <div class="quota-grid">
            ${Object.entries(this.quotas).map(([key, { current, limit }]) => html`
              <div class="quota-card">
                <div class="quota-label">${key.replace('_', ' ').toUpperCase()}</div>
                <div class="quota-value">${current} / ${limit}</div>
                <div class="quota-bar">
                  <div class="quota-fill ${this.getQuotaClass(current, limit)}"
                    style="width: ${Math.min(100, (current / limit) * 100)}%"></div>
                </div>
              </div>
            `)}
          </div>

          <!-- Multimodal Capabilities -->
          <div class="section">
            <div class="section-header">🖼️ Multimodal Capabilities</div>
            <div class="section-content">
              <!-- Image Generation -->
              <div class="capability-row">
                <div class="capability-info">
                  <div class="capability-name">
                    Image Generation (DALLE 3)
                    <span class="tag tag-billable">Billable</span>
                  </div>
                  <div class="capability-desc">AI-generated images from text prompts using OpenAI DALLE 3</div>
                  <div class="capability-options">
                    <div class="capability-option">
                      Quality:
                      <select .value=${this.config.image_quality}
                        @change=${(e: Event) => this.updateConfig('image_quality', (e.target as HTMLSelectElement).value)}>
                        <option value="standard">Standard</option>
                        <option value="hd">HD</option>
                      </select>
                    </div>
                    <div class="capability-option">
                      Style:
                      <select .value=${this.config.image_style}
                        @change=${(e: Event) => this.updateConfig('image_style', (e.target as HTMLSelectElement).value)}>
                        <option value="vivid">Vivid</option>
                        <option value="natural">Natural</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div class="capability-toggle">
                  <label class="toggle-switch">
                    <input type="checkbox" .checked=${this.config.image_enabled}
                      @change=${(e: Event) => this.updateConfig('image_enabled', (e.target as HTMLInputElement).checked)}>
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <!-- Diagram Generation -->
              <div class="capability-row">
                <div class="capability-info">
                  <div class="capability-name">Diagram Generation (Mermaid)</div>
                  <div class="capability-desc">Flowcharts, sequence diagrams, class diagrams, and more</div>
                  <div class="capability-options">
                    <div class="capability-option">
                      Format:
                      <select .value=${this.config.diagram_format}
                        @change=${(e: Event) => this.updateConfig('diagram_format', (e.target as HTMLSelectElement).value)}>
                        <option value="svg">SVG</option>
                        <option value="png">PNG</option>
                      </select>
                    </div>
                    <div class="capability-option">
                      Theme:
                      <select .value=${this.config.diagram_theme}
                        @change=${(e: Event) => this.updateConfig('diagram_theme', (e.target as HTMLSelectElement).value)}>
                        <option value="default">Default</option>
                        <option value="dark">Dark</option>
                        <option value="forest">Forest</option>
                        <option value="neutral">Neutral</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div class="capability-toggle">
                  <label class="toggle-switch">
                    <input type="checkbox" .checked=${this.config.diagram_enabled}
                      @change=${(e: Event) => this.updateConfig('diagram_enabled', (e.target as HTMLInputElement).checked)}>
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <!-- Screenshots -->
              <div class="capability-row">
                <div class="capability-info">
                  <div class="capability-name">Screenshots (Playwright)</div>
                  <div class="capability-desc">Capture web page screenshots using headless browser</div>
                  <div class="capability-options">
                    <div class="capability-option">
                      Viewport:
                      <select @change=${(e: Event) => {
                const [w, h] = (e.target as HTMLSelectElement).value.split('x').map(Number);
                this.updateConfig('screenshot_width', w);
                this.updateConfig('screenshot_height', h);
            }}>
                        <option value="1920x1080" ?selected=${this.config.screenshot_width === 1920}>1920×1080</option>
                        <option value="1366x768" ?selected=${this.config.screenshot_width === 1366}>1366×768</option>
                        <option value="375x812" ?selected=${this.config.screenshot_width === 375}>375×812 (Mobile)</option>
                      </select>
                    </div>
                    <div class="capability-option">
                      <label>
                        <input type="checkbox" .checked=${this.config.screenshot_full_page}
                          @change=${(e: Event) => this.updateConfig('screenshot_full_page', (e.target as HTMLInputElement).checked)}>
                        Full Page
                      </label>
                    </div>
                  </div>
                </div>
                <div class="capability-toggle">
                  <label class="toggle-switch">
                    <input type="checkbox" .checked=${this.config.screenshot_enabled}
                      @change=${(e: Event) => this.updateConfig('screenshot_enabled', (e.target as HTMLInputElement).checked)}>
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <!-- Video Generation -->
              <div class="capability-row" style="opacity: 0.5;">
                <div class="capability-info">
                  <div class="capability-name">
                    Video Generation
                    <span class="tag tag-enterprise">Enterprise</span>
                  </div>
                  <div class="capability-desc">AI video generation (coming soon)</div>
                </div>
                <div class="capability-toggle">
                  <label class="toggle-switch">
                    <input type="checkbox" .checked=${this.config.video_enabled} disabled>
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Vision Settings -->
          <div class="section">
            <div class="section-header">👁️ Vision Settings (Input)</div>
            <div class="section-content">
              <div class="capability-row">
                <div class="capability-info">
                  <div class="capability-name">Enable Vision (Image Understanding)</div>
                  <div class="capability-desc">Allow agent to analyze and understand uploaded images</div>
                </div>
                <div class="capability-toggle">
                  <label class="toggle-switch">
                    <input type="checkbox" .checked=${this.config.vision_enabled}
                      @change=${(e: Event) => this.updateConfig('vision_enabled', (e.target as HTMLInputElement).checked)}>
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <div class="capability-row">
                <div class="capability-info">
                  <div class="capability-name">Chat Model Vision</div>
                  <div class="capability-desc">Use vision capabilities in chat conversations</div>
                </div>
                <div class="capability-toggle">
                  <label class="toggle-switch">
                    <input type="checkbox" .checked=${this.config.chat_model_vision}
                      @change=${(e: Event) => this.updateConfig('chat_model_vision', (e.target as HTMLInputElement).checked)}>
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <div class="capability-row">
                <div class="capability-info">
                  <div class="capability-name">Browser Model Vision</div>
                  <div class="capability-desc">Use vision for web browsing agent tasks</div>
                </div>
                <div class="capability-toggle">
                  <label class="toggle-switch">
                    <input type="checkbox" .checked=${this.config.browser_model_vision}
                      @change=${(e: Event) => this.updateConfig('browser_model_vision', (e.target as HTMLInputElement).checked)}>
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Provider Preferences -->
          <div class="section">
            <div class="section-header">⚙️ Provider Preferences</div>
            <div class="section-content">
              <div class="provider-grid">
                <div class="provider-card">
                  <div class="provider-name">Image Provider</div>
                  <div class="provider-type">For image generation</div>
                  <select class="provider-select" .value=${this.config.image_provider}
                    @change=${(e: Event) => this.updateConfig('image_provider', (e.target as HTMLSelectElement).value)}>
                    <option value="dalle3">DALLE 3 (OpenAI)</option>
                    <option value="stable_diffusion">Stable Diffusion</option>
                    <option value="midjourney">Midjourney API</option>
                  </select>
                </div>

                <div class="provider-card">
                  <div class="provider-name">Diagram Provider</div>
                  <div class="provider-type">For diagram rendering</div>
                  <select class="provider-select" .value=${this.config.diagram_provider}
                    @change=${(e: Event) => this.updateConfig('diagram_provider', (e.target as HTMLSelectElement).value)}>
                    <option value="mermaid">Mermaid (Local)</option>
                    <option value="plantuml">PlantUML</option>
                    <option value="graphviz">Graphviz</option>
                  </select>
                </div>

                <div class="provider-card">
                  <div class="provider-name">Screenshot Engine</div>
                  <div class="provider-type">For page captures</div>
                  <select class="provider-select" .value=${this.config.screenshot_provider}
                    @change=${(e: Event) => this.updateConfig('screenshot_provider', (e.target as HTMLSelectElement).value)}>
                    <option value="playwright">Playwright (Local)</option>
                    <option value="puppeteer">Puppeteer</option>
                    <option value="selenium">Selenium</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-multimodal-settings': SaasMultimodalSettings;
    }
}
