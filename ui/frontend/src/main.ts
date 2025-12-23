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
        if (!DEV_MODE && !token) {
            if (path !== '/login' && path !== '/auth/callback') {
                window.history.replaceState(null, '', '/login');
                renderRoute();
                return;
            }
            app.innerHTML = '';
            app.appendChild(document.createElement('eog-login'));
            return;
        }

        // 2. Auth callback - handle OAuth response
        if (path === '/auth/callback') {
            try {
                await import('./views/eog-auth-callback.js');
                app.innerHTML = '';
                app.appendChild(document.createElement('eog-auth-callback'));
            } catch (e) {
                console.log('Auth callback processed, redirecting...');
                window.history.replaceState(null, '', '/saas/dashboard');
                renderRoute();
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

        if (path === '/platform/roles') {
            await import('./views/saas-admin-roles-list.js');
            app.appendChild(document.createElement('saas-admin-roles-list'));
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

        if (path === '/saas/tenants' || path === '/platform/tenants') {
            await import('./views/saas-tenants.js');
            app.appendChild(document.createElement('saas-tenants'));
            return;
        }

        // 4. Legacy EOG Routes
        if (path === '/login') {
            if (token) {
                window.history.replaceState(null, '', '/saas/dashboard');
                renderRoute();
                return;
            }
            app.appendChild(document.createElement('eog-login'));
            return;
        }

        if (path === '/logout') {
            localStorage.removeItem('eog_auth_token');
            localStorage.removeItem('eog_user');
            window.location.href = '/login';
            return;
        }

        if (path === '/mode-select' || path === '/select-mode') {
            await import('./views/eog-mode-selection.js');
            app.appendChild(document.createElement('eog-mode-selection'));
            return;
        }

        if (path === '/chat') {
            try {
                await import('./views/eog-chat.js');
                app.appendChild(document.createElement('eog-chat'));
            } catch {
                app.appendChild(document.createElement('eog-app'));
            }
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
console.log('🚀 SaaS Sys Admin v1.0.0 initialized');
console.log('📡 API: /api/v2/');
console.log('🔌 WebSocket: /ws/v2/');
console.log('🔧 DEV_MODE:', DEV_MODE ? 'ON' : 'OFF');


