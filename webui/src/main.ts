/**
 * SaaS Sys Admin - Main Entry Point
 * Enterprise Platform UI
 * 
 * VIBE COMPLIANT:
 * - Real routing
 * - Login flow support
 * - DEV_MODE bypass for development
 */

// Import components
import './components/index';

// Import views
import './views/index';

// Import styles
import './styles/tokens.css';

// DEV MODE: Set to true to bypass auth during development
const DEV_MODE = true;

// Routing logic
const app = document.getElementById('app');
if (app) {
    app.innerHTML = '';

    // Route handler
    const renderRoute = async () => {
        const path = window.location.pathname;
        const token = localStorage.getItem('eog_auth_token');

        // DEV MODE: Skip auth check
        if (DEV_MODE) {
            // Set fake token for dev
            if (!token) {
                localStorage.setItem('eog_auth_token', 'dev_token');
                localStorage.setItem('eog_user', JSON.stringify({
                    email: 'admin@dev.local',
                    name: 'Dev Admin',
                    role: 'saas_admin'
                }));
            }
        }

        // 1. Unauthenticated -> Login (skip in dev mode)
        // Public auth routes that don't require login
        const publicPaths = ['/login', '/auth/callback', '/register', '/forgot-password', '/reset-password', '/verify-email'];

        if (!DEV_MODE && !token) {
            if (!publicPaths.includes(path)) {
                window.history.replaceState(null, '', '/login');
                renderRoute();
                return;
            }
            app.innerHTML = '';

            // Route to appropriate auth page
            if (path === '/register') {
                await import('./views/saas-register.js');
                app.appendChild(document.createElement('saas-register'));
                return;
            }
            if (path === '/forgot-password') {
                await import('./views/saas-forgot-password.js');
                app.appendChild(document.createElement('saas-forgot-password'));
                return;
            }

            app.appendChild(document.createElement('soma-login'));
            return;
        }

        // 2. Auth callback - handle OAuth response
        if (path === '/auth/callback') {
            try {
                await import('./views/saas-auth-callback.js');
                app.innerHTML = '';
                app.appendChild(document.createElement('saas-auth-callback'));
            } catch (e) {
                // Fallback to legacy callback
                await import('./views/soma-auth-callback.js');
                app.innerHTML = '';
                app.appendChild(document.createElement('soma-auth-callback'));
            }
            return;
        }


        // Clear app content before rendering new view
        app.innerHTML = '';

        // 3. SAAS Routes
        if (path === '/saas/dashboard' || path === '/saas' || path === '/platform') {
            await import('./views/saas-platform-dashboard.js');
            app.appendChild(document.createElement('saas-platform-dashboard'));
            return;
        }

        if (path === '/platform/models') {
            await import('./views/saas-admin-models-list.js');
            app.appendChild(document.createElement('saas-admin-models-list'));
            return;
        }

        // Subscription Tier Builder
        if (path === '/platform/tiers' || path === '/saas/tiers') {
            await import('./views/saas-tier-builder.js');
            app.appendChild(document.createElement('saas-tier-builder'));
            return;
        }

        // Usage Analytics Dashboard
        if (path === '/platform/usage' || path === '/saas/usage') {
            await import('./views/saas-usage-analytics.js');
            app.appendChild(document.createElement('saas-usage-analytics'));
            return;
        }

        // Platform Integrations Dashboard
        if (path === '/platform/integrations' || path === '/saas/settings/integrations') {
            await import('./views/saas-integrations-dashboard.js');
            app.appendChild(document.createElement('saas-integrations-dashboard'));
            return;
        }

        if (path === '/platform/roles') {
            await import('./views/saas-admin-roles-list.js');
            app.appendChild(document.createElement('saas-admin-roles-list'));
            return;
        }

        // Role Matrix - Visual permission editor
        if (path === '/platform/role-matrix') {
            await import('./views/saas-role-matrix.js');
            app.appendChild(document.createElement('saas-role-matrix'));
            return;
        }

        // Tenant Creation Wizard
        if (path === '/saas/tenants/new' || path === '/platform/tenants/new') {
            await import('./views/saas-tenant-wizard.js');
            app.appendChild(document.createElement('saas-tenant-wizard'));
            return;
        }

        if (path === '/saas/permissions' || path === '/platform/permissions') {
            await import('./views/saas-permissions.js');
            app.appendChild(document.createElement('saas-permissions'));
            return;
        }

        if (path === '/platform/flags') {
            await import('./views/saas-admin-feature-flags.js');
            app.appendChild(document.createElement('saas-admin-feature-flags'));
            return;
        }

        if (path === '/platform/api-keys') {
            await import('./views/saas-admin-api-keys.js');
            app.appendChild(document.createElement('saas-admin-api-keys'));
            return;
        }

        // Feature Catalog
        if (path === '/platform/features' || path === '/saas/features') {
            await import('./views/saas-feature-catalog.js');
            app.appendChild(document.createElement('saas-feature-catalog'));
            return;
        }

        // Tenant Admin - Agent Metrics
        if (path === '/admin/metrics' || path === '/tenant/metrics') {
            await import('./views/saas-agent-metrics.js');
            app.appendChild(document.createElement('saas-agent-metrics'));
            return;
        }

        if (path === '/saas/tenants' || path === '/platform/tenants') {
            await import('./views/saas-tenants.js');
            app.appendChild(document.createElement('saas-tenants'));
            return;
        }

        if (path === '/saas/subscriptions') {
            await import('./views/saas-subscriptions.js');
            app.appendChild(document.createElement('saas-subscriptions'));
            return;
        }

        // Infrastructure Administration (Eye of God)
        if (path === '/platform/infrastructure' || path === '/saas/infrastructure') {
            await import('./views/saas-infrastructure-dashboard.js');
            app.appendChild(document.createElement('saas-infrastructure-dashboard'));
            return;
        }

        // Platform Metrics Dashboard
        if (path === '/platform/metrics' || path === '/saas/metrics') {
            await import('./views/platform-metrics-dashboard.js');
            app.appendChild(document.createElement('platform-metrics-dashboard'));
            return;
        }

        // Multimodal Settings (Agent Owner)
        if (path === '/settings/multimodal' || path === '/agent/multimodal') {
            await import('./views/saas-multimodal-settings.js');
            app.appendChild(document.createElement('saas-multimodal-settings'));
            return;
        }

        // Settings Configuration (uses SettingsForm pattern)
        if (path.startsWith('/platform/settings/')) {
            const entity = path.split('/').pop() || 'postgresql';
            await import('./components/settings-form.js');
            const form = document.createElement('settings-form') as HTMLElement;
            form.setAttribute('entity', entity);
            app.appendChild(form);
            return;
        }

        // Entity Views (Tenants, Users, Agents, Features using EntityManager)
        if (path === '/platform/tenants-new') {
            await import('./views/saas-entity-views.js');
            app.appendChild(document.createElement('saas-tenants-view'));
            return;
        }

        if (path === '/admin/users') {
            await import('./views/saas-entity-views.js');
            app.appendChild(document.createElement('saas-users-view'));
            return;
        }

        if (path === '/admin/agents') {
            await import('./views/saas-entity-views.js');
            app.appendChild(document.createElement('saas-agents-view'));
            return;
        }

        if (path === '/platform/features') {
            await import('./views/saas-entity-views.js');
            app.appendChild(document.createElement('saas-features-view'));
            return;
        }

        // Audit Log Dashboard
        if (path === '/platform/audit' || path === '/saas/audit') {
            await import('./views/saas-audit-dashboard.js');
            app.appendChild(document.createElement('saas-audit-dashboard'));
            return;
        }

        if (path === '/saas/billing') {
            await import('./views/saas-billing.js');
            app.appendChild(document.createElement('saas-billing'));
            return;
        }

        // Tenant Billing
        if (path === '/admin/billing' || path === '/tenant/billing') {
            await import('./views/saas-tenant-billing.js');
            app.appendChild(document.createElement('saas-tenant-billing'));
            return;
        }


        if (path === '/mode-select' || path === '/select-mode') {
            await import('./views/saas-mode-selection.js');
            app.appendChild(document.createElement('saas-mode-selection'));
            return;
        }

        if (path === '/cognitive' || path === '/training') {
            await import('./views/saas-cognitive-panel.js');
            app.appendChild(document.createElement('saas-cognitive-panel'));
            return;
        }

        // 4. Login Route
        if (path === '/login') {
            if (token) {
                window.history.replaceState(null, '', '/saas/dashboard');
                renderRoute();
                return;
            }
            try {
                await import('./views/saas-login.js');
                app.appendChild(document.createElement('saas-login'));
            } catch {
                // Fallback to legacy login
                app.appendChild(document.createElement('soma-login'));
            }
            return;
        }


        // Onboarding Wizard (invitation acceptance)
        if (path.startsWith('/onboarding') || path.startsWith('/invite/')) {
            await import('./views/saas-onboarding.js');
            app.appendChild(document.createElement('saas-onboarding'));
            return;
        }

        if (path === '/logout') {
            localStorage.removeItem('eog_auth_token');
            localStorage.removeItem('eog_user');
            window.location.href = '/login';
            return;
        }

        if (path === '/mode-select' || path === '/select-mode') {
            await import('./views/saas-mode-selection.js');
            app.appendChild(document.createElement('saas-mode-selection'));
            return;
        }

        // 5. Tenant Admin Routes
        if (path === '/admin/dashboard') {
            await import('./views/saas-tenant-dashboard.js');
            app.appendChild(document.createElement('saas-tenant-dashboard'));
            return;
        }

        if (path === '/admin/users') {
            await import('./views/saas-tenant-users.js');
            app.appendChild(document.createElement('saas-tenant-users'));
            return;
        }

        if (path === '/admin/agents') {
            await import('./views/saas-tenant-agents.js');
            app.appendChild(document.createElement('saas-tenant-agents'));
            return;
        }

        // MFA Setup
        if (path === '/mfa/setup' || path === '/settings/mfa') {
            await import('./views/saas-mfa-setup.js');
            app.appendChild(document.createElement('saas-mfa-setup'));
            return;
        }

        // Audit Log
        if (path === '/audit' || path === '/admin/audit' || path === '/platform/audit') {
            await import('./views/saas-audit-log.js');
            app.appendChild(document.createElement('saas-audit-log'));
            return;
        }



        if (path === '/chat') {
            try {
                await import('./views/saas-chat.js');
                app.appendChild(document.createElement('saas-chat'));
            } catch {
                // Fallback to legacy chat
                await import('./views/soma-chat.js');
                app.appendChild(document.createElement('soma-chat'));
            }
            return;
        }

        if (path === '/memory') {
            try {
                await import('./views/saas-memory-view.js');
                app.appendChild(document.createElement('saas-memory-view'));
            } catch {
                // Fallback to legacy memory
                await import('./views/soma-memory.js');
                app.appendChild(document.createElement('soma-memory'));
            }
            return;
        }

        if (path === '/settings') {
            try {
                await import('./views/saas-settings.js');
                app.appendChild(document.createElement('saas-settings'));
            } catch {
                // Fallback to legacy settings
                await import('./views/soma-settings.js');
                app.appendChild(document.createElement('soma-settings'));
            }
            return;
        }

        if (path === '/tools') {
            await import('./views/soma-tools.js');
            app.appendChild(document.createElement('soma-tools'));
            return;
        }

        if (path === '/themes') {
            await import('./views/soma-themes.js');
            app.appendChild(document.createElement('soma-themes'));
            return;
        }

        // 6. Voice Routes (AgentVoice Vox)
        if (path === '/voice/personas' || path === '/platform/voice/personas') {
            await import('./views/saas-voice-personas.js');
            app.appendChild(document.createElement('saas-voice-personas'));
            return;
        }

        if (path === '/voice/sessions' || path === '/platform/voice/sessions') {
            await import('./views/saas-voice-sessions.js');
            app.appendChild(document.createElement('saas-voice-sessions'));
            return;
        }

        if (path === '/voice/chat' || path === '/platform/voice/chat' || path === '/voice') {
            await import('./views/saas-voice-chat.js');
            app.appendChild(document.createElement('saas-voice-chat'));
            return;
        }



        // Default: New SAAS Dashboard
        await import('./views/saas-platform-dashboard.js');
        app.appendChild(document.createElement('saas-platform-dashboard'));
    };

    // Initial Render
    renderRoute();

    // Event Listeners for SPA Navigation
    window.addEventListener('popstate', renderRoute);

    // Custom navigation event from components
    window.addEventListener('saas-navigate', ((e: CustomEvent) => {
        const route = e.detail.route;
        if (route) {
            window.history.pushState(null, '', route);
            renderRoute();
        }
    }) as EventListener);
}

// Log startup
console.log('[SaaS] SaaS Sys Admin v1.0.0 initialized');
console.log('[SaaS] API: /api/v2/');
console.log('[SaaS] WebSocket: /ws/v2/');
console.log('[SaaS] DEV_MODE:', DEV_MODE ? 'ON' : 'OFF');


