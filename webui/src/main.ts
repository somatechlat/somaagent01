/**
 * Soma Sys Admin - Main Entry Point
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
            await import('./views/soma-login.js');
            app.appendChild(document.createElement('soma-login'));
            return;
        }

        if (path === '/register') {
            app.innerHTML = '';
            await import('./views/soma-register.js');
            app.appendChild(document.createElement('soma-register'));
            return;
        }

        if (path === '/forgot-password') {
            app.innerHTML = '';
            await import('./views/soma-forgot-password.js');
            app.appendChild(document.createElement('soma-forgot-password'));
            return;
        }

        // /reset-password and /verify-email are publicPaths but have no
        // screen and no mounted auth handler. Without a branch they fell
        // through to the chat workspace unauthenticated. Render an honest
        // unavailable notice instead of a fake product surface.
        if (path === '/reset-password' || path === '/verify-email') {
            app.innerHTML = '';
            const notice = document.createElement('div');
            notice.setAttribute('data-surface', path);
            notice.setAttribute('data-can-edit', 'false');
            notice.style.cssText =
                'max-width:640px;margin:15vh auto;padding:32px;text-align:center;' +
                'font-family:system-ui,sans-serif;color:#1a1a1a;';
            notice.innerHTML =
                '<h1 style="font-size:20px;margin:0 0 12px;">' +
                (path === '/reset-password' ? 'Reset password' : 'Verify email') +
                '</h1>' +
                '<p style="margin:0 0 8px;line-height:1.5;color:#444;">' +
                'This screen is present but disabled.</p>' +
                '<p disabled title="Blocked: no handler is mounted for this action." ' +
                'style="margin:0 0 16px;line-height:1.5;color:#666;">' +
                'Blocking reason: no ' +
                (path === '/reset-password' ? 'password-reset' : 'email-verification') +
                ' route is mounted in admin/auth/api.py (mounted: /token /refresh /me ' +
                '/logout /login /register /impersonate plus /sso /oauth /mfa). ' +
                'Contact your administrator.</p>' +
                '<a href="/login" style="color:#1a1a1a;">Back to login</a>';
            app.appendChild(notice);
            return;
        }

        // 2. Auth callback - handle OAuth response
        if (path === '/auth/callback') {
            await import('./views/soma-auth-callback.js');
            app.innerHTML = '';
            app.appendChild(document.createElement('soma-auth-callback'));
            return;
        }


        // Clear app content before rendering new view
        app.innerHTML = '';

        // Home `/` is the chat workspace (product hero).
        if (path === '/' || path === '' || path === '/index.html') {
            await import('./views/soma-chat.js');
            app.appendChild(document.createElement('soma-chat'));
            return;
        }

        // 3. AGENT ADMINISTRATION Routes
        //    No Soma or billing routes: this is a standalone agent, and the
        //    admin surface administers the agent only. See AGENT.md §1.1.
        if (path === '/soma/dashboard' || path === '/soma' || path === '/platform') {
            await import('./views/soma-agent-metrics.js');
            app.appendChild(document.createElement('soma-agent-metrics'));
            return;
        }

        if (path === '/platform/models') {
            // One model catalog: /llm/models on the Models settings screen.
            await import('./views/soma-settings-models.js');
            app.appendChild(document.createElement('soma-settings-models'));
            return;
        }

        // Rate Limits live on the Infrastructure dashboard (one surface).
        if (path === '/platform/infrastructure/redis/ratelimits' || path === '/platform/ratelimits') {
            await import('./views/soma-infrastructure-dashboard.js');
            const el = document.createElement('soma-infrastructure-dashboard') as HTMLElement & { activeTab?: string };
            el.activeTab = 'ratelimits';
            app.appendChild(el);
            return;
        }

        // Platform Integrations Dashboard
        if (path === '/platform/integrations' || path === '/soma/settings/integrations') {
            await import('./views/soma-integrations-dashboard.js');
            app.appendChild(document.createElement('soma-integrations-dashboard'));
            return;
        }

        // One roles screen: the catalogue plus the permission matrix as a
        // secondary pane (UI-S-23). Old matrix/permissions URLs land here.
        if (path === '/platform/roles'
            || path === '/platform/role-matrix'
            || path === '/soma/permissions' || path === '/platform/permissions') {
            await import('./views/soma-admin-roles-list.js');
            app.appendChild(document.createElement('soma-admin-roles-list'));
            return;
        }

        if (path === '/platform/api-keys') {
            await import('./views/soma-admin-api-keys.js');
            app.appendChild(document.createElement('soma-admin-api-keys'));
            return;
        }

        // Agent metrics
        if (path === '/admin/metrics') {
            await import('./views/soma-agent-metrics.js');
            app.appendChild(document.createElement('soma-agent-metrics'));
            return;
        }

        // Infrastructure Administration (Soma Platform Admin)
        if (path === '/platform/infrastructure' || path === '/soma/infrastructure') {
            await import('./views/soma-infrastructure-dashboard.js');
            app.appendChild(document.createElement('soma-infrastructure-dashboard'));
            return;
        }

        // Platform Metrics Dashboard
        if (path === '/platform/metrics' || path === '/soma/metrics') {
            await import('./views/platform-metrics-dashboard.js');
            app.appendChild(document.createElement('platform-metrics-dashboard'));
            return;
        }

        // Multimodal Settings (Agent Owner)
        if (path === '/settings/multimodal' || path === '/agent/multimodal') {
            await import('./views/soma-multimodal-settings.js');
            app.appendChild(document.createElement('soma-multimodal-settings'));
            return;
        }

        // Settings Configuration (uses SettingsForm pattern)
        if (path.startsWith('/platform/settings/')) {
            const entity = path.split('/').pop();
            if (!entity) {
                // No entity in the path: refuse rather than invent one.
                const notice = document.createElement('div');
                notice.textContent = 'Settings entity missing from the route.';
                app.appendChild(notice);
                return;
            }
            await import('./components/settings-form.js');
            const form = document.createElement('settings-form') as HTMLElement;
            form.setAttribute('entity', entity);
            app.appendChild(form);
            return;
        }

        // Entity Views (Users, Agents using EntityManager)
        if (path === '/admin/users') {
            await import('./views/soma-entity-views.js');
            app.appendChild(document.createElement('soma-users-view'));
            return;
        }

        // User Detail View
        if (path.match(/^\/admin\/users\/[^/]+$/)) {
            await import('./views/soma-user-detail.js');
            app.appendChild(document.createElement('soma-user-detail'));
            return;
        }

        // Platform Admin Profile
        if (path === '/platform/profile') {
            await import('./views/soma-platform-profile.js');
            app.appendChild(document.createElement('soma-platform-profile'));
            return;
        }

        // Agent admin profile
        if (path === '/admin/profile') {
            await import('./views/soma-platform-profile.js');
            app.appendChild(document.createElement('soma-platform-profile'));
            return;
        }

        // Personal User Profile
        if (path === '/profile') {
            await import('./views/soma-personal-profile.js');
            app.appendChild(document.createElement('soma-personal-profile'));
            return;
        }

        if (path === '/admin/agents') {
            await import('./views/soma-entity-views.js');
            app.appendChild(document.createElement('soma-agents-view'));
            return;
        }

        // Audit Log Dashboard
        if (path === '/platform/audit' || path === '/soma/audit') {
            await import('./views/soma-audit-dashboard.js');
            app.appendChild(document.createElement('soma-audit-dashboard'));
            return;
        }

        if (path === '/cognitive' || path === '/training') {
            await import('./views/soma-cognitive-panel.js');
            app.appendChild(document.createElement('soma-cognitive-panel'));
            return;
        }

        // Onboarding is the public register flow (one screen). Invite links
        // land there; there is no separate invitation router on this deployment.
        if (path.startsWith('/onboarding') || path.startsWith('/invite/')) {
            window.history.replaceState(null, '', '/register');
            renderRoute();
            return;
        }

        if (path === '/logout') {
            // SECURITY: the session lives in httpOnly cookies, so clearing
            // localStorage alone does not end it. Call the real logout first
            // (deletes the cookies), then clear client residue and leave.
            try {
                await apiClient.logout();
            } catch (err) {
                console.error('[Soma] server logout failed', err);
            }
            localStorage.removeItem('soma_auth_token');
            localStorage.removeItem('soma_user');
            window.location.href = '/login';
            return;
        }

        // MFA Setup
        if (path === '/mfa/setup' || path === '/settings/mfa') {
            await import('./views/soma-mfa-setup.js');
            app.appendChild(document.createElement('soma-mfa-setup'));
            return;
        }

        // One audit surface: the dashboard (stats + log + filters).
        if (path === '/audit' || path === '/admin/audit') {
            await import('./views/soma-audit-dashboard.js');
            app.appendChild(document.createElement('soma-audit-dashboard'));
            return;
        }



        if (path === '/chat' || path === '/chat/' || path.startsWith('/chat/') || path === '/soma/chat') {
            await import('./views/soma-chat.js');
            app.appendChild(document.createElement('soma-chat'));
            return;
        }

        // Workspace is the chat chrome (one chat surface).
        if (path === '/workspace') {
            await import('./views/soma-chat.js');
            app.appendChild(document.createElement('soma-chat'));
            return;
        }

        if (path === '/memory') {
            await import('./views/soma-memory-view.js');
            app.appendChild(document.createElement('soma-memory-view'));
            return;
        }

        if (path === '/settings/models' || path === '/agent/models') {
            await import('./views/soma-settings.js');
            const el = document.createElement('soma-settings') as HTMLElement & {
                activeTab?: string;
            };
            el.activeTab = 'models';
            app.appendChild(el);
            return;
        }

        if (path === '/settings/somabrain' || path === '/agent/somabrain') {
            await import('./views/soma-settings.js');
            const el = document.createElement('soma-settings') as HTMLElement & {
                activeTab?: string;
            };
            el.activeTab = 'somabrain';
            app.appendChild(el);
            return;
        }

        if (path === '/settings/channels' || path === '/agent/channels') {
            await import('./views/soma-settings.js');
            const el = document.createElement('soma-settings') as HTMLElement & {
                activeTab?: string;
            };
            el.activeTab = 'external';
            app.appendChild(el);
            return;
        }

        if (path === '/settings') {
            await import('./views/soma-settings.js');
            app.appendChild(document.createElement('soma-settings'));
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
            await import('./views/soma-voice-personas.js');
            app.appendChild(document.createElement('soma-voice-personas'));
            return;
        }

        if (path === '/voice/sessions' || path === '/platform/voice/sessions') {
            await import('./views/soma-voice-sessions.js');
            app.appendChild(document.createElement('soma-voice-sessions'));
            return;
        }

        if (path === '/voice/chat' || path === '/platform/voice/chat' || path === '/voice') {
            await import('./views/soma-voice-chat.js');
            app.appendChild(document.createElement('soma-voice-chat'));
            return;
        }



        // Default: chat workspace (never an admin dashboard as home)
        await import('./views/soma-chat.js');
        app.appendChild(document.createElement('soma-chat'));
    };

    // Initial Render
    renderRoute();

    // Event Listeners for SPA Navigation
    window.addEventListener('popstate', renderRoute);

    // Custom navigation event from components
    window.addEventListener('soma-navigate', ((e: CustomEvent) => {
        const route = e.detail.route;
        if (route) {
            window.history.pushState(null, '', route);
            renderRoute();
        }
    }) as EventListener);
}

// Log startup
console.log('[Soma] Soma Sys Admin v1.0.0 initialized');
console.log('[Soma] API: /api/v2/');
console.log('[Soma] WebSocket: /ws/v2/');


