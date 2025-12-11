/**
 * Offline Components Module
 * Exports offline indicator and related utilities
 * 
 * Requirements: 18.2
 */

export { offlineIndicator } from './offline-indicator.js';

/**
 * Register service worker and setup offline handling
 */
export async function initPWA() {
  if (!('serviceWorker' in navigator)) {
    console.warn('[PWA] Service workers not supported');
    return false;
  }
  
  try {
    const registration = await navigator.serviceWorker.register('/static/js/sw.js', {
      scope: '/static/'
    });
    
    console.log('[PWA] Service worker registered:', registration.scope);
    
    // Handle updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New version available
            showUpdateNotification();
          }
        });
      }
    });
    
    return true;
  } catch (error) {
    console.error('[PWA] Service worker registration failed:', error);
    return false;
  }
}

/**
 * Show notification when new version is available
 */
function showUpdateNotification() {
  if (window.Alpine && window.Alpine.store('notifications')) {
    window.Alpine.store('notifications').add({
      type: 'info',
      message: 'A new version is available. Refresh to update.',
      duration: 0,
      action: {
        label: 'Refresh',
        handler: () => window.location.reload()
      }
    });
  }
}

/**
 * Check if app can be installed (PWA install prompt)
 */
export function setupInstallPrompt() {
  let deferredPrompt = null;
  
  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67+ from automatically showing the prompt
    e.preventDefault();
    deferredPrompt = e;
    
    // Dispatch event for UI to show install button
    window.dispatchEvent(new CustomEvent('pwa:installable', { detail: { prompt: deferredPrompt } }));
  });
  
  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    window.dispatchEvent(new CustomEvent('pwa:installed'));
    
    if (window.Alpine && window.Alpine.store('notifications')) {
      window.Alpine.store('notifications').add({
        type: 'success',
        message: 'SomaAgent01 has been installed!',
        duration: 5000
      });
    }
  });
  
  return {
    canInstall: () => deferredPrompt !== null,
    install: async () => {
      if (!deferredPrompt) return false;
      
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      deferredPrompt = null;
      
      return outcome === 'accepted';
    }
  };
}

/**
 * Check if running as installed PWA
 */
export function isInstalledPWA() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
}

export default {
  initPWA,
  setupInstallPrompt,
  isInstalledPWA
};
