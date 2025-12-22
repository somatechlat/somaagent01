/**
 * Eye of God - Main Entry Point
 * Per eye-of-god-uix design.md
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

    const path = window.location.pathname;

    // Show login page for /login route OR if not authenticated
    if (path === '/login' || path === '/auth/callback') {
        const loginPage = document.createElement('eog-login');
        app.appendChild(loginPage);
    } else {
        // Check for auth token
        const token = localStorage.getItem('eog_auth_token');
        if (!token && path !== '/') {
            // Redirect to login
            window.location.href = '/login';
        } else if (!token) {
            // Show login for root without token
            const loginPage = document.createElement('eog-login');
            app.appendChild(loginPage);
        } else {
            // Authenticated - show app
            const eogApp = document.createElement('eog-app');
            app.appendChild(eogApp);
        }
    }
}

// Log startup
console.log('🔮 Eye of God UIX v1.0.0 initialized');
console.log('📡 API: /api/v2/');
console.log('🔌 WebSocket: /ws/v2/');

