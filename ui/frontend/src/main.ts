/**
 * SaaS Sys Admin - Main Entry Point
 * Enterprise Platform UI
 * 
 * VIBE COMPLIANT:
 * - Real routing
 * - Login flow support
 */

// Import components
import './components/index';

// Import views
import './views/index';

// Import styles
import './styles/tokens.css';

// Import specific views
import { EogApp } from './views/eog-app';
import { EogLogin } from './views/eog-login';

// Routing logic
const app = document.getElementById('app');
if (app) {
    app.innerHTML = '';

    // Route handler
    const handleRoute = () => {
        const path = window.location.pathname;
        const token = localStorage.getItem('eog_auth_token');

        // 1. Unauthenticated -> Login
        if (!token) {
            if (path !== '/login' && path !== '/auth/callback') {
                window.location.href = '/login';
                return;
            }
            // Show Login
            app.innerHTML = '';
            app.appendChild(document.createElement('eog-login'));
            return;
        }

        // 2. Authenticated Routes
        app.innerHTML = '';

        if (path === '/login') {
            // Already logged in
            window.location.href = '/mode-select';
            return;
        }

        if (path === '/logout') {
            localStorage.removeItem('eog_auth_token');
            localStorage.removeItem('eog_user');
            window.location.href = '/login';
            return;
        }

        if (path === '/mode-select' || path === '/select-mode') {
            import('./views/eog-mode-selection.js').then(() => {
                app.appendChild(document.createElement('eog-mode-selection'));
            });
            return;
        }

        if (path === '/platform' || path === '/platform-dashboard') {
            import('./views/eog-platform-dashboard.js').then(() => {
                app.appendChild(document.createElement('eog-platform-dashboard'));
            });
            return;
        }

        if (path === '/chat') {
            import('./views/eog-chat.js').then(() => {
                app.appendChild(document.createElement('eog-chat'));
            }).catch(() => {
                // Fallback to app if chat not implemented
                app.appendChild(document.createElement('eog-app'));
            });
            return;
        }

        // Default App (Dashboard)
        app.appendChild(document.createElement('eog-app'));
    };

    handleRoute();
}

// Log startup
console.log('🚀 SaaS Sys Admin v1.0.0 initialized');
console.log('📡 API: /api/v2/');
console.log('🔌 WebSocket: /ws/v2/');

