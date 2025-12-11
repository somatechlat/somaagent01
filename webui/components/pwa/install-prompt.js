/**
 * PWA Install Prompt Component
 * Shows install prompt on supported browsers
 * 
 * Requirements: 18.3, 18.4, 18.5
 */

export function installPrompt() {
  return {
    canInstall: false,
    isInstalled: false,
    showPrompt: false,
    deferredPrompt: null,
    
    init() {
      // Check if already installed
      this.isInstalled = this.checkIfInstalled();
      
      if (this.isInstalled) {
        console.log('[PWA] App is already installed');
        return;
      }
      
      // Listen for install prompt
      window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        this.deferredPrompt = e;
        this.canInstall = true;
        
        // Show prompt after a delay (don't interrupt user immediately)
        setTimeout(() => {
          if (!this.hasSeenPrompt()) {
            this.showPrompt = true;
          }
        }, 30000); // 30 seconds
      });
      
      // Listen for successful install
      window.addEventListener('appinstalled', () => {
        this.isInstalled = true;
        this.canInstall = false;
        this.showPrompt = false;
        this.deferredPrompt = null;
        
        // Track install
        console.log('[PWA] App installed successfully');
      });
      
      // Listen for custom events
      window.addEventListener('pwa:installable', (e) => {
        this.deferredPrompt = e.detail.prompt;
        this.canInstall = true;
      });
    },
    
    checkIfInstalled() {
      // Check display mode
      if (window.matchMedia('(display-mode: standalone)').matches) {
        return true;
      }
      
      // iOS Safari
      if (window.navigator.standalone === true) {
        return true;
      }
      
      // Check if launched from home screen (Android)
      if (document.referrer.includes('android-app://')) {
        return true;
      }
      
      return false;
    },
    
    hasSeenPrompt() {
      const lastSeen = localStorage.getItem('pwa-prompt-seen');
      if (!lastSeen) return false;
      
      // Don't show again for 7 days
      const sevenDays = 7 * 24 * 60 * 60 * 1000;
      return (Date.now() - parseInt(lastSeen)) < sevenDays;
    },
    
    markPromptSeen() {
      localStorage.setItem('pwa-prompt-seen', Date.now().toString());
    },
    
    async install() {
      if (!this.deferredPrompt) {
        console.warn('[PWA] No install prompt available');
        return false;
      }
      
      try {
        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        
        console.log('[PWA] Install prompt outcome:', outcome);
        
        this.deferredPrompt = null;
        this.showPrompt = false;
        this.markPromptSeen();
        
        if (outcome === 'accepted') {
          this.canInstall = false;
          return true;
        }
        
        return false;
      } catch (error) {
        console.error('[PWA] Install failed:', error);
        return false;
      }
    },
    
    dismiss() {
      this.showPrompt = false;
      this.markPromptSeen();
    },
    
    // For manual trigger from settings or menu
    showInstallOption() {
      if (this.canInstall) {
        this.showPrompt = true;
      }
    }
  };
}

// Register as Alpine component
if (window.Alpine) {
  window.Alpine.data('installPrompt', installPrompt);
}

export default installPrompt;
