/**
 * SomaAgent SaaS — Subscription Tiers Management
 * Per SAAS_ADMIN_SRS.md Section 4.3 - Subscription Tiers
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Django Ninja API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 *
 * Features:
 * - View and manage subscription tiers
 * - Edit tier limits (agents, users, tokens, storage)
 * - Create custom tiers
 * - View tier distribution
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-subscription-tier-cards.js';
import '../components/saas-subscription-feature-matrix.js';
import '../components/saas-subscription-editor.js';
import { SubscriptionsController, type SubscriptionTier, type SubscriptionTierInput } from '../controllers/subscriptions-controller.js';

@customElement('saas-subscriptions')
export class SaasSubscriptions extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * {
            box-sizing: border-box;
        }

        /* Material Symbols - Required for Shadow DOM */
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

        /* Sidebar */
        .sidebar {
            width: 260px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: 24px 0;
        }

        .sidebar-header {
            padding: 0 20px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            margin-bottom: 16px;
        }

        .sidebar-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 4px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .sidebar-subtitle {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
        }

        .nav-list {
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding: 0 12px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
        }

        .nav-item:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .nav-item.active {
            background: var(--saas-bg-active, #f0f0f0);
            color: var(--saas-text-primary, #1a1a1a);
            font-weight: 500;
        }

        .nav-item .material-symbols-outlined {
            font-size: 18px;
        }

        .nav-divider {
            height: 1px;
            background: var(--saas-border-light, #e0e0e0);
            margin: 12px 20px;
        }

        /* Main Content */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
        }

        .header-actions {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.1s ease;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .btn:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .btn.primary:hover {
            background: #333;
        }

        .btn .material-symbols-outlined {
            font-size: 18px;
        }

        .content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }
    `;

    @state() private _tiers: SubscriptionTier[] = [];
    @state() private _showModal = false;
    @state() private _editingTier: SubscriptionTier | null = null;

    private _controller = new SubscriptionsController();

    async connectedCallback() {
        super.connectedCallback();
        await this._loadTiers();
    }

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">
                        <span class="material-symbols-outlined">shield_person</span>
                        God Mode
                    </h1>
                    <p class="sidebar-subtitle">Platform Administration</p>
                </div>

                <nav class="nav-list">
                    <a class="nav-item" href="/saas/dashboard">
                        <span class="material-symbols-outlined">dashboard</span>
                        Dashboard
                    </a>
                    <a class="nav-item" href="/saas/tenants">
                        <span class="material-symbols-outlined">apartment</span>
                        Tenants
                    </a>
                    <a class="nav-item active" href="/saas/subscriptions">
                        <span class="material-symbols-outlined">card_membership</span>
                        Subscriptions
                    </a>
                    <a class="nav-item" href="/saas/billing">
                        <span class="material-symbols-outlined">payments</span>
                        Billing
                    </a>
                    <div class="nav-divider"></div>
                    <a class="nav-item" href="/platform/models">
                        <span class="material-symbols-outlined">model_training</span>
                        Models
                    </a>
                    <a class="nav-item" href="/platform/roles">
                        <span class="material-symbols-outlined">admin_panel_settings</span>
                        Roles
                    </a>
                    <a class="nav-item" href="/platform/flags">
                        <span class="material-symbols-outlined">toggle_on</span>
                        Feature Flags
                    </a>
                    <a class="nav-item" href="/platform/api-keys">
                        <span class="material-symbols-outlined">vpn_key</span>
                        API Keys
                    </a>
                </nav>
            </aside>

            <!-- Main Content -->
            <main class="main">
                <header class="header">
                    <h2 class="header-title">Subscription Tiers</h2>
                    <div class="header-actions">
                        <button class="btn primary" @click=${() => this._openModal()}>
                            <span class="material-symbols-outlined">add</span>
                            Create Custom Tier
                        </button>
                    </div>
                </header>

                <div class="content">
                    <saas-subscription-tier-cards
                        .tiers=${this._tiers}
                        @edit-tier=${this._onEditTier}
                        @delete-tier=${this._onDeleteTier}>
                    </saas-subscription-tier-cards>

                    <saas-subscription-feature-matrix .tiers=${this._tiers}></saas-subscription-feature-matrix>
                </div>
            </main>

            <!-- Modal -->
            <saas-subscription-editor
                .open=${this._showModal}
                .editingTier=${this._editingTier}
                @close-editor=${this._closeModal}
                @save-tier=${this._onSaveTier}>
            </saas-subscription-editor>
        `;
    }

    private async _loadTiers() {
        this._tiers = await this._controller.loadTiers();
    }

    private _openModal(tier?: SubscriptionTier) {
        this._editingTier = tier || null;
        this._showModal = true;
    }

    private _closeModal() {
        this._showModal = false;
        this._editingTier = null;
    }

    private _onEditTier = (e: CustomEvent<SubscriptionTier>) => {
        this._openModal(e.detail);
    };

    private _onDeleteTier = async (e: CustomEvent<string>) => {
        if (!confirm('Delete this custom tier? Tenants using it will need to be reassigned.')) {
            return;
        }
        try {
            await this._controller.deleteTier(e.detail);
            await this._loadTiers();
        } catch (error) {
            console.error('Failed to delete tier:', error);
        }
    };

    private _onSaveTier = async (e: CustomEvent<SubscriptionTierInput>) => {
        try {
            if (this._editingTier) {
                await this._controller.updateTier(this._editingTier.id, e.detail);
            } else {
                await this._controller.createTier(e.detail);
            }
            await this._loadTiers();
            this._closeModal();
        } catch (error) {
            console.error('Failed to save tier:', error);
        }
    };
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-subscriptions': SaasSubscriptions;
    }
}
