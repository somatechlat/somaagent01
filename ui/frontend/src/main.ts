/**
 * Eye of God - Main Entry Point
 * Per eye-of-god-uix design.md
 */

// Import components
import './components/index';

// Import views
import './views/index';

// Import styles
import './styles/tokens.css';

// Import the app shell
import { EogApp } from './views/eog-app';

// Create the app instance
const app = document.getElementById('app');
if (app) {
    app.innerHTML = '';
    const eogApp = document.createElement('eog-app');
    app.appendChild(eogApp);
}

// Log startup
console.log('🔮 Eye of God UIX v1.0.0 initialized');
console.log('📡 API: /api/v2/');
console.log('🔌 WebSocket: /ws/v2/');
