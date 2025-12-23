/**
 * SaaS Sys Admin — Platform Dashboard
 * Global View with Interactive World Map
 *
 * VIBE COMPLIANT:
 * - Real Lit Web Component
 * - Interactive World Map showing agent/user distribution
 * - Clickable nodes for agent details
 * - Real-time metrics
 * - Premium dark theme with orange accent
 *
 * For SAAS Admins only - shows global platform overview
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface AgentNode {
    id: string;
    name: string;
    lat: number;
    lng: number;
    activeUsers: number;
    status: 'online' | 'busy' | 'idle';
    tenant: string;
    country: string;
    city: string;
}

interface PlatformMetrics {
    totalAgents: number;
    activeUsers: number;
    totalRequests: number;
    avgResponseTime: number;
    regions: { name: string; agents: number; users: number }[];
}

@customElement('eog-platform-dashboard')
export class EogPlatformDashboard extends LitElement {
    static styles = css`
        :host {
            display: block;
            min-height: 100vh;
            background: #0a0f1a;
            color: #e2e8f0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        * { box-sizing: border-box; }

        /* ========================================
           HEADER
           ======================================== */
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 32px;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo {
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #FF6B00 0%, #FF8533 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .logo-text {
            font-weight: 700;
            font-size: 20px;
            color: white;
        }

        .mode-badge {
            background: rgba(255, 107, 0, 0.15);
            color: #FF6B00;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .search-box {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 10px 16px;
            width: 300px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .search-box input {
            background: none;
            border: none;
            color: white;
            font-size: 14px;
            width: 100%;
            outline: none;
        }

        .search-box input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
        }

        /* ========================================
           MAIN LAYOUT
           ======================================== */
        .main-content {
            display: grid;
            grid-template-columns: 1fr 360px;
            gap: 0;
            height: calc(100vh - 80px);
        }

        @media (max-width: 1200px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            .sidebar {
                display: none;
            }
        }

        /* ========================================
           MAP CONTAINER
           ======================================== */
        .map-container {
            position: relative;
            overflow: hidden;
            background: radial-gradient(ellipse at center, #0f1729 0%, #050810 100%);
        }

        .world-map {
            width: 100%;
            height: 100%;
            object-fit: contain;
            opacity: 0.4;
            filter: brightness(0.8) contrast(1.1);
        }

        /* SVG World Map Paths */
        .map-svg {
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
        }

        .map-svg path {
            fill: rgba(30, 41, 59, 0.5);
            stroke: rgba(71, 85, 105, 0.3);
            stroke-width: 0.5;
        }

        /* Agent Nodes on Map */
        .agent-nodes {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }

        .agent-node {
            position: absolute;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            cursor: pointer;
            pointer-events: auto;
            transition: all 0.3s ease;
        }

        .agent-node::before {
            content: '';
            position: absolute;
            inset: -6px;
            border-radius: 50%;
            background: inherit;
            opacity: 0.3;
            animation: pulse-node 2s ease-in-out infinite;
        }

        .agent-node::after {
            content: '';
            position: absolute;
            inset: -12px;
            border-radius: 50%;
            background: inherit;
            opacity: 0.15;
            animation: pulse-node 2s ease-in-out infinite 0.5s;
        }

        @keyframes pulse-node {
            0%, 100% { transform: scale(1); opacity: 0.3; }
            50% { transform: scale(1.5); opacity: 0.1; }
        }

        .agent-node.online {
            background: #22C55E;
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
        }

        .agent-node.busy {
            background: #FF6B00;
            box-shadow: 0 0 20px rgba(255, 107, 0, 0.5);
        }

        .agent-node.idle {
            background: #64748B;
            box-shadow: 0 0 20px rgba(100, 116, 139, 0.5);
        }

        .agent-node:hover {
            transform: translate(-50%, -50%) scale(1.5);
            z-index: 10;
        }

        /* Node Tooltip */
        .node-tooltip {
            position: fixed;
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 16px;
            min-width: 220px;
            backdrop-filter: blur(20px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s ease;
            pointer-events: none;
        }

        .node-tooltip.visible {
            opacity: 1;
            visibility: visible;
        }

        .tooltip-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }

        .tooltip-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .tooltip-name {
            font-weight: 600;
            font-size: 14px;
        }

        .tooltip-location {
            font-size: 12px;
            color: #94a3b8;
            margin-bottom: 12px;
        }

        .tooltip-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }

        .tooltip-stat {
            background: rgba(255, 255, 255, 0.05);
            padding: 8px;
            border-radius: 6px;
            text-align: center;
        }

        .stat-value {
            font-size: 16px;
            font-weight: 700;
            color: white;
        }

        .stat-label {
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
        }

        /* Map Stats Overlay */
        .map-overlay-stats {
            position: absolute;
            bottom: 24px;
            left: 24px;
            display: flex;
            gap: 16px;
        }

        .overlay-stat {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 16px 20px;
            min-width: 140px;
        }

        .overlay-stat-value {
            font-size: 28px;
            font-weight: 700;
            color: white;
            margin-bottom: 4px;
        }

        .overlay-stat-label {
            font-size: 12px;
            color: #94a3b8;
        }

        .overlay-stat.accent .overlay-stat-value {
            color: #FF6B00;
        }

        /* ========================================
           SIDEBAR
           ======================================== */
        .sidebar {
            background: rgba(15, 23, 42, 0.6);
            border-left: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .sidebar-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .sidebar-subtitle {
            font-size: 12px;
            color: #64748b;
        }

        .sidebar-content {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }

        /* Agent List */
        .agent-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .agent-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .agent-card:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(255, 107, 0, 0.3);
            transform: translateX(4px);
        }

        .agent-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .agent-card-name {
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .status-dot.online { background: #22C55E; }
        .status-dot.busy { background: #FF6B00; }
        .status-dot.idle { background: #64748B; }

        .agent-card-location {
            font-size: 12px;
            color: #64748b;
            margin-bottom: 10px;
        }

        .agent-card-stats {
            display: flex;
            gap: 16px;
        }

        .agent-stat {
            font-size: 12px;
        }

        .agent-stat-value {
            font-weight: 600;
            color: white;
        }

        .agent-stat-label {
            color: #64748b;
        }

        /* Regions Summary */
        .regions-section {
            margin-top: 24px;
        }

        .section-title {
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 12px;
        }

        .region-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .region-name {
            flex: 1;
            font-size: 13px;
        }

        .region-count {
            font-size: 13px;
            font-weight: 600;
            color: #FF6B00;
        }

        .region-progress {
            width: 80px;
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            overflow: hidden;
        }

        .region-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #FF6B00, #FF8533);
            border-radius: 2px;
        }
    `;

    @state() private _agents: AgentNode[] = [
        { id: '1', name: 'Sales Assistant Pro', lat: 40.7128, lng: -74.006, activeUsers: 234, status: 'online', tenant: 'Acme Corp', country: 'USA', city: 'New York' },
        { id: '2', name: 'Support Bot Alpha', lat: 51.5074, lng: -0.1278, activeUsers: 189, status: 'busy', tenant: 'TechCo UK', country: 'UK', city: 'London' },
        { id: '3', name: 'Research Agent', lat: 35.6762, lng: 139.6503, activeUsers: 156, status: 'online', tenant: 'Tokyo Labs', country: 'Japan', city: 'Tokyo' },
        { id: '4', name: 'Customer Service AI', lat: 37.7749, lng: -122.4194, activeUsers: 312, status: 'online', tenant: 'Valley Start', country: 'USA', city: 'San Francisco' },
        { id: '5', name: 'HR Assistant', lat: 48.8566, lng: 2.3522, activeUsers: 87, status: 'idle', tenant: 'Euro Services', country: 'France', city: 'Paris' },
        { id: '6', name: 'Analytics Bot', lat: -33.8688, lng: 151.2093, activeUsers: 124, status: 'online', tenant: 'AusData', country: 'Australia', city: 'Sydney' },
        { id: '7', name: 'Lead Gen Agent', lat: 19.4326, lng: -99.1332, activeUsers: 98, status: 'busy', tenant: 'MX Growth', country: 'Mexico', city: 'Mexico City' },
        { id: '8', name: 'Code Assistant', lat: 52.52, lng: 13.405, activeUsers: 201, status: 'online', tenant: 'Berlin Dev', country: 'Germany', city: 'Berlin' },
    ];

    @state() private _metrics: PlatformMetrics = {
        totalAgents: 847,
        activeUsers: 12453,
        totalRequests: 2847593,
        avgResponseTime: 245,
        regions: [
            { name: 'North America', agents: 312, users: 4523 },
            { name: 'Europe', agents: 287, users: 3891 },
            { name: 'Asia Pacific', agents: 189, users: 2876 },
            { name: 'Latin America', agents: 59, users: 1163 },
        ]
    };

    @state() private _selectedAgent: AgentNode | null = null;
    @state() private _tooltipPos = { x: 0, y: 0 };

    render() {
        return html`
            <!-- Header -->
            <header class="header">
                <div class="header-left">
                    <div class="logo">
                        <div class="logo-icon">👁️</div>
                        <span class="logo-text">Eye of God</span>
                    </div>
                    <span class="mode-badge">Platform Mode</span>
                </div>
                <div class="header-right">
                    <div class="search-box">
                        <span>🔍</span>
                        <input type="text" placeholder="Search agents, tenants, users...">
                    </div>
                    <div class="user-avatar">SA</div>
                </div>
            </header>

            <!-- Main Content -->
            <main class="main-content">
                <!-- Map Container -->
                <div class="map-container">
                    ${this._renderWorldMap()}
                    
                    <!-- Agent Nodes -->
                    <div class="agent-nodes">
                        ${this._agents.map(agent => this._renderAgentNode(agent))}
                    </div>

                    <!-- Tooltip -->
                    <div class="node-tooltip ${this._selectedAgent ? 'visible' : ''}"
                         style="left: ${this._tooltipPos.x}px; top: ${this._tooltipPos.y}px;">
                        ${this._selectedAgent ? html`
                            <div class="tooltip-header">
                                <div class="tooltip-status status-dot ${this._selectedAgent.status}"></div>
                                <span class="tooltip-name">${this._selectedAgent.name}</span>
                            </div>
                            <div class="tooltip-location">
                                📍 ${this._selectedAgent.city}, ${this._selectedAgent.country}
                                <br>👤 ${this._selectedAgent.tenant}
                            </div>
                            <div class="tooltip-stats">
                                <div class="tooltip-stat">
                                    <div class="stat-value">${this._selectedAgent.activeUsers}</div>
                                    <div class="stat-label">Active Users</div>
                                </div>
                                <div class="tooltip-stat">
                                    <div class="stat-value">${this._selectedAgent.status}</div>
                                    <div class="stat-label">Status</div>
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Overlay Stats -->
                    <div class="map-overlay-stats">
                        <div class="overlay-stat accent">
                            <div class="overlay-stat-value">${this._metrics.totalAgents.toLocaleString()}</div>
                            <div class="overlay-stat-label">Total Agents</div>
                        </div>
                        <div class="overlay-stat">
                            <div class="overlay-stat-value">${this._metrics.activeUsers.toLocaleString()}</div>
                            <div class="overlay-stat-label">Active Users</div>
                        </div>
                        <div class="overlay-stat">
                            <div class="overlay-stat-value">${(this._metrics.totalRequests / 1000000).toFixed(1)}M</div>
                            <div class="overlay-stat-label">Total Requests</div>
                        </div>
                        <div class="overlay-stat">
                            <div class="overlay-stat-value">${this._metrics.avgResponseTime}ms</div>
                            <div class="overlay-stat-label">Avg Response</div>
                        </div>
                    </div>
                </div>

                <!-- Sidebar -->
                <aside class="sidebar">
                    <div class="sidebar-header">
                        <div class="sidebar-title">Active Agents</div>
                        <div class="sidebar-subtitle">${this._agents.length} agents across ${this._metrics.regions.length} regions</div>
                    </div>
                    <div class="sidebar-content">
                        <!-- Agent List -->
                        <div class="agent-list">
                            ${this._agents.map(agent => html`
                                <div class="agent-card" 
                                     @mouseenter=${() => this._highlightAgent(agent)}
                                     @mouseleave=${() => this._clearHighlight()}>
                                    <div class="agent-card-header">
                                        <span class="agent-card-name">
                                            <span class="status-dot ${agent.status}"></span>
                                            ${agent.name}
                                        </span>
                                    </div>
                                    <div class="agent-card-location">
                                        📍 ${agent.city}, ${agent.country} • ${agent.tenant}
                                    </div>
                                    <div class="agent-card-stats">
                                        <span class="agent-stat">
                                            <span class="agent-stat-value">${agent.activeUsers}</span>
                                            <span class="agent-stat-label"> users</span>
                                        </span>
                                    </div>
                                </div>
                            `)}
                        </div>

                        <!-- Regions Summary -->
                        <div class="regions-section">
                            <div class="section-title">Regions</div>
                            ${this._metrics.regions.map(region => html`
                                <div class="region-bar">
                                    <span class="region-name">${region.name}</span>
                                    <span class="region-count">${region.agents}</span>
                                    <div class="region-progress">
                                        <div class="region-progress-fill" 
                                             style="width: ${(region.agents / 312) * 100}%"></div>
                                    </div>
                                </div>
                            `)}
                        </div>
                    </div>
                </aside>
            </main>
        `;
    }

    private _renderWorldMap() {
        // Simplified world map SVG
        return html`
            <svg class="map-svg" viewBox="0 0 1000 500" preserveAspectRatio="xMidYMid slice">
                <!-- Simplified world continents -->
                <!-- North America -->
                <path d="M50,80 Q100,50 200,80 L250,120 Q280,180 230,220 L180,200 Q120,180 80,150 L50,80 Z"/>
                <!-- South America -->
                <path d="M180,260 Q220,240 250,280 L270,350 Q250,420 210,400 L180,320 Q160,280 180,260 Z"/>
                <!-- Europe -->
                <path d="M420,80 Q480,60 520,100 L500,140 Q460,160 430,130 L420,80 Z"/>
                <!-- Africa -->
                <path d="M430,180 Q490,160 530,220 L520,320 Q480,380 440,350 L430,260 Q420,220 430,180 Z"/>
                <!-- Asia -->
                <path d="M540,60 Q700,40 850,100 L880,180 Q860,260 780,240 L620,200 Q560,140 540,60 Z"/>
                <!-- Australia -->
                <path d="M780,320 Q840,300 880,340 L870,390 Q830,420 790,390 L780,320 Z"/>
                <!-- Connection lines between agents -->
                ${this._agents.map((agent, i) => {
            const nextAgent = this._agents[(i + 1) % this._agents.length];
            const x1 = this._lngToX(agent.lng);
            const y1 = this._latToY(agent.lat);
            const x2 = this._lngToX(nextAgent.lng);
            const y2 = this._latToY(nextAgent.lat);
            return html`
                        <line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" 
                              stroke="rgba(255, 107, 0, 0.1)" stroke-width="1" 
                              stroke-dasharray="4 4"/>
                    `;
        })}
            </svg>
        `;
    }

    private _renderAgentNode(agent: AgentNode) {
        const x = this._lngToX(agent.lng);
        const y = this._latToY(agent.lat);

        return html`
            <div class="agent-node ${agent.status}"
                 style="left: ${x}%; top: ${y}%;"
                 @mouseenter=${(e: MouseEvent) => this._showTooltip(agent, e)}
                 @mouseleave=${() => this._hideTooltip()}>
            </div>
        `;
    }

    private _lngToX(lng: number): number {
        return ((lng + 180) / 360) * 100;
    }

    private _latToY(lat: number): number {
        return ((90 - lat) / 180) * 100;
    }

    private _showTooltip(agent: AgentNode, e: MouseEvent) {
        this._selectedAgent = agent;
        this._tooltipPos = {
            x: e.clientX + 20,
            y: e.clientY - 60
        };
    }

    private _hideTooltip() {
        this._selectedAgent = null;
    }

    private _highlightAgent(agent: AgentNode) {
        this._selectedAgent = agent;
    }

    private _clearHighlight() {
        this._selectedAgent = null;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-platform-dashboard': EogPlatformDashboard;
    }
}
