/**
 * SaaS Sys Admin - Main Entry Point
 * Enterprise Platform UI
 * 
 * VIBE COMPLIANT:
 * - Real routing
 * - Login flow support
 * - httpOnly cookie auth in every environment
 */

// Import components
import './components/index';

// Import views
import './views/index';

// Import styles
import './styles/tokens.css';
import './styles/material-symbols.css';

// Theme: light default + dark toggle (localStorage)
import './services/theme-boot.js';
import { apiClient } from './services/api-client.js';

// Routing logic
const app = document.getElementById('app');
if (app) {
    app.innerHTML = '';

    // Route handler
    const renderRoute = async () => {
        const path = window.location.pathname;

        // Public auth routes that don't require login
        const publicPaths = ['/login', '/auth/callback', '/register', '/forgot-password', '/reset-password', '/verify-email'];

        const checkAuth = async (): Promise<boolean> => {
            try {
                const res = await fetch('/api/v2/auth/me', { credentials: 'include' });
                return res.ok;
            } catch {
                return false;
            }
        };

        // 1. Unauthenticated -> Login
        const isAuthenticated = await checkAuth();
        if (!isAuthenticated && !publicPaths.includes(path)) {
            window.history.replaceState(null, '', '/login');
            renderRoute();
            return;
        }

        if (path === '/login') {
            if (isAuthenticated) {
                // Home is the chat workspace
                window.history.replaceState(null, '', '/chat');
                renderRoute();
                return;
            }
            app.innerHTML = '';
            await import('./views/saas-login.js');
            app.appendChild(document.createElement('saas-login'));
            return;
        }

        if (path === '/register') {
            app.innerHTML = '';
            await import('./views/saas-register.js');
            app.appendChild(document.createElement('saas-register'));
            return;
        }

        if (path === '/forgot-password') {
            app.innerHTML = '';
            await import('./views/saas-forgot-password.js');
            app.appendChild(document.createElement('saas-forgot-password'));
            return;
        }

        // 2. Auth callback - handle OAuth response
        if (path === '/auth/callback') {
            await import('./views/saas-auth-callback.js');
            app.innerHTML = '';
            app.appendChild(document.createElement('saas-auth-callback'));
            return;
        }


        // Clear app content before rendering new view
        app.innerHTML = '';

        // Home `/` is the chat workspace (product hero).
        if (path === '/' || path === '' || path === '/index.html') {
            await import('./views/saas-chat.js');
            app.appendChild(document.createElement('saas-chat'));
            return;
        }

        // 3. AGENT ADMINISTRATION Routes
        //    No SaaS or billing routes: this is a standalone agent, and the
        //    admin surface administers the agent only. See AGENT.md §1.1.
        if (path === '/saas/dashboard' || path === '/saas' || path === '/platform') {
            await import('./views/saas-agent-metrics.js');
            app.appendChild(document.createElement('saas-agent-metrics'));
            return;
        }

        if (path === '/platform/models') {
            // One model catalog: /llm/models on the Models settings screen.
            await import('./views/saas-settings-models.js');
            app.appendChild(document.createElement('saas-settings-models'));
            return;
        }

        // Rate Limits Dashboard
        if (path === '/platform/infrastructure/redis/ratelimits' || path === '/platform/ratelimits') {
            await import('./views/saas-rate-limits.js');
            app.appendChild(document.createElement('saas-rate-limits'));
            return;
        }

        // Platform Integrations Dashboard
        if (path === '/platform/integrations' || path === '/saas/settings/integrations') {
            await import('./views/saas-integrations-dashboard.js');
            app.appendChild(document.createElement('saas-integrations-dashboard'));
            return;
        }

        // One roles list + one permission matrix (the old permissions screen is folded in).
        if (path === '/platform/roles') {
            await import('./views/saas-admin-roles-list.js');
            app.appendChild(document.createElement('saas-admin-roles-list'));
            return;
        }
        if (path === '/platform/role-matrix'
            || path === '/saas/permissions' || path === '/platform/permissions') {
            await import('./views/saas-role-matrix.js');
            app.appendChild(document.createElement('saas-role-matrix'));
            return;
        }

        if (path === '/platform/api-keys') {
            await import('./views/saas-admin-api-keys.js');
            app.appendChild(document.createElement('saas-admin-api-keys'));
            return;
        }

        // Agent metrics
        if (path === '/admin/metrics') {
            await import('./views/saas-agent-metrics.js');
            app.appendChild(document.createElement('saas-agent-metrics'));
            return;
        }

        // Infrastructure Administration (SaaS Platform Admin)
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

        // Entity Views (Users, Agents using EntityManager)
        if (path === '/admin/users') {
            await import('./views/saas-entity-views.js');
            app.appendChild(document.createElement('saas-users-view'));
            return;
        }

        // User Detail View
        if (path.match(/^\/admin\/users\/[^/]+$/)) {
            await import('./views/saas-user-detail.js');
            app.appendChild(document.createElement('saas-user-detail'));
            return;
        }

        // Platform Admin Profile
        if (path === '/platform/profile') {
            await import('./views/saas-platform-profile.js');
            app.appendChild(document.createElement('saas-platform-profile'));
            return;
        }

        // Agent admin profile
        if (path === '/admin/profile') {
            await import('./views/saas-platform-profile.js');
            app.appendChild(document.createElement('saas-platform-profile'));
            return;
        }

        // Personal User Profile
        if (path === '/profile') {
            await import('./views/saas-personal-profile.js');
            app.appendChild(document.createElement('saas-personal-profile'));
            return;
        }

        if (path === '/admin/agents') {
            await import('./views/saas-entity-views.js');
            app.appendChild(document.createElement('saas-agents-view'));
            return;
        }

        // Audit Log Dashboard
        if (path === '/platform/audit' || path === '/saas/audit') {
            await import('./views/saas-audit-dashboard.js');
            app.appendChild(document.createElement('saas-audit-dashboard'));
            return;
        }

        if (path === '/cognitive' || path === '/training') {
            await import('./views/saas-cognitive-panel.js');
            app.appendChild(document.createElement('saas-cognitive-panel'));
            return;
        }

        // Onboarding Wizard (invitation acceptance)
        if (path.startsWith('/onboarding') || path.startsWith('/invite/')) {
            await import('./views/saas-onboarding.js');
            app.appendChild(document.createElement('saas-onboarding'));
            return;
        }

        if (path === '/logout') {
            // SECURITY: the session lives in httpOnly cookies, so clearing
            // localStorage alone does not end it. Call the real logout first
            // (deletes the cookies), then clear client residue and leave.
            try {
                await apiClient.logout();
            } catch (err) {
                console.error('[SaaS] server logout failed', err);
            }
            localStorage.removeItem('saas_auth_token');
            localStorage.removeItem('saas_user');
            window.location.href = '/login';
            return;
        }

        // MFA Setup
        if (path === '/mfa/setup' || path === '/settings/mfa') {
            await import('./views/saas-mfa-setup.js');
            app.appendChild(document.createElement('saas-mfa-setup'));
            return;
        }

        // One audit surface: the dashboard (stats + log + filters).
        if (path === '/audit' || path === '/admin/audit') {
            await import('./views/saas-audit-dashboard.js');
            app.appendChild(document.createElement('saas-audit-dashboard'));
            return;
        }



        if (path === '/chat' || path === '/chat/' || path.startsWith('/chat/') || path === '/saas/chat') {
            await import('./views/saas-chat.js');
            app.appendChild(document.createElement('saas-chat'));
            return;
        }

        if (path === '/workspace') {
            await import('./views/saas-workspace.js');
            app.appendChild(document.createElement('saas-workspace'));
            return;
        }

        if (path === '/memory') {
            await import('./views/saas-memory-view.js');
            app.appendChild(document.createElement('saas-memory-view'));
            return;
        }

        if (path === '/settings/models' || path === '/agent/models') {
            await import('./views/saas-settings-models.js');
            app.appendChild(document.createElement('saas-settings-models'));
            return;
        }

        if (path === '/settings/channels' || path === '/agent/channels') {
            await import('./views/saas-settings-channels.js');
            app.appendChild(document.createElement('saas-settings-channels'));
            return;
        }

        if (path === '/settings') {
            await import('./views/saas-settings.js');
            app.appendChild(document.createElement('saas-settings'));
            return;
        }

        if (path === '/themes') {
            // Skins/theming is specified in SOMA-UI-SKINS-001 but NOT implemented:
            // appearance is compiled into component styles and the only runtime
            // control is light/dark polarity (services/theme-boot.ts). The old
            // behaviour silently redirected to /settings, which is not a themes
            // surface either. Per REQ-UIX-020: present-but-disabled with the
            // blocking reason — never a fake destination, never an omission.
            const notice = document.createElement('div');
            notice.setAttribute('data-surface', 'themes');
            notice.setAttribute('data-can-edit', 'false');
            notice.style.cssText =
                'max-width:640px;margin:15vh auto;padding:32px;text-align:center;' +
                'font-family:system-ui,sans-serif;color:#1a1a1a;';
            notice.innerHTML =
                '<h1 style="font-size:20px;margin:0 0 12px;">Skins</h1>' +
                '<p style="margin:0 0 8px;line-height:1.5;color:#444;">' +
                'This surface is not available on this deployment.</p>' +
                '<p disabled title="Blocked: skins are specified but not implemented." ' +
                'style="margin:0 0 16px;line-height:1.5;color:#666;">' +
                'Blocking reason: Capsule-owned skins are specified in SOMA-UI-SKINS-001 ' +
                'and not implemented yet. Appearance is compiled into component styles. ' +
                'The only appearance control available today is light / dark polarity.</p>' +
                '<button type="button" data-can-edit="true" ' +
                'style="padding:8px 16px;border:1px solid #ccc;border-radius:8px;background:#fff;cursor:pointer;">' +
                'Toggle light / dark</button>';
            const btn = notice.querySelector('button');
            btn?.addEventListener('click', () => {
                void import('./services/theme-boot.js').then((m) => m.toggleTheme());
            });
            app.appendChild(notice);
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



        // Default: chat workspace (never an admin dashboard as home)
        await import('./views/saas-chat.js');
        app.appendChild(document.createElement('saas-chat'));
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


