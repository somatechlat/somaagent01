/**
 * Offline Indicator Component
 * Shows offline status banner when network is unavailable
 * 
 * Requirements: 18.2
 */

export function offlineIndicator() {
  return {
    isOffline: !navigator.onLine,
    showBanner: false,
    
    init() {
      // Listen for online/offline events
      window.addEventListener('online', () => this.handleOnline());
      window.addEventListener('offline', () => this.handleOffline());
      
      // Check initial state
      if (!navigator.onLine) {
        this.handleOffline();
      }
    },
    
    handleOffline() {
      this.isOffline = true;
      this.showBanner = true;
      
      // Dispatch custom event for other components
      window.dispatchEvent(new CustomEvent('app:offline'));
      
      // Show toast notification
      if (window.Alpine && window.Alpine.store('notifications')) {
        window.Alpine.store('notifications').add({
          type: 'warning',
          message: 'You are offline. Some features may be unavailable.',
          duration: 0, // Don't auto-dismiss
        });
      }
    },
    
    handleOnline() {
      this.isOffline = false;
      
      // Keep banner visible briefly to show reconnection
      setTimeout(() => {
        this.showBanner = false;
      }, 2000);
      
      // Dispatch custom event for other components
      window.dispatchEvent(new CustomEvent('app:online'));
      
      // Show toast notification
      if (window.Alpine && window.Alpine.store('notifications')) {
        window.Alpine.store('notifications').add({
          type: 'success',
          message: 'Back online!',
          duration: 3000,
        });
      }
    },
    
    dismissBanner() {
      this.showBanner = false;
    },
  };
}

// Register as Alpine component
if (window.Alpine) {
  window.Alpine.data('offlineIndicator', offlineIndicator);
}

export default offlineIndicator;
