/**
 * Multimodal Jobs & Assets Screen
 *
 * Route: /multimodal/jobs
 * Lists multimodal job plans and stored assets.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';

import '../components/saas-sidebar.js';

interface MultimodalJob {
    id: string;
    name: string;
    status: string;
    total_steps: number;
    completed_steps: number;
    created_at: string;
    updated_at: string;
    error_message?: string | null;
}

interface Asset {
    asset_id: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    created_at: string;
    created_by?: string | null;
    tags?: string[];
}

@customElement('saas-multimodal-jobs')
export class SaasMultimodalJobs extends LitElement {
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

        .content { flex: 1; overflow-y: auto; padding: 32px; }

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

        .section-content { padding: 0; }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px 16px;
            text-align: left;
            font-size: 13px;
            border-bottom: 1px solid #222;
        }

        th {
            color: #888;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.05em;
            background: #0d0d0d;
        }

        tr:last-child td { border-bottom: none; }

        .id-cell {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11px;
            color: #888;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-pending { background: rgba(251, 191, 36, 0.15); color: #f59e0b; }
        .status-running { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
        .status-completed { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
        .status-failed { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
        .status-cancelled { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }

        .progress {
            width: 100%;
            height: 6px;
            background: #333;
            border-radius: 3px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: #3b82f6;
            border-radius: 3px;
        }

        .loading, .empty-state, .error-banner {
            padding: 40px;
            text-align: center;
            color: #888;
        }

        .error-banner {
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.1);
            border-radius: 8px;
            margin: 0 32px 24px 32px;
        }

        .tag {
            display: inline-block;
            padding: 2px 6px;
            background: #333;
            border-radius: 4px;
            font-size: 10px;
            margin-right: 4px;
        }
    `;

    @state() private jobs: MultimodalJob[] = [];
    @state() private assets: Asset[] = [];
    @state() private loadingJobs = true;
    @state() private loadingAssets = true;
    @state() private error = '';

    connectedCallback() {
        super.connectedCallback();
        this._loadData();
    }

    private async _loadData() {
        await Promise.all([this._loadJobs(), this._loadAssets()]);
    }

    private async _loadJobs() {
        this.loadingJobs = true;
        try {
            const data = await apiClient.get<{ items: MultimodalJob[]; total: number }>('/multimodal/jobs');
            this.jobs = data.items || [];
        } catch (e) {
            this.error = e instanceof ApiError ? e.message : 'Failed to load multimodal jobs.';
        }
        this.loadingJobs = false;
    }

    private async _loadAssets() {
        this.loadingAssets = true;
        try {
            const data = await apiClient.get<{ assets: Asset[]; total: number }>('/assets');
            this.assets = data.assets || [];
        } catch (e) {
            console.error('Failed to load assets:', e);
        }
        this.loadingAssets = false;
    }

    private _formatDate(iso?: string): string {
        if (!iso) return '-';
        return new Date(iso).toLocaleString();
    }

    private _formatBytes(bytes: number): string {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / k ** i).toFixed(1))} ${sizes[i]}`;
    }

    private _progress(job: MultimodalJob): number {
        if (!job.total_steps) return 0;
        return Math.round((job.completed_steps / job.total_steps) * 100);
    }

    render() {
        return html`
            <aside class="sidebar">
                <saas-sidebar active-route="/multimodal/jobs"></saas-sidebar>
            </aside>

            <main class="main">
                <header class="header">
                    <div>
                        <h1 class="header-title">
                            <span class="material-symbols-outlined">perm_media</span>
                            Multimodal Jobs & Assets
                        </h1>
                        <p class="header-subtitle">Generated content, diagrams, images, and screenshots</p>
                    </div>
                </header>

                ${this.error ? html`<div class="error-banner">${this.error}</div>` : ''}

                <div class="content">
                    <div class="section">
                        <div class="section-header">
                            <span class="material-symbols-outlined">task</span>
                            Jobs
                        </div>
                        <div class="section-content">
                            ${this.loadingJobs
                                ? html`<div class="loading">Loading jobs...</div>`
                                : this.jobs.length === 0
                                  ? html`<div class="empty-state">No multimodal jobs yet.</div>`
                                  : html`
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>ID</th>
                                                    <th>Name</th>
                                                    <th>Status</th>
                                                    <th>Progress</th>
                                                    <th>Created</th>
                                                    <th>Updated</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${this.jobs.map(
                                                    (job) => html`
                                                        <tr>
                                                            <td class="id-cell">${job.id}</td>
                                                            <td>${job.name || '-'}</td>
                                                            <td>
                                                                <span class="status-badge status-${job.status}">
                                                                    ${job.status}
                                                                </span>
                                                            </td>
                                                            <td>
                                                                <div class="progress">
                                                                    <div
                                                                        class="progress-fill"
                                                                        style="width: ${this._progress(job)}%"
                                                                    ></div>
                                                                </div>
                                                                <div style="font-size:10px;color:#888;margin-top:4px;">
                                                                    ${job.completed_steps}/${job.total_steps} steps
                                                                </div>
                                                            </td>
                                                            <td>${this._formatDate(job.created_at)}</td>
                                                            <td>${this._formatDate(job.updated_at)}</td>
                                                        </tr>
                                                    `
                                                )}
                                            </tbody>
                                        </table>
                                    `}
                        </div>
                    </div>

                    <div class="section">
                        <div class="section-header">
                            <span class="material-symbols-outlined">photo_library</span>
                            Assets
                        </div>
                        <div class="section-content">
                            ${this.loadingAssets
                                ? html`<div class="loading">Loading assets...</div>`
                                : this.assets.length === 0
                                  ? html`<div class="empty-state">No assets stored yet.</div>`
                                  : html`
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>ID</th>
                                                    <th>Filename</th>
                                                    <th>Type</th>
                                                    <th>Size</th>
                                                    <th>Created</th>
                                                    <th>Tags</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${this.assets.map(
                                                    (asset) => html`
                                                        <tr>
                                                            <td class="id-cell">${asset.asset_id}</td>
                                                            <td>${asset.filename || '-'}</td>
                                                            <td>${asset.content_type}</td>
                                                            <td>${this._formatBytes(asset.size_bytes)}</td>
                                                            <td>${this._formatDate(asset.created_at)}</td>
                                                            <td>
                                                                ${(asset.tags || []).map(
                                                                    (tag) => html`<span class="tag">${tag}</span>`
                                                                )}
                                                            </td>
                                                        </tr>
                                                    `
                                                )}
                                            </tbody>
                                        </table>
                                    `}
                        </div>
                    </div>
                </div>
            </main>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-multimodal-jobs': SaasMultimodalJobs;
    }
}
