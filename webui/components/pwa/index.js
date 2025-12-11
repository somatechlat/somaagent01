/**
 * PWA Components Module
 * Exports PWA-related components and utilities
 * 
 * Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
 */

export { installPrompt } from './install-prompt.js';

/**
 * Initialize PWA functionality
 * Registers service worker and sets up install prompt
 */
export async function initPWA() {
  const results = {
    serviceWorker: false,
    installPrompt: false
  };
  
  // Register service worker
  if ('serviceWorker' in navigator) {
    try {
      // Service worker must be in the same directory or parent of its scope
      const registration = await navigator.serviceWorker.register('/static/js/sw.js', {
        scope: '/static/js/'
      });
      
      console.log('[PWA] Service worker registered:', registration.scope);
      results.serviceWorker = true;
      
      // Check for updates periodically
      setInterval(() => {
        registration.update();
      }, 60 * 60 * 1000); // Every hour
      
      // Handle updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              dispatchUpdateAvailable();
            }
          });
        }
      });
      
    } catch (error) {
      console.error('[PWA] Service worker registration failed:', error);
    }
  } else {
    console.warn('[PWA] Service workers not supported');
  }
  
  // Setup install prompt handling
  results.installPrompt = setupInstallPromptHandler();
  
  // Setup offline/online handlers
  setupNetworkHandlers();
  
  return results;
}

/**
 * Setup install prompt event handler
 */
function setupInstallPromptHandler() {
  let deferredPrompt = null;
  
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Expose install function globally
    window.pwaInstall = async () => {
      if (!deferredPrompt) return false;
      
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      deferredPrompt = null;
      
      return outcome === 'accepted';
    };
    
    // Dispatch event for UI components
    window.dispatchEvent(new CustomEvent('pwa:installable'));
  });
  
  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    window.pwaInstall = null;
    window.dispatchEvent(new CustomEvent('pwa:installed'));
  });
  
  return true;
}

/**
 * Setup network status handlers
 */
function setupNetworkHandlers() {
  const updateOnlineStatus = () => {
    const isOnline = navigator.onLine;
    document.body.classList.toggle('offline', !isOnline);
    
    window.dispatchEvent(new CustomEvent(isOnline ? 'app:online' : 'app:offline'));
  };
  
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  
  // Initial check
  updateOnlineStatus();
}

/**
 * Dispatch update available event
 */
function dispatchUpdateAvailable() {
  window.dispatchEvent(new CustomEvent('pwa:update-available'));
  
  // Show notification if Alpine store is available
  if (window.Alpine && window.Alpine.store('notifications')) {
    window.Alpine.store('notifications').add({
      type: 'info',
      message: 'A new version is available!',
      duration: 0,
      action: {
        label: 'Update',
        handler: () => {
          if (navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
          }
          window.location.reload();
        }
      }
    });
  }
}

/**
 * Check if app is running as installed PWA
 */
export function isInstalledPWA() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
}

/**
 * Check if device is iOS
 */
export function isIOS() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}

/**
 * Get iOS install instructions
 */
export function getIOSInstallInstructions() {
  return {
    steps: [
      'Tap the Share button in Safari',
      'Scroll down and tap "Add to Home Screen"',
      'Tap "Add" to install'
    ],
    note: 'iOS requires Safari to install web apps'
  };
}

/**
 * Clear all caches (for troubleshooting)
 */
export async function clearAllCaches() {
  if ('caches' in window) {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map(name => caches.delete(name)));
    console.log('[PWA] All caches cleared');
  }
  
  if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' });
  }
}

export default {
  initPWA,
  isInstalledPWA,
  isIOS,
  getIOSInstallInstructions,
  clearAllCaches
};
